"""Installation script that receives the houdini.env file to modify, and will append to (or create if not existing) the HOUDINI_PATH variable with the location
of the houdini subdirectory within the SDMTools library.

__author__ = Sasha Ouellet (www.sashaouellet.com)
__version__ = 1.1.0 (Now works for any OS)
__date__ = 11/21/17
"""

import sys, os, re, platform
from tempfile import mkstemp
from shutil import move
from argparse import ArgumentParser

def main(houdiniEnvPath):
	"""Executes the modification of houdini.env with the path to the houdini subdirectory of this toolset

	Args:
	    houdiniEnvPath (str): The absolute path where the user's houdini.env file resides
	"""
	# TODO - set PYTHONPATH as well
	pathname = os.path.dirname(sys.argv[0])
	toolsLoc = os.path.abspath(pathname)
	pythonLoc = os.path.join(os.path.abspath(os.path.dirname(pathname)), 'python')
	hPathRegx = re.compile(r'HOUDINI_PATH\s*=\s*"*([\w\\\/;&-_\s]+)')
	pyPathRegx = re.compile(r'PYTHONPATH\s*=\s*"*([\w\\\/;&-_\s]+)')
	_, tmp = mkstemp()

	with open(tmp, 'w') as output, open(houdiniEnvPath) as env:
		replacedHPath = False
		replacedPyPath = False

		for l in env:
			hMatch = hPathRegx.match(l)
			pyMatch = pyPathRegx.match(l)

			# If the user has already defined HOUDINI_PATH, we just append ours
			if hMatch:
				oldPath = hMatch.group(1)
				newPath = '{};{}'.format(oldPath, toolsLoc)
				pathParts = oldPath.split(';')

				pathParts.append(toolsLoc)

				pathParts = list(set(pathParts))

				output.write('\nHOUDINI_PATH = "{};&"'.format(';'.join(pathParts).replace(';&', '')))
				replacedHPath = True
			# Same for PYTHONPATH..
			elif pyMatch:
				oldPath = pyMatch.group(1)
				newPath = '{};{}'.format(oldPath, pythonLoc)
				pathParts = oldPath.split(';')

				pathParts.append(pythonLoc)

				pathParts = list(set(pathParts))

				output.write('\nPYTHONPATH = "{}"'.format(';'.join(pathParts).replace(';&', '')))
				replacedPyPath = True
			else:
				output.write(l)

		# If we didn't find HOUDINI_PATH originally, we'll write it at the end
		if not replacedHPath:
			output.write('\nHOUDINI_PATH = "{};&"'.format(toolsLoc))

		# Same for PYTHONPATH..
		if not replacedPyPath:
			output.write('\nPYTHONPATH = "{}"'.format(pythonLoc))

		env.close()
		output.close()

	os.remove(houdiniEnvPath)
	move(tmp, houdiniEnvPath)

def getHoudiniEnv(version):
	system = platform.system()
	home = os.path.expanduser('~')
	versionPattern = r'^(?P<major>\d+)\.(?P<minor>\d+)(?P<build>\.\d+)?$'
	versionRegx = re.compile(versionPattern)
	match = versionRegx.match(version)

	if not match:
		raise ValueError('Incorrect version specified {}. Must be of format X.X or X.X.X i.e 16.0 (or 16.0.557)'.format(version))
		sys.exit(1)

	version = '{}.{}'.format(match.group('major'), match.group('minor'))
	envDir = None

	if system == 'Linux':
		envDir = os.path.join(home, 'houdini{}'.format(version))
	elif system == 'Windows':
		envDir = os.path.join(home, 'Documents', 'houdini{}'.format(version))
	elif system == 'Darwin': # Mac
		envDir = os.path.join(home, 'Library', 'Preferences', 'houdini', version)
	else:
		raise RuntimeError('Unknown OS, cancelling installation')
		sys.exit(1)

	if not os.path.exists(envDir):
		print('Could not find expected Houdini directory: {} (incorrect version specified?)\nManual installation is required'.format(envDir))
		sys.exit(1)

	if not os.path.exists(os.path.join(envDir, 'houdini.env')):
		print('houdini.env does not exist at path: {}\nTry opening Houdini, closing it, and running this script again.'.format(envDir))
		sys.exit(1)

	return os.path.join(envDir, 'houdini.env')

parser = ArgumentParser(usage='python install.py <houdiniVersion>', description='Installs these tools to the Houdini environment by modifying HOUDINI_PATH and PYTHONPATH in the houdini.env file for the given Houdini version')

parser.add_argument('houdiniVersion', help='The version of Houdini to install for. i.e.: 16.0')

args = parser.parse_args()
houdiniEnv = getHoudiniEnv(args.houdiniVersion)

main(houdiniEnv)
