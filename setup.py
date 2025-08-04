from setuptools import setup, find_packages

setup(
    name="openllm-cli",
    version="0.1.0",
    description="CLI for Open LLM Code Assistant",
    author="Open LLM Community",
    author_email="community@openllm.com",
    url="https://github.com/bozozeclown/open_llm",
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        "click>=8.0.0",
        "requests>=2.25.0",
        "pydantic>=2.0.0",
        "rich>=13.0.0",
        "pyyaml>=6.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "black>=22.0.0",
            "flake8>=5.0.0",
            "mypy>=1.0.0",
        ]
    },
    entry_points={
        "console_scripts": [
            "openllm=cli.main:cli",
        ],
    },
    python_requires=">=3.8",
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Text Processing :: Linguistic",
    ],
    keywords="llm ai code assistant cli",
    project_urls={
        "Bug Reports": "https://github.com/bozozeclown/open_llm/issues",
        "Source": "https://github.com/bozozeclown/open_llm",
        "Documentation": "https://github.com/bozozeclown/open_llm/docs",
    },
)