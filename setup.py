import setuptools
import pymoebot.__about__ as about


with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name=about.__title__,
    version=about.__version__,
    author=about.__author__,
    author_email=about.__email__,
    description=about.__summary__,
    long_description=long_description,
    long_description_content_type="text/markdown",
    url=about.__uri__,
    packages=setuptools.find_packages(),
    install_requires=[
        'tinytuya',  # Encryption - AES can also be provided via PyCrypto or pyaes
    ],
    classifiers=[
        "Programming Language :: Python :: 3",
        "Operating System :: OS Independent",
    ],
)