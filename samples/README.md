# Samples

Each subdirectory is a standalone Azure Functions app deployable via `azd up`.

## Structure

Every sample follows the same layout:

```
sample-name/
├── azure.yaml
├── README.md
├── infra/
│   ├── main.bicep
│   └── main.parameters.json
└── src/
    ├── function_app.py
    ├── host.json
    ├── requirements.txt
    └── main.agent.md
```

- **`requirements.txt`** — installs `copilot-functions` from a GitHub release `.whl`.
- **`function_app.py`** — minimal entry point:
  ```python
  from copilot_functions import create_function_app

  app = create_function_app()
  ```
- **`main.agent.md`** — the agent definition (instructions, tool config, triggers).
- **`infra/`** — Bicep templates for provisioning Azure resources.

## Running a Sample

```bash
cd samples/<sample-name>
azd up
```

See each sample's `README.md` for prerequisites and configuration details.
