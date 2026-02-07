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

### Option 1: Binary Installation (Mac Users - Recommended)

**No Python required!** Download and install the standalone binary.

#### Step 1: Download the GIA binary

Visit the release page:
**https://github.com/srallapally/gia/releases/tag/early-access**

Or download directly from terminal:
```bash
curl -L -o gia https://github.com/srallapally/gia/releases/download/early-access/gia
```

#### Step 2: Make it executable and install

```bash
chmod +x gia
sudo mv gia /usr/local/bin/
```

#### Step 3: Verify installation

```bash
gia --version
```

#### macOS Security Note

If macOS blocks the binary with "cannot be opened because it is from an unidentified developer":

**Option A: Remove quarantine attribute**
```bash
sudo xattr -d com.apple.quarantine /usr/local/bin/gia
```

**Option B: Allow via System Preferences**
1. Try to run `gia --help`
2. Go to **System Preferences → Security & Privacy**
3. Click **"Allow Anyway"**
4. Run `gia --help` again and click **"Open"**

### Option 2: Python Library Installation

For developers who want to use GIA as a Python library:

```bash
# From source
pip install .

# For development
pip install -e ".[dev]"
```

The CLI is automatically installed as `gia` when you install the package.

```bash
# Verify installation
gia --version
```

---

## Getting Started (5 minutes)

### 1. Configure your credentials

```bash
gia configure
```

You'll be prompted for:
- **Base URL**: Your PingOne tenant URL (e.g., `https://tenant.forgeblocks.com`)
- **Client ID**: Your OAuth2 client ID
- **Client Secret**: Your OAuth2 client secret
- **Token Endpoint**: (auto-suggested, just press Enter)
- **Scopes**: (optional, just press Enter to skip)

### 2. Test the connection

```bash
gia app list
```

This should display your existing applications.

### 3. Create your first application

**Interactive mode:**
```bash
gia app create --interactive
```

**From a config file:**

Create `my-app.yaml`:
```yaml
name: "Test Application"
description: "My first GIA app"

object_types:
  __ACCOUNT__:
    type: account
    properties:
      email: {type: string}
      firstName: {type: string}
      lastName: {type: string}
```

Then run:
```bash
gia app create my-app.yaml
```

### 4. Load data

```bash
gia data load <app-id> users.csv --type __ACCOUNT__
gia data status <app-id> <upload-id>
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

---

## Troubleshooting

### Command not found: gia
**Solution:** Make sure you ran `sudo mv gia /usr/local/bin/`

### Permission denied when running gia
**Solution:** Run `chmod +x /usr/local/bin/gia`

### "gia" is damaged and can't be opened (macOS)
**Solution:** Remove the quarantine attribute:
```bash
sudo xattr -d com.apple.quarantine /usr/local/bin/gia
```

### Authentication fails
**Solution:**
1. Verify your credentials are correct
2. Reconfigure: `gia configure`
3. Check your config: `cat ~/.gia/config.yaml`

### Upload failures
**Solution:** View detailed errors:
```bash
gia data failures <app-id> <upload-id>
gia data failures <app-id> <upload-id> --export errors.csv
```

---

## Uninstall

```bash
# Remove binary
sudo rm /usr/local/bin/gia

# Remove configuration
rm -rf ~/.gia
```

---

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
