"""Utility functions for manipulating nodes and the data attached to them

__author__ = Sasha Ouellet (www.sashaouellet.com)
__version__ = 1.0.0
__date__ = 12/04/17
"""

import os, re
from tempfile import mkstemp
from shutil import move

import hou
import sdm.houdini

def getRopNode(node):
	"""Given a node, attempts to figure out
	where the cache node (hou.RopNode) is located.

	There are cases where this is just the given node
	itself, but others (like the File Cache SOP, or
	potentially an HDA) the ROP node may be a child
	within the subnet. This convenience function will
	return that child.

	Args:
	    node (hou.Node): The node to look for the ROP
	    	node in (also tests if the node itself is a
	    	ROP node)

	Returns:
	    hou.Node: The node (either the one given or
	    	a child) that is a hou.RopNode. Returns
	    	None if no ROP node is found
	"""
	if isinstance(node, hou.RopNode):
		return node

	if not node:
		return None

	for child in node.children():
		if isinstance(child, hou.RopNode):
			return child

	return None

def getNodeTypeCategory(node):
	"""Convenience for calling hou.Node.type().category()

	Args:
	    node (hou.Node): The node to get the node type category
	    	of

	Returns:
	    hou.NodeTypeCategory: The node type category of the given
	    	node
	"""
	return node.type().category()

def getShape(node):
	# Check user data first
	shapeName = node.userDataDict().get('nodeshape')

	if not shapeName:
		# Pull from defaults now
		shapeName = node.type().defaultShape()

	if not shapeName:
		shapeName = 'rect'

	return shapeName

def applyDefaultShapesAndColors():
	opCustomizePath = os.path.join(sdm.houdini.folder, 'OPcustomize')

	if os.path.exists(opCustomizePath):
		with open(opCustomizePath, 'r+') as opCustomize:
			for l in opCustomize:
				l = l.strip()

				if l:
					hou.hscript(l)

def saveNodeShapeAndColor(node):
	color = node.color().rgb()
	shape = getShape(node)
	typeName = node.type().name()
	category = getNodeTypeCategory(node).name()
	shapeString = 'opdefaultshape {} {} {}\n'.format(category, typeName, shape)
	colorString = 'opdefaultcolor {} {} \'RGB {} {} {}\'\n'.format(category, typeName, *color)
	opCustomizePath = os.path.join(sdm.houdini.folder, 'OPcustomize')

	if not os.path.exists(opCustomizePath):
		opCustomize = open(opCustomizePath, 'w+')

		opCustomize.write(shapeString)
		opCustomize.write(colorString)
	else:
		opCustomize = open(opCustomizePath, 'r+')
		_, tmp = mkstemp()

		with open(tmp, 'w') as output:
			replacedShape = False
			replacedColor = False

			for l in opCustomize:
				if l.startswith('opdefaultshape {} {}'.format(category, typeName)):
					output.write(shapeString)

					replacedShape = True
				elif l.startswith('opdefaultcolor {} {}'.format(category, typeName)):
					output.write(colorString)

					replacedColor = True
				else:
					if l.strip():
						output.write(l)

			if not replacedShape:
				output.write(shapeString)

			if not replacedColor:
				output.write(colorString)

		output.close()
		opCustomize.close()

		os.remove(opCustomizePath)
		move(tmp, opCustomizePath)

		# Apply new defaults to whole scene
		applyDefaultShapesAndColors()
