import setuptools

with open("README.md", "r") as f:
    long_description = f.read()

setuptools.setup(
    name="Tami4EdgeAPI",
    version="1.1",
    author="Guy Shefer",
    license="MIT",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/Guy293/Tami4EdgeAPI",
    packages=setuptools.find_packages(),
    install_requires=["requests", "pypasser"],
)
