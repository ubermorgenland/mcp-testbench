"""Setup configuration for mcp-testbench."""
from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="mcp-testbench",
    version="0.1.0",
    author="ApInference Team",
    description="Docker-isolated security testing for MCP servers",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/ApInference/mcp-testbench",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Testing",
        "Topic :: Security",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
    ],
    python_requires=">=3.8",
    install_requires=[
        "httpx>=0.24.0",
    ],
    entry_points={
        "console_scripts": [
            "mcp-testbench=cli:main",
        ],
    },
)
