"""The fileutils module offers utility functions for manipulating, writing, and checking certain file operations such as determining
file path hierarchy inside and outside the $HIP context.

__author__ = Sasha Ouellet (www.sashaouellet.com)
__version__ = 1.0.0
__date__ = 11/27/17
"""

import sdm.houdini
import hou

import os, json, re, logging

logger = logging.getLogger(__name__)

class ValidationType():
	EMAIL = 1

class SettingsFile():
	_settings = dict({
			'version':'v1.0.0',
			'disabledTools':['savePrefsToStuhome', 'calculateMocapLocomotion'],
			'autoCheckUpdates':False
		})

	def __init__(self):
		logger.info('Loading settings file')
		self._settingsJsonPath = os.path.join(sdm.houdini.folder, 'settings.json')
		settingsFile = ''

		if not os.path.exists(self._settingsJsonPath):
			logger.debug('settings.json doesn\'t exist, creating')
			settingsFile = open(self._settingsJsonPath, 'w+')
		else:
			logger.debug('Found settings.json')
			settingsFile = open(self._settingsJsonPath, 'r+')

		try:
			logger.info('Loading JSON from file')
			self._settings = json.loads(settingsFile.read())
			logger.info('Loaded: {}'.format(self._settings))
		except ValueError: # Empty, or bad JSON - use defaults
			logger.warning('JSON was empty or malformed, defaulting to: {}'.format(self._settings))
			pass

	def set(self, setting, value, overwrite=True, validation=None):
		"""Given a setting to change and the new value, updates
		the settings dictionary

		Args:
		    setting (str): The setting to change
		    value (any): The new value of the setting
		    overwrite (bool, optional): By default, existing settings
		    	will be overwritten by the given value. If this is False,
		    	existing settings will not be overwritten. Settings that
		    	didn't exist previously are added regardless of this option
		    validation (ValidationType, optional): The type of validation to
		    	perform on the input. A ValueError is raised if value does not
		    	pass this validation. By default, no validation occurs
		"""
		# Setting exists, but we aren't overwriting
		logger.info('Setting {} to: {} (overwrite={}, validation={})'.format(setting, value, overwrite, validation))
		if self._settings.get(setting) and not overwrite:
			logger.debug('Setting exists but overwrite is False - not updating')
			return

		if validation:
			logger.info('Performing validation: {}'.format(validation))
			if validation == ValidationType.EMAIL and not re.match(r'[^@]+@[^@]+\.[^@]+', value):
				logger.warning('Email: {} did not match email pattern'.format(value))
				raise ValueError('Invalid email, could not update settings')
				return

		self._settings[setting] = value
		logger.info('Value set')

	def get(self, setting, default=None):
		"""Given a setting, retrieves its value

		Args:
			setting (str): The setting to get the value of
			default (any, optional): In the case that the given
				setting does not exist, this will be returned
				instead. By default, None will be returned in
				the event that this does occur.

		Returns:
			any: The value of the setting, or the value of 'default'
				if the setting does not exist
		"""
		val = self._settings.get(setting, default)

		logger.debug('Got: {} for setting: {} (default={})'.format(val, setting, default))

		return val

	def write(self):
		"""Writes the settings file out to the proper path of settings.json
		"""
		logger.info('Writing to {}'.format(self._settingsJsonPath))
		settingsFile = open(self._settingsJsonPath, 'r+')

		settingsFile.seek(0)
		json.dump(self._settings, settingsFile, sort_keys=True, indent=4, separators=(',', ': '))
		settingsFile.truncate()

def getLargerVersions(compareTo, otherVersions):
	"""For all the given versions, returns a list of all those that are larger
	than the version given to compare against

	Args:
		compareTo (str): The version to compare all other versions against
		otherVersions (list): The list of versions (JSON objects form Github API) to compare

	Returns:
		list: A subset of the original version list that is larger than the given
			version to compare against
	"""
	return [v for v in otherVersions if compareVersions(compareTo.replace('v', ''), v['tag_name'].replace('v', ''))]

def compareVersions(verA, verB):
	"""Given two versions formatted as 'major.minor.build' (i.e. 2.0.1), compares
	A to B and returns B if B is larger than A, else returns None

	A version is larger if stepping down from major -> build results in a larger
	difference.

	Ex:

	1.0.1 > 1.0.0
	2.2.1 > 1.0.5
	2.2.1 > 2.1.3

	Args:
		verA (str): Version A, what we compare Version B against
		verB (str): Version B, what we compare to Version A and return if it
			is larger than A.

	Returns:
		str: verB if verB is larger than verA, or None if verB is equal or smaller
	"""
	aParts = verA.split('.')
	bParts = verB.split('.')

	for i in range(3):
		diff = int(bParts[i]) - int(aParts[i])

		if diff == 0:
			continue
		elif diff > 0:
			return verB
		else:
			return None

	return None

def changeBaseDir(path, newBaseDir):
	"""Given a path and a new base directory, swaps out the first
	directory in the path with the new base directory. The given path
	is unchanged if newBaseDir is None

	Ex:

	changeBaseDir('foo/bar/path.txt', 'someOtherDir') --> 'someOtherDir/bar/path.txt'

	Args:
		path (str): The path to change
		newBaseDir (str): The new directory to swap the root directory of the path
			with

	Returns:
		str: The updated path, or the same initial path if newBaseDir is None
	"""
	pathParts = path.split(os.path.sep)

	if newBaseDir:
		pathParts[0] = newBaseDir

	return os.path.join(*pathParts)

def writeFileWithStructure(content, sourcePath, baseDir=None):
	"""Writes the given content to sourcePath, which may have
	a different root directory if baseDir is specified. This
	is a utility for copying the file structure over from
	a ZIP directory.

	Args:
		content (str): The content to write
		sourcePath (str): The original path this content came from
		baseDir (str, optional): The new base directory of the file
			this content will be written to
	"""
	path = changeBaseDir(sourcePath, baseDir)

	if not os.path.exists(os.path.dirname(path)):
		os.makedirs(os.path.dirname(path))

	if os.path.isdir(path):
		return

	with open(path, 'w+') as f:
		f.write(content)

def mergeDict(source, target):
	"""Merges the source dictionary into the target one, keeping
	values for duplicate keys from the target dictionary. Keys that
	don't exist in 1 or the other are left untouched but are still
	copied over to the resulting dictionary.

	Args:
		source (dict): The initial dictionary
		target (dict): The dictionary to merge into, with its values
			prioritized over the source

	Returns:
		dict: The merged dictionary
	"""
	merged = source.copy()

	merged.update(target)

	return merged

def isDescendant(file, root=None):
	"""Determines if the given file is a hierarchical descendant
	of the given root directory

	Args:
		file (str): The file path to check
		root (str, optional): The root directory that serves as the parent
			for the descendant comparison. If None, root is assumed to be the HIP
			dir.

	Returns:
		bool: True if 'file' is a descendant of 'root', meaning
			that file is (at some point) a subdirectory under 'root',
			otherwise False
	"""
	if not root:
		root = hou.getenv('HIP')

	return file.startswith(root)

def getRelativeToHip(file):
	"""Converts the given file path to a path that uses the $HIP
	environment var, if applicable. In other words, converts the file
	path from absolute to relative to the value of $HIP.

	Args:
		file (str): The file path to convert

	Returns:
		str: The file path, relative to $HIP
	"""
	hip = hou.getenv('HIP')

	return os.path.normpath(file.replace(hip, os.path.join('$HIP', '')))

def getAllFileReferences():
	"""Gets all files referenced by any parameter in the scene, INCLUDING duplicate
	references. As a result, this function compiles the full list of all referencing
	parameters, as opposed to hou.fileReferences() which only returns 1 of potentially
	many parameters that references a file.
	"""
	refs = []

	for node in hou.node('/').allSubChildren():
		for parm in node.globParms('*'):
			template = parm.parmTemplate()
			if isinstance(template, hou.StringParmTemplate) and template.stringType() == hou.stringParmType.FileReference:
				val = parm.evalAsString()

				if val and os.path.isfile(val) and isDescendant(val):
					refs.append((parm, val))

	return refs
