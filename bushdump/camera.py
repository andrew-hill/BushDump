"""HTTP client for the trail camera's local API.

See docs/camera-api.md for the wire protocol. The camera serves unencrypted
HTTP on its own WiFi AP (default 192.168.1.8).
"""

from __future__ import annotations

import time
from collections.abc import Iterator
from dataclasses import dataclass
from pathlib import Path

# httpx is imported lazily inside CameraClient so the pure helpers above
# (CameraFile, parse_file_page) and the sync logic stay importable without it.

DEFAULT_HOST = "192.168.1.8"
MediaType = str  # "Photo" | "Video"


@dataclass(frozen=True, slots=True)
class CameraFile:
    """One entry from a /Storage?GetFilePage listing."""

    name: str  # "n"
    timestamp: int  # "dt" — unix seconds
    size: int  # "s" — bytes
    fid: str  # "fid" — file ID used for download/thumb/delete

    @classmethod
    def from_json(cls, obj: dict) -> CameraFile:
        return cls(
            name=obj["n"],
            timestamp=int(obj["dt"]),
            size=int(obj["s"]),
            fid=str(obj["fid"]),
        )


def parse_file_page(data: object) -> list[CameraFile]:
    """Parse a GetFilePage response into CameraFiles.

    The firmware's envelope isn't fully pinned down, so we tolerate either a
    bare list or a dict wrapping the list under a common key. Entries missing
    required fields are skipped. TODO: tighten once confirmed against a device.
    """
    if isinstance(data, dict):
        for key in ("files", "Files", "list", "data"):
            if isinstance(data.get(key), list):
                data = data[key]
                break
    if not isinstance(data, list):
        return []
    out: list[CameraFile] = []
    for obj in data:
        if isinstance(obj, dict) and {"n", "dt", "s", "fid"} <= obj.keys():
            out.append(CameraFile.from_json(obj))
    return out


class CameraClient:
    """Thin wrapper over the camera HTTP API."""

    def __init__(self, host: str = DEFAULT_HOST, timeout: float = 10.0) -> None:
        import httpx

        self.host = host
        self.base_url = f"http://{host}"
        self._client = httpx.Client(base_url=self.base_url, timeout=timeout)

    def __enter__(self) -> CameraClient:
        return self

    def __exit__(self, *exc: object) -> None:
        self.close()

    def close(self) -> None:
        self._client.close()

    # --- readiness ---------------------------------------------------------

    def is_ready(self) -> bool:
        """True if the camera HTTP server is responding."""
        import httpx

        try:
            self._client.get("/SetMode", params={"Storage": ""}, timeout=2.0)
            return True
        except httpx.HTTPError:
            return False

    def wait_until_ready(self, timeout: float = 30.0, interval: float = 1.0) -> bool:
        """Poll until the camera answers HTTP, or give up after `timeout`s."""
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            if self.is_ready():
                return True
            time.sleep(interval)
        return False

    # --- API calls ---------------------------------------------------------

    def enter_storage_mode(self) -> None:
        self._client.get("/SetMode", params={"Storage": ""}).raise_for_status()

    def iter_files(self, media_type: MediaType) -> Iterator[CameraFile]:
        """Yield every file of a type, walking pages until one comes back empty."""
        page = 0
        while True:
            resp = self._client.get("/Storage", params={"GetFilePage": page, "type": media_type})
            resp.raise_for_status()
            files = parse_file_page(resp.json())
            if not files:
                return
            yield from files
            page += 1

    def download(self, file: CameraFile, dest_dir: Path) -> Path:
        """Stream a file to dest_dir. Skips if a same-size copy already exists."""
        dest_dir.mkdir(parents=True, exist_ok=True)
        dest = dest_dir / file.name
        if dest.exists() and dest.stat().st_size == file.size:
            return dest
        tmp = dest.with_suffix(dest.suffix + ".part")
        with self._client.stream("GET", "/Storage", params={"Download": file.fid}) as resp:
            resp.raise_for_status()
            with tmp.open("wb") as fh:
                for chunk in resp.iter_bytes():
                    fh.write(chunk)
        tmp.replace(dest)
        return dest

    def describe(self) -> str:
        """One-line summary for the add-confirm step (best-effort file counts)."""
        counts = []
        for media in ("Photo", "Video"):
            try:
                counts.append(f"{sum(1 for _ in self.iter_files(media))} {media.lower()}s")
            except Exception:
                counts.append(f"? {media.lower()}s")
        return f"camera at {self.host} — " + ", ".join(counts)

    def power_off(self) -> None:
        """Turn the camera's WiFi off (saves its battery)."""
        self._client.get("/Misc", params={"PowerOff": ""})
