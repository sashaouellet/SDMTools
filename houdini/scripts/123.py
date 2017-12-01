import os, json

import sdm.houdini
from sdm.houdini.dialog import checkForUpdates

def checkUpdates():
	settingsPath = os.path.join(sdm.houdini.folder, 'settings.json')

	if os.path.exists(settingsPath):
			with open(settingsPath) as file:
				settingsJson = json.loads(file.read())

				autoCheckUpdates = settingsJson.get('autoCheckUpdates', False)

				if not autoCheckUpdates:
					return

				checkForUpdates(silent=True)

# checkUpdates()
