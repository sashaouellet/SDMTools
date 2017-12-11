"""Utility functions for cameras

__author__ = Sasha Ouellet (www.sashaouellet.com)
__version__ = 1.0.0
__date__ = 12/07/17
"""

import hou

import os

def getCameras():
	"""Gets all cameras in the scene

	Returns:
		list: List of all hou.Node in the current scene that have the type 'cam'
	"""
	return [c for c in hou.node('/').allSubChildren() if c.type().name() == 'cam']

def flipbook(camera, output=None, frameRange=None):
	"""Outputs a flipbook animation from the given camera

	Args:
	    camera (hou.Node): The camera node to flipbook from
	    output (str, optional): The file path to output the flipbook sequence from. By default,
	    	uses MPlay instead of outputting to a file sequence
	    frameRange (tuple, optional): A tuple representing the start frame, end frame, and frame
	    	increment of the flipbook sequence
	"""

	assert camera.type().name() == 'cam', 'Node is not a camera: {}'.format(camera.path())

	if output:
		output = os.path.split(output)[1]

	sceneViewer = hou.ui.curDesktop().paneTabOfType(hou.paneTabType.SceneViewer)

	if not sceneViewer:
		hou.ui.displayMessage('Could not find Scene Viewer pane tab, please create it and try again', title='Flipbook Error', severity=hou.severityType.Error)
		return

	frameStart = int(sceneViewer.flipbookSettings().frameRange()[0])
	frameEnd = int(sceneViewer.flipbookSettings().frameRange()[1])
	frameInc = sceneViewer.flipbookSettings().frameIncrement()

	if frameRange and len(frameRange) >= 2:
		frameStart = frameRange[0]
		frameEnd = frameRange[1]
		frameInc = 1 if len(frameRange) == 2 else frameRange[2]

	viewport = [vp for vp in sceneViewer.viewports() if vp.type() == hou.geometryViewportType.Perspective][0]

	if not viewport:
		hou.ui.displayMessage('Could not find the "Persp" viewport', title='Flipbook Error', severity=hou.severityType.Error)
		return

	viewportFullName = '{}.{}.world.{}'.format(hou.ui.curDesktop().name(), sceneViewer.name(), viewport.name())

	hou.setFrame(frameStart)
	viewport.setCamera(camera)

	if output:
		hou.hscript("viewwrite -f {} {} -i {} {} '{}'".format(frameStart, frameEnd, frameInc, viewportFullName, output))
	else: # Use Mplay flag instead
		hou.hscript("viewwrite -f {} {} -i {} -M {}".format(frameStart, frameEnd, frameInc, viewportFullName))