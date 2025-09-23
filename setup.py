from setuptools import setup, find_packages

setup(
    name="bs2pro-controller",
    version="2.5.0",  # Major smart mode improvements: graph mode, profiles, temperature sources
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        "hidapi",
        "Pillow",
        "PyQt6",
        "pyqtgraph",
    ],
    entry_points={
        "console_scripts": [
            "bs2pro=bs2pro.main_native:main"  # Updated to use new native main
        ]
    },
)
