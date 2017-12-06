import os, json
import hdefereval

import sdm.houdini
from sdm.houdini.dialog import checkForUpdates
from sdm.houdini.shelves import addShelf
from sdm.houdini.node import applyDefaultShapesAndColors

def checkUpdates():
	settingsPath = os.path.join(sdm.houdini.folder, 'settings.json')

	if os.path.exists(settingsPath):
			with open(settingsPath) as file:
				settingsJson = json.loads(file.read())

				autoCheckUpdates = settingsJson.get('autoCheckUpdates', False)

				if not autoCheckUpdates:
					return

				checkForUpdates(silent=True)

hdefereval.executeDeferred(checkUpdates)
hdefereval.executeDeferred(addShelf)
hdefereval.executeDeferred(applyDefaultShapesAndColors)
