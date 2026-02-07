# GIA CLI - Governance Identity API Command Line Interface

A command-line tool for managing applications in PingOne Advanced Identity Cloud's Governance (IGA) service.

## Installation

### Via Homebrew (Recommended)

```bash
# Add the tap
brew tap pingidentity/tap

# Install GIA CLI
brew install gia

# Verify installation
gia --version
```

### Manual Installation

Download the latest binary from [Releases](https://github.com/pingidentity/gia/releases):

```bash
# Download and install
curl -L -o gia https://github.com/pingidentity/gia/releases/latest/download/gia
chmod +x gia
sudo mv gia /usr/local/bin/

# Verify
gia --version
```

## Quick Start

### 1. Configure Credentials

```bash
gia configure
```

You'll be prompted for:
- **Base URL**: Your PingOne tenant URL (e.g., `https://tenant.forgeblocks.com`)
- **Client ID**: OAuth2 client ID
- **Client Secret**: OAuth2 client secret  
- **Token Endpoint**: OAuth2 token URL (auto-suggested)

Credentials are stored securely in `~/.gia/config.yaml` with restrictive permissions.

### 2. Create an Application

#### From YAML Config

```bash
gia app create app-config.yaml
```

#### Interactive Mode

```bash
gia app create --interactive
```

### 3. Load Data

```bash
gia data load <app-id> accounts.csv --type __ACCOUNT__
```

## Command Reference

### Application Management

#### List Applications

```bash
gia app list
gia app list --format json    # JSON output
gia app list --format yaml    # YAML output
```

#### Get Application Details

```bash
gia app get <app-id>
gia app get <app-id> --export app.yaml    # Export to file
```

#### Create Application

```bash
# From YAML file
gia app create app-config.yaml

# Interactive mode
gia app create --interactive
```

#### Update Application

```bash
gia app update <app-id> app-config.yaml
```

#### Delete Application

```bash
gia app delete <app-id>
gia app delete <app-id> --yes    # Skip confirmation
```

### Object Type Management

#### Add Object Type

```bash
gia object add <app-id> object-config.yaml
```

#### Update Object Type

```bash
gia object update <app-id> <type-id> object-config.yaml
```

#### Delete Object Type

```bash
gia object delete <app-id> <type-id>
gia object delete <app-id> <type-id> --yes    # Skip confirmation
```

### Data Loading & Monitoring

#### Upload CSV Data

```bash
gia data load <app-id> data.csv --type __ACCOUNT__
```

Returns an upload ID for tracking progress.

#### Check Upload Status

```bash
gia data status <app-id> <upload-id>
gia data status <app-id> <upload-id> --format json
```

#### View Upload Failures

```bash
# Display failures
gia data failures <app-id> <upload-id>

# Export failures to CSV
gia data failures <app-id> <upload-id> --export errors.csv
```

## Configuration Files

### Application Config (`app-config.yaml`)

```yaml
name: "Corporate SAP"
description: "Main SAP HR system"

object_types:
  __ACCOUNT__:
    type: account
    properties:
      email: {type: string}
      firstName: {type: string}
      lastName: {type: string}
      department: {type: string}
  
  __GROUP__:
    type: group
    properties:
      name: {type: string}
      description: {type: string}
```

See `examples/app-config.yaml` for a complete example.

### Object Type Config (`object-config.yaml`)

```yaml
id: "__RESOURCE__"
type: resource
properties:
  name: {type: string}
  resourceType: {type: string}
  owner: {type: string}
```

See `examples/object-type-config.yaml` for details.

## Common Workflows

### Creating a Complete Application

1. **Create YAML config**
   ```yaml
   # sap-app.yaml
   name: "SAP HR"
   description: "SAP human resources system"
   object_types:
     __ACCOUNT__:
       type: account
       properties:
         employeeId: {type: string}
         email: {type: string}
         department: {type: string}
   ```

2. **Create application**
   ```bash
   gia app create sap-app.yaml
   # Returns: Application ID: abc-123
   ```

3. **Load employee data**
   ```bash
   gia data load abc-123 employees.csv --type __ACCOUNT__
   # Returns: Upload ID: upload-456
   ```

4. **Monitor progress**
   ```bash
   gia data status abc-123 upload-456
   ```

5. **Check for failures**
   ```bash
   gia data failures abc-123 upload-456 --export errors.csv
   ```

### Updating an Existing Application

1. **Export current config**
   ```bash
   gia app get abc-123 --export app.yaml
   ```

2. **Edit the file** (add/modify object types)

3. **Update application**
   ```bash
   gia app update abc-123 app.yaml
   ```

### Adding a New Object Type to Existing App

1. **Create object type config**
   ```yaml
   # permission.yaml
   id: "__PERMISSION__"
   type: permission
   properties:
     permissionName: {type: string}
     riskLevel: {type: string}
   ```

2. **Add to application**
   ```bash
   gia object add abc-123 permission.yaml
   ```

3. **Load permission data**
   ```bash
   gia data load abc-123 permissions.csv --type __PERMISSION__
   ```

## Multiple Profiles

For working with multiple tenants:

```bash
# Configure production
gia configure --profile prod

# Configure staging
gia configure --profile staging

# Use specific profile
gia app list --profile prod
gia app list --profile staging
```

## CSV Data Format

CSV files should have headers matching the object type properties:

```csv
email,firstName,lastName,department
john@example.com,John,Doe,Engineering
jane@example.com,Jane,Smith,Sales
```

**Requirements:**
- First row must be headers
- Headers must match property names in object type schema
- Use UTF-8 encoding
- Comma-separated (CSV standard)

## Troubleshooting

### Authentication Errors

```bash
# Reconfigure credentials
gia configure

# Verify config
cat ~/.gia/config.yaml
```

### Binary Won't Run (macOS)

macOS may block unsigned binaries:

```bash
# Remove quarantine attribute
xattr -d com.apple.quarantine $(which gia)
```

Or: System Preferences → Security & Privacy → Allow

### Upload Failures

```bash
# Get detailed failure information
gia data failures <app-id> <upload-id>

# Common issues:
# - Missing required properties
# - Invalid property values
# - Incorrect object type
# - CSV encoding issues
```

### Permission Denied

```bash
# Fix config file permissions
chmod 600 ~/.gia/config.yaml

# Fix binary permissions
chmod +x /usr/local/bin/gia
```

## Advanced Usage

### Output Formats

Most commands support multiple output formats:

```bash
gia app list --format table    # Default
gia app list --format json     # JSON
gia app list --format yaml     # YAML
```

### Scripting

Use in shell scripts:

```bash
#!/bin/bash
set -e

# Create app
APP_ID=$(gia app create app.yaml | grep "Application ID:" | cut -d: -f2 | tr -d ' ')

# Load data
UPLOAD_ID=$(gia data load "$APP_ID" data.csv --type __ACCOUNT__ | grep "Upload ID:" | cut -d: -f2 | tr -d ' ')

# Monitor until complete
while true; do
    STATUS=$(gia data status "$APP_ID" "$UPLOAD_ID" --format json | jq -r '.status')
    if [ "$STATUS" = "complete" ]; then
        break
    fi
    sleep 5
done

echo "Upload complete!"
```

## Getting Help

```bash
# General help
gia --help

# Command-specific help
gia app --help
gia data load --help
```

## Examples Directory

The `examples/` directory contains:
- `app-config.yaml` - Complete application example
- `object-type-config.yaml` - Single object type example
- `accounts.csv` - Sample account data

## Related Documentation

- [Deployment Guide](DEPLOYMENT.md) - For building and distributing
- [API Documentation](https://docs.pingidentity.com) - PingOne IGA API docs
- [GitHub Repository](https://github.com/pingidentity/gia) - Source code

## License

MIT License - See LICENSE file for details
