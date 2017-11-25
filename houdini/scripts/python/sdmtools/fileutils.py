import os

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
	pathParts = path.split(os.path.sep)

	if newBaseDir:
		pathParts[0] = newBaseDir

	return os.path.join(*pathParts)

def writeFileWithStructure(content, sourcePath, baseDir=None):
	path = changeBaseDir(sourcePath, baseDir)

	if os.path.isdir(path):
		return

	if not os.path.exists(os.path.split(path)[0]):
		os.makedirs(path)

	with open(path, 'w+') as f:
		f.write(content)

def mergeJsonFiles(source, target):
	merged = {}

	for sourceKey in source:
		merged[sourceKey] = target.get(sourceKey, source[sourceKey])

	return merged
