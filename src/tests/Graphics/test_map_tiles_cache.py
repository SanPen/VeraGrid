from VeraGrid.Gui.Diagrams.MapWidget.Tiles.tiles import Tiles


class _TileCacheErrorStub(dict):
    __slots__ = ("reorder_calls", "enforce_calls", "setitem_calls")

    def __init__(self) -> None:
        dict.__init__(self)
        self.reorder_calls: list[tuple[int, float, float]] = list()
        self.enforce_calls: int = 0
        self.setitem_calls: int = 0

    def __setitem__(self, key: tuple[int, float, float], value: object) -> None:
        """
        Record unexpected write-through calls.

        :param key: Cache key.
        :param value: Cached value.
        :return: ``None``.
        """
        self.setitem_calls += 1
        dict.__setitem__(self, key, value)

    def _reorder_lru(self, key: tuple[int, float, float], remove: bool = False) -> None:
        """
        Record one LRU reorder operation.

        :param key: Cache key.
        :param remove: Unused removal flag.
        :return: ``None``.
        """
        self.reorder_calls.append(key)

    def _enforce_lru_size(self) -> None:
        """
        Record one LRU-size enforcement call.

        :return: ``None``.
        """
        self.enforce_calls += 1


class _TileCacheSuccessStub(dict):
    __slots__ = ("set_calls",)

    def __init__(self) -> None:
        dict.__init__(self)
        self.set_calls: list[tuple[tuple[int, float, float], object]] = list()

    def __setitem__(self, key: tuple[int, float, float], value: object) -> None:
        """
        Record one normal write-through cache update.

        :param key: Cache key.
        :param value: Cached value.
        :return: ``None``.
        """
        self.set_calls.append((key, value))
        dict.__setitem__(self, key, value)


class _TilesStub:
    __slots__ = ("cache", "queued_requests", "callback", "callback_calls")

    def __init__(self, cache: dict) -> None:
        self.cache = cache
        self.queued_requests: dict[tuple[int, float, float], bool] = {(3, 4.0, 5.0): True}
        self.callback_calls: list[tuple[int, float, float, object, bool]] = list()
        self.callback = self.record_callback

    def record_callback(self, level: int, x: float, y: float, image: object, available: bool) -> None:
        """
        Record one tile-available callback.

        :param level: Tile level.
        :param x: Tile x coordinate.
        :param y: Tile y coordinate.
        :param image: Tile image object.
        :param available: Availability flag.
        :return: ``None``.
        """
        self.callback_calls.append((level, x, y, image, available))


def test_error_tiles_do_not_use_write_through_cache_path() -> None:
    """
    Error tiles should stay out of the on-disk cache and update only the in-memory cache state.
    """
    image: object = object()
    cache: _TileCacheErrorStub = _TileCacheErrorStub()
    stub: _TilesStub = _TilesStub(cache=cache)

    Tiles.tile_is_available(stub, level=3, x=4.0, y=5.0, image=image, error=True)

    assert cache[(3, 4.0, 5.0)] is image
    assert cache.setitem_calls == 0
    assert cache.reorder_calls == [(3, 4.0, 5.0)]
    assert cache.enforce_calls == 1
    assert stub.queued_requests == dict()
    assert stub.callback_calls == [(3, 4.0, 5.0, image, True)]


def test_successful_tiles_keep_normal_write_through_cache_path() -> None:
    """
    Successful tiles should still use the regular write-through cache update.
    """
    image: object = object()
    cache: _TileCacheSuccessStub = _TileCacheSuccessStub()
    stub: _TilesStub = _TilesStub(cache=cache)

    Tiles.tile_is_available(stub, level=3, x=4.0, y=5.0, image=image, error=False)

    assert cache.set_calls == [((3, 4.0, 5.0), image)]
    assert stub.queued_requests == dict()
    assert stub.callback_calls == [(3, 4.0, 5.0, image, True)]
