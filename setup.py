from setuptools import setup, find_packages

with open("README.md", "r") as fh:
    long_description = fh.read()

setup(
    name='PyResourcePool',
    version='0.1.5',
    author='Jason Milen',
    author_email='jpmilen@gmail.com',
    url='http://pypi.python.org/pypi/PyResourcePool/',
    license='LICENSE.txt',
    description='Provides a thread safe resource pool',
    long_description=long_description,
    long_description_content_type="text/markdown",
    packages=find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    install_requires=[],
    setup_requires=[
        'pytest-runner'
    ],
    tests_require=[
        'pytest'
    ],
)
