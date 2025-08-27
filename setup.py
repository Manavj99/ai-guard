#!/usr/bin/env python3
"""Setup script for AI-Guard."""

from setuptools import setup, find_packages

if __name__ == "__main__":
    setup(
        name="ai-guard",
        version="0.1.0",
        description="Smart Code Quality Gatekeeper for AI-generated code",
        long_description=open("README.md").read(),
        long_description_content_type="text/markdown",
        author="AI-Guard Contributors",
        author_email="contributors@ai-guard.dev",
        url="https://github.com/your-org/ai-guard",
        packages=find_packages(where="src"),
        package_dir={"": "src"},
        python_requires=">=3.11",
        install_requires=[
            "typer>=0.12.5",
            "rich>=13.7.1",
            "pygithub>=2.4.0",
        ],
        extras_require={
            "dev": [
                "flake8>=7.1.1",
                "mypy>=1.11.1",
                "pytest>=8.3.2",
                "pytest-cov>=5.0.0",
                "bandit>=1.7.9",
                "hypothesis>=6.112.0",
                "pre-commit>=3.0.0",
            ],
        },
        entry_points={
            "console_scripts": [
                "ai-guard=ai_guard.analyzer:main",
            ],
        },
        classifiers=[
            "Development Status :: 3 - Alpha",
            "Intended Audience :: Developers",
            "License :: OSI Approved :: MIT License",
            "Programming Language :: Python :: 3",
            "Programming Language :: Python :: 3.11",
            "Programming Language :: Python :: 3.12",
            "Topic :: Software Development :: Quality Assurance",
            "Topic :: Software Development :: Testing",
        ],
    )
