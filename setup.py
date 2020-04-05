from setuptools import setup

setup(
    name='PyResourcePool',
    version='0.1.0',
    author='Jason Milen',
    author_email='jpmilen@gmail.com',
    packages=['pyresourcepool', 'pyresourcepool.test'],
    url='http://pypi.python.org/pypi/PyResourcePool/',
    license='LICENSE.txt',
    description='Provides a thread safe resource pool',
    long_description=open('README.md').read(),
    install_requires=[],
    setup_requires=[
        'pytest-runner'
    ],
    tests_require=[
        'pytest'
    ],
)
