import setuptools
import pymoebot


with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="pymoebot",
    version=pymoebot.__version__,
    author="David Whyte",
    author_email="David@Whyte.xyz",
    description="A Python library intended to monitor and control MoeBot robotic lawn mowers.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url='https://github.com/Whytey/pymoebot',
    packages=setuptools.find_packages(),
    install_requires=[
        'tinytuya',  # Encryption - AES can also be provided via PyCrypto or pyaes
    ],
    classifiers=[
        "Programming Language :: Python :: 3",
        "Operating System :: OS Independent",
    ],
)