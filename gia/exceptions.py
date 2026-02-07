"""Exception types for the IGA client."""


class IGAClientError(Exception):
    """Raised when the IGA API returns an error response."""

    def __init__(self, message: str, status_code: int | None = None, details: list | None = None):
        self.message = message
        self.status_code = status_code
        self.details = details or []
        super().__init__(message)

    def __str__(self) -> str:
        parts = [self.message]
        if self.status_code:
            parts.append(f"(HTTP {self.status_code})")
        return " ".join(parts)


class IGAAuthError(IGAClientError):
    """Raised when authentication or token refresh fails."""
    pass


class IGANotFoundError(IGAClientError):
    """Raised when a requested resource is not found (HTTP 404)."""
    pass