from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="graphrag",
    version="0.1.0",
    author="GraphRAG Team",
    description="A complete GraphRAG system with hybrid retrieval (vector + graph)",
    long_description=long_description,
    long_description_content_type="text/markdown",
    packages=find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.9",
    install_requires=[
        "fastapi>=0.109.1",
        "uvicorn[standard]>=0.27.0",
        "pydantic>=2.5.3",
        "pydantic-settings>=2.1.0",
        "qdrant-client>=1.9.0",
        "neo4j>=5.16.0",
        "sentence-transformers>=2.3.1",
        "torch>=2.6.0",
        "ollama>=0.1.6",
        "redis>=5.0.1",
        "python-dotenv>=1.0.0",
        "httpx>=0.26.0",
        "tenacity>=8.2.3",
    ],
)
