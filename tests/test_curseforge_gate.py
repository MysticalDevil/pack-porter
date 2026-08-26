from pack_porter import cli


class _Args:
    download_curseforge = False


def test_default_off():
    assert cli._should_download_curseforge({}, _Args()) is False


def test_flag_on():
    args = _Args()
    args.download_curseforge = True
    assert cli._should_download_curseforge({}, args) is True


def test_config_on():
    assert cli._should_download_curseforge({"download_curseforge": True}, _Args()) is True
