# img2term
A simple Python program that displays images in your terminal.

## Requirements
 - Python 3.13 or higher (older versions down to 3.8 might still work)
 - A terminal with 24-bit true color support. Some examples include:

### Required Packages
`img2term` depends on the following packages:
 - [Blessed](https://pypi.org/project/blessed/)
 - [NumPy](https://numpy.org/)
 - [Pillow](https://pypi.org/project/pillow/)

### Operating Systems
I have personally only tested `img2term` under Linux. However, it should work on any operating system that satisfies the requirements above.

## Getting Started
The easiest way is to install via `pip`:
```bash
pip install img2term
```
Alternatively, you can clone this repository and install the dependencies manually. This approach is **not recommended** unless you want to develop `img2term`:
```bash
git clone https://github.com/myswang/img2term
cd img2term
# OPTIONAL: create a virtual environment
# python -m venv .venv
# source .venv/bin/activate
pip install -r requirements.txt
```

## Usage

### Display a single image

```bash
img2term peacock.png
```

The image will be resized to fit the terminal window. `img2term` will also adapt to any changes in the window size and resize the image accordingly.

### Display multiple images

You can specify more than one image to display:

```bash
img2term peacock.png car.jpg foo/bar/baz.webp
```

You can navigate between images via the left/right arrow keys, or vim-style h/j keys.

### Display all images within a directory

You can specify a directory instead of a single file:

```bash
img2term /home/mike/my-images
```

`img2term` will non-recursively search for all images within the given directory.

## Supported File Formats
Any format that the Pillow library supports, including common formats like JPEG, PNG, and WEBP, should work. You can check out supported image formats [here](https://hugovk-pillow.readthedocs.io/en/stable/handbook/image-file-formats.html).


