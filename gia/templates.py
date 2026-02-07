"""Local builder for constructing a disconnected application and pushing it.

Mirrors the Veza OAA pattern: build in memory, then push to the server
via an orchestrated sequence of API calls.
"""

from __future__ import annotations

import logging
import warnings
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

from .exceptions import IGAClientError, IGANotFoundError

if TYPE_CHECKING:
    from .client import IGAClient

log = logging.getLogger(__name__)


@dataclass
class ObjectTypeDefinition:
    """A single object type within a disconnected application.

    Args:
        id: Object type identifier (e.g. ``__ACCOUNT__``, ``Roles``).
        type: Either ``account`` or ``resource``.
        properties: Schema properties dict describing the columns.
    """
    id: str
    type: str  # "account" or "resource"
    properties: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {"id": self.id, "type": self.type, "properties": self.properties}


@dataclass
class FileUpload:
    """A CSV file to upload for a specific object type.

    Args:
        file_path: Local path to the CSV file.
        object_type: The object type this file populates (e.g. ``__ACCOUNT__``).
    """
    file_path: str
    object_type: str


class DisconnectedApplication:
    """Local builder for a PingOne IGA disconnected application.

    Construct the application, its object types, and file uploads in memory,
    then push everything via :meth:`push`.

    Example::

        app = DisconnectedApplication(name="SAP HR", description="SAP HR system")
        app.add_object_type("__ACCOUNT__", "account", properties={
            "user_name": {"type": "string", "displayName": "User Name"},
            "id": {"type": "string", "required": True, "displayName": "ID"},
        })
        app.add_object_type("Roles", "resource", properties={
            "displayName": {"type": "string", "required": True, "displayName": "Display Name"},
        })
        app.add_file_upload("accounts.csv", "__ACCOUNT__")
        app.add_file_upload("roles.csv", "Roles")

        client = IGAClient(base_url, client_id, client_secret, token_endpoint)
        result = app.push(client)
    """

    def __init__(
        self,
        name: str,
        description: str = "",
        owner_ids: list[str] | None = None,
        icon: str = "",
        **extra_fields: Any,
    ):
        self.name = name
        self.description = description
        self.owner_ids = owner_ids or []
        self.icon = icon
        self.extra_fields = extra_fields

        self._object_types: dict[str, ObjectTypeDefinition] = {}
        self._file_uploads: list[FileUpload] = []

    # ------------------------------------------------------------------
    # Builder methods
    # ------------------------------------------------------------------

    def add_object_type(
        self,
        id: str,
        type: str,
        properties: dict[str, Any] | None = None,
    ) -> ObjectTypeDefinition:
        """Define an object type for this application.

        Args:
            id: Identifier such as ``__ACCOUNT__``, ``__GROUP__``, or a custom name.
            type: ``account`` or ``resource``.
            properties: Column/property definitions for this object type.

        Returns:
            The created :class:`ObjectTypeDefinition`.

        Raises:
            ValueError: If an object type with this ID already exists.
        """
        if id in self._object_types:
            raise ValueError(f"Object type '{id}' already defined")
        obj = ObjectTypeDefinition(id=id, type=type, properties=properties or {})
        self._object_types[id] = obj
        return obj

    def add_file_upload(self, file_path: str, object_type: str) -> FileUpload:
        """Register a CSV file to upload during push.

        Args:
            file_path: Local path to the CSV.
            object_type: Which object type this file populates.

        Returns:
            The created :class:`FileUpload`.

        Raises:
            ValueError: If ``object_type`` has not been defined via
                :meth:`add_object_type`.
        """
        if object_type not in self._object_types:
            raise ValueError(
                f"Object type '{object_type}' not defined. "
                f"Call add_object_type('{object_type}', ...) first."
            )
        upload = FileUpload(file_path=file_path, object_type=object_type)
        self._file_uploads.append(upload)
        return upload

    @property
    def object_types(self) -> dict[str, ObjectTypeDefinition]:
        """Read-only access to defined object types."""
        return dict(self._object_types)

    @property
    def file_uploads(self) -> list[FileUpload]:
        """Read-only access to registered file uploads."""
        return list(self._file_uploads)

    # ------------------------------------------------------------------
    # Payload generation
    # ------------------------------------------------------------------

    def to_application_payload(self) -> dict:
        """Serialize to the ``ApplicationDisconnected`` schema for create/update."""
        payload: dict[str, Any] = {
            "name": self.name,
            "description": self.description,
            "isDisconnected": True,
            "datasourceId": "disconnected",
            "authoritative": False,
        }
        if self.owner_ids:
            payload["ownerIds"] = self.owner_ids
        if self.icon:
            payload["icon"] = self.icon

        object_types = {}
        for ot in self._object_types.values():
            object_types[ot.id] = ot.to_dict()
        if object_types:
            payload["objectTypes"] = object_types

        payload.update(self.extra_fields)
        return payload

    # ------------------------------------------------------------------
    # Push orchestration
    # ------------------------------------------------------------------

    def push(self, client: IGAClient, upsert: bool = True) -> PushResult:
        """Push this application to PingOne IGA.

        Orchestrates: create/update application → add/update object types
        → upload CSV files.

        Args:
            client: An authenticated :class:`~gia.client.IGAClient`.
            upsert: If ``True`` (default), warn and update if the application
                    already exists. If ``False``, raise an error on conflict.

        Returns:
            A :class:`PushResult` with the application ID and upload responses.
        """
        apps_api = client.applications

        # Step 1: Create or update the application
        existing = apps_api.find_application_by_name(self.name)
        app_payload = self.to_application_payload()

        if existing:
            if not upsert:
                raise IGAClientError(
                    f"Application '{self.name}' already exists (id={existing['id']}). "
                    "Set upsert=True to update."
                )
            warnings.warn(
                f"Application '{self.name}' already exists (id={existing['id']}). Updating.",
                stacklevel=2,
            )
            app_id = existing["id"]
            app_response = apps_api.update_application(app_id, app_payload)
            log.info("Updated application '%s' (%s)", self.name, app_id)
        else:
            app_response = apps_api.create_application(app_payload)
            app_id = app_response["id"]
            log.info("Created application '%s' (%s)", self.name, app_id)

        # Step 2: Add/update object types
        object_type_responses = {}
        for ot in self._object_types.values():
            try:
                existing_ot = apps_api.get_object_type(app_id, ot.id)
                resp = apps_api.update_object_type(app_id, ot.id, ot.to_dict())
                log.info("Updated object type '%s' on application '%s'", ot.id, self.name)
            except IGANotFoundError:
                resp = apps_api.add_object_type(app_id, ot.to_dict())
                log.info("Added object type '%s' to application '%s'", ot.id, self.name)
            object_type_responses[ot.id] = resp

        # Step 3: Upload files
        upload_responses = []
        for upload in self._file_uploads:
            resp = apps_api.upload_file(app_id, upload.file_path, upload.object_type)
            log.info(
                "Uploaded '%s' for object type '%s' on application '%s'",
                upload.file_path, upload.object_type, self.name,
            )
            upload_responses.append(resp)

        return PushResult(
            application_id=app_id,
            application_response=app_response,
            object_type_responses=object_type_responses,
            upload_responses=upload_responses,
        )


@dataclass
class PushResult:
    """Result of a :meth:`DisconnectedApplication.push` operation."""
    application_id: str
    application_response: dict
    object_type_responses: dict[str, dict]
    upload_responses: list[dict]