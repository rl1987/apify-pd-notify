# ProjectDiscovery Notify – Send Slack, Discord & Telegram Notifications from Apify

**Send instant notifications to Slack, Discord, Telegram, Email, Microsoft Teams, Google Chat, Pushover, Gotify, and custom webhooks — straight from your Apify runs.** ProjectDiscovery Notify turns any scraper, monitor, or data pipeline into a **real-time alerting system**, with no servers, cron jobs, or glue code to maintain.

It wraps the popular open-source [`notify`](https://github.com/projectdiscovery/notify) CLI from [ProjectDiscovery](https://projectdiscovery.io) and makes it a first-class, **chainable Apify Actor**: a scraping or monitoring Actor produces data, and this Actor **fans that data out as notifications** to all your team's channels at once.

> 💬 **One Actor, every channel.** Configure once, deliver everywhere. Perfect for price-drop alerts, new-listing monitors, security recon findings, uptime checks, lead notifications, and any "tell me the moment something changes" workflow.

## What does ProjectDiscovery Notify do?

ProjectDiscovery Notify takes input text — typed directly **or read automatically from another Actor's dataset** — and delivers it to one or more notification channels you configure. Each line can become its own message, or you can send everything as a single **bulk** message.

Because it runs on the Apify platform, you get **scheduling, a REST API, run history, secret-encrypted credentials, proxy support, and effortless chaining** with thousands of other Actors — without running any infrastructure yourself.

## Why use ProjectDiscovery Notify?

- 🔔 **Real-time alerting for any pipeline** — get pinged the moment a scraper finds new results, a price changes, a competitor updates, or a monitor trips.
- 📡 **Multi-channel from one config** — Slack, Discord, Telegram, Email (SMTP), Microsoft Teams, Google Chat, Pushover, Gotify, or any custom webhook.
- 🔗 **Built for chaining** — read straight from an upstream Actor's dataset, so you can wire `scraper → transform → notify` in minutes.
- 🛡️ **Security & recon ready** — the classic ProjectDiscovery use case: pipe subdomain, vulnerability, or asset-discovery findings to your channels.
- 🔒 **Secrets stay secret** — webhook URLs and bot tokens are stored as encrypted Apify secrets.
- ⚡ **Zero infrastructure** — schedule it, trigger it from other Actors, or call it from the API.

## How to use ProjectDiscovery Notify to send notifications

1. Open the Actor in the Apify Console and click **Try for free**.
2. **Choose where to send.** Fill in a **quick-setup** field (Slack / Discord / Telegram), and/or paste a full **Advanced provider config (YAML)**. Both are merged, so you can mix channels freely.
3. **Provide the content.** Type **Text to send**, or point the Actor at a **Source dataset ID** from a previous run.
4. **(Optional) tune delivery** — enable **bulk** mode, restrict to specific **providers**/**IDs**, add a **delay**, **rate limit**, or a custom **message format** like `🚨 Alert: {{data}}`.
5. Click **Start**. The Actor delivers your notifications and saves a run summary to the dataset.

### How to send Slack / Discord / Telegram notifications (quick start)

- **Slack:** paste your [incoming webhook URL](https://api.slack.com/messaging/webhooks) into `slackWebhookUrl`.
- **Discord:** paste a [channel webhook URL](https://support.discord.com/hc/en-us/articles/228383668) into `discordWebhookUrl`.
- **Telegram:** create a bot with [@BotFather](https://core.telegram.org/bots#botfather), then set `telegramApiKey` (the bot token) and `telegramChatId`.

### Build a notification pipeline (chaining Actors)

This is where ProjectDiscovery Notify shines. Set **Source dataset ID** to the default dataset ID of an upstream Actor run, and use **Dataset fields** to choose which fields of each item become the notification line — e.g. `["title", "price", "url"]` joined by the **Dataset field separator**. Leave **Dataset fields** empty to send each item as compact JSON.

Using Apify **integrations/webhooks**, you can fire this automatically: when your scraper finishes, it triggers Notify with `{{resource.defaultDatasetId}}`, turning any scrape into an alert — `scrape → format → notify`, fully hands-off.

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
| `sourceDatasetId` | string | Apify dataset to read input items from (for pipeline chaining). |
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

### Provider config example (advanced YAML)

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
    "skipped": false,
    "sendErrors": [],
    "exitCode": 0,
    "linesSent": 3,
    "bulk": true,
    "providers": ["telegram"],
    "ids": [],
    "startedAt": "2026-06-27T12:00:00+00:00",
    "finishedAt": "2026-06-27T12:00:02+00:00",
    "stdout": "...",
    "stderr": ""
}
```

You can download the dataset in various formats such as **JSON, HTML, CSV, or Excel**, or access it via the Apify API.

### Data table

| Field | Description |
| --- | --- |
| `success` | Whether all notifications were delivered. |
| `skipped` | `true` when there was no input to send (a no-op run). |
| `sendErrors` | List of delivery errors reported by notify (empty on success). |
| `exitCode` | Process exit code. |
| `linesSent` | Number of input lines processed. |
| `bulk` | Whether bulk mode was used. |
| `providers` / `ids` | Filters applied to the send. |
| `startedAt` / `finishedAt` | Run timestamps (UTC, ISO 8601). |
| `stdout` / `stderr` | Captured notify output. |

## Pricing — how much does it cost to send notifications?

ProjectDiscovery Notify uses simple, predictable **pay-per-event** pricing:

| Event | Price |
| --- | --- |
| **Notification sent** (per run that successfully delivers ≥ 1 notification) | **$0.01** |

- ✅ **You only pay for delivered value.** Runs that have **nothing to send** (no new data) or that **fail to deliver** are **never charged**.
- 💸 **Bulk-friendly.** In bulk mode, an entire batch (e.g. all new matches in one cycle) is one message and one $0.01 charge — so a monitor that runs every 15 minutes but only alerts occasionally costs almost nothing.
- 🧾 Platform usage (compute/proxy) is billed at cost on top of the event price. This Actor is intentionally lightweight (256 MB, runs in seconds), so usage cost is minimal.

> **Example:** A scheduled monitor that checks every 15 minutes and sends an alert on ~10 cycles per day costs about **$0.10/day** in event charges.

New to Apify? The **free tier** includes monthly usage credits, so you can try ProjectDiscovery Notify at no cost.

## Tips & advanced options

- Use **bulk** mode for large outputs to avoid flooding a channel with one message per line (and to minimize cost).
- Set a **delay** or **rate limit** if a provider throttles you.
- Use **IDs** to route different pipelines to different channels from one shared config.
- Paste credentials carefully — leading/trailing whitespace is stripped automatically, but a wrong/revoked token will surface as a delivery error in `sendErrors`.

## FAQ, legality, and support

**Are my webhook URLs and tokens stored securely?** Yes. Credential fields are marked as Apify **secrets** (encrypted at rest) and are written to a temporary, restricted file inside the run, then deleted after notify finishes.

**Which providers are supported?** All providers supported by ProjectDiscovery `notify` (currently v1.0.7): **Slack, Discord, Telegram, Pushover, SMTP/Email, Google Chat, Microsoft Teams, Gotify, and custom webhooks.**

**Will I be charged if there's nothing to send?** No. Empty/no-op runs and failed deliveries are not billed for the notification event.

**A notification failed — what now?** Check the `sendErrors` field in the dataset and the run log. Most failures are bad/revoked webhook URLs or bot tokens, an incorrect chat ID, or provider rate limits. (Telegram `Unauthorized` means an invalid bot token; "chat not found" means a wrong chat ID.)

**Is this legal?** This Actor only delivers messages to channels **you** own and configure. You are responsible for the content you send and for complying with each provider's terms of service and anti-spam rules.

For issues or feature requests, use the Actor's **Issues** tab. This Actor is a wrapper around the open-source `notify` tool, which is maintained by ProjectDiscovery.
