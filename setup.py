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
        "pydantic==1.10.13",
        "pydantic-core==1.10.13",
        "tavily-python==0.3.1",
        "typing-extensions==4.10.0",
        "openai==1.12.0",
        "python-dotenv==1.0.1"
    ],
    package_dir={"": "."},
    python_requires=">=3.8,<3.12",  # Restrict to Python versions before 3.12
) 