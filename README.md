# pyresourcepool

Github: https://github.com/bensonrodney/pyresourcepool

Simple thread-safe resource pool to wait and/or use a limited set of resources, where a resource is a python object.

An example use case, and the reason this module was created, is when there exists a queue of actions to be performed but on a limited number of resources. Workers take actions from the queue and pull resources from the resource pool, perform the action and return the resource to the pool. The worker then pulls the next action from the queue and another recourse and this continues until there are no more actions in the queue.

Basically, you create a resource pool with a list of objects and then processes in multiple threads can use those resources and return them to the pool when finished.

Example usage:
```python
from pyresourcepool.pyresourcepool import ResourcePool

# create a list of instances of "SomeObjectClass" class
objects = [SomeObjectClass() for o in range(10)]

# create the resrouce pool
rp = RecourcePool(objects)

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
