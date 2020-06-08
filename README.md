# pyresourcepool

Github: https://github.com/bensonrodney/pyresourcepool

Simple thread-safe resource pool to wait and/or use a limited set of resources, where a resource is a python object.

An example use case, and the reason this module was created, is when there exists a queue of actions to be performed but on a limited number of resources. Workers take actions from the queue and pull resources from the resource pool, perform the action and return the resource to the pool. The worker then pulls the next action from the queue and another resource and this continues until there are no more actions in the queue.

Basically, you create a resource pool with a list of objects and then processes in multiple threads can use those resources and return them to the pool when finished.

Example usage:
```python
from pyresourcepool.pyresourcepool import ResourcePool

# create a list of instances of "SomeObjectClass" class
objects = [SomeObjectClass() for o in range(10)]

# create the resrouce pool
rp = ResourcePool(objects)

# using an object would normally be done in some worker thread
# but for this example we'll just do it here
# Using the with block will wait for a resource to be available, return that
# resource and once the with block is exited, the resource will be returned
# to the pool.
with rp.get_resource() as obj:
    do_stuff_with_object(obj)

# at this point, outside the 'with' block, the object will have been
# returned to the object pool.
```

If a resource/object becomes invalid and should not be used again it can be removed from the pool with the pool's `remove_resource(obj)` method. An exception will be raised when the last resource is removed from the pool or when an attempt is made to get a resource from an empty pool.

## Return-to-Pool Callbacks
You can also run a function or method on an object as it's being returned to the pool but do so in a way that doesn't hold up the consumer of the resource. You can set a callback when creating the pool or you can assign a callback onto the object before you return the resource. Callbacks attached to objects take precendence over the one set for the whole pool. The idea here is that if a resource needs to have some time consuming process run on it before it should be available in the pool again you can do so without having to make the process that is returning the resource wait for that return callback to complete. An example is shown below but the unit tests show in detail how this functionality can be used.


This example sets up all objects in the pool to run the callback each time they're returned to the pool. The second object obtained from the pool `obj2` overrides the callback with the one specified, `reset2`. You have the option to specify a callback for the whole pool or a specific one for the object, or both keeping in mind that the object specific callback will take precendence over the pool callback.
```python
def reset1(obj):
   some_time_consuming_process(obj)

def reset2(obj):
   some_different_time_consuming_process(obj)

rp = ResourcePool(objects, return_callback=reset1)

with rp.get_resource() as obj1:
    do_stuff_with_object(obj1)

with rp.get_resource() as obj2:
    obj2.resource_pool_return_callback = reset2()
    do_stuff_with_object(obj2)
```

_NOTE:_ the `resource_pool_return_callback` attribute is removed from the object once it has been returned to the pool. If you need to run the object specific callback on the object again next time then you need to set that callback attribute again.
