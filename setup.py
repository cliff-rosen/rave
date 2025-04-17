from setuptools import setup, find_packages

setup(
    name="rave",
    version="0.1",
    packages=find_packages(),
    install_requires=[
        "langchain",
        "langchain-anthropic",
        "langgraph",
        "python-dotenv",
        "streamlit",
        "openai",
        "tavily-python",
    ],
    package_dir={"": "."},
    python_requires=">=3.8",
) 