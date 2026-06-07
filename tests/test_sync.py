from types import SimpleNamespace

from bushdump.camera import CameraFile
from bushdump.sync import cameras_present, files_to_download, next_watermark


def _file(fid: str, ts: int) -> CameraFile:
    return CameraFile(name=f"{fid}.jpg", timestamp=ts, size=100, fid=fid)


def test_first_run_downloads_everything_oldest_first():
    files = [_file("c", 30), _file("a", 10), _file("b", 20)]
    result = files_to_download(files, watermark=None)
    assert [f.fid for f in result] == ["a", "b", "c"]


def test_only_files_newer_than_watermark():
    files = [_file("a", 10), _file("b", 20), _file("c", 30)]
    result = files_to_download(files, watermark=20)
    assert [f.fid for f in result] == ["c"]


def test_watermark_is_exclusive():
    files = [_file("a", 20)]
    assert files_to_download(files, watermark=20) == []


def test_next_watermark_takes_max():
    downloaded = [_file("a", 10), _file("b", 30), _file("c", 20)]
    assert next_watermark(downloaded, previous=15) == 30


def test_next_watermark_keeps_previous_when_nothing_downloaded():
    assert next_watermark([], previous=42) == 42


def test_next_watermark_first_run():
    assert next_watermark([_file("a", 5)], previous=None) == 5


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
