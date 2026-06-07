"""Incremental, id-based sync logic.

We persist the id of the newest downloaded file and, on the next run, only pull
files with a higher id than that watermark. Pure functions here so they're easy
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
    watermark: int | None,
) -> list[CameraFile]:
    """Return files strictly newer than `watermark`, lowest id first.

    `watermark` is the `id` of the newest file downloaded on a prior run, or
    None for a first run (download everything).
    """
    cutoff = watermark if watermark is not None else -1
    newer = [f for f in available if f.id > cutoff]
    return sorted(newer, key=lambda f: f.id)


def next_watermark(downloaded: Iterable[CameraFile], previous: int | None) -> int | None:
    """Compute the new watermark after a run: the max id seen."""
    ids = [f.id for f in downloaded]
    if not ids:
        return previous
    newest = max(ids)
    return newest if previous is None else max(newest, previous)
