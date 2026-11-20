# OpenTAXII

EclecticIQ originally developed OpenTAXII, a TAXII server in Python. The MISP Project fully maintains this fork. [EclecticIQ](https://www.eclecticiq.com) · [MISP Project](https://misp-project.org/)

OpenTAXII is a robust Python implementation of TAXII Services that
delivers rich feature set and friendly pythonic API built on top of well
designed application.

OpenTAXII is guaranteed to be compatible with [Cabby](https://github.com/eclecticiq/cabby), TAXII client library.

[MISP fork](https://github.com/MISP/OpenTAXII) | [EclecticIQ upstream](https://github.com/eclecticiq/OpenTAXII) | [Documentation](https://misp.github.io/OpenTAXII/) | [Download](https://pypi.org/project/opentaxii/)


[![Build status](https://github.com/MISP/OpenTAXII/actions/workflows/tox.yml/badge.svg?branch=master)](https://github.com/MISP/OpenTAXII/actions/workflows/tox.yml?query=branch%3Amaster)
[![Upstream coverage](https://coveralls.io/repos/eclecticiq/OpenTAXII/badge.svg)](https://coveralls.io/r/eclecticiq/OpenTAXII "EclecticIQ upstream coverage")
[![Documentation](https://github.com/MISP/OpenTAXII/actions/workflows/quarto.yml/badge.svg?branch=master)](https://misp.github.io/OpenTAXII/)

## State of the project

EclecticIQ considers the upstream project **feature-complete** and focuses on bug fixes. Contributions to the MISP fork are welcome.

## Getting started

See how to install OpenTAXII from PyPI or a source checkout and start the development server. [Install with `uv`](https://misp.github.io/OpenTAXII/installation/installation.html#install-with-uv)

## Getting started with OpenTAXII using Docker

OpenTAXII can also be run using docker. This guide assumes that you have
access to a local or remote docker server, and won't go into the setup
of docker.

From the root of this repository, build and run a development image.

```bash
docker build -t opentaxii:local .
docker run --pull=never -d -p 9000:9000 opentaxii:local
```

To preload the instance with example data, see the [Docker volume documentation](https://misp.github.io/OpenTAXII/installation/docker.html#volumes).

> **NOTE:**
> OpenTAXII is now accessible through port 9000, with data stored
> locally in a SQLite databases optionally using services/collections/accounts defined
> in [data-configuration.yml](examples/data-configuration.yml).

See the [Docker guide](https://misp.github.io/OpenTAXII/installation/docker.html) for configuration and Compose examples.

## Feedback

Report bugs or suggest improvements in the MISP fork’s issue tracker. [OpenTAXII issues](https://github.com/MISP/OpenTAXII/issues)

