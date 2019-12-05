#!/usr/bin/env python3

""" Basic python object resource pool.
"""

import copy
import time
from threading import RLock
from contextlib import contextmanager


class ResourcePool(object):
    def __init__(self, objects):
        # used to track the original pool of resources, not used yet
        self._objects = objects

        # create another list with the same object references:
        # copy.copy() only copies the references so the two lists are
        # separate lists that point to the same objects
        self._available = copy.copy(objects)
        self._lock = RLock()

    @contextmanager
    def get_resource(self, block=True):
        """
        Returns an object from the pool and waits if necessary. If 'block' is
        False, then None is returned if the pool has been depleted.
        """
        obj = None
        try:
            # if the pool is empty, wait for an object to be returned to the
            # pool
            while True:
                with self._lock:
                    if self._available:
                        obj = self._available.pop(0)

                if obj or (not block):
                    break
                time.sleep(0.1)

            yield obj
        finally:
            if obj:
                with self._lock:
                    self._available.append(obj)
