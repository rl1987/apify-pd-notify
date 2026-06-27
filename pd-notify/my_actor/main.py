"""Apify Actor that wraps the ProjectDiscovery `notify` CLI.

`notify` streams text (line by line or in bulk) to a variety of notification
platforms (Slack, Discord, Telegram, Email, Microsoft Teams, Google Chat,
Pushover, Gotify, custom webhooks, ...). This Actor is designed to be dropped
into larger Apify pipelines (via Apify tasks): a preceding Actor produces data,
and this Actor fans that data out as notifications.

See https://github.com/projectdiscovery/notify for the underlying tool.
"""

from __future__ import annotations

import asyncio
import json
import os
import tempfile
from datetime import datetime, timezone

import yaml
from apify import Actor, Event

NOTIFY_BIN = 'notify'


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _append_provider(config: dict, key: str, entry: dict) -> None:
    """Append a provider entry to the config, keeping each provider type a list."""
    existing = config.get(key)
    if existing is None:
        config[key] = [entry]
    elif isinstance(existing, list):
        existing.append(entry)
    else:
        # Tolerate a single-mapping form from raw YAML by promoting it to a list.
        config[key] = [existing, entry]


def _build_provider_config(actor_input: dict) -> str:
    """Merge the quick-setup provider fields with the raw YAML escape hatch.

    Returns the serialized provider-config.yaml content for the notify CLI.
    """
    raw = actor_input.get('providerConfigYaml') or ''
    if raw.strip():
        config = yaml.safe_load(raw)
        if config is None:
            config = {}
        if not isinstance(config, dict):
            raise ValueError('`providerConfigYaml` must be a YAML mapping of provider types.')
    else:
        config = {}

    slack_url = actor_input.get('slackWebhookUrl')
    if slack_url:
        entry = {'id': 'slack', 'slack_format': '{{data}}', 'slack_webhook_url': slack_url}
        if actor_input.get('slackChannel'):
            entry['slack_channel'] = actor_input['slackChannel']
        _append_provider(config, 'slack', entry)

    discord_url = actor_input.get('discordWebhookUrl')
    if discord_url:
        _append_provider(config, 'discord', {
            'id': 'discord',
            'discord_format': '{{data}}',
            'discord_webhook_url': discord_url,
        })

    telegram_key = actor_input.get('telegramApiKey')
    telegram_chat = actor_input.get('telegramChatId')
    if telegram_key or telegram_chat:
        if not (telegram_key and telegram_chat):
            raise ValueError('Both `telegramApiKey` and `telegramChatId` are required to use Telegram.')
        _append_provider(config, 'telegram', {
            'id': 'telegram',
            'telegram_format': '{{data}}',
            'telegram_api_key': telegram_key,
            'telegram_chat_id': telegram_chat,
        })

    if not config:
        raise ValueError(
            'No provider configured. Fill in a quick-setup provider field '
            '(Slack/Discord/Telegram) and/or `providerConfigYaml`.'
        )

    return yaml.safe_dump(config, sort_keys=False, default_flow_style=False)


def _format_item(item: dict, fields: list[str], separator: str) -> str:
    """Turn a single dataset item into one line of notification text."""
    if not fields:
        return json.dumps(item, ensure_ascii=False, separators=(',', ':'))

    parts: list[str] = []
    for field in fields:
        value = item.get(field)
        if value is None:
            parts.append('')
        elif isinstance(value, str):
            parts.append(value)
        else:
            parts.append(json.dumps(value, ensure_ascii=False))
    return separator.join(parts)


async def _collect_lines(actor_input: dict) -> list[str]:
    """Build the list of notification lines from direct text and/or a dataset."""
    lines: list[str] = []

    data = actor_input.get('data')
    if data:
        lines.extend(line for line in data.splitlines() if line.strip())

    source_dataset_id = actor_input.get('sourceDatasetId')
    if source_dataset_id:
        fields = actor_input.get('datasetFields') or []
        separator = actor_input.get('datasetFieldSeparator', ' | ')
        Actor.log.info('Reading input from source dataset %s', source_dataset_id)
        dataset = await Actor.open_dataset(id=source_dataset_id)
        count = 0
        async for item in dataset.iterate_items():
            line = _format_item(item, fields, separator)
            if line.strip():
                lines.append(line)
                count += 1
        Actor.log.info('Read %d item(s) from source dataset', count)

    return lines


def _build_command(actor_input: dict, provider_config_path: str, data_path: str) -> list[str]:
    """Assemble the notify command-line invocation from the Actor input."""
    # -duc disables the automatic update check (no GitHub calls at runtime),
    # -nc disables ANSI colors so the captured logs stay clean.
    cmd: list[str] = [
        NOTIFY_BIN,
        '-provider-config', provider_config_path,
        '-data', data_path,
        '-duc',
        '-nc',
    ]

    if actor_input.get('bulk'):
        cmd.append('-bulk')

    char_limit = actor_input.get('charLimit')
    if char_limit:
        cmd += ['-char-limit', str(char_limit)]

    delay = actor_input.get('delay')
    if delay:
        cmd += ['-delay', str(delay)]

    rate_limit = actor_input.get('rateLimit')
    if rate_limit:
        cmd += ['-rate-limit', str(rate_limit)]

    providers = actor_input.get('providers') or []
    if providers:
        cmd += ['-provider', ','.join(providers)]

    ids = actor_input.get('ids') or []
    if ids:
        cmd += ['-id', ','.join(ids)]

    msg_format = actor_input.get('msgFormat')
    if msg_format:
        cmd += ['-msg-format', msg_format]

    proxy = actor_input.get('proxy')
    if proxy:
        cmd += ['-proxy', proxy]

    if actor_input.get('verbose'):
        cmd.append('-verbose')

    return cmd


async def main() -> None:
    """Main entry point for the Apify Actor."""
    async with Actor:
        # Terminate quickly when the run is aborted by the user or the platform.
        async def on_aborting() -> None:
            await asyncio.sleep(1)
            await Actor.exit()

        Actor.on(Event.ABORTING, on_aborting)

        actor_input = await Actor.get_input() or {}

        provider_config = _build_provider_config(actor_input)

        lines = await _collect_lines(actor_input)
        if not lines:
            raise ValueError(
                'No input to send. Provide `data` text and/or a `sourceDatasetId` with items.'
            )

        Actor.log.info('Prepared %d line(s) to notify', len(lines))

        # Write provider config and data to temp files for the notify CLI.
        # The provider config holds secrets, so restrict its permissions.
        tmp_dir = tempfile.mkdtemp(prefix='pd-notify-')
        provider_config_path = os.path.join(tmp_dir, 'provider-config.yaml')
        data_path = os.path.join(tmp_dir, 'data.txt')

        with open(provider_config_path, 'w', encoding='utf-8') as fh:
            fh.write(provider_config)
        os.chmod(provider_config_path, 0o600)

        with open(data_path, 'w', encoding='utf-8') as fh:
            fh.write('\n'.join(lines) + '\n')

        cmd = _build_command(actor_input, provider_config_path, data_path)
        # Log the command without leaking the provider-config path contents.
        Actor.log.info('Running notify: %s', ' '.join(cmd))

        started_at = _now_iso()
        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout_b, stderr_b = await proc.communicate()
        finished_at = _now_iso()

        # Clean up the secret-bearing temp files as soon as notify is done.
        try:
            os.remove(provider_config_path)
            os.remove(data_path)
            os.rmdir(tmp_dir)
        except OSError:
            pass

        stdout = stdout_b.decode('utf-8', errors='replace').strip()
        stderr = stderr_b.decode('utf-8', errors='replace').strip()
        exit_code = proc.returncode or 0
        success = exit_code == 0

        if stdout:
            Actor.log.info('notify stdout:\n%s', stdout)
        if stderr:
            log = Actor.log.info if success else Actor.log.error
            log('notify stderr:\n%s', stderr)

        await Actor.push_data({
            'success': success,
            'exitCode': exit_code,
            'linesSent': len(lines),
            'bulk': bool(actor_input.get('bulk')),
            'providers': actor_input.get('providers') or [],
            'ids': actor_input.get('ids') or [],
            'charLimit': actor_input.get('charLimit'),
            'delay': actor_input.get('delay'),
            'rateLimit': actor_input.get('rateLimit'),
            'startedAt': started_at,
            'finishedAt': finished_at,
            'stdout': stdout,
            'stderr': stderr,
        })

        if not success:
            raise RuntimeError(f'notify exited with code {exit_code}. See stderr in the dataset/log.')

        Actor.log.info('Notifications sent successfully.')
