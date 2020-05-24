#!/usr/bin/env python3

import pytest
from threading import Thread
import time
from contextlib import ExitStack
import pyresourcepool.pyresourcepool as rp


class Person(object):
    def __init__(self, name):
        self.name = name


def do_callback_upper(obj):
    obj.name = obj.name.upper()


def do_callback_exception(obj):
    raise ValueError("some random error")
    # the next line should never be run
    obj.name = obj.name.upper()


@pytest.fixture
def pool():
    return rp.ResourcePool([Person("John"),
                            Person("Jim"),
                            Person("Jake"),
                            Person("Jason")])


@pytest.fixture
def pool_with_callback_ok():
    return rp.ResourcePool([Person("John"),
                            Person("Jim"),
                            Person("Jake"),
                            Person("Jason")],
                           return_callback=do_callback_upper)


@pytest.fixture
def pool_with_callback_exception():
    return rp.ResourcePool([Person("John"),
                            Person("Jim"),
                            Person("Jake"),
                            Person("Jason")],
                           return_callback=do_callback_exception)


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


def test_pool_add(pool):
    with pool.get_resource() as obj1:
        assert obj1.name == "John"

    newPerson = Person("Jenny")
    pool.add(newPerson)
    assert len(pool._available) == 5

    with ExitStack() as stack:
        obj1 = stack.enter_context(pool.get_resource(block=False))
        assert obj1.name == "Jim"

        obj2 = stack.enter_context(pool.get_resource(block=False))
        assert obj2.name == "Jake"

        obj3 = stack.enter_context(pool.get_resource(block=False))
        assert obj3.name == "Jason"

        obj4 = stack.enter_context(pool.get_resource(block=False))
        assert obj4.name == "John"

        obj5 = stack.enter_context(pool.get_resource(block=False))
        assert obj5.name == "Jenny"
        # pool should be depleted by this point

        with pytest.raises(rp.ObjectAlreadyInPool):
            pool.add(obj2)
            # shouldn't make to the bad assert below
            assert False

        obj6 = stack.enter_context(pool.get_resource(block=False))
        assert obj6 is None

        assert len(pool._available) == 0

    assert len(pool._available) == 5

    with pytest.raises(rp.ObjectAlreadyInPool):
        pool.add(newPerson)
        # shouldn't make to the 'assert False' below
        assert False

    assert len(pool._available) == 5


def test_pool_add_list(pool):
    newPeople = [Person("Jenny"), Person("Jasmin"), Person("June")]
    pool.add(newPeople)
    assert len(pool._available) == 7

    with ExitStack() as stack:
        obj1 = stack.enter_context(pool.get_resource(block=False))
        assert obj1.name == "John"

        obj2 = stack.enter_context(pool.get_resource(block=False))
        assert obj2.name == "Jim"

        obj3 = stack.enter_context(pool.get_resource(block=False))
        assert obj3.name == "Jake"

        obj4 = stack.enter_context(pool.get_resource(block=False))
        assert obj4.name == "Jason"

        obj5 = stack.enter_context(pool.get_resource(block=False))
        assert obj5.name == "Jenny"

        obj6 = stack.enter_context(pool.get_resource(block=False))
        assert obj6.name == "Jasmin"

        obj7 = stack.enter_context(pool.get_resource(block=False))
        assert obj7.name == "June"
        # pool should be depleted by this point

        with pytest.raises(rp.ObjectAlreadyInPool):
            pool.add(obj2)
            # shouldn't make to the bad assert below
            assert False

        obj8 = stack.enter_context(pool.get_resource(block=False))
        assert obj8 is None

        assert len(pool._available) == 0

    assert len(pool._available) == 7


def test_pool_return_with_callback_ok(pool_with_callback_ok):
    assert pool_with_callback_ok._return_callback == do_callback_upper
    with pool_with_callback_ok.get_resource() as obj1:
        assert obj1.name == "John"
        assert obj1 not in pool_with_callback_ok._available
        with pool_with_callback_ok.get_resource() as obj2:
            assert obj2.name == "Jim"
            assert obj2 not in pool_with_callback_ok._available
    time.sleep(1)
    assert obj1.name == "JOHN"
    assert obj1 in pool_with_callback_ok._available
    assert obj2.name == "JIM"
    assert obj2 in pool_with_callback_ok._available


def test_pool_return_with_callback_exception(pool_with_callback_exception):
    assert pool_with_callback_exception._return_callback == do_callback_exception
    with pool_with_callback_exception.get_resource() as obj1:
        assert obj1.name == "John"
        assert obj1 not in pool_with_callback_exception._available
        with pool_with_callback_exception.get_resource() as obj2:
            assert obj2.name == "Jim"
            assert obj2 not in pool_with_callback_exception._available
    time.sleep(1)
    assert obj1.name == "John"
    assert obj1 not in pool_with_callback_exception._available
    assert pool_with_callback_exception._removed[id(obj1)]
    assert obj2.name == "Jim"
    assert obj2 not in pool_with_callback_exception._available
    assert pool_with_callback_exception._removed[id(obj2)]
