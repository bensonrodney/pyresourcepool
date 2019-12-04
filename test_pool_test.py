#!/usr/bin/env python3

import pytest
from threading import Thread
import time
import pyresourcepool as rp


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
    with p.get_resource() as x:
        time.sleep(t)


def test_pool(pool):
    num = len(pool._available)
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

    time.sleep(2.0)

    assert len(pool._available) == 4
    assert (pool._available[0].name == "Jason")
    assert (pool._available[1].name == "John")
    assert (pool._available[2].name == "Jake")
    assert (pool._available[3].name == "Jim")
