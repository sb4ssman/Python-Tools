# -*- coding: utf-8 -*-
# """
# Created on Sun Jul 7 17:06:12 2024

# @author: Thomas
# """

# Run to regenerate on structural changes:
    # pip install -e C:\Users\tmill\Documents\GitHub\Python-Tools
    # 

from setuptools import setup, find_packages

setup(
    name="python_tools",
    version="0.1",
    packages=find_packages(),
    package_dir={'python_tools': '.'},
    install_requires=[
        # List your package dependencies here
    ],
)