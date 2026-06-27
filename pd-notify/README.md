# ProjectDiscovery Notify

**Notify** is an Apify Actor that wraps the open-source [`notify`](https://github.com/projectdiscovery/notify) CLI from [ProjectDiscovery](https://projectdiscovery.io). It **streams text or dataset records to Slack, Discord, Telegram, Email, Microsoft Teams, Google Chat, Pushover, Gotify, and custom webhooks** — turning any Apify run into a real-time notification step.

It is built to slot into larger **Apify pipelines via Apify tasks**: a scraping or monitoring Actor produces data, and this Actor fans that data out as notifications to your team's channels.

## What does ProjectDiscovery Notify do?

This Actor takes input text (typed directly or read from another Actor's dataset) and sends it to one or more notification providers you configure. Each line becomes its own message, or you can send everything as a single bulk message. Running it on the Apify platform gives you scheduling, API access, run history, and easy chaining with other Actors — no server to maintain.

## Why use ProjectDiscovery Notify?

- **Pipeline alerting** — notify your team when a scraper finds new results, a price changes, or a monitor detects something.
- **Multi-channel** — send to Slack, Discord, Telegram, Email, Teams, Google Chat, Pushover, Gotify, or any custom webhook from a single config.
- **Security recon workflows** — the classic ProjectDiscovery use case: pipe subdomain/vulnerability findings into your channels.
- **No infrastructure** — schedule it, trigger it from other Actors, or call it from the API.

## How to use ProjectDiscovery Notify

1. Open the Actor in the Apify Console.
2. Configure where to send: fill in a **quick-setup** field (Slack / Discord / Telegram), and/or paste a full **Advanced provider config (YAML)**. Both are merged.
3. Provide the **Text to send**, or point the Actor at a **Source dataset ID** produced by a previous run.
4. (Optional) Choose **bulk** mode, restrict to specific **providers** / **IDs**, set a **delay**, **rate limit**, or **message format**.
5. Click **Start**. The Actor sends the notifications and saves a run summary to the dataset.

### Chaining in a pipeline

Set **Source dataset ID** to the default dataset ID of an upstream Actor run (available from its run object / API). Use **Dataset fields** to pick which fields of each item become the notification line — e.g. `["url", "title"]` joined by the **Dataset field separator**. Leave **Dataset fields** empty to send each item as compact JSON.

## Input

You must configure **at least one provider** — via the quick-setup fields, the advanced YAML, or both.

| Field | Type | Description |
| --- | --- | --- |
| `slackWebhookUrl` | string (secret) | Quick setup: Slack incoming webhook URL. |
| `slackChannel` | string | Quick setup: optional Slack channel name. |
| `discordWebhookUrl` | string (secret) | Quick setup: Discord webhook URL. |
| `telegramApiKey` | string (secret) | Quick setup: Telegram bot token (needs chat ID). |
| `telegramChatId` | string | Quick setup: Telegram chat ID. |
| `providerConfigYaml` | string (secret) | Advanced: full notify `provider-config.yaml` (any provider, multiple entries). Merged with quick-setup fields. |
| `data` | string | Raw text; one notification per non-empty line. |
| `sourceDatasetId` | string | Apify dataset to read input items from. |
| `datasetFields` | array | Fields to extract per dataset item (empty = whole item as JSON). |
| `datasetFieldSeparator` | string | Separator used to join multiple fields. Default `" \| "`. |
| `providers` | array | Restrict to provider types (`-provider`), e.g. `slack`, `discord`. |
| `ids` | array | Restrict to provider entry IDs (`-id`). |
| `bulk` | boolean | Send as one chunked message instead of per line (`-bulk`). |
| `charLimit` | integer | Max characters per message (`-char-limit`, default 4000). |
| `delay` | integer | Seconds between notifications (`-delay`). |
| `rateLimit` | integer | Max requests per second (`-rate-limit`). |
| `msgFormat` | string | Custom format template, e.g. `Alert: {{data}}` (`-msg-format`). |
| `proxy` | string | HTTP/SOCKSv5 proxy (`-proxy`). |
| `verbose` | boolean | Verbose notify logging (`-verbose`). |

### Provider config example

```yaml
slack:
  - id: recon
    slack_channel: recon
    slack_username: notify
    slack_format: "{{data}}"
    slack_webhook_url: "https://hooks.slack.com/services/XXXX"

telegram:
  - id: tel
    telegram_api_key: "XXXX"
    telegram_chat_id: "XXXX"
    telegram_format: "{{data}}"
```

See the full provider reference: https://github.com/projectdiscovery/notify#provider-config

## Output

The Actor pushes a single summary record per run to the dataset:

```json
{
    "success": true,
    "exitCode": 0,
    "linesSent": 3,
    "bulk": false,
    "providers": ["slack"],
    "ids": [],
    "startedAt": "2026-06-27T12:00:00+00:00",
    "finishedAt": "2026-06-27T12:00:02+00:00",
    "stdout": "...",
    "stderr": ""
}
```

You can download the dataset in various formats such as JSON, HTML, CSV, or Excel.

### Data table

| Field | Description |
| --- | --- |
| `success` | Whether notify exited cleanly. |
| `exitCode` | Process exit code. |
| `linesSent` | Number of input lines processed. |
| `bulk` | Whether bulk mode was used. |
| `providers` / `ids` | Filters applied to the send. |
| `startedAt` / `finishedAt` | Run timestamps (UTC, ISO 8601). |
| `stdout` / `stderr` | Captured notify output. |

## Cost estimation

This Actor is lightweight — it only sends HTTP requests to your notification providers. Cost is driven almost entirely by run duration (compute units), which is typically seconds. Large bulk sends with a `delay` will run longer. There are no third-party API costs beyond what your own providers may charge.

## Tips

- Use **bulk** mode for large outputs to avoid flooding a channel with one message per line.
- Set a **delay** or **rate limit** if a provider throttles you.
- Use **IDs** to route different pipelines to different channels from one shared config.
- Keep your webhooks and tokens in **`providerConfigYaml`**, which is treated as a secret.

## FAQ and support

**Is the provider config stored securely?** The `providerConfigYaml` field is marked as a secret and is written to a temporary, restricted file inside the run, then deleted after notify finishes.

**Which providers are supported?** All providers supported by ProjectDiscovery `notify` (currently v1.0.7): Slack, Discord, Telegram, Pushover, SMTP/Email, Google Chat, Microsoft Teams, Gotify, and custom webhooks.

**Notifications failed — what now?** Check the `stderr` field in the dataset and the run log. Most failures are bad webhook URLs/tokens or provider rate limits.

For issues or feature requests, use the Actor's **Issues** tab. This Actor is a wrapper; the underlying tool is maintained by ProjectDiscovery.
