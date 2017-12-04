import os, glob
import hou
import urllib2, json, zipfile, StringIO, uuid, shutil
import webbrowser
from datetime import datetime

from PySide2.QtCore import *
from PySide2.QtGui import *
from PySide2.QtWidgets import *
from PySide2.QtUiTools import QUiLoader

import sdm.houdini
from sdm.houdini.fileutils import SettingsFile, getLargerVersions, writeFileWithStructure, changeBaseDir, mergeDict
from sdm.utils import splitByCamelCase

class PreferencesDialog(QDialog):
	def __init__(self, settings):
		QDialog.__init__(self)

		uiPath = os.path.join(sdm.houdini.folder, 'ui', 'MENU_preferences.ui')

		file = QFile(uiPath)
		file.open(QFile.ReadOnly)

		loader = QUiLoader()
		self.ui = loader.load(file)
		self.ui.tools = {}
		self.ui.madeChanges = False
		self.settings = settings

		self.ui.LBL_version.setText(self.settings.get('version', 'v1.0.0'))
		self.ui.CHK_autoCheckUpdates.setChecked(self.settings.get('autoCheckUpdates', False))
		self.ui.CHK_autoCheckUpdates.clicked.connect(self._handleCheck)

		shelfToolsDir = os.path.join(sdm.houdini.folder, 'toolbar')
		allTools = glob.glob(os.path.join(shelfToolsDir, '*.shelf'))

		# Add all tools as enabled initially, except for sdm_tools which is the shelf file itself
		for tool in allTools:
			if tool == 'sdm_tools':
				continue

			toolName = os.path.splitext(os.path.split(tool)[1])[0]

			self._addTool(toolName)

		# No go disable the ones that have been marked as such
		for tool in self.settings.get('disabledTools', []):
			self.ui.tools[tool].setChecked(False)

		self.ui.setStyleSheet(hou.qt.styleSheet())

		self.ret = self.ui.exec_()

		hou.session.dummy = self.ui # Keeps the dialog open

	def _handleCheck(self):
		self.ui.madeChanges = True

	def _addTool(self, name):
		chk = QCheckBox(' '.join([s.capitalize() for s in splitByCamelCase(name)]))
		chk.setChecked(True)
		chk.clicked.connect(self._handleCheck)

		self.ui.LAY_tools.addWidget(chk)

		self.ui.tools[name] = chk

	def getSettings(self):
		disabledTools = []
		for tool, chk in self.ui.tools.iteritems():
			if not chk.isChecked():
				disabledTools.append(tool)

		self.settings.set('disabledTools', disabledTools)
		self.settings.set('autoCheckUpdates', self.ui.CHK_autoCheckUpdates.isChecked())

		return self.settings

class CheckForUpdatesDialog(QDialog):
	def __init__(self, newVersions, autoCheckUpdates):
		QDialog.__init__(self)

		uiPath = os.path.join(sdm.houdini.folder, 'ui', 'MENU_checkForUpdates.ui')

		file = QFile(uiPath)
		file.open(QFile.ReadOnly)

		loader = QUiLoader()
		self.ui = loader.load(file)

		self.ui.setStyleSheet(hou.qt.styleSheet())

		self.ui.TBL_versions.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
		self.ui.TBL_versions.horizontalHeader().setDefaultAlignment(Qt.AlignLeft)
		self.ui.TBL_versions.setSelectionBehavior(QAbstractItemView.SelectItems);
		self.ui.TBL_versions.setSelectionMode(QAbstractItemView.SingleSelection);

		self.ui.BTN_install.setEnabled(False)

		# Signal connection
		self.ui.BTN_cancel.clicked.connect(self.ui.reject)
		self.ui.BTN_install.clicked.connect(self.ui.accept)
		self.ui.TBL_versions.itemSelectionChanged.connect(self.handleSelectionChanged)

		self.ui.CHK_autoCheckUpdates.setChecked(autoCheckUpdates)

		self.populateRows(newVersions)

		self.ret = self.ui.exec_()

		hou.session.dummy = self.ui # Keeps the dialog open

	def handleSelectionChanged(self):
		self.ui.BTN_install.setEnabled(len(self.ui.TBL_versions.selectedItems()) > 0)

	def populateRows(self, newVersions):
		numRows = len(newVersions)
		cols = ['tag_name', 'body', 'created_at']

		self.ui.TBL_versions.setRowCount(numRows)

		for r in range(numRows):
			for c in range(len(cols)):
				key = cols[c]
				data = newVersions[r].get(key, None)

				if key == 'created_at' and data:
					date = datetime.strptime(data, '%Y-%m-%dT%H:%M:%SZ')
					data = date.strftime('%m/%d/%y (%I:%M:%S %p EST)')

				item = QTableWidgetItem(data)
				flags = item.flags() & ~Qt.ItemIsEditable

				if key != 'tag_name': # Every other column is non-selectable
					flags &= ~Qt.ItemIsSelectable

				item.setFlags(flags)

				self.ui.TBL_versions.setItem(r, c, item)

def about():
	webbrowser.open('http://www.sashaouellet.com')

def checkForUpdates():
	settingsJsonPath = os.path.join(sdm.houdini.folder, 'settings.json')
	currVer = 'v1.0.0'
	autoCheckUpdates = False
	settingsJson = {}
	settingsFile = open(settingsJsonPath, 'r+')

	if not os.path.exists(settingsJsonPath):
		settingsFile = open(settingsJsonPath, 'w+')

	try:
		settingsJson = json.loads(settingsFile.read())
	except ValueError:
		pass

	currVer = settingsJson.get('version', 'v1.0.0')
	autoCheckUpdates = settingsJson.get('autoCheckUpdates', False)

	releasesUrl = 'https://api.github.com/repos/sashaouellet/SDMTools/releases'
	allVersions = []

	try:
		response = urllib2.urlopen(releasesUrl)
		data = json.loads(response.read())

		for release in data:
			allVersions.append(release)
	except urllib2.URLError, e:
		hou.ui.displayMessage('Error when retrieving new versions: {}'.format(e), title='SDMTools Updates', severity=hou.severityType.Error)
		return

	newVersions = getLargerVersions(currVer, allVersions)

	if len(newVersions) > 0: # Prompt user for new versions
		dialog = CheckForUpdatesDialog(newVersions, autoCheckUpdates)

		if dialog.ret == QDialog.Rejected:
			settingsJson['autoCheckUpdates'] = dialog.ui.CHK_autoCheckUpdates.isChecked()

			settingsFile.seek(0)
			json.dump(settingsJson, settingsFile, sort_keys=True, indent=4, separators=(',', ': '))
			settingsFile.truncate()

			return

		autoCheckUpdates = dialog.ui.CHK_autoCheckUpdates.isChecked()

		ret = hou.ui.displayMessage('The selected version will be downloaded and installed. Would you like to proceed?', title='SDMTools Updates', buttons=('Yes', 'No'), close_choice=1)

		if ret == 1: # Denied installation
			return

		if dialog.ui.TBL_versions.selectedItems(): # Double check to make sure we have something selected
			selectedTag = dialog.ui.TBL_versions.selectedItems()[0].text()
			version = None

			for v in allVersions:
				if v['tag_name'] == selectedTag:
					version = v
					break

			if version:
				targetDir =  os.path.join(os.path.split(os.path.dirname(sdmtools.folder))[0], 'temp_{}'.format(uuid.uuid4())) # temp SDMTools base directory - to rename after deleting old one
				oldSettings = '{}'

				for dirpath, dirs, files in os.walk(os.path.dirname(sdmtools.folder)):
					for f in files:
						if f == 'settings.json':
							oldSettings = json.load(open(os.path.join(dirpath, f)))

				try:
					response = urllib2.urlopen(version['zipball_url'])
					s = StringIO.StringIO()

					s.write(response.read())

					with zipfile.ZipFile(s) as zip:
						sourceBase = os.path.split(zip.namelist()[0])[0]

						for file in zip.namelist():
							fileName = os.path.split(file)[1]

							if fileName != 'settings.json': # Don't want to override this
								writeFileWithStructure(zip.read(file), file, baseDir=targetDir)
							else:
								settingsData = json.loads(zip.read(file))
								overwriteSettings = settingsData.get('forceOverwrite', False)

								if overwriteSettings:
									writeFileWithStructure(zip.read(file), file, baseDir=targetDir)
								else: # Line by line merge
									targetSettings = open(changeBaseDir(file, targetDir), 'w+')
									mergedJson = mergeDict(json.load(zip.open(file)), oldSettings)
									mergedJson['version'] = version['tag_name']
									mergedJson['autoCheckUpdates'] = autoCheckUpdates

									json.dump(mergedJson, targetSettings, sort_keys=True, indent=4, separators=(',', ': '))

					oldFolder = os.path.dirname(sdmtools.folder)
					shutil.rmtree(oldFolder) # Delete old folder
					os.rename(targetDir, oldFolder)

					hou.ui.displayMessage('Successfully installed {}!'.format(version['tag_name']), title='SDMTools updates')

				except urllib2.URLError, e:
					hou.ui.displayMessage('Error when downloading new version: {}'.format(e), title='SDMTools Updates', severity=hou.severityType.Error)
					return
			else:
				hou.ui.displayMessage('Error loading version from selection. Please try again.', title='SDMTools Updates', severity=hou.severityType.Error)
				return
	else:
		hou.ui.displayMessage('No updates available', title='SDMTools Updates')

def showPreferences():
	settings = SettingsFile()

	dialog = PreferencesDialog(settings)

	if dialog.ret == QDialog.Rejected:
		return

	if dialog.ui.madeChanges:
		hou.ui.displayMessage('Changes made will only be reflected once you restart Houdini')

	settings = dialog.getSettings()

	settings.write()
