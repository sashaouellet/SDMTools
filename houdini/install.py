import sys, os, re
from tempfile import mkstemp
from shutil import move
from os.path import expanduser

def main():
	home = expanduser('~')
	toolsLoc = os.path.split(sys.argv[0])[0]
	regx = re.compile(r'HOUDINI_PATH\s*=\s*"*([\w\\\/]+);&')
	houdiniEnvPath = os.path.join(home, 'houdini16.0', 'houdini.env')
	_, tmp = mkstemp()
	
	with open(tmp, 'w') as output, open(houdiniEnvPath) as env:
		replacedPath = False

		for l in env:
			match = regx.match(l)

			# If the user has already defined HOUDINI_PATH, we just append ours
			if match:
				oldPath = match.group(1)
				newPath = '{};{}'.format(oldPath, toolsLoc)
				
				output.write('HOUDINI_PATH = "{};&"'.format(newPath))
				replacedPath = True
			
			output.write(l)
		
		# If we didn't find HOUDINI_PATH originally, we'll write it at the end
		if not replacedPath:
			output.write('HOUDINI_PATH = "{};&"'.format(toolsLoc))
		
		env.close()
		output.close()

	os.remove(houdiniEnvPath)
	move(tmp, houdiniEnvPath)

main()
