"""Base HTTP client for PingOne IGA API."""

import logging
from urllib.parse import urljoin

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from .auth import OAuth2ClientCredentials
from .exceptions import IGAClientError, IGANotFoundError

log = logging.getLogger(__name__)

DEFAULT_PAGE_SIZE = 50
MAX_RETRIES = 3
RETRY_BACKOFF = 0.5
RETRY_STATUS_CODES = (429, 500, 502, 503, 504)


class IGAClient:
    """Low-level REST client for PingOne Advanced Identity Cloud — IGA.

    Handles OAuth2 authentication, retries, and pagination.

    Args:
        base_url: Tenant URL (e.g. ``https://mytenant.forgeblocks.com``).
        client_id: OAuth2 client ID.
        client_secret: OAuth2 client secret.
        token_endpoint: Full URL for the token endpoint.
        scopes: Optional OAuth2 scopes string.
        page_size: Default page size for paginated requests.
    """

    def __init__(
        self,
        base_url: str,
        client_id: str,
        client_secret: str,
        token_endpoint: str,
        scopes: str | None = None,
        page_size: int = DEFAULT_PAGE_SIZE,
    ):
        self.base_url = base_url.rstrip("/")
        self.page_size = page_size
        self._auth = OAuth2ClientCredentials(client_id, client_secret, token_endpoint, scopes)
        self._session = self._build_session()

        # Lazily initialized sub-APIs
        self._applications: "ApplicationsAPI | None" = None

    @property
    def applications(self) -> "ApplicationsAPI":
        """Access the ``/governance/application`` endpoints."""
        # Import here to avoid circular dependency
        from .applications import ApplicationsAPI
        if self._applications is None:
            self._applications = ApplicationsAPI(self)
        return self._applications

    # ------------------------------------------------------------------
    # HTTP helpers
    # ------------------------------------------------------------------

    def api_get(self, path: str, params: dict | None = None) -> dict:
        return self._request("GET", path, params=params)

    def api_post(self, path: str, json: dict | None = None, params: dict | None = None, **kwargs) -> dict:
        return self._request("POST", path, json=json, params=params, **kwargs)

    def api_put(self, path: str, json: dict | None = None) -> dict:
        return self._request("PUT", path, json=json)

    def api_delete(self, path: str) -> dict:
        return self._request("DELETE", path)

    def api_get_paginated(
        self,
        path: str,
        params: dict | None = None,
        page_size: int | None = None,
        max_pages: int | None = None,
    ) -> list[dict]:
        """Fetch all pages from a paginated list endpoint.

        Uses ``_pageSize`` and ``_pagedResultsOffset`` parameters.
        Returns the combined ``result`` list across all pages.
        """
        page_size = page_size or self.page_size
        params = dict(params or {})
        params["_pageSize"] = page_size
        offset = params.pop("_pagedResultsOffset", 0)

        all_results: list[dict] = []
        pages_fetched = 0

        while True:
            params["_pagedResultsOffset"] = offset
            body = self.api_get(path, params=params)

            results = body.get("result", [])
            all_results.extend(results)
            pages_fetched += 1

            total = body.get("totalCount", 0)
            if not results or len(all_results) >= total:
                break
            if max_pages and pages_fetched >= max_pages:
                log.info("Stopped pagination after %d pages (%d/%d results)", pages_fetched, len(all_results), total)
                break

            offset += page_size

        return all_results

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _build_url(self, path: str) -> str:
        # Paths from the OpenAPI spec are relative to /iga
        if not path.startswith("/"):
            path = f"/{path}"
        if not path.startswith("/iga"):
            path = f"/iga{path}"
        return f"{self.base_url}{path}"

    def _headers(self) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {self._auth.access_token}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

    def _request(self, method: str, path: str, **kwargs) -> dict:
        url = self._build_url(path)
        headers = self._headers()

        # For multipart uploads, drop Content-Type so requests sets it
        if "files" in kwargs:
            headers.pop("Content-Type", None)

        log.debug("%s %s", method, url)
        try:
            resp = self._session.request(method, url, headers=headers, timeout=60, **kwargs)
        except requests.RequestException as exc:
            raise IGAClientError(f"Request failed: {exc}") from exc

        return self._handle_response(resp)

    def _handle_response(self, resp: requests.Response) -> dict:
        if resp.status_code == 404:
            raise IGANotFoundError("Resource not found", status_code=404)

        if resp.status_code >= 400:
            try:
                body = resp.json()
                message = body.get("message", body.get("error", resp.text))
                details = body.get("details", [])
            except Exception:
                message = resp.text
                details = []
            raise IGAClientError(message, status_code=resp.status_code, details=details)

        if resp.status_code == 204 or not resp.content:
            return {}

        return resp.json()

    @staticmethod
    def _build_session() -> requests.Session:
        session = requests.Session()
        retry = Retry(
            total=MAX_RETRIES,
            backoff_factor=RETRY_BACKOFF,
            status_forcelist=RETRY_STATUS_CODES,
            allowed_methods=["GET", "POST", "PUT", "DELETE"],
        )
        adapter = HTTPAdapter(max_retries=retry)
        session.mount("https://", adapter)
        session.mount("http://", adapter)
        return session