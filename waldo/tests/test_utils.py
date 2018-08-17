from waldo.fn import mapvalue, get_filesize


def test_mapvalue():
    assert mapvalue(5, 0, 10, 0, 100) == 50


def test_getfilesize():
    assert get_filesize(2 ** 40, 1) == '1.0 TiB'
