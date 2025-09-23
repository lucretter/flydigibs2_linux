from setuptools import setup, find_packages

setup(
    name="bs2pro-controller",
    version="2.5.2",  # Fixed RPM PyQt6 bundling to use system package
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
