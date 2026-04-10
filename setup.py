from setuptools import setup, find_packages

setup(
    name="CapstoneQuillxo",
    version="0.1.0",
    description="Multiplayer drawing app built with Pygame and Firebase",
    packages=find_packages(),
    python_requires=">=3.13",
    install_requires=[
        "pygame",
        "requests",
        "sseclient-py",
        "python-dotenv",
    ],
    entry_points={
        "console_scripts": [
            "quillxo=main:main",
        ],
    },
)