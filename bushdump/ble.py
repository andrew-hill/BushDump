"""BLE: list nearby devices and wake a camera's WiFi AP.

Waking writes the magic value to service 0xFF00 / characteristic 0xFF01, after
which the camera brings up its WiFi access point. See docs/camera-api.md.

On macOS, BLE peripherals are identified by a CoreBluetooth UUID (not a MAC).
`discover` lists everything nearby so you can pick yours in `bushdump add`.
"""

from __future__ import annotations

import asyncio
from collections.abc import Callable

from bleak import BleakClient, BleakScanner

SERVICE_UUID = "0000ff00-0000-1000-8000-00805f9b34fb"
CHARACTERISTIC_UUID = "0000ff01-0000-1000-8000-00805f9b34fb"
WIFI_ON_PAYLOAD = b"BT_Key_On"  # hex 42-54-5F-4B-65-79-5F-4F-6E


async def discover(timeout: float = 8.0) -> list[tuple[str, str | None]]:
    """Scan for BLE devices, returning (address, name) for each one found."""
    devices = await BleakScanner.discover(timeout=timeout)
    return [(d.address, d.name) for d in devices]


async def watch(
    seconds: float = 10.0,
    on_found: Callable[[str, str | None], None] | None = None,
) -> list[tuple[str, str | None]]:
    """Live-scan for BLE devices, calling `on_found(address, name)` as each new
    device appears. Returns the accumulated (address, name) list after `seconds`.
    """
    found: dict[str, str | None] = {}

    def callback(device, adv) -> None:
        if device.address not in found:
            name = device.name or (adv.local_name if adv else None)
            found[device.address] = name
            if on_found is not None:
                on_found(device.address, name)

    scanner = BleakScanner(detection_callback=callback)
    await scanner.start()
    try:
        await asyncio.sleep(seconds)
    finally:
        await scanner.stop()
    return list(found.items())


async def wake_wifi(address: str, timeout: float = 20.0) -> None:
    """Connect to the camera by BLE address and enable its WiFi AP."""
    async with BleakClient(address, timeout=timeout) as client:
        await client.write_gatt_char(CHARACTERISTIC_UUID, WIFI_ON_PAYLOAD, response=True)
