"""
Setup.py для Sudoku Solver
Позволяет установить приложение через pip или PyPI
"""

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="sudoku-solver",
    version="1.0.0",
    author="AI Assistant",
    description="Судоку решатель с распознаванием из фотографий",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/sudoku-solver",
    packages=find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Intended Audience :: End Users/Desktop",
        "Topic :: Games/Entertainment :: Puzzle Games",
    ],
    python_requires=">=3.7",
    install_requires=[
        "opencv-python>=4.5.0",
        "pytesseract>=0.3.10",
        "numpy>=1.20.0",
        "mediapipe>=0.8.0",
        "PyQt5>=5.15.0",
    ],
    entry_points={
        "console_scripts": [
            "sudoku-solver=sudoku_solver:main",
        ],
        "gui_scripts": [
            "sudoku-app=sudoku_app:main",
        ],
    },
)
