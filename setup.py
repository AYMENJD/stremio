from re import findall
from setuptools import setup, find_packages


with open("stremio/__init__.py", "r") as f:
    version = findall(r"__version__ = \"(.+)\"", f.read())[0]

with open("README.md", "r") as f:
    readme = f.read()

with open("requirements.txt", "r") as f:
    requirements = [x.strip() for x in f.readlines()]


setup(
    name="Stremio",
    version=version,
    description="An asynchronous Python library for building Stremio addons with ease",
    long_description=readme,
    long_description_content_type="text/markdown",
    author="AYMEN Mohammed",
    author_email="let.me.code.safe@gmail.com",
    url="https://github.com/AYMENJD/stremio",
    license="MIT",
    python_requires=">=3.9",
    install_requires=requirements,
    project_urls={
        "Source": "https://github.com/AYMENJD/stremio",
        "Tracker": "https://github.com/AYMENJD/stremio/issues",
    },
    packages=find_packages(exclude=["examples"]),
    keywords=[
        "stremio",
        "stremio-addon",
        "stremio-addon-sdk",
        "addon",
        "plugin",
        "async",
    ],
)
