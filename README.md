<p align="center">
  <img src="https://ai.codesphere.com/img/codesphere-logo.png" alt="Codesphere API SDK Banner" width="100">
</p>

<h1 align="center">Codesphere Python SDK</h1>

<p align="center">
  <strong>The official Python client for the Codesphere Public API.</strong>
  <br />
  <br />
  <a href="https://pypi.org/project/codesphere/">
    <img alt="PyPI Version" src="https://img.shields.io/pypi/v/codesphere.svg?style=flat-square&logo=pypi&logoColor=white">
  </a>
  <a href="https://github.com/Datata1/codesphere-python-sdk/actions/workflows/publish.yml">
    <img alt="Build Status" src="https://img.shields.io/github/actions/workflow/status/datata1/codesphere-python-sdk/publish.yml?branch=main&style=flat-square&logo=githubactions&logoColor=white">
  </a>
  <a href="[LINK_TO_YOUR_CODECOV_REPORT_IF_ANY]">
    <img alt="Code Coverage" src="https://img.shields.io/codecov/c/github/datata1/codesphere-python-sdk.svg?style=flat-square&logo=codecov&logoColor=white">
  </a>
  <a href="https://pypi.org/project/codesphere/">
    <img alt="Python Versions" src="https://img.shields.io/pypi/pyversions/codesphere.svg?style=flat-square&logo=python&logoColor=white">
  </a>
  <a href="[LINK_TO_YOUR_DOCUMENTATION]">
    <img alt="Documentation" src="https://img.shields.io/badge/docs-latest-blue.svg?style=flat-square">
  </a>
  <a href="https://github.com/Datata1/codesphere-python-sdk/releases/latest">
    <img alt="Latest Release" src="https://img.shields.io/github/v/release/Datata1/codesphere-python-sdk?style=flat-square&logo=github&logoColor=white">
  </a>
  <a href="https://github.com/Datata1/Codesphere-Python-SDK/blob/main/LICENSE">
    <img alt="License" src="https://img.shields.io/pypi/l/codesphere.svg?style=flat-square">
  </a>
</p>

---

## Overview

The Codesphere Python SDK provides a convenient wrapper for the [Codesphere Public API](https://codesphere.com/api/swagger-ui/?ref=codesphere.ghost.io&anonymousId=K9iszev), allowing you to interact with all API resources from your Python applications.

This SDK is auto-generated from our official [OpenAPI specification]([https://github.com/Datata1/Codesphere-Python-SDK/blob/main/openapi.json) and includes:
* **Modern Features**: Fully typed with Pydantic models and supports `asyncio`.
* **Easy to Use**: A high-level client that simplifies authentication and requests.
* **Comprehensive**: Covers all available API endpoints, including [e.g., Orgs, Apps, Deployments].

## Installation

You can install the SDK directly from PyPI using `pip` (or your favorite package manager like `uv`).

```bash
pip install codesphere
```

##Getting Started

**Authentication**
To use the client, you need an API token. You can generate one from your Codesphere dashboard at [Link to API token generation page].

It's recommended to store your token in an environment variable:
```sh
export CS_TOKEN="your_api_token_here"
```

## TODO
