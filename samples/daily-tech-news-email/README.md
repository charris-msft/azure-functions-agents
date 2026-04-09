# Daily Tech News Email

A timer-triggered agent that fetches the day's top tech news headlines, summarizes them, and emails a digest using the Office 365 connector.

## Features

- **Timer trigger** — runs daily at 15:00 UTC
- **Code execution** — uses ACA Dynamic Sessions to fetch tech news from public RSS feeds and Hacker News
- **Office 365 connector** — sends the email via an Azure API Connection
- **Variable substitution** — recipient email address configured via `$TO_EMAIL` environment variable, resolved at load time in the agent instructions

## Prerequisites

- [Azure Developer CLI (`azd`)](https://learn.microsoft.com/azure/developer/azure-developer-cli/install-azd)
- [Azure Functions Core Tools](https://learn.microsoft.com/azure/azure-functions/functions-run-local)
- A [GitHub Personal Access Token](../../README.md#github-token) with **Copilot** scope
- An Azure subscription

## Deploy

1. **Set environment variables:**

   ```bash
   cd samples/daily-tech-news-email
   azd init
   azd env set GITHUB_TOKEN <your-github-pat>
   azd env set TO_EMAIL <recipient@example.com>
   ```

   Optional:

   ```bash
   azd env set COPILOT_MODEL claude-opus-4.6     # default
   ```

2. **Deploy to Azure:**

   ```bash
   azd up
   ```

   This provisions all resources (Function App, storage, ACA session pool, Office 365 API connection) and deploys the code.

3. **Authenticate the Office 365 connector:**

   After deployment, the Office 365 connection is created but **not yet authenticated**. You need to authorize it manually:

   - Go to the [Azure portal](https://portal.azure.com)
   - Navigate to the resource group created by `azd` (named `rg-<environment-name>`)
   - Find the **API Connection** resource (named `office365-...`)
   - Click **Edit API connection** in the left menu
   - Click **Authorize**, sign in with your Microsoft account, then click **Save**

4. **Verify:**

   The timer fires daily at 15:00 UTC. To test immediately, trigger the function with curl:

   ```bash
   # Get the master key
   az functionapp keys list -g <resource-group> -n <function-app-name> --query "masterKey" -o tsv

   # Trigger the function
   curl -X POST "https://<function-app-name>.azurewebsites.net/admin/functions/daily_tech_news_agent" \
     -H "x-functions-key: <master-key>" \
     -H "Content-Type: application/json" \
     -d '{}'
   ```

## How It Works

- [`daily_tech_news.agent.md`](src/daily_tech_news.agent.md) defines the agent with a timer trigger, code execution sandbox, and Office 365 connector tools
- The `tools_from_connections` frontmatter references the Office 365 API Connection. At runtime, the framework discovers **all available actions** on the connector (send email, manage contacts, calendar operations, etc.) and exposes them as tools the agent can call. This agent uses the send email action, but any connector action is available without additional configuration.
- When the timer fires, the agent:
  1. Uses `execute_python` to fetch tech news from public RSS feeds and Hacker News
  2. Summarizes the top stories into an HTML email
  3. Calls the Office 365 send email tool to deliver the summary to the configured recipient
- The `$TO_EMAIL` variable in the agent instructions is replaced with the actual email address at load time (via environment variable substitution)
