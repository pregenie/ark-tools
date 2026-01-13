"""
Setup configuration for ARK-TOOLS
=================================

Installation and dependency management.
"""

from setuptools import setup, find_packages

# Read README for long description
with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

# Core dependencies
install_requires = [
    "click>=8.1.0",
    "rich>=13.0.0",
    "python-dotenv>=1.0.0",
    "pydantic>=2.0.0",
    "fastapi>=0.100.0",
    "uvicorn>=0.23.0",
    "aiofiles>=23.0.0",
]

# Optional dependencies for full functionality
extras_require = {
    "postgresql": ["asyncpg>=0.28.0", "psycopg2-binary>=2.9.0"],
    "redis": ["redis>=5.0.0"],
    "ai": ["openai>=1.0.0", "anthropic>=0.8.0"],
    "monitoring": ["prometheus-client>=0.18.0"],
    "ui": ["textual>=0.40.0"],
    "full": [
        "asyncpg>=0.28.0",
        "redis>=5.0.0",
        "openai>=1.0.0",
        "anthropic>=0.8.0",
        "prometheus-client>=0.18.0",
        "textual>=0.40.0",
        "psycopg2-binary>=2.9.0",
    ],
    "dev": [
        "pytest>=7.4.0",
        "pytest-asyncio>=0.21.0",
        "pytest-cov>=4.1.0",
        "black>=23.0.0",
        "flake8>=6.0.0",
        "mypy>=1.5.0",
    ],
}

setup(
    name="ark-tools",
    version="0.1.0",
    author="ARK-TOOLS Team",
    author_email="support@ark-tools.io",
    description="Intelligent code consolidation and analysis framework",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/your-org/ark-tools",
    package_dir={"": "src"},
    packages=find_packages(where="src"),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Libraries :: Application Frameworks",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
    ],
    python_requires=">=3.9",
    install_requires=install_requires,
    extras_require=extras_require,
    entry_points={
        "console_scripts": [
            "ark-setup=ark_tools.setup.cli:cli",
            "ark-analyze=ark_tools.cli:main",
            "ark-server=ark_tools.server:main",
        ],
    },
    include_package_data=True,
    package_data={
        "ark_tools": [
            "templates/**/*",
            "static/**/*",
        ],
    },
)