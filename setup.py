import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="ppdpy",
    version="0.0.1",
    author="Eric J. Kinoshita",
    author_email="eric.void@gmail.com",
    description="Minimal templating using preprocessor directives",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/ericvoid/ppdpy",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.6',
)
