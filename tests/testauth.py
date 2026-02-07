"""Tests for OAuth2 client credentials auth."""

import time
from unittest.mock import patch, MagicMock

import pytest

from gia.auth import OAuth2ClientCredentials
from gia.exceptions import IGAAuthError


class TestOAuth2ClientCredentials:

    def test_fetches_token_on_first_access(self):
        auth = OAuth2ClientCredentials("cid", "csec", "https://example.com/token")

        mock_resp = MagicMock()
        mock_resp.json.return_value = {"access_token": "tok-123", "expires_in": 3600}
        mock_resp.raise_for_status = MagicMock()

        with patch("gia.auth.requests.post", return_value=mock_resp) as mock_post:
            token = auth.access_token
            assert token == "tok-123"
            mock_post.assert_called_once()
            call_data = mock_post.call_args[1]["data"]
            assert call_data["grant_type"] == "client_credentials"
            assert call_data["client_id"] == "cid"
            assert call_data["client_secret"] == "csec"

    def test_caches_token(self):
        auth = OAuth2ClientCredentials("cid", "csec", "https://example.com/token")

        mock_resp = MagicMock()
        mock_resp.json.return_value = {"access_token": "tok-123", "expires_in": 3600}
        mock_resp.raise_for_status = MagicMock()

        with patch("gia.auth.requests.post", return_value=mock_resp) as mock_post:
            _ = auth.access_token
            _ = auth.access_token
            assert mock_post.call_count == 1

    def test_refreshes_expired_token(self):
        auth = OAuth2ClientCredentials("cid", "csec", "https://example.com/token")
        auth._access_token = "old"
        auth._expires_at = time.time() - 10  # already expired

        mock_resp = MagicMock()
        mock_resp.json.return_value = {"access_token": "new-tok", "expires_in": 3600}
        mock_resp.raise_for_status = MagicMock()

        with patch("gia.auth.requests.post", return_value=mock_resp):
            token = auth.access_token
            assert token == "new-tok"

    def test_includes_scopes_when_set(self):
        auth = OAuth2ClientCredentials("cid", "csec", "https://example.com/token", scopes="fr:idm:*")

        mock_resp = MagicMock()
        mock_resp.json.return_value = {"access_token": "tok", "expires_in": 3600}
        mock_resp.raise_for_status = MagicMock()

        with patch("gia.auth.requests.post", return_value=mock_resp) as mock_post:
            _ = auth.access_token
            call_data = mock_post.call_args[1]["data"]
            assert call_data["scope"] == "fr:idm:*"

    def test_raises_on_request_failure(self):
        auth = OAuth2ClientCredentials("cid", "csec", "https://example.com/token")

        import requests as req
        with patch("gia.auth.requests.post", side_effect=req.ConnectionError("nope")):
            with pytest.raises(IGAAuthError, match="Token request failed"):
                _ = auth.access_token