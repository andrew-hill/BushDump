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


def test_command_aliases_preserve_arguments():
    parser = cli.build_parser()

    sync_args = parser.parse_args(["s", "frontgate", "--manual-wifi"])
    assert sync_args.name == "frontgate"
    assert sync_args.manual_wifi is True

    keepalive_args = parser.parse_args(["ka", "frontgate", "--interval", "3"])
    assert keepalive_args.name == "frontgate"
    assert keepalive_args.interval == 3
