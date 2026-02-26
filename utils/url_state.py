"""URL State — helpers for reading/writing URL query parameters."""

from urllib.parse import parse_qs, urlencode


def get_param(search: str, key: str, default=None) -> str:
    """Extract a query parameter from URL search string."""
    if not search:
        return default
    params = parse_qs(search.lstrip("?"))
    values = params.get(key, [])
    return values[0] if values else default


def set_params(base_path: str, **kwargs) -> str:
    """Build a URL with query parameters."""
    filtered = {k: v for k, v in kwargs.items() if v is not None}
    if not filtered:
        return base_path
    return f"{base_path}?{urlencode(filtered)}"
