from waldo.fn import mapvalue, getfilesize


def test_mapvalue():
    assert mapvalue(5, 0, 10, 0, 100) == 50


def test_getfilesize():
    assert getfilesize(2 ** 40, 1) == '1.0 TiB'
