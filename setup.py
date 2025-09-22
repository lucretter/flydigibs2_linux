from setuptools import setup, find_packages

setup(
    name="bs2pro-controller",
    version="2.3.0",  # Updated for native PyQt6 GUI support
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        "ttkbootstrap",
        "hidapi",
        "Pillow",
        "customtkinter",
        "PyQt6",
    ],
    entry_points={
        "console_scripts": [
            "bs2pro=bs2pro.main_native:main"  # Updated to use new native main
        ]
    },
)
