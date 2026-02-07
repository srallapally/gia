"""Thin REST wrappers for /governance/application endpoints."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from .client import IGAClient

log = logging.getLogger(__name__)

BASE_PATH = "/governance/application"


class ApplicationsAPI:
    """Wraps all ``/governance/application`` endpoints.

    Instantiated automatically via ``IGAClient.applications``.
    """

    def __init__(self, client: IGAClient):
        self._client = client

    # ------------------------------------------------------------------
    # Application CRUD
    # ------------------------------------------------------------------

    def list_applications(
        self,
        query_filter: str | None = None,
        fields: str | None = None,
        page_size: int | None = None,
        sort_keys: str | None = None,
        sort_dir: str | None = None,
        **extra_params: Any,
    ) -> list[dict]:
        """List all applications (auto-paginated).

        Args:
            query_filter: ``_queryFilter`` expression.
            fields: Comma-separated field names to return.
            page_size: Override default page size.
            sort_keys: Property to sort by.
            sort_dir: ``asc`` or ``desc``.
        """
        params: dict[str, Any] = {**extra_params}
        if query_filter is not None:
            params["_queryFilter"] = query_filter
        if fields is not None:
            params["_fields"] = fields
        if sort_keys is not None:
            params["_sortKeys"] = sort_keys
        if sort_dir is not None:
            params["_sortDir"] = sort_dir
        return self._client.api_get_paginated(BASE_PATH, params=params, page_size=page_size)

    def get_application(
        self,
        application_id: str,
        fields: str | None = None,
        scope_permission: str | None = None,
        end_user_id: str | None = None,
    ) -> dict:
        """Get a single application by ID."""
        params: dict[str, str] = {}
        if fields is not None:
            params["_fields"] = fields
        if scope_permission is not None:
            params["scopePermission"] = scope_permission
        if end_user_id is not None:
            params["endUserId"] = end_user_id
        return self._client.api_get(f"{BASE_PATH}/{application_id}", params=params or None)

    def create_application(self, payload: dict) -> dict:
        """Create a disconnected application.

        Args:
            payload: Application body matching ``ApplicationDisconnected`` schema.
        """
        return self._client.api_post(BASE_PATH, json=payload, params={"action": "create"})

    def update_application(self, application_id: str, payload: dict) -> dict:
        """Update an application by ID (full replace)."""
        return self._client.api_put(f"{BASE_PATH}/{application_id}", json=payload)

    def delete_application(self, application_id: str) -> dict:
        """Delete an application by ID."""
        return self._client.api_delete(f"{BASE_PATH}/{application_id}")

    # ------------------------------------------------------------------
    # Object Types
    # ------------------------------------------------------------------

    def add_object_type(self, application_id: str, payload: dict) -> dict:
        """Add an object type to an application.

        Args:
            payload: Body matching ``ApplicationObjectType`` schema
                     (id, type, properties).
        """
        return self._client.api_post(f"{BASE_PATH}/{application_id}/objectType", json=payload)

    def get_object_type(self, application_id: str, object_type_id: str) -> dict:
        """Get a specific object type for an application."""
        return self._client.api_get(f"{BASE_PATH}/{application_id}/objectType/{object_type_id}")

    def update_object_type(self, application_id: str, object_type_id: str, payload: dict) -> dict:
        """Update a specific object type."""
        return self._client.api_put(f"{BASE_PATH}/{application_id}/objectType/{object_type_id}", json=payload)

    def delete_object_type(self, application_id: str, object_type_id: str) -> dict:
        """Delete a specific object type from an application."""
        return self._client.api_delete(f"{BASE_PATH}/{application_id}/objectType/{object_type_id}")

    def get_object_type_schema(self, application_id: str, object_type: str) -> dict:
        """Get the schema for a given application object type."""
        return self._client.api_get(f"{BASE_PATH}/{application_id}/{object_type}/schema")

    # ------------------------------------------------------------------
    # File Upload
    # ------------------------------------------------------------------

    def upload_file(self, application_id: str, file_path: str, object_type: str) -> dict:
        """Upload a CSV file for a disconnected application.

        Args:
            application_id: Target application ID.
            file_path: Path to the CSV file on disk.
            object_type: The object type this file contains (e.g. ``__ACCOUNT__``).

        Returns:
            Upload response with extraction IDs.
        """
        with open(file_path, "rb") as f:
            files = {"file": f}
            data = {"objectType": object_type}
            return self._client.api_post(
                f"{BASE_PATH}/{application_id}",
                params={"_action": "upload"},
                files=files,
                data=data,
            )

    def get_files(self, application_id: str) -> list[dict]:
        """Get metadata for all files uploaded to an application."""
        body = self._client.api_get(f"{BASE_PATH}/{application_id}/files")
        return body.get("result", [])

    def get_upload_status(self, application_id: str, upload_id: str) -> dict:
        """Get the summary for a specific upload operation."""
        return self._client.api_get(f"{BASE_PATH}/{application_id}/upload/:{upload_id}")

    def get_upload_failures(self, application_id: str, upload_id: str) -> dict:
        """Get failure records for a specific upload operation."""
        return self._client.api_get(f"{BASE_PATH}/{application_id}/upload/:{upload_id}/failures")

    # ------------------------------------------------------------------
    # Accounts (raw disconnected data)
    # ------------------------------------------------------------------

    def list_accounts(self, application_id: str) -> list[dict]:
        """List raw account data for an application."""
        body = self._client.api_get(f"{BASE_PATH}/{application_id}/account")
        return body.get("result", [])

    def get_account(self, application_id: str, account_id: str) -> dict:
        """Get a single raw account by ID."""
        return self._client.api_get(f"{BASE_PATH}/{application_id}/account/{account_id}")

    # ------------------------------------------------------------------
    # Resources (raw disconnected data)
    # ------------------------------------------------------------------

    def list_resources(self, application_id: str) -> list[dict]:
        """List raw resource data for an application."""
        body = self._client.api_get(f"{BASE_PATH}/{application_id}/resource")
        return body.get("result", [])

    def get_resource(self, application_id: str, resource_id: str) -> dict:
        """Get a single raw resource by ID."""
        return self._client.api_get(f"{BASE_PATH}/{application_id}/resource/{resource_id}")

    # ------------------------------------------------------------------
    # Lookup helpers
    # ------------------------------------------------------------------

    def find_application_by_name(self, name: str) -> dict | None:
        """Find an application by exact name match. Returns None if not found."""
        results = self.list_applications(query_filter=f'name eq "{name}"')
        return results[0] if results else None