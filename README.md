## Description

This is a modified verion of Labelme which permit label keypoint quickly with pre-defined class

## Requirements

- Ubuntu / macOS / Windows
- Python3
- [PyQt5 / PySide2](http://www.riverbankcomputing.co.uk/software/pyqt/intro)


## Installation

There are options:

- Platform agnostic installation: [Anaconda](#anaconda)
- Platform specific installation: [Ubuntu](#ubuntu), [macOS](#macos), [Windows](#windows)
- Pre-build binaries from [the release section](https://github.com/wkentaro/labelme/releases)

### Anaconda

clone the repo, create anaconda environment, then run below:

```bash
pip install -e .

```


## Usage

```bash
labelme  --config [path to con file] 
```

- open the image folder
- Ctrl+N for create new point
- E for modify the existing point
- Left click, right click, middle click to create new point for coresponding class that specify in config file
- Ctrl + Left click, right click, middle click to create new point for coresponding class that specify in config file
- Ctrl + Z for undo

## Acknowledgement

This repo is the modified version of https://github.com/wkentaro/labelme
