from types import SimpleNamespace

from bushdump.camera import CameraFile
from bushdump.sync import cameras_present, files_to_download, next_watermark


def _file(id: int) -> CameraFile:
    return CameraFile(id=id, type=1, date="2026-05-10 13:00:01", size=100)


def test_first_run_downloads_everything_oldest_first():
    files = [_file(3), _file(1), _file(2)]
    result = files_to_download(files, watermark=None)
    assert [f.id for f in result] == [1, 2, 3]


def test_only_files_newer_than_watermark():
    files = [_file(1), _file(2), _file(3)]
    result = files_to_download(files, watermark=2)
    assert [f.id for f in result] == [3]


def test_watermark_is_exclusive():
    files = [_file(2)]
    assert files_to_download(files, watermark=2) == []


def test_next_watermark_takes_max():
    downloaded = [_file(10), _file(30), _file(20)]
    assert next_watermark(downloaded, previous=15) == 30


def test_next_watermark_keeps_previous_when_nothing_downloaded():
    assert next_watermark([], previous=42) == 42


def test_next_watermark_first_run():
    assert next_watermark([_file(5)], previous=None) == 5


def _cam(name, ble):
    return SimpleNamespace(name=name, ble_address=ble)


def test_cameras_present_matches_case_insensitively():
    cams = [_cam("front", "AAA-111"), _cam("back", "BBB-222")]
    result = cameras_present(cams, {"aaa-111"})
    assert [c.name for c in result] == ["front"]


def test_cameras_present_skips_cameras_without_address():
    cams = [_cam("noble", None), _cam("yes", "CCC")]
    result = cameras_present(cams, {"ccc", "ddd"})
    assert [c.name for c in result] == ["yes"]
