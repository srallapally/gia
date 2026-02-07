"""Tests for the thin REST client and applications API."""

import json
from unittest.mock import MagicMock, patch

import pytest

from gia import IGAClient, IGAClientError, IGANotFoundError


@pytest.fixture
def mock_auth():
    """Patch OAuth2 so no real token fetch occurs."""
    with patch("gia.client.OAuth2ClientCredentials") as mock_cls:
        instance = mock_cls.return_value
        instance.access_token = "fake-token"
        yield instance


@pytest.fixture
def client(mock_auth):
    return IGAClient(
        base_url="https://tenant.example.com",
        client_id="cid",
        client_secret="csec",
        token_endpoint="https://tenant.example.com/am/oauth2/access_token",
    )


class TestClientURLBuilding:

    def test_builds_url_with_iga_prefix(self, client):
        url = client._build_url("/governance/application")
        assert url == "https://tenant.example.com/iga/governance/application"

    def test_does_not_double_prefix(self, client):
        url = client._build_url("/iga/governance/application")
        assert url == "https://tenant.example.com/iga/governance/application"

    def test_adds_leading_slash(self, client):
        url = client._build_url("governance/application")
        assert url == "https://tenant.example.com/iga/governance/application"

    def test_strips_trailing_slash_from_base(self):
        with patch("gia.client.OAuth2ClientCredentials"):
            c = IGAClient("https://example.com/", "a", "b", "https://x/token")
            assert c.base_url == "https://example.com"


class TestApplicationsAPI:

    @patch("gia.client.IGAClient._request")
    def test_create_application(self, mock_req, client):
        mock_req.return_value = {"id": "abc-123", "name": "TestApp"}
        result = client.applications.create_application({"name": "TestApp", "isDisconnected": True})
        mock_req.assert_called_once_with(
            "POST", "/governance/application",
            json={"name": "TestApp", "isDisconnected": True},
            params={"action": "create"},
        )
        assert result["id"] == "abc-123"

    @patch("gia.client.IGAClient._request")
    def test_get_application(self, mock_req, client):
        mock_req.return_value = {"id": "abc-123", "name": "TestApp"}
        result = client.applications.get_application("abc-123")
        mock_req.assert_called_once_with("GET", "/governance/application/abc-123", params=None)
        assert result["name"] == "TestApp"

    @patch("gia.client.IGAClient._request")
    def test_get_application_with_fields(self, mock_req, client):
        mock_req.return_value = {"name": "TestApp"}
        client.applications.get_application("abc-123", fields="name,id")
        mock_req.assert_called_once_with(
            "GET", "/governance/application/abc-123",
            params={"_fields": "name,id"},
        )

    @patch("gia.client.IGAClient._request")
    def test_update_application(self, mock_req, client):
        mock_req.return_value = {"id": "abc-123", "name": "Updated"}
        result = client.applications.update_application("abc-123", {"name": "Updated"})
        mock_req.assert_called_once_with("PUT", "/governance/application/abc-123", json={"name": "Updated"})

    @patch("gia.client.IGAClient._request")
    def test_delete_application(self, mock_req, client):
        mock_req.return_value = {}
        client.applications.delete_application("abc-123")
        mock_req.assert_called_once_with("DELETE", "/governance/application/abc-123")

    @patch("gia.client.IGAClient._request")
    def test_add_object_type(self, mock_req, client):
        payload = {"id": "__ACCOUNT__", "type": "account", "properties": {}}
        mock_req.return_value = payload
        client.applications.add_object_type("abc-123", payload)
        mock_req.assert_called_once_with(
            "POST", "/governance/application/abc-123/objectType", json=payload, params=None,
        )

    @patch("gia.client.IGAClient._request")
    def test_get_object_type(self, mock_req, client):
        mock_req.return_value = {"id": "__ACCOUNT__"}
        client.applications.get_object_type("abc-123", "__ACCOUNT__")
        mock_req.assert_called_once_with("GET", "/governance/application/abc-123/objectType/__ACCOUNT__", params=None)

    @patch("gia.client.IGAClient._request")
    def test_update_object_type(self, mock_req, client):
        payload = {"id": "__ACCOUNT__", "type": "account", "properties": {"name": {}}}
        mock_req.return_value = payload
        client.applications.update_object_type("abc-123", "__ACCOUNT__", payload)
        mock_req.assert_called_once_with(
            "PUT", "/governance/application/abc-123/objectType/__ACCOUNT__", json=payload,
        )

    @patch("gia.client.IGAClient._request")
    def test_delete_object_type(self, mock_req, client):
        mock_req.return_value = {"message": "Object type deleted successfully"}
        client.applications.delete_object_type("abc-123", "__ACCOUNT__")
        mock_req.assert_called_once_with("DELETE", "/governance/application/abc-123/objectType/__ACCOUNT__")

    @patch("gia.client.IGAClient._request")
    def test_get_object_type_schema(self, mock_req, client):
        mock_req.return_value = {"$schema": "http://json-schema.org/draft-03/schema"}
        client.applications.get_object_type_schema("abc-123", "__GROUP__")
        mock_req.assert_called_once_with("GET", "/governance/application/abc-123/__GROUP__/schema", params=None)

    @patch("gia.client.IGAClient._request")
    def test_get_upload_status(self, mock_req, client):
        mock_req.return_value = {"id": "upload-1", "status": "COMPLETED"}
        client.applications.get_upload_status("abc-123", "upload-1")
        mock_req.assert_called_once_with("GET", "/governance/application/abc-123/upload/:upload-1", params=None)

    @patch("gia.client.IGAClient._request")
    def test_get_upload_failures(self, mock_req, client):
        mock_req.return_value = {"result": [], "totalCount": 0}
        client.applications.get_upload_failures("abc-123", "upload-1")
        mock_req.assert_called_once_with("GET", "/governance/application/abc-123/upload/:upload-1/failures", params=None)

    @patch("gia.client.IGAClient._request")
    def test_list_accounts(self, mock_req, client):
        mock_req.return_value = {"result": [{"id": "acct-1"}], "totalCount": 1}
        result = client.applications.list_accounts("abc-123")
        assert result == [{"id": "acct-1"}]

    @patch("gia.client.IGAClient._request")
    def test_get_account(self, mock_req, client):
        mock_req.return_value = {"id": "acct-1"}
        client.applications.get_account("abc-123", "acct-1")
        mock_req.assert_called_once_with("GET", "/governance/application/abc-123/account/acct-1", params=None)

    @patch("gia.client.IGAClient._request")
    def test_list_resources(self, mock_req, client):
        mock_req.return_value = {"result": [{"id": "res-1"}], "totalCount": 1}
        result = client.applications.list_resources("abc-123")
        assert result == [{"id": "res-1"}]

    @patch("gia.client.IGAClient._request")
    def test_get_resource(self, mock_req, client):
        mock_req.return_value = {"id": "res-1"}
        client.applications.get_resource("abc-123", "res-1")
        mock_req.assert_called_once_with("GET", "/governance/application/abc-123/resource/res-1", params=None)

    @patch("gia.client.IGAClient._request")
    def test_find_application_by_name_found(self, mock_req, client):
        mock_req.return_value = {
            "result": [{"id": "abc-123", "name": "MyApp"}],
            "totalCount": 1,
        }
        result = client.applications.find_application_by_name("MyApp")
        assert result["id"] == "abc-123"

    @patch("gia.client.IGAClient._request")
    def test_find_application_by_name_not_found(self, mock_req, client):
        mock_req.return_value = {"result": [], "totalCount": 0}
        result = client.applications.find_application_by_name("NonExistent")
        assert result is None


class TestPagination:

    @patch("gia.client.IGAClient._request")
    def test_auto_paginates(self, mock_req, client):
        mock_req.side_effect = [
            {"result": [{"id": "1"}, {"id": "2"}], "totalCount": 3, "resultCount": 2},
            {"result": [{"id": "3"}], "totalCount": 3, "resultCount": 1},
        ]
        results = client.api_get_paginated("/governance/application", page_size=2)
        assert len(results) == 3
        assert mock_req.call_count == 2

    @patch("gia.client.IGAClient._request")
    def test_respects_max_pages(self, mock_req, client):
        mock_req.return_value = {"result": [{"id": "1"}], "totalCount": 100, "resultCount": 1}
        results = client.api_get_paginated("/governance/application", page_size=1, max_pages=2)
        assert mock_req.call_count == 2

    @patch("gia.client.IGAClient._request")
    def test_single_page(self, mock_req, client):
        mock_req.return_value = {"result": [{"id": "1"}], "totalCount": 1, "resultCount": 1}
        results = client.api_get_paginated("/governance/application")
        assert len(results) == 1
        assert mock_req.call_count == 1


class TestResponseHandling:

    def test_404_raises_not_found(self, client):
        mock_resp = MagicMock()
        mock_resp.status_code = 404
        with pytest.raises(IGANotFoundError):
            client._handle_response(mock_resp)

    def test_500_raises_client_error(self, client):
        mock_resp = MagicMock()
        mock_resp.status_code = 500
        mock_resp.json.return_value = {"message": "Internal error"}
        with pytest.raises(IGAClientError) as exc_info:
            client._handle_response(mock_resp)
        assert exc_info.value.status_code == 500

    def test_204_returns_empty_dict(self, client):
        mock_resp = MagicMock()
        mock_resp.status_code = 204
        mock_resp.content = b""
        result = client._handle_response(mock_resp)
        assert result == {}