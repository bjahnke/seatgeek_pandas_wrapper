from setuptools import setup

setup(
    name="seatgeek_pandas_wrapper",
    version="0.0.0.3",
    packages=["env", "src/scalpyr"],
    url="",
    license="",
    author="bjahnke",
    author_email="",
    description="",
    install_requires=[
        "pandas",
        "pydantic",
        "beautifulsoup4",
        "python-dotenv",
    ],
)
