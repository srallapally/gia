# GIA CLI - Quick Start Guide

## What You Got

A complete command-line interface that makes the GIA client installable via Homebrew (`brew install gia`), eliminating the need for customers to install Python or PyCharm.

## Immediate Next Steps

### 1. Integration (5 minutes)

Copy the CLI code into your GIA repository:

```bash
cd /path/to/your/gia/repository

# Copy CLI module
cp -r gia-cli-implementation/gia_cli ./

# Copy build files
cp gia-cli-implementation/pyproject.toml ./
cp gia-cli-implementation/gia.spec ./
cp gia-cli-implementation/build.sh ./
cp gia-cli-implementation/gia.rb ./

# Copy examples (optional)
cp -r gia-cli-implementation/examples ./

# Copy docs (optional)
cp gia-cli-implementation/CLI-README.md ./
cp gia-cli-implementation/DEPLOYMENT.md ./
```

### 2. Install Dependencies (1 minute)

```bash
pip install -e ".[dev]"
```

This adds:
- `click` - CLI framework
- `pyyaml` - YAML config parsing
- `pyinstaller` - Binary builder

### 3. Test Locally (2 minutes)

```bash
# Test the CLI works
python -m gia_cli --help

# Should show:
# Usage: __main__.py [OPTIONS] COMMAND [ARGS]...
# 
# GIA - Governance Identity API CLI for PingOne Advanced Identity Cloud.
# 
# Commands:
#   app         Manage applications.
#   configure   Configure GIA credentials interactively.
#   data        Load and monitor application data.
#   object      Manage application object types.
```

### 4. Configure & Test with Real API (5 minutes)

```bash
# Configure credentials
python -m gia_cli configure

# Enter your credentials:
# - Base URL: https://your-tenant.forgeblocks.com
# - Client ID: your-client-id
# - Client Secret: your-client-secret
# - Token Endpoint: (auto-suggested)

# Test listing applications
python -m gia_cli app list
```

If this works, your integration is successful! ✅

### 5. Build Standalone Binary (2 minutes)

```bash
chmod +x build.sh
./build.sh

# Test the binary
./dist/gia --version
./dist/gia app list
```

### 6. Create GitHub Release (5 minutes)

```bash
# Tag release
git add .
git commit -m "Add CLI interface"
git tag -a v0.1.0 -m "Release v0.1.0 with CLI"
git push origin main
git push origin v0.1.0

# On GitHub:
# 1. Go to your repo → Releases → "Draft a new release"
# 2. Choose tag: v0.1.0
# 3. Title: "GIA CLI v0.1.0"
# 4. Upload file: dist/gia
# 5. Click "Publish release"
```

### 7. Set Up Homebrew (10 minutes)

```bash
# Create homebrew-tap repository on GitHub
# Organization: pingidentity
# Repository name: homebrew-tap

# Clone it
git clone https://github.com/pingidentity/homebrew-tap.git
cd homebrew-tap

# Add formula
mkdir -p Formula
cp /path/to/gia.rb Formula/

# Update SHA256 in gia.rb
curl -L https://github.com/pingidentity/gia/archive/refs/tags/v0.1.0.tar.gz | shasum -a 256
# Copy the hash and update gia.rb line: sha256 "PASTE_HASH_HERE"

# Commit and push
git add Formula/gia.rb
git commit -m "Add GIA CLI formula"
git push
```

### 8. Test Installation (2 minutes)

On a clean Mac:

```bash
# Add tap
brew tap pingidentity/tap

# Install
brew install gia

# Test
gia --version
gia --help
```

Done! 🎉

## User Experience

Your customers can now install GIA with:

```bash
brew install gia
```

No Python, no PyCharm, just works.

## Files Explained

```
gia-cli-implementation/
├── gia_cli/                 # CLI source code
│   ├── cli.py              # Main commands
│   ├── config.py           # Credential management
│   ├── interactive.py      # Interactive mode
│   └── utils.py            # Formatting
├── examples/               # Example configs
│   ├── app-config.yaml     # Full app example
│   ├── object-type-config.yaml
│   └── accounts.csv        # Sample data
├── pyproject.toml          # Updated dependencies
├── gia.spec                # PyInstaller config
├── build.sh                # Build script
├── gia.rb                  # Homebrew formula
├── CLI-README.md           # User docs
├── DEPLOYMENT.md           # Build/deploy guide
└── IMPLEMENTATION.md       # Integration details
```

## Support Commands

All user requirements are covered:

✅ **Create app (complete)**: `gia app create config.yaml` or `--interactive`
✅ **Create app (incremental)**: `gia object add <id> object.yaml`
✅ **Update app (complete)**: `gia app update <id> config.yaml`
✅ **Update app (incremental)**: `gia object update <id> <type> config.yaml`
✅ **Delete app**: `gia app delete <id>`
✅ **Load data**: `gia data load <id> file.csv --type __ACCOUNT__`
✅ **Check progress**: `gia data status <id> <upload-id>`
✅ **View failures**: `gia data failures <id> <upload-id>`

## Example Workflow

```bash
# 1. Create app
gia app create examples/app-config.yaml
# → Application ID: abc-123

# 2. Load data
gia data load abc-123 examples/accounts.csv --type __ACCOUNT__
# → Upload ID: upload-456

# 3. Check progress
gia data status abc-123 upload-456
# → Status: complete, Success: 11, Failures: 0

# 4. Add another object type
gia object add abc-123 examples/object-type-config.yaml

# 5. Update app later
gia app get abc-123 --export my-app.yaml
# Edit my-app.yaml
gia app update abc-123 my-app.yaml
```

## Troubleshooting

**Issue**: Import errors when testing
**Fix**: `pip install -e ".[dev]"`

**Issue**: Binary build fails
**Fix**: `pip install pyinstaller`

**Issue**: Authentication fails
**Fix**: `gia configure` with correct credentials

**Issue**: Homebrew install fails
**Fix**: Check SHA256 in `gia.rb` matches release tarball

## Questions?

- **User docs**: See CLI-README.md
- **Build/deploy**: See DEPLOYMENT.md  
- **Integration**: See IMPLEMENTATION.md
- **Code details**: Comments in gia_cli/*.py

Ready to ship! 🚀
