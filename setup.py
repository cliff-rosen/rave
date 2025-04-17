from setuptools import setup, find_packages

setup(
    name="rave",
    version="0.1",
    packages=find_packages(),
    install_requires=[
        "streamlit==1.32.0",
        "langchain==0.1.12",
        "langchain-openai==0.0.8",
        "langgraph==0.0.27",
        "pydantic==2.6.4",
        "pydantic-core==2.16.2",
        "tavily-python==0.3.1",
        "typing-extensions==4.10.0",
        "openai==1.12.0",
        "langsmith==0.1.0",
        "python-dotenv",
    ],
    package_dir={"": "."},
    python_requires=">=3.8",
) 