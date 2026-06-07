from bushdump.camera import CameraFile, parse_file_page


def test_camerafile_from_json_parses_fields():
    obj = {"id": "42", "type": "1", "date": "2026-05-10 13:00:01", "size": "204800"}
    f = CameraFile.from_json(obj)
    assert f.id == 42
    assert f.type == 1
    assert f.date == "2026-05-10 13:00:01"
    assert f.size == 204800
    assert isinstance(f.id, int)


def test_camerafile_kind_and_name():
    jpg = CameraFile(id=1, type=1, date="2026-05-10 13:00:01", size=100)
    assert jpg.kind == "JPG"
    assert jpg.name == "00000001.jpg"
    mp4 = CameraFile(id=2, type=2, date="2026-05-10 13:00:02", size=200)
    assert mp4.kind == "MP4"
    assert mp4.name == "00000002.mp4"


def test_parse_file_page_data_envelope():
    data = {"code": 0, "data": [{"id": 1, "type": 1, "date": "2026-05-10 13:00:01", "size": 100}]}
    result = parse_file_page(data)
    assert len(result) == 1
    assert result[0].id == 1


def test_parse_file_page_skips_malformed():
    assert parse_file_page({"code": 0, "data": [{"id": 1}]}) == []  # missing fields
    assert parse_file_page({"code": 0, "data": []}) == []
    assert parse_file_page(None) == []
