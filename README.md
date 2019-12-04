# pyresourcepool

Simple resource pool to wait and/or use a limited set of resources, where a resource is a python object.

Basically, you create a resource pool with a list of objects and then processes can use those resources and return them to the pool when finished.

See the test file for an example of how to use the resource pool.
