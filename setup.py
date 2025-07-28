from setuptools import setup, find_packages

setup(
    name="zmeasure",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "numpy",
        "matplotlib",
        "pyvisa",
        "scipy",
        'zhinst',
        'screeninfo',
        'pandas',
        'pyqt5',
        # add other dependencies
    ],
    author="Zhenhai",
    description="Lab automation and measurement control system",
)