from unittest.mock import MagicMock, patch

from bushdump import cli


def test_command_aliases_resolve_to_canonical_handlers():
    parser = cli.build_parser()

    cases = [
        (["cams"], cli.cmd_cameras),
        (["reg"], cli.cmd_register),
        (["s", "frontgate"], cli.cmd_sync),
        (["w", "frontgate"], cli.cmd_wake),
        (["st", "frontgate"], cli.cmd_stats),
        (["ka", "frontgate"], cli.cmd_keepalive),
    ]

    for argv, handler in cases:
        args = parser.parse_args(argv)
        assert args.func is handler


def test_clock_parser():
    parser = cli.build_parser()

    args = parser.parse_args(["clock", "frontgate"])
    assert args.func is cli.cmd_clock
    assert args.name == "frontgate"
    assert args.sync is False

    args = parser.parse_args(["clock", "frontgate", "--sync"])
    assert args.func is cli.cmd_clock
    assert args.sync is True


def test_settings_parser():
    parser = cli.build_parser()
    args = parser.parse_args(["settings", "frontgate"])
    assert args.func is cli.cmd_settings
    assert args.name == "frontgate"


def _make_settings_client(settings: dict | None = None, ready: bool = True) -> MagicMock:
    client = MagicMock()
    client.wait_until_ready.return_value = ready
    client.get_settings.return_value = settings or {"resolution": "4K", "video_length": "30s"}
    client.__enter__ = lambda s: client
    client.__exit__ = MagicMock(return_value=False)
    return client


def test_settings_prints_key_value(capsys):
    mock_cam = MagicMock()
    mock_cam.camera_host = "192.168.8.1:8080"
    client = _make_settings_client({"resolution": "4K", "video_length": "30s"})

    with (
        patch("bushdump.cli._resolve_camera", return_value=mock_cam),
        patch("bushdump.cli._wake_join"),
        patch("bushdump.camera.CameraClient", return_value=client),
    ):
        args = cli.build_parser().parse_args(["settings", "frontgate"])
        result = args.func(args)

    assert result == 0
    out = capsys.readouterr().out
    assert "resolution: 4K" in out
    assert "video_length: 30s" in out


def test_settings_unknown_camera_returns_nonzero():
    with patch("bushdump.cli._resolve_camera", return_value=None):
        args = cli.build_parser().parse_args(["settings", "bogus"])
        result = args.func(args)
    assert result == 1


def test_settings_http_not_ready_returns_nonzero():
    mock_cam = MagicMock()
    mock_cam.camera_host = "192.168.8.1:8080"
    client = _make_settings_client(ready=False)

    with (
        patch("bushdump.cli._resolve_camera", return_value=mock_cam),
        patch("bushdump.cli._wake_join"),
        patch("bushdump.camera.CameraClient", return_value=client),
    ):
        args = cli.build_parser().parse_args(["settings", "frontgate"])
        result = args.func(args)

    assert result == 1
    client.get_settings.assert_not_called()


def test_settings_api_error_returns_nonzero(capsys):
    mock_cam = MagicMock()
    mock_cam.camera_host = "192.168.8.1:8080"
    client = _make_settings_client()
    client.get_settings.side_effect = RuntimeError("bad response")

    with (
        patch("bushdump.cli._resolve_camera", return_value=mock_cam),
        patch("bushdump.cli._wake_join"),
        patch("bushdump.camera.CameraClient", return_value=client),
    ):
        args = cli.build_parser().parse_args(["settings", "frontgate"])
        result = args.func(args)

    assert result == 1
    assert "bad response" in capsys.readouterr().err


def test_command_aliases_preserve_arguments():
    parser = cli.build_parser()

    sync_args = parser.parse_args(["s", "frontgate", "--manual-wifi"])
    assert sync_args.name == "frontgate"
    assert sync_args.manual_wifi is True

    keepalive_args = parser.parse_args(["ka", "frontgate", "--interval", "3"])
    assert keepalive_args.name == "frontgate"
    assert keepalive_args.interval == 3
