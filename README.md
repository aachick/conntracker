# conntracker

[![CI](https://github.com/aachick/conntracker/actions/workflows/test.yaml/badge.svg)](https://github.com/aachick/conntracker/actions/workflows/test.yaml/badge.svg)
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

Dynamically track socket connections opened by one more processes.

This is by no means a perfect tool but it was kind of fun building.

## Installation

Use the package manager [pip](https://pip.pypa.io/en/stable/) to install `conntracker`.

```bash
pip install git+https://github.com/aachick/conntracker.git
```

## Usage

### From Python

The preferred way to use `conntracker` in code is to use the provided decorator like so:

```python
from conntracker import trackconn


@trackconn()
def my_func_that_may_or_may_not_open_connections():
    # do your thing
    ...
```

Once the decorated function has returned, the `trackconn` decorator will print to stdout
what connections were opened and in which process.

You may use the `stream` parameter of the `trackconn` decorator to control where output
will be written to (which can be your own stream or a file path).

### From the CLI

`conntracker` can be used to tracked open connections in a running process. The output will
be similar to the one produced by the `trackconn` decorator.

```bash
conntracker python myscript.py
```

## License

[MIT](https://choosealicense.com/licenses/mit/)
