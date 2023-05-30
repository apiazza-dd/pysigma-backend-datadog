![Tests](https://github.com/apiazza-dd/pySigma-backend-datadog/actions/workflows/test.yml/badge.svg)
![Coverage Badge](https://img.shields.io/endpoint?url=https://gist.githubusercontent.com/apiazza-dd/GitHub Gist identifier containing coverage badge JSON expected by shields.io./raw/apiazza-dd-pySigma-backend-datadog.json)
![Status](https://img.shields.io/badge/Status-pre--release-orange)

# pySigma datadog Backend

This repository contains the Datadog backend for pySigma which provides the package `sigma.backends.datadog` with the `datadogBackend` class.
Further, it contains the following processing pipelines in `sigma.pipelines.datadog`:

* datadog_pipeline: Contains Conversion Logic from Generic Log Source to Datadog Query Syntax, maps fields, and informs users of unsupported rule conditions

It supports the following output formats:

* default: plain datadog queries

This backend is currently maintained by:

* [Andrea Piazza](https://github.com/apiazza-dd/)
