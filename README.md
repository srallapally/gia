# GIA - Governance Identity API Client

`gia` is a Python client for the Governance Identity API (IGA) in PingOne Advanced Identity Cloud. It provides both a thin REST client wrapper for the `/governance/application` endpoints and a high-level builder for managing disconnected applications.

## Features

- **OAuth2 Authentication**: Automatic token management using client credentials.
- **Auto-Pagination**: Seamlessly fetch all results from paginated endpoints.
- **Disconnected Applications**: High-level template builder for creating and updating disconnected applications.
- **File Uploads**: Easy CSV upload support for disconnected data (accounts, resources).
- **Retry Logic**: Built-in retries for transient network errors and rate limiting.

## Installation

```bash
# From source (development)
pip install -e .
```

## Quick Start

### Thin REST Client

The `IGAClient` provides direct access to the application endpoints.

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

# Get a specific application
app = client.applications.get_application("abc-123")
```

### Disconnected Application Builder

The `DisconnectedApplication` class provides a declarative way to define and "push" an application configuration to PingOne IGA.

```python
from gia import IGAClient, DisconnectedApplication

# Define the application structure
app = DisconnectedApplication(
    name="Corporate SAP", 
    description="Main SAP HR system"
)

# Add object types
app.add_object_type(
    id="__ACCOUNT__", 
    type="account", 
    properties={"email": {"type": "string"}}
)

# Attach a CSV file for upload
app.add_file_upload("users.csv", "__ACCOUNT__")

# Initialize client
client = IGAClient(...)

# Push to IGA (finds existing application by name or creates a new one)
result = app.push(client, upsert=True)
print(f"Application ID: {result.application_id}")
```

## Project Structure

- `gia/client.py`: Core `IGAClient` with HTTP helper methods.
- `gia/applications.py`: Wrappers for `/governance/application` endpoints.
- `gia/templates.py`: `DisconnectedApplication` builder and CSV upload logic.
- `gia/auth.py`: OAuth2 Client Credentials implementation.
- `gia/exceptions.py`: Custom exception classes.

## Development

### Running Tests

```bash
pip install -e ".[dev]"
pytest
```
