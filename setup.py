import pathlib

import setuptools


def read(file_name: pathlib.Path):
    directory_name = pathlib.Path(__file__).parent
    return open(directory_name / file_name, "r", encoding="utf-8").read()


def read_requirements(file_name: pathlib.Path):
    return read(file_name).strip().split("\n")


setuptools.setup(
    name="amnesis",
    version="0.0.2",
    author="Gabriel Lauzier",
    author_email="gabriel.lauzier@usherbrooke.ca",
    url="",
    description="A local experiments tracking tool",
    long_description=read("README.md"),
    long_description_content_type="text/markdown",
    keywords="experiments tracking",
    package_dir={"": "src"},
    packages=setuptools.find_packages(where="src", exclude=["tests", "tests.*"]),
    python_requires=">=3.8",
    install_requires=[
        *read_requirements(pathlib.Path("requirements/requirements.txt")),
    ],
    extras_require={
        "dev": read_requirements(pathlib.Path("requirements/dev_requirements.txt")),
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    entry_points={"console_scripts": ["amnesis=amnesis.command.cli:main"]},
)
