from io import open
from os import environ

from setuptools import setup


def read(filename):
    with open(filename, encoding="utf-8") as file:
        return file.read()


def requirements():
    with open("requirements.txt", "r") as req:
        return [r for r in req.read().split("\n") if r]


setup(
    name="neolegoff_bank",
    version=environ.get("TAG_VERSION").replace("v", ""),
    packages=[
        "neolegoff_bank",
        "neolegoff_bank.exceptions",
        "neolegoff_bank.models",
    ],
    url="https://github.com/WhiteApfel/neolegoff_bank",
    license="Mozilla Public License 2.0",
    author="WhiteApfel",
    author_email="white@pfel.ru",
    description="Simple Tinkoff Bank API client",
    install_requires=requirements(),
    project_urls={
        "Source code": "https://github.com/WhiteApfel/neolegoff_bank",
        "Write me": "https://t.me/whiteapfel",
    },
    long_description=read("README.md"),
    long_description_content_type="text/markdown",
    keywords="tinkoff api bank",
)
