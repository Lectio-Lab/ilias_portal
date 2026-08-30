"""Local ILIAS URL guards for server-side requests."""

from __future__ import annotations

import ipaddress
import re
from urllib.parse import urlparse

from .client import BASE_URL

_ALLOWED_HOST = urlparse(BASE_URL).hostname or "ovidius.uni-tuebingen.de"
_ALLOWED_PATHS = (
    re.compile(r"^/goto\.php/(file|fold|exc|frm)/\d+/?$"),
    re.compile(r"^/ilias\.php$"),
)


def validate_ilias_download_url(url: str) -> str:
    """
    Restrict download proxying to HTTPS ILIAS asset URLs on the configured host.

    Blocks SSRF to internal networks, arbitrary hosts, and non-asset paths.
    """
    parsed = urlparse(url.strip())
    if parsed.scheme != "https":
        raise ValueError("Download URL must use HTTPS.")

    if not parsed.hostname:
        raise ValueError("Download URL must include a hostname.")

    if parsed.hostname != _ALLOWED_HOST:
        raise ValueError(
            f"Download URL must point to {_ALLOWED_HOST}, not {parsed.hostname}."
        )

    if parsed.port not in (None, 443):
        raise ValueError("Download URL must use the default HTTPS port.")

    if parsed.username or parsed.password:
        raise ValueError("Download URL must not include embedded credentials.")

    try:
        ip = ipaddress.ip_address(parsed.hostname)
        if ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_reserved:
            raise ValueError("Download URL must not target a private or local address.")
    except ValueError as exc:
        if "does not appear to be an IPv4 or IPv6 address" not in str(exc):
            raise

    if parsed.params or parsed.fragment:
        raise ValueError("Download URL must not include params or fragments.")

    if not any(pattern.match(parsed.path) for pattern in _ALLOWED_PATHS):
        raise ValueError(
            "Download URL must be an ILIAS file, folder, exercise, forum, or ilias.php link."
        )

    if parsed.path == "/ilias.php" and not parsed.query:
        raise ValueError("ilias.php download URLs must include query parameters.")

    return url
