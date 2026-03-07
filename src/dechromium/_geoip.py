"""GeoIP database manager — maps proxy IPs to geographic data."""

from __future__ import annotations

import dataclasses
import gzip
import json
import logging
import os
import socket
import tempfile
import warnings
from datetime import UTC, datetime, timedelta
from pathlib import Path
from urllib.error import HTTPError
from urllib.parse import urlparse
from urllib.request import Request, urlopen

logger = logging.getLogger(__name__)

_META_FILE = ".geoip_meta.json"
_DB_NAME = "dbip-city-lite.mmdb"
_STALE_DAYS = 35

# Fallback when DB-IP Lite doesn't return timezone for an IP.
# Primary timezone per country (covers datacentre / VPN locations).
_COUNTRY_TIMEZONES: dict[str, str] = {
    "AD": "Europe/Andorra",
    "AE": "Asia/Dubai",
    "AF": "Asia/Kabul",
    "AL": "Europe/Tirane",
    "AM": "Asia/Yerevan",
    "AR": "America/Argentina/Buenos_Aires",
    "AT": "Europe/Vienna",
    "AU": "Australia/Sydney",
    "AZ": "Asia/Baku",
    "BA": "Europe/Sarajevo",
    "BD": "Asia/Dhaka",
    "BE": "Europe/Brussels",
    "BG": "Europe/Sofia",
    "BH": "Asia/Bahrain",
    "BR": "America/Sao_Paulo",
    "BY": "Europe/Minsk",
    "CA": "America/Toronto",
    "CH": "Europe/Zurich",
    "CL": "America/Santiago",
    "CN": "Asia/Shanghai",
    "CO": "America/Bogota",
    "CR": "America/Costa_Rica",
    "CY": "Asia/Nicosia",
    "CZ": "Europe/Prague",
    "DE": "Europe/Berlin",
    "DK": "Europe/Copenhagen",
    "DO": "America/Santo_Domingo",
    "DZ": "Africa/Algiers",
    "EC": "America/Guayaquil",
    "EE": "Europe/Tallinn",
    "EG": "Africa/Cairo",
    "ES": "Europe/Madrid",
    "FI": "Europe/Helsinki",
    "FR": "Europe/Paris",
    "GB": "Europe/London",
    "GE": "Asia/Tbilisi",
    "GR": "Europe/Athens",
    "HK": "Asia/Hong_Kong",
    "HR": "Europe/Zagreb",
    "HU": "Europe/Budapest",
    "ID": "Asia/Jakarta",
    "IE": "Europe/Dublin",
    "IL": "Asia/Jerusalem",
    "IN": "Asia/Kolkata",
    "IQ": "Asia/Baghdad",
    "IR": "Asia/Tehran",
    "IS": "Atlantic/Reykjavik",
    "IT": "Europe/Rome",
    "JO": "Asia/Amman",
    "JP": "Asia/Tokyo",
    "KE": "Africa/Nairobi",
    "KG": "Asia/Bishkek",
    "KH": "Asia/Phnom_Penh",
    "KR": "Asia/Seoul",
    "KW": "Asia/Kuwait",
    "KZ": "Asia/Almaty",
    "LB": "Asia/Beirut",
    "LT": "Europe/Vilnius",
    "LU": "Europe/Luxembourg",
    "LV": "Europe/Riga",
    "MA": "Africa/Casablanca",
    "MD": "Europe/Chisinau",
    "ME": "Europe/Podgorica",
    "MK": "Europe/Skopje",
    "MM": "Asia/Yangon",
    "MN": "Asia/Ulaanbaatar",
    "MX": "America/Mexico_City",
    "MY": "Asia/Kuala_Lumpur",
    "NG": "Africa/Lagos",
    "NL": "Europe/Amsterdam",
    "NO": "Europe/Oslo",
    "NZ": "Pacific/Auckland",
    "OM": "Asia/Muscat",
    "PA": "America/Panama",
    "PE": "America/Lima",
    "PH": "Asia/Manila",
    "PK": "Asia/Karachi",
    "PL": "Europe/Warsaw",
    "PT": "Europe/Lisbon",
    "QA": "Asia/Qatar",
    "RO": "Europe/Bucharest",
    "RS": "Europe/Belgrade",
    "RU": "Europe/Moscow",
    "SA": "Asia/Riyadh",
    "SE": "Europe/Stockholm",
    "SG": "Asia/Singapore",
    "SI": "Europe/Ljubljana",
    "SK": "Europe/Bratislava",
    "TH": "Asia/Bangkok",
    "TN": "Africa/Tunis",
    "TR": "Europe/Istanbul",
    "TW": "Asia/Taipei",
    "UA": "Europe/Kyiv",
    "US": "America/New_York",
    "UZ": "Asia/Tashkent",
    "VN": "Asia/Ho_Chi_Minh",
    "ZA": "Africa/Johannesburg",
}


@dataclasses.dataclass(frozen=True, slots=True)
class GeoInfo:
    """Geographic information for an IP address."""

    country_code: str  # "US", "JP", "DE"
    timezone: str  # "America/New_York"
    latitude: float  # 40.7128
    longitude: float  # -74.0060
    city: str  # "New York"


def download(data_dir: Path, *, progress: bool = True) -> Path:
    """Download DB-IP City Lite MMDB to ``{data_dir}/data/geoip/``.

    Tries current month first, falls back to previous month.
    Uses atomic write via tmpfile + ``os.replace()``.

    Returns:
        Path to the downloaded MMDB file.
    """
    dest_dir = data_dir / "data" / "geoip"
    dest_dir.mkdir(parents=True, exist_ok=True)
    dest = dest_dir / _DB_NAME

    now = datetime.now(UTC)
    candidates = [
        now.strftime("%Y-%m"),
        (now.replace(day=1) - timedelta(days=1)).strftime("%Y-%m"),
    ]

    last_err: Exception | None = None
    for month in candidates:
        url = f"https://download.db-ip.com/free/dbip-city-lite-{month}.mmdb.gz"
        if progress:
            print(f"  Downloading GeoIP database ({month})...")

        try:
            req = Request(url, headers={"User-Agent": "dechromium"})
            with urlopen(req, timeout=60) as resp:
                compressed = resp.read()
        except HTTPError as exc:
            last_err = exc
            if progress:
                print(f"  {month} not available, trying previous month...")
            continue

        data = gzip.decompress(compressed)

        # Atomic write
        fd, tmp_path = tempfile.mkstemp(dir=dest_dir, suffix=".mmdb.tmp")
        try:
            os.write(fd, data)
            os.close(fd)
            os.replace(tmp_path, dest)
        except BaseException:
            os.close(fd) if not os.get_inheritable(fd) else None
            with _suppress():
                os.unlink(tmp_path)
            raise

        # Write metadata
        meta = {"downloaded_at": now.isoformat(), "month": month, "size": len(data)}
        (dest_dir / _META_FILE).write_text(json.dumps(meta, indent=2) + "\n")

        if progress:
            print(f"  GeoIP database saved ({len(data) / 1024 / 1024:.1f} MB)")
        return dest

    msg = f"Failed to download GeoIP database: {last_err}"
    raise OSError(msg)


def get_reader(data_dir: Path):
    """Get a maxminddb Reader, downloading the database if missing.

    Warns if the database is older than 35 days.

    Returns:
        ``maxminddb.Reader`` instance.
    """
    import maxminddb

    db_path = data_dir / "data" / "geoip" / _DB_NAME
    if not db_path.exists():
        download(data_dir, progress=False)

    # Check staleness
    meta_path = db_path.parent / _META_FILE
    if meta_path.exists():
        with _suppress():
            meta = json.loads(meta_path.read_text())
            downloaded = datetime.fromisoformat(meta["downloaded_at"])
            age = datetime.now(UTC) - downloaded
            if age > timedelta(days=_STALE_DAYS):
                warnings.warn(
                    f"GeoIP database is {age.days} days old. "
                    "Run `dechromium download-geoip` to update.",
                    UserWarning,
                    stacklevel=2,
                )

    return maxminddb.open_database(str(db_path))


def lookup(ip: str, data_dir: Path) -> GeoInfo | None:
    """Look up geographic info for an IP address.

    Returns:
        ``GeoInfo`` or ``None`` if the IP is not found.
    """
    try:
        reader = get_reader(data_dir)
    except Exception:
        logger.debug("GeoIP lookup failed: could not open database", exc_info=True)
        return None

    try:
        record = reader.get(ip)
    except Exception:
        logger.debug("GeoIP lookup failed for %s", ip, exc_info=True)
        return None

    if not record or not isinstance(record, dict):
        return None

    country = record.get("country", {})
    country_code = country.get("iso_code", "")
    if not country_code:
        return None

    location = record.get("location", {})
    timezone = location.get("time_zone", "") or _COUNTRY_TIMEZONES.get(country_code, "")
    latitude = location.get("latitude")
    longitude = location.get("longitude")

    if latitude is None or longitude is None:
        return None

    city_data = record.get("city", {})
    names = city_data.get("names", {})
    city = names.get("en", "")

    return GeoInfo(
        country_code=country_code,
        timezone=timezone,
        latitude=float(latitude),
        longitude=float(longitude),
        city=city,
    )


def resolve_public_ip() -> str | None:
    """Detect the machine's public IP address.

    Tries multiple services for reliability. Returns IP string or None.
    """
    services = [
        "https://api.ipify.org",
        "https://ifconfig.me/ip",
        "https://checkip.amazonaws.com",
    ]
    for url in services:
        try:
            req = Request(url, headers={"User-Agent": "dechromium"})
            with urlopen(req, timeout=5) as resp:
                ip = resp.read().decode().strip()
                if ip:
                    return ip
        except Exception:
            continue
    return None


def resolve_exit_ip(proxy: str) -> str | None:
    """Resolve the actual exit IP by making a request through the proxy.

    For SOCKS5 proxies, the proxy server IP and exit IP are often different.
    This queries an external service through the proxy to find the real exit IP.

    Args:
        proxy: Full proxy URL like ``socks5://user:pass@host:1080``.

    Returns:
        Exit IP address string, or None if resolution fails.
    """
    import subprocess

    services = [
        "http://api.ipify.org",
        "http://ifconfig.me/ip",
        "http://checkip.amazonaws.com",
    ]
    for url in services:
        try:
            result = subprocess.run(
                ["curl", "-s", "--max-time", "10", "--proxy", proxy, url],
                capture_output=True,
                text=True,
                timeout=15,
            )
            ip = result.stdout.strip()
            if ip and _is_valid_ip(ip):
                return ip
        except Exception:
            continue
    return None


def _is_valid_ip(s: str) -> bool:
    """Check if a string is a valid IPv4 or IPv6 address."""
    for family in (socket.AF_INET, socket.AF_INET6):
        try:
            socket.inet_pton(family, s)
            return True
        except OSError:
            continue
    return False


def resolve_proxy_ip(proxy: str) -> str:
    """Extract hostname from proxy URL and resolve to IP address.

    Args:
        proxy: Proxy URL like ``socks5://host:1080`` or ``http://user:pass@host:8080``.

    Returns:
        Resolved IP address string.

    Raises:
        OSError: If DNS resolution fails.
    """
    parsed = urlparse(proxy)
    hostname = parsed.hostname
    if not hostname:
        msg = f"Cannot extract hostname from proxy URL: {proxy}"
        raise ValueError(msg)

    # Fast path: already an IP address
    try:
        socket.inet_pton(socket.AF_INET, hostname)
        return hostname
    except OSError:
        pass
    try:
        socket.inet_pton(socket.AF_INET6, hostname)
        return hostname
    except OSError:
        pass

    # DNS resolution
    results = socket.getaddrinfo(hostname, None, socket.AF_UNSPEC, socket.SOCK_STREAM)
    if not results:
        msg = f"Could not resolve proxy hostname: {hostname}"
        raise OSError(msg)

    return results[0][4][0]


class _suppress:
    """Minimal context manager that suppresses all exceptions."""

    def __enter__(self):
        return self

    def __exit__(self, *_):
        return True
