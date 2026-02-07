"""OAuth2 client_credentials token management."""

import time
import logging
import requests

from .exceptions import IGAAuthError

log = logging.getLogger(__name__)


class OAuth2ClientCredentials:
    """Fetches and caches an OAuth2 access token using the client_credentials grant.

    Automatically refreshes the token when it expires (with a small buffer).
    """

    TOKEN_EXPIRY_BUFFER_SECONDS = 30

    def __init__(self, client_id: str, client_secret: str, token_endpoint: str, scopes: str | None = None):
        self.client_id = client_id
        self.client_secret = client_secret
        self.token_endpoint = token_endpoint
        self.scopes = scopes

        self._access_token: str | None = None
        self._expires_at: float = 0.0

    @property
    def access_token(self) -> str:
        """Return a valid access token, fetching or refreshing as needed."""
        if self._is_expired():
            self._fetch_token()
        return self._access_token  # type: ignore[return-value]

    def _is_expired(self) -> bool:
        if self._access_token is None:
            return True
        return time.time() >= (self._expires_at - self.TOKEN_EXPIRY_BUFFER_SECONDS)

    def _fetch_token(self) -> None:
        data: dict[str, str] = {
            "grant_type": "client_credentials",
            "client_id": self.client_id,
            "client_secret": self.client_secret,
        }
        if self.scopes:
            data["scope"] = self.scopes

        log.debug("Requesting access token from %s", self.token_endpoint)
        try:
            resp = requests.post(self.token_endpoint, data=data, timeout=30)
            resp.raise_for_status()
        except requests.RequestException as exc:
            raise IGAAuthError(f"Token request failed: {exc}") from exc

        body = resp.json()
        self._access_token = body["access_token"]
        expires_in = body.get("expires_in", 3600)
        self._expires_at = time.time() + expires_in
        log.debug("Access token acquired, expires in %ds", expires_in)