"""Installation script that receives the houdini.env file to modify, and will append to (or create if not existing) the HOUDINI_PATH variable with the location
of the houdini subdirectory within the SDMTools library.

__author__ = Sasha Ouellet (www.sashaouellet.com)
__version__ = 1.1 (Now works for any OS)
__date__ = 11/21/17
"""

import sys, os, re
from tempfile import mkstemp
from shutil import move
from argparse import ArgumentParser

def main(houdiniEnvPath):
	"""Executes the modification of houdini.env with the path to the houdini subdirectory of this toolset

	Args:
	    houdiniEnvPath (str): The absolute path where the user's houdini.env file resides
	"""
	home = os.path.expanduser('~')
	pathname = os.path.dirname(sys.argv[0])
	toolsLoc = os.path.abspath(pathname)
	regx = re.compile(r'HOUDINI_PATH\s*=\s*"*([\w\\\/;&-_\s]+)')
	_, tmp = mkstemp()

	with open(tmp, 'w') as output, open(houdiniEnvPath) as env:
		replacedPath = False

		for l in env:
			match = regx.match(l)

			# If the user has already defined HOUDINI_PATH, we just append ours
			if match:
				oldPath = match.group(1)
				newPath = '{};{}'.format(oldPath, toolsLoc)
				pathParts = oldPath.split(';')

				pathParts.append(toolsLoc)

				pathParts = list(set(pathParts))

				output.write('HOUDINI_PATH = "{};&"'.format(';'.join(pathParts).replace(';&', '')))
				replacedPath = True
			else:
				output.write(l)

		# If we didn't find HOUDINI_PATH originally, we'll write it at the end
		if not replacedPath:
			output.write('\nHOUDINI_PATH = "{};&"'.format(toolsLoc))

		env.close()
		output.close()

	os.remove(houdiniEnvPath)
	move(tmp, houdiniEnvPath)

parser = ArgumentParser(usage='python install.py <houdiniEnvPath>', description='Installs these tools to the Houdini environment by modifying HOUDINI_PATH in the given houdini.env file')

parser.add_argument('houdiniEnvPath', help='The absolute path where the user\'s houdini.env file resides.\n Depending on OS this is probably: ~\\Documents\\{HOUDINI_VERSION}\\houdini.env (Windows)\n ~{HOUDINI_VERSION}/houdini.env (Linux)\n ~/Library/Preferences/houdini/{HOUDINI_VERSION}/houdini.env (Mac)\n Note: "~" represents your HOME directory')

args = parser.parse_args()

main(args.houdiniEnvPath)
