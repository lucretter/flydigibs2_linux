from setuptools import setup, find_packages

setup(
    name="bs2pro-controller",
    version="2.0.0",
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        "ttkbootstrap",
        "hidapi",
    ],
    entry_points={
        "console_scripts": [
            "bs2pro=bs2pro.main:main"
        ]
    },
)
