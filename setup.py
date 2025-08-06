from setuptools import setup, find_packages

setup(
    name="quant-trading-engine",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "MetaTrader5",
        "pandas",
        "numpy",
        "matplotlib",
        "PyYAML",
        "seaborn",
    ],
    extras_require={
        "dev": [
            "pytest",
            "pytest-cov"
        ]
    }
)
