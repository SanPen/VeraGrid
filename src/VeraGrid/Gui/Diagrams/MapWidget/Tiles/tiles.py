# MIT License
#
# Copyright (c) 2018 Ross Wilson
# Copyright (c) 2024, Santiago Peñate Vera
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
"""
A server Tiles object for pySlipQt tiles.

All server tile sources should inherit from this class.
For example, see osm_tiles.py.
"""
import http.client
import os
import time
import math
import traceback
import urllib
from urllib import request
from urllib.error import HTTPError
import queue
from typing import List, Union
from collections.abc import Callable
from warnings import warn
from PySide6.QtCore import QObject, Slot, Qt
from PySide6.QtGui import QPixmap, QColor

from VeraGrid.Gui.Diagrams.MapWidget.Tiles.base_tiles import BaseTiles
from VeraGrid.Gui.Diagrams.MapWidget.Tiles.tile_worker import TileWorker


# # set how old disk-cache tiles can be before we re-request them from the
# # server.  this is the number of days old a tile is before we re-request.
# # if 'None', never re-request tiles after first satisfied request.
# RefreshTilesAfterDays = 60


class TileCallbackBridge(QObject):
    """
    GUI-thread bridge for tile worker results.
    """

    __slots__ = ('_tiles',)

    def __init__(self, tiles: "Tiles") -> None:
        """
        Store the tile source that receives decoded images.
        """
        QObject.__init__(self)
        self._tiles: Tiles = tiles

    @Slot(int, float, float, bytes, bool)
    def tile_is_available(self, level: int, x: float, y: float, image_data: bytes, error: bool) -> None:
        """
        Forward worker bytes to the tile source on this object's Qt thread.
        """
        self._tiles.tile_is_available(level=level,
                                      x=x,
                                      y=y,
                                      image_data=image_data,
                                      error=error)


class Tiles(BaseTiles):
    """
    A tile object to source server tiles for the widget.
    """

    def __init__(self,
                 tile_set_name: str,
                 tile_set_short_name: str,
                 tile_set_version: str,
                 levels: List[int],
                 tile_width: int,
                 tile_height: int,
                 tiles_dir: str,
                 max_lru: int,
                 servers: List[str],
                 url_path: str,
                 max_server_requests: int,
                 http_proxy,
                 re_fetch_days: int = 60,
                 attribution: str = "",
                 start_workers: bool = True):
        """
        Initialise a Tiles instance.
        :param tile_set_name: Name of the tile set.
        :param tile_set_short_name: Short name of the tile set.
        :param tile_set_version: Version of the tile set.
        :param levels: a list of level numbers that are to be served
        :param tile_width: width of each tile in pixels
        :param tile_height: height of each tile in pixels
        :param tiles_dir: path to on-disk tile cache directory
        :param max_lru: maximum number of tiles cached in-memory
        :param servers: list of tile servers
        :param url_path: path on server to each tile
        :param max_server_requests: maximum number of requests per server
        :param http_proxy: proxy to use if required
        :param re_fetch_days: fetch new server tile if older than this in days (0 means don't ever update tiles)
        :param start_workers: Start network tile workers immediately.
        """
        # perform the base class initialization
        super().__init__(levels, tile_width, tile_height, tiles_dir, max_lru)

        # allowed file types and associated values
        self.AllowedFileTypes = {'png': 'PNG', 'jpg': 'JPG'}

        # the number of seconds in a day
        self.SecondsInADay = 60 * 60 * 24

        self.tile_set_name = tile_set_name
        self.tile_set_short_name = tile_set_short_name
        self.tile_set_version = tile_set_version

        self.attribution_string = attribution

        # prepare the tile cache directory, if required
        # we have to do this *before* the base class initialization!
        for level in levels:
            level_dir = os.path.join(tiles_dir, '%d' % level)
            if not os.path.isdir(level_dir):
                os.makedirs(level_dir)

        # save params not saved in super()
        self.servers = servers
        self.url_path = url_path
        self.max_requests = max_server_requests
        self.http_proxy = http_proxy
        self.refresh_tiles_after_days = re_fetch_days

        # callback must be set by higher-level code
        self.callback: Union[None, Callable[[int, float, float, QPixmap, bool], None]] = None
        self._shutdown: bool = False

        # calculate a re-request age, if specified
        self.re_request_age = (time.time() - self.refresh_tiles_after_days * self.SecondsInADay)

        # tiles extent for tile data (left, right, top, bottom)
        self.extent = (-180.0, 180.0, -85.0511, 85.0511)

        self.level = levels[len(levels) - 1]
        self.num_tiles_x = 0
        self.num_tiles_y = 0
        self.ppd_x = 0
        self.ppd_y = 0

        # figure out tile filename extension from 'url_path'
        tile_extension = os.path.splitext(url_path)[1][1:]
        tile_extension_lower = tile_extension.lower()  # ensure lower case

        if tile_extension_lower == "":
            tile_extension_lower = 'jpg'

        # determine the file bitmap type
        try:
            self.filetype = self.AllowedFileTypes[tile_extension_lower]
        except KeyError:
            raise TypeError("Bad tile_extension value, got '%s', "
                            "expected one of %s"
                            % (str(tile_extension),
                               str(self.AllowedFileTypes.keys()))) from None

        # compose the expected 'Content-Type' string on request result
        # if we get here we know the extension is in self.AllowedFileTypes
        # if tile_extension_lower in ['png', 'jpg']:

        self.content_type = 'image/png'

        # set the list of queued unsatisfied requests to 'empty'
        self.queued_requests = {}
        self.tile_callback_bridge: TileCallbackBridge = TileCallbackBridge(tiles=self)

        # prepare the "pending" and "error" images
        self.pending_tile = QPixmap(256, 256)
        self.pending_tile.fill(QColor.fromRgb(50, 50, 50, 255))

        self.error_tile = QPixmap(256, 256)
        self.error_tile.fill(QColor.fromRgb(255, 0, 0, 255))

        # define the error messages for various failures
        StatusError = {401: 'Looks like you need to be authorised for this server.',
                       404: 'You might need to check the tile addressing for this server.',
                       429: 'You are asking for too many tiles.', }

        # set up the request queue and worker threads
        self.request_queue = queue.Queue()  # entries are (level, x, y)
        self.workers: List[TileWorker] = list()

        if start_workers:
            # test for firewall - use proxy (if supplied)
            test_url = self.servers[0] + self.url_path.format(Z=0, X=0, Y=0)
            try:
                r = request.Request(test_url, headers={'User-Agent': 'VeraGrid 5'})
                request.urlopen(r, timeout=5.0).read()

            except HTTPError as e:
                # if it's fatal, log it and die, otherwise try a proxy
                status_code = e.code
                warn('Error: test_url=%s, status_code=%s' % (test_url, str(status_code)))
                error_msg = StatusError.get(status_code, None)
                if status_code:
                    msg = "\nYou got a " + str(status_code) + " (" + str(error_msg) + ") error from: " + str(test_url)
                    print(msg)
                    # raise RuntimeError(msg) from None
                else:
                    pass

                warn('%s exception doing simple connection to: %s' % (type(e).__name__, test_url))
                warn(''.join(traceback.format_exc()))

                if http_proxy:
                    proxy = request.ProxyHandler({'http': http_proxy})
                    opener = request.build_opener(proxy)
                    request.install_opener(opener)
                    try:
                        request.urlopen(test_url)
                    except (HTTPError, urllib.error.URLError, http.client.IncompleteRead) as proxy_error:
                        msg = "Using HTTP proxy but still can't get through a firewall!"
                        print(msg)
                        warn('%s exception doing simple connection through proxy to: %s' % (type(proxy_error).__name__, test_url))
                        warn(''.join(traceback.format_exc()))
                        # raise Exception(msg) from None
                else:
                    msg = "There is a firewall but you didn't give me an HTTP proxy to get through it?"
                    print(msg)
                    # raise Exception(msg) from None
            except urllib.error.URLError as e:
                print(e)

            except http.client.IncompleteRead as e:
                print(e)

            server: str
            for server in self.servers:
                num_thread: int
                for num_thread in range(self.max_requests):
                    worker = TileWorker(id_num=num_thread,
                                        server=server,
                                        tile_path=self.url_path,
                                        requests_cue=self.request_queue,
                                        content_type=self.content_type,
                                        re_request_age=self.re_request_age,
                                        refresh_tiles_after_days=60)
                    worker.tile_available.connect(self.tile_callback_bridge.tile_is_available,
                                                  Qt.ConnectionType.QueuedConnection)
                    self.workers.append(worker)
                    worker.start()
        else:
            pass

    def copy(self) -> "Tiles":
        """
        Create a fresh tile source with the same configuration.
        """
        cpy = Tiles(tile_set_name=self.tile_set_name,
                    tile_set_short_name=self.tile_set_short_name,
                    tile_set_version=self.tile_set_version,
                    levels=self.levels.copy(),
                    tile_width=self.tile_width,
                    tile_height=self.tile_height,
                    tiles_dir=self.tiles_dir,
                    max_lru=self.max_lru,
                    servers=self.servers.copy(),
                    url_path=self.url_path,
                    max_server_requests=self.max_requests,
                    http_proxy=self.http_proxy,
                    re_fetch_days=self.refresh_tiles_after_days,
                    attribution=self.attribution_string)

        cpy.wrap_x = self.wrap_x
        cpy.wrap_y = self.wrap_y
        cpy.extent = self.extent
        cpy.set_level(self.level)

        return cpy

    def set_level(self, level: int):
        """
        Prepare to serve tiles from the required level.
        :param level: the required level
        :return: True if level change occurred, else False if not possible.
        """
        # first, CAN we zoom to this level?
        if self.level_in_range(level):

            # get tile info
            info = self.GetInfo(level)
            if info is None:
                return False

            # OK, save new level
            self.level = level
            self.num_tiles_x, self.num_tiles_y, self.ppd_x, self.ppd_y = info

            # flush any outstanding requests.
            # we do this to speed up multiple-level zooms so the user doesn't
            # sit waiting for tiles to arrive that won't be shown.
            self.FlushRequests()

            return True

        else:
            # the zoom is out of bounds...
            return False

    def GetTile(self, x: float, y: float) -> QPixmap:
        """
        Get bitmap for tile at tile coords (x, y) and current level.

        :param x:  X coord of tile required (tile coordinates)
        :param y:  Y coord of tile required (tile coordinates)

        Returns bitmap object for the tile image.
        Tile coordinates are measured from map top-left.

        We override the existing GetTile() method to add code to retrieve
        tiles from the servers if not in on-disk cache.

        We also check the date on the tile from disk-cache.  If "too old",
        return old tile after starting the process to get new tile from servers.
        """

        try:
            # get tile from cache
            tile = self.cache[(self.level, x, y)]
            if self.tile_on_disk(level=self.level, x=x, y=y):
                tile_date = self.cache.tile_date((self.level, x, y))
                if self.re_request_age and (tile_date < self.re_request_age):
                    self.get_server_tile(level=self.level, x=x, y=y)
        except KeyError:
            # not cached, start process of getting tile from 'net, return 'pending' image
            self.get_server_tile(level=self.level, x=x, y=y)
            tile = self.pending_tile

        return tile

    def GetInfo(self, level: int):
        """
        Get tile info for a particular level.

        level  the level to get tile info for

        Returns (num_tiles_x, num_tiles_y, ppd_x, ppd_y) or None if 'level'
        doesn't exist.

        Note that ppd_? may be meaningless for some tiles, so its
        value will be None.

        This method is for server tiles.  It will be overridden for GMT tiles.
        """

        # is required level available?
        if self.level_in_range(level):

            # otherwise get the information
            self.num_tiles_x = int(math.pow(2, level))
            self.num_tiles_y = int(math.pow(2, level))

            return self.num_tiles_x, self.num_tiles_y, None, None
        else:
            return None

    def FlushRequests(self):
        """
        Delete any outstanding tile requests.
        """

        # if we are serving server tiles ...
        if self.servers:
            with self.request_queue.mutex:
                self.request_queue.queue.clear()
            self.queued_requests.clear()

    def shutdown(self) -> None:
        """
        Stop tile callbacks and background workers for this tile source.
        """
        if self._shutdown:
            return

        self._shutdown = True
        self.callback = None
        self.FlushRequests()

        for worker in self.workers:
            worker.stop()

        for worker in self.workers:
            worker.wait(6000)

    def get_server_tile(self, level: int, x: float, y: float) -> None:
        """
        Start the process to get a server tile.

        level, x, y  identify the required tile

        If we don't already have this tile (or getting it), queue a request and
        also put the request into a 'queued request' dictionary.  We
        do this since we can't peek into a queue to see what's there.
        """

        tile_key = (level, x, y)
        if tile_key not in self.queued_requests:
            # add tile request to the server request queue
            self.request_queue.put(tile_key)
            self.queued_requests[tile_key] = True

    def tile_on_disk(self, level: int, x: float, y: float):
        """
        Return True if tile at (level, x, y) is on-disk.
        """

        tile_path = self.cache.tile_path((level, x, y))
        return os.path.exists(tile_path)

    def setCallback(self, callback: Callable[[int, float, float, QPixmap, bool], None] | None):
        """Set the "tile available" callback.

        callback  reference to object to call when tile is found.
        """

        self.callback = callback

    def tile_is_available(self, level: int, x: float, y: float, image_data: bytes, error: bool):
        """
        Callback routine - a 'net tile is available.

        level   level for the tile
        x       x coordinate of tile
        y       y coordinate of tile
        image_data   tile image data
        error   True if image is 'error' image, don't cache in that case
        """
        tile_key: tuple[int, float, float] = (level, x, y)
        image: QPixmap

        if error:
            image = self.error_tile
        else:
            image = QPixmap()
            if image.loadFromData(image_data):
                pass
            else:
                image = self.error_tile
                error = True

        # Keep error tiles in the in-memory LRU only.
        # Writing them through the normal cache assignment would persist the red
        # fallback tile to disk because PyCacheBack.__setitem__() is write-through.
        if error:
            dict.__setitem__(self.cache, tile_key, image)
            self.cache._reorder_lru(tile_key)
            self.cache._enforce_lru_size()
        else:
            # Successful tiles still use the normal write-through cache path so the
            # in-memory and on-disk caches stay synchronized.
            self.cache[tile_key] = image

        # delete the request from the queued requests
        # note that it may not be there - a level change can flush the dict
        try:
            del self.queued_requests[tile_key]
        except KeyError:
            pass

        # tell the world a new tile is available
        if self.callback:
            self.callback(level, x, y, image, True)
        else:
            pass

    def SetAgeThresholdDays(self, num_days):
        """
        Set the tile re-fetch threshold time.

        num_days  number of days before re-fetching tiles

        If 'num_days' is 0 re-fetching is inhibited.
        """

        # update the global in case we instantiate again

        self.refresh_tiles_after_days = num_days

        # recalculate this instance's age threshold in UNIX time
        self.re_request_age = time.time() - self.refresh_tiles_after_days * self.SecondsInADay
