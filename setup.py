from setuptools import setup, find_packages

setup(
    name="langchain-project",
    version="0.1",
    packages=find_packages(),
    install_requires=[
        "langchain",
        "langchain-anthropic",
        "langgraph",
        "python-dotenv",
    ],
) 