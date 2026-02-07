"""GIA CLI - Command-line interface for Governance Identity API."""

import sys
from pathlib import Path

import click
import yaml

from gia import IGAClient, DisconnectedApplication
from gia.exceptions import IGAClientError, IGANotFoundError

from .config import ConfigManager
from .interactive import InteractiveAppBuilder
from .utils import format_table, success, error, info, warning


@click.group()
@click.version_option(version="0.1.0")
def cli():
    """GIA - Governance Identity API CLI for PingOne Advanced Identity Cloud."""
    pass


# ============================================================================
# CONFIGURE
# ============================================================================


@cli.command()
@click.option("--profile", default="default", help="Configuration profile name")
def configure(profile):
    """Configure GIA credentials interactively."""
    config_mgr = ConfigManager()
    
    click.echo(f"\n🔧 Configuring GIA profile: {profile}\n")
    
    base_url = click.prompt("Base URL (e.g., https://tenant.forgeblocks.com)")
    client_id = click.prompt("Client ID")
    client_secret = click.prompt("Client Secret", hide_input=True)
    token_endpoint = click.prompt(
        "Token Endpoint",
        default=f"{base_url.rstrip('/')}/am/oauth2/access_token"
    )
    scopes = click.prompt("Scopes (optional)", default="", show_default=False)
    
    config_mgr.set_profile(
        profile,
        base_url=base_url,
        client_id=client_id,
        client_secret=client_secret,
        token_endpoint=token_endpoint,
        scopes=scopes or None
    )
    
    success(f"Configuration saved for profile '{profile}'")
    info(f"Config location: {config_mgr.config_path}")


# ============================================================================
# APP COMMANDS
# ============================================================================


@cli.group()
def app():
    """Manage applications."""
    pass


@app.command("list")
@click.option("--profile", default="default", help="Configuration profile to use")
@click.option("--format", type=click.Choice(["table", "json", "yaml"]), default="table")
def app_list(profile, format):
    """List all applications."""
    client = _get_client(profile)
    
    try:
        apps = client.applications.list_applications()
        
        if format == "json":
            import json
            click.echo(json.dumps(apps, indent=2))
        elif format == "yaml":
            click.echo(yaml.dump(apps, default_flow_style=False))
        else:
            headers = ["ID", "Name", "Description"]
            rows = [[app.get("id", ""), app.get("name", ""), app.get("description", "")] for app in apps]
            click.echo(format_table(headers, rows))
            info(f"Total applications: {len(apps)}")
    except IGAClientError as e:
        error(f"Failed to list applications: {e}")
        sys.exit(1)


@app.command("get")
@click.argument("app_id")
@click.option("--profile", default="default", help="Configuration profile to use")
@click.option("--export", type=click.Path(), help="Export to YAML file")
@click.option("--format", type=click.Choice(["json", "yaml"]), default="yaml")
def app_get(app_id, profile, export, format):
    """Get application details by ID."""
    client = _get_client(profile)
    
    try:
        app_data = client.applications.get_application(app_id)
        
        # Convert to friendly YAML structure
        config_data = _app_to_config(app_data)
        
        if export:
            with open(export, "w") as f:
                yaml.dump(config_data, f, default_flow_style=False, sort_keys=False)
            success(f"Application exported to {export}")
        else:
            if format == "json":
                import json
                click.echo(json.dumps(config_data, indent=2))
            else:
                click.echo(yaml.dump(config_data, default_flow_style=False, sort_keys=False))
    except IGANotFoundError:
        error(f"Application '{app_id}' not found")
        sys.exit(1)
    except IGAClientError as e:
        error(f"Failed to get application: {e}")
        sys.exit(1)


@app.command("create")
@click.argument("config_file", type=click.Path(exists=True), required=False)
@click.option("--profile", default="default", help="Configuration profile to use")
@click.option("--interactive", "-i", is_flag=True, help="Interactive mode")
def app_create(config_file, profile, interactive):
    """Create an application from YAML config or interactively."""
    client = _get_client(profile)
    
    if interactive:
        builder = InteractiveAppBuilder()
        app = builder.build()
    elif config_file:
        app = _load_app_from_config(config_file)
    else:
        error("Either provide a config file or use --interactive flag")
        sys.exit(1)
    
    try:
        result = app.push(client, upsert=False)
        success(f"Application created successfully!")
        info(f"Application ID: {result.application_id}")
        info(f"Object types created: {len(result.object_type_responses)}")
        if result.upload_responses:
            info(f"Files uploaded: {len(result.upload_responses)}")
    except IGAClientError as e:
        error(f"Failed to create application: {e}")
        sys.exit(1)


@app.command("update")
@click.argument("app_id")
@click.argument("config_file", type=click.Path(exists=True))
@click.option("--profile", default="default", help="Configuration profile to use")
def app_update(app_id, config_file, profile):
    """Update an application from YAML config."""
    client = _get_client(profile)
    
    # Load config
    app = _load_app_from_config(config_file)
    
    try:
        # Force the app to update by setting upsert=True
        # But first check if it exists
        existing = client.applications.get_application(app_id)
        
        # Update the application
        payload = app.to_application_payload()
        updated = client.applications.update_application(app_id, payload)
        
        success(f"Application '{app_id}' updated successfully!")
        
        # Update object types
        for ot_id, ot_def in app.object_types.items():
            try:
                client.applications.get_object_type(app_id, ot_id)
                client.applications.update_object_type(app_id, ot_id, ot_def.to_dict())
                info(f"Updated object type: {ot_id}")
            except IGANotFoundError:
                client.applications.add_object_type(app_id, ot_def.to_dict())
                info(f"Added new object type: {ot_id}")
        
    except IGANotFoundError:
        error(f"Application '{app_id}' not found")
        sys.exit(1)
    except IGAClientError as e:
        error(f"Failed to update application: {e}")
        sys.exit(1)


@app.command("delete")
@click.argument("app_id")
@click.option("--profile", default="default", help="Configuration profile to use")
@click.option("--yes", "-y", is_flag=True, help="Skip confirmation")
def app_delete(app_id, profile, yes):
    """Delete an application."""
    client = _get_client(profile)
    
    if not yes:
        click.confirm(f"Are you sure you want to delete application '{app_id}'?", abort=True)
    
    try:
        client.applications.delete_application(app_id)
        success(f"Application '{app_id}' deleted successfully")
    except IGANotFoundError:
        error(f"Application '{app_id}' not found")
        sys.exit(1)
    except IGAClientError as e:
        error(f"Failed to delete application: {e}")
        sys.exit(1)


# ============================================================================
# OBJECT COMMANDS
# ============================================================================


@cli.group()
def object():
    """Manage application object types."""
    pass


@object.command("add")
@click.argument("app_id")
@click.argument("config_file", type=click.Path(exists=True))
@click.option("--profile", default="default", help="Configuration profile to use")
def object_add(app_id, config_file, profile):
    """Add an object type to an application."""
    client = _get_client(profile)
    
    with open(config_file) as f:
        config = yaml.safe_load(f)
    
    try:
        result = client.applications.add_object_type(app_id, config)
        success(f"Object type '{config.get('id')}' added to application '{app_id}'")
    except IGAClientError as e:
        error(f"Failed to add object type: {e}")
        sys.exit(1)


@object.command("update")
@click.argument("app_id")
@click.argument("type_id")
@click.argument("config_file", type=click.Path(exists=True))
@click.option("--profile", default="default", help="Configuration profile to use")
def object_update(app_id, type_id, config_file, profile):
    """Update an object type."""
    client = _get_client(profile)
    
    with open(config_file) as f:
        config = yaml.safe_load(f)
    
    try:
        result = client.applications.update_object_type(app_id, type_id, config)
        success(f"Object type '{type_id}' updated on application '{app_id}'")
    except IGANotFoundError:
        error(f"Object type '{type_id}' not found in application '{app_id}'")
        sys.exit(1)
    except IGAClientError as e:
        error(f"Failed to update object type: {e}")
        sys.exit(1)


@object.command("delete")
@click.argument("app_id")
@click.argument("type_id")
@click.option("--profile", default="default", help="Configuration profile to use")
@click.option("--yes", "-y", is_flag=True, help="Skip confirmation")
def object_delete(app_id, type_id, profile, yes):
    """Delete an object type from an application."""
    client = _get_client(profile)
    
    if not yes:
        click.confirm(f"Delete object type '{type_id}' from application '{app_id}'?", abort=True)
    
    try:
        client.applications.delete_object_type(app_id, type_id)
        success(f"Object type '{type_id}' deleted from application '{app_id}'")
    except IGANotFoundError:
        error(f"Object type '{type_id}' not found")
        sys.exit(1)
    except IGAClientError as e:
        error(f"Failed to delete object type: {e}")
        sys.exit(1)


# ============================================================================
# DATA COMMANDS
# ============================================================================


@cli.group()
def data():
    """Load and monitor application data."""
    pass


@data.command("load")
@click.argument("app_id")
@click.argument("csv_file", type=click.Path(exists=True))
@click.option("--type", "object_type", required=True, help="Object type (e.g., __ACCOUNT__)")
@click.option("--profile", default="default", help="Configuration profile to use")
def data_load(app_id, csv_file, object_type, profile):
    """Upload CSV data for an application object type."""
    client = _get_client(profile)
    
    try:
        result = client.applications.upload_file(app_id, csv_file, object_type)
        
        upload_id = result.get("extractionId") or result.get("id", "unknown")
        
        success(f"File upload started successfully")
        info(f"Upload ID: {upload_id}")
        info(f"File: {csv_file}")
        info(f"Object type: {object_type}")
        click.echo(f"\nCheck status with: gia data status {app_id} {upload_id}")
    except IGAClientError as e:
        error(f"Failed to upload file: {e}")
        sys.exit(1)


@data.command("status")
@click.argument("app_id")
@click.argument("upload_id")
@click.option("--profile", default="default", help="Configuration profile to use")
@click.option("--format", type=click.Choice(["json", "yaml", "table"]), default="table")
def data_status(app_id, upload_id, profile, format):
    """Check upload progress status."""
    client = _get_client(profile)
    
    try:
        status = client.applications.get_upload_status(app_id, upload_id)
        
        if format == "json":
            import json
            click.echo(json.dumps(status, indent=2))
        elif format == "yaml":
            click.echo(yaml.dump(status, default_flow_style=False))
        else:
            click.echo(f"\n📊 Upload Status for {upload_id}\n")
            click.echo(f"Application ID: {app_id}")
            click.echo(f"Status: {status.get('status', 'unknown')}")
            click.echo(f"Total Records: {status.get('totalCount', 0)}")
            click.echo(f"Success: {status.get('successCount', 0)}")
            click.echo(f"Failures: {status.get('failureCount', 0)}")
            
            if status.get('failureCount', 0) > 0:
                warning(f"\nUse 'gia data failures {app_id} {upload_id}' to view errors")
    except IGANotFoundError:
        error(f"Upload '{upload_id}' not found for application '{app_id}'")
        sys.exit(1)
    except IGAClientError as e:
        error(f"Failed to get upload status: {e}")
        sys.exit(1)


@data.command("failures")
@click.argument("app_id")
@click.argument("upload_id")
@click.option("--profile", default="default", help="Configuration profile to use")
@click.option("--export", type=click.Path(), help="Export failures to CSV file")
@click.option("--format", type=click.Choice(["json", "yaml", "table"]), default="table")
def data_failures(app_id, upload_id, profile, export, format):
    """View upload failure records."""
    client = _get_client(profile)
    
    try:
        failures_data = client.applications.get_upload_failures(app_id, upload_id)
        failures = failures_data.get("result", [])
        
        if not failures:
            success("No failures found for this upload")
            return
        
        if export:
            import csv
            with open(export, "w", newline="") as f:
                if failures:
                    writer = csv.DictWriter(f, fieldnames=failures[0].keys())
                    writer.writeheader()
                    writer.writerows(failures)
            success(f"Failures exported to {export}")
        else:
            if format == "json":
                import json
                click.echo(json.dumps(failures, indent=2))
            elif format == "yaml":
                click.echo(yaml.dump(failures, default_flow_style=False))
            else:
                click.echo(f"\n❌ Upload Failures ({len(failures)} records)\n")
                for idx, failure in enumerate(failures[:10], 1):  # Show first 10
                    click.echo(f"{idx}. Row: {failure.get('rowNumber', 'N/A')}")
                    click.echo(f"   Error: {failure.get('error', 'No error message')}")
                    click.echo()
                
                if len(failures) > 10:
                    info(f"Showing 10 of {len(failures)} failures. Use --export to get all.")
    except IGANotFoundError:
        error(f"Upload '{upload_id}' not found or has no failures")
        sys.exit(1)
    except IGAClientError as e:
        error(f"Failed to get upload failures: {e}")
        sys.exit(1)


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================


def _get_client(profile: str) -> IGAClient:
    """Get an authenticated IGAClient from config."""
    config_mgr = ConfigManager()
    
    try:
        creds = config_mgr.get_profile(profile)
    except ValueError as e:
        error(f"Configuration error: {e}")
        info(f"Run 'gia configure' to set up credentials")
        sys.exit(1)
    
    return IGAClient(
        base_url=creds["base_url"],
        client_id=creds["client_id"],
        client_secret=creds["client_secret"],
        token_endpoint=creds["token_endpoint"],
        scopes=creds.get("scopes")
    )


def _load_app_from_config(config_file: str) -> DisconnectedApplication:
    """Load application from YAML config file."""
    with open(config_file) as f:
        config = yaml.safe_load(f)
    
    app = DisconnectedApplication(
        name=config["name"],
        description=config.get("description", ""),
        owner_ids=config.get("owner_ids"),
        icon=config.get("icon")
    )
    
    # Add object types
    for type_id, type_config in config.get("object_types", {}).items():
        app.add_object_type(
            id=type_id,
            type=type_config["type"],
            properties=type_config.get("properties", {})
        )
    
    return app


def _app_to_config(app_data: dict) -> dict:
    """Convert API application data to YAML-friendly config format."""
    config = {
        "name": app_data.get("name"),
        "description": app_data.get("description", ""),
    }
    
    if app_data.get("ownerIds"):
        config["owner_ids"] = app_data["ownerIds"]
    
    if app_data.get("icon"):
        config["icon"] = app_data["icon"]
    
    if app_data.get("objectTypes"):
        config["object_types"] = app_data["objectTypes"]
    
    return config


if __name__ == "__main__":
    cli()
