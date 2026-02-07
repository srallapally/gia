"""GIA - Governance Identity API client for PingOne IGA.

Provides both a thin REST client and a local builder/push pattern
for the ``/governance/application`` endpoints.

Thin client usage::

    from gia import IGAClient

    client = IGAClient(
        base_url="https://mytenant.forgeblocks.com",
        client_id="my-client-id",
        client_secret="my-secret",
        token_endpoint="https://mytenant.forgeblocks.com/am/oauth2/access_token",
    )
    apps = client.applications.list_applications()

Builder usage::

    from gia import IGAClient, DisconnectedApplication

    app = DisconnectedApplication(name="SAP HR", description="SAP system")
    app.add_object_type("__ACCOUNT__", "account", properties={...})
    app.add_file_upload("accounts.csv", "__ACCOUNT__")

    client = IGAClient(...)
    result = app.push(client, upsert=True)
"""

from .client import IGAClient
from .exceptions import IGAAuthError, IGAClientError, IGANotFoundError
from .templates import DisconnectedApplication, FileUpload, ObjectTypeDefinition, PushResult

__all__ = [
    "IGAClient",
    "IGAClientError",
    "IGAAuthError",
    "IGANotFoundError",
    "DisconnectedApplication",
    "ObjectTypeDefinition",
    "FileUpload",
    "PushResult",
]