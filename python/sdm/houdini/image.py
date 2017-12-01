"""This module represents various utilities and structures for image manipulation

__author__ = Sasha Ouellet (www.sashaouellet.com)
__version__ = 1.0.0
__date__ = 11/27/17
"""

import hou

import os
import imghdr
import subprocess

ALTERNATE_IMAGE_EXTS = ['.hdr']

def convertImageToRAT(file, maxDim, scale):
	"""Converts the given absolute file path to RAT, using the icp command from $HFS/bin

	Args:
	    file (str): The absolute file path of the image to convert. The converted image will
	    	have the same path/filename, but with a .rat extension instead
	    maxDim (float): The maximimum dimension of either side of the outputted image. If the
	    	image (after scaling) still does not meet this dimension, it will be further scaled
	    	down
	    scale (float): The initial scale factor to apply to the outputted image. The final calculated
	    	scale gets passed to icp with the -s flag

	Returns:
        str: The path to the outputted .rat file
	"""
	args = [os.path.join(hou.getenv('HFS'), 'bin', 'icp')]
	scale /= 100.0
	resolution = hou.imageResolution(file)
	width = float(resolution[0]) * scale
	height = float(resolution[1]) * scale

	resizeFactor = 1.0

	if maxDim != -1: # Only calculate if user hasn't selected 'None'
		resizeFactor = float(maxDim) / width
		resizeFactor = min(resizeFactor, float(maxDim) / height) # if a smaller ratio, use that

	if resizeFactor < 1.0: # only want to scale down
		scale *= resizeFactor

	args.append('-u') # uncompressed, if supported

	args.append('-s')
	args.append(str(float(scale * 100)))

	newPath = '{}.rat'.format(os.path.splitext(file)[0])

	args.append(file)
	args.append(newPath)

	subprocess.call(args)

	return newPath

def isImage(file):
    """Determines if the given absolute file path points to an image filetype

    Args:
        file (str): The absolute path of the file to test

    Returns:
        bool: True if the file is an image, otherwise False
    """
    if imghdr.what(file) is not None:
        return True

    path, ext = os.path.splitext(file)

    if ext in ALTERNATE_IMAGE_EXTS:
        return True

    return False