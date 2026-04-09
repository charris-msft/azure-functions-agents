# Daily Azure Report

A timer-triggered agent that lists Azure resources created or changed in the last 24 hours and emails a summary report. Uses a custom tool for querying Azure Resource Manager and the Office 365 connector for sending email.

## Features

- **Timer trigger** — runs daily at 15:00 UTC
- **Custom `azure_rest` tool** — makes authenticated ARM REST API calls using the function app's managed identity to list resources
- **Office 365 connector** — sends the report via email
- **Microsoft Learn MCP server** — gives the agent access to Azure documentation for looking up correct API paths and versions
- **`azure-resources` skill** — packages ARM REST API knowledge (paths, api-versions, tips) so the agent instructions can focus on the job, not the technical details
- **Variable substitution** — subscription ID and recipient email configured via environment variables, resolved at load time in the agent instructions

## Prerequisites

- [Azure Developer CLI (`azd`)](https://learn.microsoft.com/azure/developer/azure-developer-cli/install-azd)
- [Azure Functions Core Tools](https://learn.microsoft.com/azure/azure-functions/functions-run-local)
- A [GitHub Personal Access Token](../../README.md#github-token) with **Copilot** scope
- An Azure subscription

## Deploy

1. **Set environment variables:**

   ```bash
   cd samples/daily-azure-report
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

   This provisions all resources (Function App, storage, Office 365 API connection) and deploys the code. The subscription ID is automatically detected from the deployment. The managed identity is granted Reader access on the subscription for querying resources.

3. **Authenticate the Office 365 connector:**

   After deployment, the Office 365 connection is created but **not yet authenticated**. You need to authorize it manually:

   - Go to the [Azure portal](https://portal.azure.com)
   - Navigate to the resource group created by `azd` (named `rg-<environment-name>`)
   - Find the **API Connection** resource (`office365-...`)
   - Click **Edit API connection** in the left menu
   - Click **Authorize**, sign in with your Microsoft account, then click **Save**

   The `azure_rest` custom tool uses the function app's managed identity — no manual authentication needed.

4. **Verify:**

   The timer fires daily at 15:00 UTC. To test immediately, trigger the function with curl:

   ```bash
   # Get the master key
   az functionapp keys list -g <resource-group> -n <function-app-name> --query "masterKey" -o tsv

   # Trigger the function
   curl -X POST "https://<function-app-name>.azurewebsites.net/admin/functions/daily_azure_report_agent" \
     -H "x-functions-key: <master-key>" \
     -H "Content-Type: application/json" \
     -d '{}'
   ```

## How It Works

- [`daily_azure_report.agent.md`](src/daily_azure_report.agent.md) defines the agent with a timer trigger, a custom tool, Office 365 connector tools, and an external MCP server
- [`tools/azure_rest.py`](src/tools/azure_rest.py) is a custom tool that makes authenticated requests to the Azure Resource Manager REST API using the function app's managed identity. It accepts any ARM API path and HTTP method — RBAC on the identity controls what operations are allowed.
- [`mcp.json`](src/mcp.json) configures the Microsoft Learn MCP server, giving the agent access to Azure documentation for looking up correct API paths and versions.
- [`skills/azure-resources/SKILL.md`](src/skills/azure-resources/SKILL.md) packages ARM REST API knowledge — common paths, api-versions, and usage tips — so the agent instructions can stay focused on the task rather than implementation details.
- The `tools_from_connections` frontmatter references the Office 365 API Connection. At runtime, the framework discovers all available actions on the connector and exposes them as tools the agent can call.
- When the timer fires, the agent:
  1. Calls the `azure_rest` tool to list resources in the subscription
  2. Filters for resources created or modified in the last 24 hours
  3. Formats a summary report as an HTML email
  4. Sends the report to the configured recipient via the Office 365 connector
- `$SUBSCRIPTION_ID` and `$TO_EMAIL` in the agent instructions are replaced with actual values at load time (via environment variable substitution)
- `SUBSCRIPTION_ID` is automatically set from the deployment subscription — no manual input needed
