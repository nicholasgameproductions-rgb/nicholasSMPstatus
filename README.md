# NicholasSMP Discord Status (GitHub Actions)

No local installation and no paid promotional Discord bot. Uses the TopEaglerServers public status API and your Discord webhook.

## Setup
1. In Discord, create a **text channel** `#server-status`. Open Edit Channel > Integrations > Webhooks > New Webhook. Name it NicholasSMP Status, then copy the webhook URL. **Keep this secret.**
2. On GitHub create a **private** repository named `nicholassmp-status` (with a README or empty). If empty, create the README to initialize the default branch.
3. Upload `status.py` to the repository root. Create `.github/workflows/status.yml` with the included file's contents. The easiest way to do this is GitHub's **Add file > Create new file** and use the full path for the workflow file.
4. Go to repository **Settings > Secrets and variables > Actions > New repository secret**. Name: `DISCORD_WEBHOOK_URL`. Value: your webhook URL.
5. Go to **Actions > NicholasSMP Discord Status > Run workflow**. Open the latest run, click **update**, and expand **Update Discord embed**. It prints `MESSAGE ID: <number>`. The embed should now be in Discord.
6. Under **Settings > Secrets and variables > Actions**, create a second repository secret `DISCORD_MESSAGE_ID` with exactly that number. This is essential: subsequent runs will **edit** the original message rather than posting new ones.
7. Optionally run the workflow again to test. The scheduled workflow runs roughly every five minutes; GitHub may delay runs, and scheduled workflows on inactive public repos may be disabled.

## Troubleshooting
- Wrong message / 404: verify `DISCORD_MESSAGE_ID`, and ensure the webhook still exists and the message was not deleted.
- No messages: check the Actions run logs and verify webhook URL is copied in full.
- Yellow `STATUS UNAVAILABLE`: API may be down or use a different response shape; the script doesn't equate API failure with server downtime.
- If a new duplicate appears, `DISCORD_MESSAGE_ID` was missing when that run started. Set it and delete extras from Discord.
- Never paste your webhook URL into `status.py`, a workflow file, screenshots, or public chat. Rotate the webhook if exposed.

## Files
- `status.py`: fetches and formats server status and creates/edits a Discord webhook message.
- `.github/workflows/status.yml`: runs the Python script on GitHub Actions.

The monitor only knows the status information made available by the third-party status API. CPU and RAM readings from your host dashboard are not accessible with this API.
