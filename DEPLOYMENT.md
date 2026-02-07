# GIA CLI - Deployment & Distribution Guide

This guide explains how to build and distribute the GIA CLI tool for macOS using Homebrew.

## Overview

The GIA CLI is distributed as a standalone executable that doesn't require customers to install Python or PyCharm. The distribution strategy:

1. **Build**: Create a standalone binary using PyInstaller
2. **Package**: Create a GitHub release with the binary
3. **Distribute**: Publish a Homebrew formula for easy installation

## Build Process

### Prerequisites

- Python 3.10+
- PyInstaller
- Access to the GIA repository

### Step 1: Install Dependencies

```bash
pip install -e ".[dev]"
```

This installs:
- `requests` - HTTP client
- `click` - CLI framework
- `pyyaml` - YAML parsing
- `pyinstaller` - Binary builder

### Step 2: Build Standalone Binary

```bash
./build.sh
```

This creates a single executable at `dist/gia` that includes:
- Python runtime
- All dependencies
- GIA library code
- CLI code

The binary is ~25-30MB and requires no installation of Python.

### Step 3: Test the Binary

```bash
./dist/gia --version
./dist/gia --help
```

## Distribution via Homebrew

### Option A: Homebrew Tap (Recommended for Organizations)

Create a custom Homebrew tap for your organization:

```bash
# 1. Create a GitHub repository named "homebrew-tap"
# Organization: pingidentity
# Repo: homebrew-tap

# 2. Add the formula
cp gia.rb /path/to/homebrew-tap/Formula/

# 3. Commit and push
git add Formula/gia.rb
git commit -m "Add GIA CLI formula"
git push
```

Users can then install with:

```bash
brew tap pingidentity/tap
brew install gia
```

### Option B: Official Homebrew (For Public Release)

Submit to homebrew-core (requires more review):

1. Fork https://github.com/Homebrew/homebrew-core
2. Add formula to `Formula/gia.rb`
3. Submit pull request

### Formula Setup

The `gia.rb` formula needs to be updated with:

1. **URL**: Point to a GitHub release tarball
   ```ruby
   url "https://github.com/pingidentity/gia/archive/refs/tags/v0.1.0.tar.gz"
   ```

2. **SHA256**: Calculate the checksum
   ```bash
   curl -L https://github.com/pingidentity/gia/archive/refs/tags/v0.1.0.tar.gz | shasum -a 256
   ```

3. **Update formula**:
   ```ruby
   sha256 "abc123..."  # Replace with actual hash
   ```

## Creating a GitHub Release

### Step 1: Tag the Release

```bash
git tag -a v0.1.0 -m "Release v0.1.0"
git push origin v0.1.0
```

### Step 2: Create Release on GitHub

1. Go to repository → Releases → "Draft a new release"
2. Choose tag: v0.1.0
3. Add release notes
4. Attach the binary: `dist/gia`
5. Publish release

### Step 3: Update Homebrew Formula

Calculate SHA256 of the release tarball:

```bash
curl -L https://github.com/pingidentity/gia/archive/refs/tags/v0.1.0.tar.gz | shasum -a 256
```

Update `gia.rb` with the correct URL and sha256.

## Installation (End User Experience)

### Via Homebrew (Recommended)

```bash
# Add the tap
brew tap pingidentity/tap

# Install
brew install gia

# Verify
gia --version
```

### Manual Installation

```bash
# Download binary
curl -L -o gia https://github.com/pingidentity/gia/releases/download/v0.1.0/gia

# Make executable
chmod +x gia

# Move to PATH
sudo mv gia /usr/local/bin/

# Verify
gia --version
```

## Usage Examples

### First Time Setup

```bash
gia configure
```

This prompts for:
- Base URL
- Client ID
- Client Secret
- Token Endpoint

Credentials are stored in `~/.gia/config.yaml` with restricted permissions.

### Create Application from YAML

```yaml
# app.yaml
name: "Corporate SAP"
description: "Main HR System"
object_types:
  __ACCOUNT__:
    type: account
    properties:
      email: {type: string}
      firstName: {type: string}
      lastName: {type: string}
```

```bash
gia app create app.yaml
```

### Interactive Mode

```bash
gia app create --interactive
```

### Load Data

```bash
gia data load abc-123 users.csv --type __ACCOUNT__
gia data status abc-123 upload-456
gia data failures abc-123 upload-456
```

## Updating the CLI

### For Developers

1. Make code changes
2. Update version in `pyproject.toml`
3. Build new binary: `./build.sh`
4. Create new release
5. Update Homebrew formula

### For Users

```bash
brew upgrade gia
```

## Troubleshooting

### Binary Won't Run

macOS may block unsigned binaries:

```bash
# Remove quarantine attribute
xattr -d com.apple.quarantine /usr/local/bin/gia
```

Or: System Preferences → Security & Privacy → Allow

### Python Version Issues

The formula specifies Python 3.11. If you have a different version:

```bash
brew install python@3.11
brew link python@3.11
```

### Permission Issues

```bash
# Config file permissions
chmod 600 ~/.gia/config.yaml

# Binary permissions
chmod +x /usr/local/bin/gia
```

## Architecture Notes

### Why PyInstaller?

- Creates a truly standalone binary
- Bundles Python runtime
- No customer-side Python installation needed
- Single file distribution

### Why Homebrew?

- Native macOS package manager
- Handles dependencies automatically
- Familiar to developers
- Easy updates

### Alternative: Docker

If Homebrew isn't suitable, consider:

```dockerfile
FROM python:3.11-slim
COPY . /app
WORKDIR /app
RUN pip install -e .
ENTRYPOINT ["gia"]
```

Usage:
```bash
docker run --rm -v ~/.gia:/root/.gia gia-cli app list
```

## File Structure

```
gia/
├── gia/                    # Core library
│   ├── client.py
│   ├── applications.py
│   ├── templates.py
│   └── ...
├── gia_cli/               # CLI package
│   ├── __init__.py
│   ├── __main__.py
│   ├── cli.py            # Main CLI commands
│   ├── config.py         # Config management
│   ├── interactive.py    # Interactive mode
│   └── utils.py          # Formatting utilities
├── gia.spec              # PyInstaller spec
├── build.sh              # Build script
├── gia.rb                # Homebrew formula
└── pyproject.toml        # Package config
```

## Next Steps

1. ✅ CLI code complete
2. ⏳ Test with actual GIA library
3. ⏳ Build binary
4. ⏳ Create GitHub release
5. ⏳ Publish Homebrew tap
6. ⏳ Update documentation
