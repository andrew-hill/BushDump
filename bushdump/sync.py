"""Incremental, date-based sync logic.

We persist the date string of the newest downloaded file and, on the next run,
only pull files with a strictly later date. Pure functions here so they're easy
to test without a camera.
"""

from __future__ import annotations

from collections.abc import Iterable
from typing import TYPE_CHECKING

from bushdump.camera import CameraFile

if TYPE_CHECKING:
    from bushdump.config import Camera


def cameras_present(cameras: Iterable[Camera], present_addresses: Iterable[str]) -> list[Camera]:
    """Pick configured cameras whose BLE address showed up in a scan (case-insensitive)."""
    present = {a.lower() for a in present_addresses}
    return [c for c in cameras if c.ble_address and c.ble_address.lower() in present]


def files_to_download(
    available: Iterable[CameraFile],
    watermark: str | None,
) -> list[CameraFile]:
    """Return files strictly newer than `watermark`, oldest first.

    `watermark` is the `date` of the newest file downloaded on a prior run
    ("YYYY-MM-DD HH:MM:SS"), or None for a first run (download everything).
    Legacy int watermarks from the old id-based scheme are treated as None so
    they trigger a full re-scan (already-on-disk files are skipped by size).
    """
    if watermark is None or isinstance(watermark, int):
        newer = list(available)
    else:
        newer = [f for f in available if f.date > watermark]
    return sorted(newer, key=lambda f: (f.date, f.id))
