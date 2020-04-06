#!/usr/bin/env python3

import pytest
from threading import Thread
import time
from contextlib import ExitStack
import pyresourcepool.pyresourcepool as rp


class Person(object):
    def __init__(self, name):
        self.name = name


@pytest.fixture
def pool():
    return rp.ResourcePool([Person("John"),
                            Person("Jim"),
                            Person("Jake"),
                            Person("Jason")])


def get_and_hold_resource(p, t):
    """ wait/get resource and sleep for 't' seconds """
    with p.get_resource():
        time.sleep(t)


def test_pool_use(pool):
    assert len(pool._available) == 4
    assert (pool._available[0].name == "John")

    with pool.get_resource() as x:
        assert (x.name == "John")
        assert len(pool._available) == 3
        assert (pool._available[0].name == "Jim")

    assert len(pool._available) == 4
    assert (pool._available[0].name == "Jim")
    assert (pool._available[1].name == "Jake")
    assert (pool._available[2].name == "Jason")
    assert (pool._available[3].name == "John")

    threads = [Thread(target=get_and_hold_resource, args=(pool, 0.4)),
               Thread(target=get_and_hold_resource, args=(pool, 0.3)),
               Thread(target=get_and_hold_resource, args=(pool, 0.2))]

    for t in threads:
        t.start()

    time.sleep(0.05)

    assert len(pool._available) == 1
    assert (pool._available[0].name == "John")
    assert (pool._available[-1].name == "John")

    time.sleep(0.5)

    assert len(pool._available) == 4
    assert (pool._available[0].name == "John")
    assert (pool._available[1].name == "Jason")
    assert (pool._available[2].name == "Jake")
    assert (pool._available[3].name == "Jim")

    # Jim will initially be release first, then held for a second time
    #    the longest so will appear last
    # Jake will initially be released second, then be held for a
    #    second time the second longest so end up second last
    threads = [Thread(target=get_and_hold_resource, args=(pool, 0.6)),
               Thread(target=get_and_hold_resource, args=(pool, 0.5)),
               Thread(target=get_and_hold_resource, args=(pool, 0.4)),
               Thread(target=get_and_hold_resource, args=(pool, 0.3)),
               Thread(target=get_and_hold_resource, args=(pool, 0.7)),
               Thread(target=get_and_hold_resource, args=(pool, 0.5))]

    for t in threads:
        t.start()

    time.sleep(4.0)

    assert len(pool._available) == 4
    assert (pool._available[0].name == "Jason")
    assert (pool._available[1].name == "John")
    assert (pool._available[2].name == "Jake")
    assert (pool._available[3].name == "Jim")


def test_pool_object_removal(pool):
    # remove all but one from the pool
    for i in range(3):
        with pool.get_resource() as x:
            pool.remove(x)
            assert len(pool._available) == 3 - i
        assert len(pool._available) == 3 - i

    # remove the last item from the pool and expect an exception
    with pytest.raises(rp.AllResourcesRemoved):
        with pool.get_resource() as x:
            pool.remove(x)
            # we should not get to this bad assertion because an exception
            # should be raised
            assert False

    # try to get an object from the pool and expect an exception
    with pytest.raises(rp.AllResourcesRemoved):
        with pool.get_resource() as x:
            # we should not get to this bad assertion because an exception
            # should be raised
            assert False


def test_pool_object_removal_non_member(pool):
    # create a new object
    obj = Person("Jeff")
    with pytest.raises(rp.ObjectNotInPool):
        pool.remove(obj)
        # we should not get to this bad assertion because an exception
        # should be raised
        assert False


def test_pool_non_block(pool):
    with ExitStack() as stack:
        obj1 = stack.enter_context(pool.get_resource(block=False))
        assert obj1.name == "John"

        obj2 = stack.enter_context(pool.get_resource(block=False))
        assert obj2.name == "Jim"

        obj3 = stack.enter_context(pool.get_resource(block=False))
        assert obj3.name == "Jake"

        obj4 = stack.enter_context(pool.get_resource(block=False))
        assert obj4.name == "Jason"

        # pool should be depleted by this point
        obj5 = stack.enter_context(pool.get_resource(block=False))
        assert obj5 is None

        obj6 = stack.enter_context(pool.get_resource(block=False))
        assert obj6 is None

    assert len(pool._available) == 4
