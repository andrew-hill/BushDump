from bushdump.camera import CameraFile, parse_file_page


def test_camerafile_from_json_parses_fields():
    obj = {"n": "IMG_0001.jpg", "dt": "1700000000", "s": "204800", "fid": "42"}
    f = CameraFile.from_json(obj)
    assert f.name == "IMG_0001.jpg"
    assert f.timestamp == 1700000000
    assert f.size == 204800
    assert f.fid == "42"
    assert isinstance(f.timestamp, int)


def test_parse_file_page_bare_list():
    data = [{"n": "a.jpg", "dt": 1, "s": 10, "fid": "1"}]
    assert [f.fid for f in parse_file_page(data)] == ["1"]


def test_parse_file_page_wrapped_in_dict():
    data = {"files": [{"n": "a.jpg", "dt": 1, "s": 10, "fid": "1"}]}
    assert [f.fid for f in parse_file_page(data)] == ["1"]


def test_parse_file_page_skips_malformed_and_empty():
    assert parse_file_page([{"n": "x"}]) == []  # missing fields
    assert parse_file_page({}) == []
    assert parse_file_page(None) == []
