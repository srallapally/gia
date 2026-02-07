# GIA - Governance Identity API Client

`gia` is a comprehensive toolkit for interacting with the PingOne Advanced Identity Cloud Governance (IGA) API. It provides a powerful Python library for programmatic access and a feature-rich CLI for manual or scripted management of Governance applications.

## Key Features

- **OAuth2 Authentication**: Automatic token management using client credentials.
- **Python Library**: High-level and low-level interfaces for IGA applications and data.
- **CLI Tool**: Full command-line interface for application management and data loading.
- **Disconnected Applications**: Declarative way to define and manage disconnected applications.
- **CSV Data Loading**: Seamlessly upload and monitor CSV data for accounts and resources.
- **Pagination & Retries**: Built-in handling for large datasets and transient network errors.

## Installation

### Python Library
```bash
# From source
pip install .

# For development
pip install -e ".[dev]"
```

### CLI Tool
The CLI is automatically installed as `gia` when you install the package.

```bash
# Verify installation
gia --version
```

---

## CLI Usage

The GIA CLI allows you to manage applications and data directly from your terminal.

### 1. Configuration
Set up your connection to PingOne IGA:
```bash
gia configure
```
You will be prompted for your Tenant URL, Client ID, Client Secret, and Token Endpoint. Profiles are supported via the `--profile` flag.

### 2. Application Management
```bash
# List applications
gia app list

# Create an application from a YAML config
gia app create app-config.yaml

# Get application details and export to YAML
gia app get <app-id> --export app.yaml
```

### 3. Data Loading
```bash
# Load CSV data to an application
gia data load <app-id> users.csv --type __ACCOUNT__

# Monitor upload status
gia data status <app-id> <upload-id>
```

For more detailed CLI information, see [CLI-README.md](CLI-README.md).

---

## Python Library Usage

The `gia` package offers two main ways to interact with the API.

### IGAClient (REST Wrapper)
`IGAClient` provides direct access to the `/governance/application` endpoints.

```python
from gia import IGAClient

client = IGAClient(
    base_url="https://tenant.forgeblocks.com",
    client_id="my-client-id",
    client_secret="my-secret",
    token_endpoint="https://tenant.forgeblocks.com/am/oauth2/access_token",
)

# List all applications
apps = client.applications.list_applications()
for app in apps:
    print(f"{app['id']}: {app['name']}")
```

### DisconnectedApplication (High-Level Builder)
Declaratively define an application and its schema, then "push" it to IGA.

```python
from gia import IGAClient, DisconnectedApplication

# Define the application structure
app = DisconnectedApplication(
    name="Corporate SAP", 
    description="Main SAP HR system"
)

# Add object types and schema
app.add_object_type(
    id="__ACCOUNT__", 
    type="account", 
    properties={"email": {"type": "string"}}
)

# Attach a CSV file for upload
app.add_file_upload("users.csv", "__ACCOUNT__")

# Initialize client and push
client = IGAClient(...)
result = app.push(client, upsert=True)
print(f"Application ID: {result.application_id}")
```

---

## Project Structure

- `gia/`: Core Python library.
    - `client.py`: Base HTTP client and pagination logic.
    - `applications.py`: REST wrappers for application endpoints.
    - `templates.py`: Disconnected application builder.
    - `auth.py`: OAuth2 authentication.
- `gia_cli/`: CLI implementation using Click.
- `examples/`: Sample configuration and data files.
- `tests/`: Comprehensive test suite.

## Documentation

- [CLI-README.md](CLI-README.md) - Full CLI command reference.
- [QUICK-START.md](QUICK-START.md) - Get up and running in minutes.
- [DEPLOYMENT.md](DEPLOYMENT.md) - Building and distribution guide.
- [IMPLEMENTATION.md](IMPLEMENTATION.md) - Technical architecture details.

## Development

### Running Tests
```bash
pytest
```

## License
MIT
