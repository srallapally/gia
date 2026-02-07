"""Interactive mode for building applications."""

import click

from gia import DisconnectedApplication


class InteractiveAppBuilder:
    """Guide users through creating an application interactively."""
    
    def build(self) -> DisconnectedApplication:
        """Build an application through interactive prompts."""
        click.echo("\n✨ Interactive Application Builder\n")
        
        # Basic app info
        name = click.prompt("Application name")
        description = click.prompt("Application description", default="")
        
        app = DisconnectedApplication(name=name, description=description)
        
        # Object types
        click.echo("\n📦 Object Types\n")
        
        if click.confirm("Add object types?", default=True):
            while True:
                self._add_object_type(app)
                
                if not click.confirm("Add another object type?", default=False):
                    break
        
        click.echo(f"\n✅ Application '{name}' configured with {len(app.object_types)} object type(s)")
        
        return app
    
    def _add_object_type(self, app: DisconnectedApplication) -> None:
        """Add a single object type interactively."""
        click.echo()
        
        type_id = click.prompt("Object type ID (e.g., __ACCOUNT__)")
        type_name = click.prompt(
            "Object type",
            type=click.Choice(["account", "group", "resource", "permission"], case_sensitive=False),
            default="account"
        )
        
        # Properties
        properties = {}
        
        if click.confirm("Add properties?", default=True):
            click.echo("\nEnter properties (name: type). Leave name blank to finish.")
            
            while True:
                prop_name = click.prompt("Property name", default="", show_default=False)
                
                if not prop_name:
                    break
                
                prop_type = click.prompt(
                    "Property type",
                    type=click.Choice(["string", "number", "boolean", "array", "object"]),
                    default="string"
                )
                
                properties[prop_name] = {"type": prop_type}
        
        app.add_object_type(id=type_id, type=type_name, properties=properties)
        click.echo(f"✓ Added object type '{type_id}'")
