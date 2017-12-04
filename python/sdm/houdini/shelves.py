"""Utilities for managing the shelves within Houdini

__author__ = Sasha Ouellet (www.sashaouellet.com)
__version__ = 1.0.0
__date__ = 12/03/17
"""

import os, re

import hou
import sdm.houdini
from sdm.houdini.fileutils import SettingsFile

SDMTOOLS_SHELF_NAME = 'com.sashaouellet::sdm_tools'

def addShelf():
	shelfSets = hou.ui.curDesktop().shelfDock().shelfSets()

	if not shelfSets:
		return

	shelfSet = shelfSets[0]

	for s in shelfSets:
		if s.name() == 'shelf_set_td':
			shelfSet = s

	currShelves = shelfSet.shelves()
	sdmToolsShelf = None

	# Try seeing if it's in the current shelf set
	for shelf in currShelves:
		if shelf.name() == SDMTOOLS_SHELF_NAME:
			sdmToolsShelf = shelf
			break

	# Try in all available shelves Houdini sees
	if not sdmToolsShelf:
		sdmToolsShelf = hou.shelves.shelves().get(SDMTOOLS_SHELF_NAME)

	# I don't think this is possible, but whatever
	if not sdmToolsShelf:
		return

	filterTools(sdmToolsShelf)

	currShelves += (sdmToolsShelf,)

	shelfSet.setShelves(currShelves) # Add our shelf to the shelf set

def filterTools(shelf):
	newTools = []
	toolNamePattern = re.compile(r'com.sashaouellet::(\w+)::(\d\.*)+')
	settings = SettingsFile()
	disabledTools = settings.get('disabledTools', [])
	disabledTools = [t.lower() for t in disabledTools]

	for tool in getAllTools():
		match = toolNamePattern.match(tool.name())
		if match and match.group(1) not in disabledTools:
			newTools.append(tool)

	shelf.setTools(newTools)

def getAllTools():
	"""Gets all SDMTools shelf tools loaded into Houdini

	Returns:
		list: List of all hou.Tool that are a part of the SDMTools toolset
	"""
	toolbarDir = os.path.join(sdm.houdini.folder, 'toolbar')

	return [t[1] for t in hou.shelves.tools().iteritems() if t[0].startswith('com.sashaouellet') and t[1].filePath().startswith(toolbarDir)]

def getTool(toolName):
	"""Given a tool name, returns the hou.Tool instance

	Args:
		toolName (str): The tool name (from SDMTools toolset) to retrieve

	Returns:
		hou.Tool: The tool with the given toolName (regardless of version), None if
			not found
	"""
	tools = getAllTools()

	for tool in tools:
		if tool.name().startswith('com.sashaouellet::{}'.format(toolName.lower())):
			return tool

	return None