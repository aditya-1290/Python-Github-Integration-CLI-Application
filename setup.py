from setuptools import setup, find_packages

setup(
    name="github_vector_cli",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "click",
        "PyGithub",
        "chromadb",
        "rich",
        "python-dotenv",
        "typer",
        "sentence-transformers"
    ],
    entry_points={
        "console_scripts": [
            "github-vector-cli=github_vector_cli.cli:main",
        ],
    },
)