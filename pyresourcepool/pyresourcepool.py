#!/usr/bin/env python3

""" Basic python object resource pool.
"""

import copy
import time
import traceback
from threading import RLock, Thread
from contextlib import contextmanager

# Callback attribute name when adding a return callback to an object
CALLBACK_ATTRIBUTE = 'resource_pool_return_callback'


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
    def __init__(self, objects, return_callback=None):
        """
        Instantiate with a list of objects you want in the resource pool.

        'return_callback' is a function or method that can be used to
        perform some action on an object before it is returned to the
        pool but without making the process that returned the object
        needing to wait for that function to be run.

        This is useful for performing a time consumeing "factory reset"
        (or similar) on an object before it is returned to the pool but
        without holding up the process that used the resource.

        The callback function, if specified should just take the object as an
        argument and success is measured by no exceptions being raised. If
        an exception is raised by the callback then the object will be removed
        from the pool rather than being returned as an available resource.
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
        self._return_callback = return_callback

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
                        "the resource pool is void unless new resources are"
                        "added.")
                if self._available:
                    obj = self._available.pop(0)

            if obj or (not block):
                break
            time.sleep(0.1)

        return obj

    def return_resource(self, obj, force=False):
        """ Returns a resource to the pool but if:
          - obj has a property named  'resource_pool_return_callback' and it is
            not None
          OR
          - self._return_callback is not None
        then start a thread that calls that callback before returning the resource
        to the pool. This allows the calling process to not have to wait for that
        pre-return-to-pool operation (eg. factory reset of a device that is being
        tested).

        NOTE: the callback added as a property to the object gets precedence
              over the one specified for the pool.
        NOTE: the callback property is stripped from the obj during the return
              process.
        """
        if (not obj) or (obj not in self._objects):
            raise ObjectNotInPool("Object {} not a member of the pool".format(str(obj)))

        if not force:
            callback = None
            if hasattr(obj, CALLBACK_ATTRIBUTE) and \
                    getattr(obj, CALLBACK_ATTRIBUTE) is not None:
                callback = getattr(obj, CALLBACK_ATTRIBUTE)
                # strip the callback attribute from the object
                delattr(obj, CALLBACK_ATTRIBUTE)
            elif self._return_callback:
                callback = self._return_callback
            if callback:
                thread = Thread(target=self._run_return_callback, args=(obj, callback))
                thread.setName("return_obj_{}".format(id(obj)))
                thread.start()
                return

        with self._lock:
            if not self._removed[id(obj)]:
                self._available.append(obj)

    def _run_return_callback(self, obj, callback):
        """ This should only really be called by self.return_resource() and is intended
        to be run in a thread to perform some pre-returnn-to-pool process without
        the process that used the resource having to wait for that operation to occur.

        If running the callback raises an exception the resource will be removed from
        the pool.
        """
        try:
            callback(obj)
            self.return_resource(obj, force=True)
        except Exception:
            traceback.print_exc()
            self.remove(obj)

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
            if obj:
                self.return_resource(obj)
