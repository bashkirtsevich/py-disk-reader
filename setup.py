from setuptools import setup, find_packages


setup(
    name="disk_reader",
    version="0.0.1",
    description="Python low-level disk reader",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    packages=find_packages("src"),
    package_dir={"": "src"},
    python_requires=">=3.6.*"
)