#!/usr/bin/env python3

""" Basic python object resource pool.
"""

import copy
import time
from threading import RLock
from contextlib import contextmanager


class AllResourcesRemoved(Exception):
    """ Raised when all recources in the pool have been removed.
    """


class ObjectAlreadyInPool(Exception):
    """ Raised when adding an object that is already in the pool.
    """


class ObjectNotInPool(Exception):
    """ Raise when operations are performed for an object that is
    not part of the resource pool.
    """


class ResourcePool(object):
    def __init__(self, objects):
        """
        Instantiate with a list of objects you want in the resource pool.
        """
        # used to track the original pool of resources, not used yet
        self._objects = objects
        self._removed = {}
        for o in self._objects:
            self._removed[id(o)] = False

        # create another list with the same object references:
        # copy.copy() only copies the references so the two lists are
        # separate lists that point to the same objects
        self._available = copy.copy(objects)
        self._lock = RLock()

    def all_removed(self):
        return all(self._removed[id(o)] for o in self._objects)

    def add(self, obj):
        """
         Adds new objects to the pool, 'obj' can be a single object or a list of
         objects and new objects are added to the end of the available resources.
         """
        if type(obj) is not list:
            obj = [obj]
        with self._lock:
            for o in obj:
                if o in self._objects:
                    raise ObjectAlreadyInPool("Object is already in the pool.")
                self._objects.append(o)
                self._available.append(o)
                self._removed[id(o)] = False

    def remove(self, obj):
        """
        Removes an object from the pool so that it can't be handed out as an
        available resource again. If the object passed in is not in the pool
        an ObjectNotInPool exception is raised.
        """
        with self._lock:
            if obj not in self._objects:
                raise ObjectNotInPool("Object is not in the list of pool objects.")
            # mark the resource as deleted
            self._removed[id(obj)] = True
            # if it is currently in the available set, remove it
            self._available = [o for o in self._available if o is not obj]
            if self.all_removed():
                raise AllResourcesRemoved(
                    "All resources have been removed. "
                    "Further use of the resource pool is void.")

    def get_resource_unmanaged(self, block=True):
        """
        Gets a resource from the pool but in an "unmanaged" fashion. It is
        up to you to return the resource to the pool by calling
        return_resource().

        Return value is an object from the pool but see the note below.

        NOTE:
        You should consider using get_resource() instead in a 'with' statement
        as this will handle returning the resource automatically. eg:

            with pool.get_resrouce() as r:
                do_stuff(r)

        The resource will be automatically returned upon exiting the 'with'
        block.
        """
        # if the pool is empty, wait for an object to be returned to the
        # pool
        obj = None
        while True:
            with self._lock:
                if self.all_removed():
                    raise AllResourcesRemoved(
                        "All resources have been removed. Further use of "
                        "the resource pool is void.")
                if self._available:
                    obj = self._available.pop(0)

            if obj or (not block):
                break
            time.sleep(0.1)

        return obj

    def return_resource(self, obj):
        if obj and (obj in self._objects):
            with self._lock:
                if not self._removed[id(obj)]:
                    self._available.append(obj)

    @contextmanager
    def get_resource(self, block=True):
        """
        Intended to be used in a 'with' statement or a contextlib.ExitStack.

        Returns an object from the pool and waits if necessary. If 'block' is
        False, then None is returned if the pool has been depleted.

        Example useage:

            with get_resrouce() as r:
                do_stuff(r)
            # at this point, outside the with block, the resource has
            # been returned to the pool.
        """
        obj = None
        try:
            obj = self.get_resource_unmanaged(block=block)
            yield obj
        finally:
            self.return_resource(obj)
