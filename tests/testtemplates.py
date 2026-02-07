"""Tests for the DisconnectedApplication builder and push orchestration."""

import warnings
from unittest.mock import MagicMock, patch, call

import pytest

from gia import (
    DisconnectedApplication,
    IGAClient,
    IGAClientError,
    IGANotFoundError,
)


class TestDisconnectedApplicationBuilder:

    def test_basic_construction(self):
        app = DisconnectedApplication(name="TestApp", description="A test app")
        assert app.name == "TestApp"
        assert app.description == "A test app"
        assert app.object_types == {}
        assert app.file_uploads == []

    def test_add_object_type(self):
        app = DisconnectedApplication(name="TestApp")
        props = {"user_name": {"type": "string", "displayName": "User Name"}}
        ot = app.add_object_type("__ACCOUNT__", "account", properties=props)
        assert ot.id == "__ACCOUNT__"
        assert ot.type == "account"
        assert "__ACCOUNT__" in app.object_types

    def test_duplicate_object_type_raises(self):
        app = DisconnectedApplication(name="TestApp")
        app.add_object_type("__ACCOUNT__", "account")
        with pytest.raises(ValueError, match="already defined"):
            app.add_object_type("__ACCOUNT__", "account")

    def test_add_file_upload(self):
        app = DisconnectedApplication(name="TestApp")
        app.add_object_type("__ACCOUNT__", "account")
        upload = app.add_file_upload("accounts.csv", "__ACCOUNT__")
        assert upload.file_path == "accounts.csv"
        assert upload.object_type == "__ACCOUNT__"
        assert len(app.file_uploads) == 1

    def test_file_upload_requires_object_type(self):
        app = DisconnectedApplication(name="TestApp")
        with pytest.raises(ValueError, match="not defined"):
            app.add_file_upload("accounts.csv", "__ACCOUNT__")

    def test_to_application_payload(self):
        app = DisconnectedApplication(
            name="MyApp",
            description="desc",
            owner_ids=["user-1"],
            icon="https://example.com/icon.png",
        )
        app.add_object_type("__ACCOUNT__", "account", properties={"id": {"type": "string"}})

        payload = app.to_application_payload()
        assert payload["name"] == "MyApp"
        assert payload["isDisconnected"] is True
        assert payload["datasourceId"] == "disconnected"
        assert payload["ownerIds"] == ["user-1"]
        assert payload["icon"] == "https://example.com/icon.png"
        assert "__ACCOUNT__" in payload["objectTypes"]

    def test_extra_fields_in_payload(self):
        app = DisconnectedApplication(name="X", custom_field="custom_value")
        payload = app.to_application_payload()
        assert payload["custom_field"] == "custom_value"

    def test_payload_omits_empty_optionals(self):
        app = DisconnectedApplication(name="Minimal")
        payload = app.to_application_payload()
        assert "ownerIds" not in payload
        assert "icon" not in payload
        assert "objectTypes" not in payload


class TestPushOrchestration:

    @pytest.fixture
    def mock_client(self):
        client = MagicMock(spec=IGAClient)
        apps_api = MagicMock()
        client.applications = apps_api
        return client

    def test_push_creates_new_app(self, mock_client):
        apps = mock_client.applications
        apps.find_application_by_name.return_value = None
        apps.create_application.return_value = {"id": "new-id", "name": "TestApp"}
        apps.get_object_type.side_effect = IGANotFoundError("not found")
        apps.add_object_type.return_value = {}

        app = DisconnectedApplication(name="TestApp")
        app.add_object_type("__ACCOUNT__", "account")

        result = app.push(mock_client, upsert=False)

        apps.create_application.assert_called_once()
        apps.add_object_type.assert_called_once()
        assert result.application_id == "new-id"

    def test_push_upsert_true_warns_and_updates(self, mock_client):
        apps = mock_client.applications
        apps.find_application_by_name.return_value = {"id": "existing-id", "name": "TestApp"}
        apps.update_application.return_value = {"id": "existing-id", "name": "TestApp"}

        app = DisconnectedApplication(name="TestApp")

        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            result = app.push(mock_client, upsert=True)
            assert len(w) == 1
            assert "already exists" in str(w[0].message)

        apps.update_application.assert_called_once()
        apps.create_application.assert_not_called()
        assert result.application_id == "existing-id"

    def test_push_upsert_false_raises_on_existing(self, mock_client):
        apps = mock_client.applications
        apps.find_application_by_name.return_value = {"id": "existing-id", "name": "TestApp"}

        app = DisconnectedApplication(name="TestApp")

        with pytest.raises(IGAClientError, match="already exists"):
            app.push(mock_client, upsert=False)

    def test_push_updates_existing_object_types(self, mock_client):
        apps = mock_client.applications
        apps.find_application_by_name.return_value = None
        apps.create_application.return_value = {"id": "new-id"}
        apps.get_object_type.return_value = {"id": "__ACCOUNT__"}  # exists
        apps.update_object_type.return_value = {}

        app = DisconnectedApplication(name="TestApp")
        app.add_object_type("__ACCOUNT__", "account")

        result = app.push(mock_client)

        apps.update_object_type.assert_called_once()
        apps.add_object_type.assert_not_called()

    def test_push_creates_new_object_types(self, mock_client):
        apps = mock_client.applications
        apps.find_application_by_name.return_value = None
        apps.create_application.return_value = {"id": "new-id"}
        apps.get_object_type.side_effect = IGANotFoundError("not found")
        apps.add_object_type.return_value = {}

        app = DisconnectedApplication(name="TestApp")
        app.add_object_type("__ACCOUNT__", "account")

        result = app.push(mock_client)

        apps.add_object_type.assert_called_once()

    def test_push_uploads_files(self, mock_client, tmp_path):
        apps = mock_client.applications
        apps.find_application_by_name.return_value = None
        apps.create_application.return_value = {"id": "new-id"}
        apps.get_object_type.side_effect = IGANotFoundError("not found")
        apps.add_object_type.return_value = {}
        apps.upload_file.return_value = {"message": "Upload started"}

        csv_file = tmp_path / "accounts.csv"
        csv_file.write_text("id,user_name\n1,alice\n")

        app = DisconnectedApplication(name="TestApp")
        app.add_object_type("__ACCOUNT__", "account")
        app.add_file_upload(str(csv_file), "__ACCOUNT__")

        result = app.push(mock_client)

        apps.upload_file.assert_called_once_with("new-id", str(csv_file), "__ACCOUNT__")
        assert len(result.upload_responses) == 1

    def test_push_result_fields(self, mock_client):
        apps = mock_client.applications
        apps.find_application_by_name.return_value = None
        apps.create_application.return_value = {"id": "new-id", "name": "TestApp"}
        apps.get_object_type.side_effect = IGANotFoundError("not found")
        apps.add_object_type.return_value = {"id": "__ACCOUNT__"}

        app = DisconnectedApplication(name="TestApp")
        app.add_object_type("__ACCOUNT__", "account")

        result = app.push(mock_client)

        assert result.application_id == "new-id"
        assert result.application_response == {"id": "new-id", "name": "TestApp"}
        assert "__ACCOUNT__" in result.object_type_responses
        assert result.upload_responses == []