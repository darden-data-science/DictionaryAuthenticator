"""Compatibility shim for legacy setuptools-based workflows.

All metadata lives in pyproject.toml.
"""

from setuptools import setup


if __name__ == "__main__":
    setup()
