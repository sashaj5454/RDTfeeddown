from setuptools import setup, find_packages

setup(
    name="rdtfeeddown",
    version="0.1.0",
    description="RDT feed-down Analysis Package",
    author="Sasha Horney",
    packages=find_packages(),
    install_requires=[
        "numpy",
        "matplotlib",
        "scipy",
        "pytimber",
    ],
    entry_points={
        "console_scripts": [
            "rdtfeeddown=rdtfeeddown.cli:main",
        ],
    },
)