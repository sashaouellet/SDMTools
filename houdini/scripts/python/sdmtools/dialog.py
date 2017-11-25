import os
import hou
import urllib2, json, zipfile, StringIO
from datetime import datetime

from PySide2.QtCore import *
from PySide2.QtGui import *
from PySide2.QtWidgets import *
from PySide2.QtUiTools import QUiLoader

import sdmtools
from sdmtools.fileutils import getLargerVersions, writeFileWithStructure

class CheckForUpdatesDialog(QDialog):
	def __init__(self, newVersions, autoCheckUpdates):
		QDialog.__init__(self)

		uiPath = os.path.join(sdmtools.folder, 'ui', 'MENU_checkForUpdates.ui')

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
		self.ui.BTN_cancel.clicked.connect(self.ui.reject)
		self.ui.BTN_install.clicked.connect(self.ui.accept)

		self.ui.CHK_autoCheckUpdates.setChecked(autoCheckUpdates)

		self.populateRows(newVersions)

		self.ui.TBL_versions.itemSelectionChanged.connect(self.handleSelectionChanged)

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
				data = newVersions[r][cols[c]]

				if key == 'created_at':
					date = datetime.strptime(data, '%Y-%m-%dT%H:%M:%SZ')
					data = date.strftime('%m/%d/%y (%I:%M:%S %p EST)')

				item = QTableWidgetItem(data)
				flags = item.flags() & ~Qt.ItemIsEditable

				if key != 'tag_name': # Every other column is non-selectable
					flags &= ~Qt.ItemIsSelectable

				item.setFlags(flags)

				self.ui.TBL_versions.setItem(r, c, item)

def about():
	print 'about2'

def checkForUpdates():
	settingsJsonPath = os.path.join(sdmtools.folder, 'settings.json')
	currVer = 'v1.0.0'
	autoCheckUpdates = False

	if os.path.exists(settingsJsonPath):
		with open(settingsJsonPath) as file:
			settingsJson = json.loads(file.read())

			currVer = settingsJson['version']
			autoCheckUpdates = settingsJson['autoCheckUpdates'] != 'False'
	else: # make file with version set to 1.0.0
		pass

	releasesUrl = 'https://api.github.com/repos/sashaouellet/SDMTools/releases'
	allVersions = [dict({'tag_name':'v1.0.2', 'body':'This is a test description', 'created_at':'2017-11-22T23:24:38Z', 'zipball_url':'https://api.github.com/repos/sashaouellet/SDMTools/zipball/v1.0.0'})] # TODO: Make empty after testing

	allVersions.append(dict({'tag_name':'v2.0.2', 'body':'This is another test', 'created_at':'2017-11-23T17:20:10Z'}))

	try:
		response = urllib2.urlopen(releasesUrl)
		data = json.loads(response.read())

		for release in data:
			allVersions.append(release)
	except urllib2.URLError, e:
		hou.ui.displayMessage('Error when retrieving new versions: {}'.format(e), title='SDMTools Updates', severity=hou.severityType.Error)
		return

	newVersions = getLargerVersions(currVer, allVersions)

	if newVersions: # Prompt user for new
		dialog = CheckForUpdatesDialog(newVersions, autoCheckUpdates)

		if dialog.ret == QDialog.Rejected:
			return

        ret = hou.ui.displayMessage('The selected version will be downloaded and installed. Would you like to proceed?', title='SDMTools Updates', buttons=('Yes', 'No'), close_choice=1)

        if ret != 1: # Confirmed installation
	        if dialog.ui.TBL_versions.selectedItems(): # Double check to make sure we have something selected
	        	selectedTag = dialog.ui.TBL_versions.selectedItems()[0].text()
	        	version = None

	        	for v in allVersions:
	        		if v['tag_name'] == selectedTag:
	        			version = v
	        			break

	        	if version:
	        		try:
	        			response = urllib2.urlopen(version['zipball_url'])
	        			s = StringIO.StringIO()

	        			s.write(response.read())

	        			targetDir = os.path.dirname(sdmtools.folder) # SDMTools base directory
	        			with zipfile.ZipFile(s) as zip:
	        				sourceBase = os.path.split(zip.namelist()[0])[0]

	        				for file in zip.namelist():
	        					fileName = os.path.split(file)

	        					if fileName != 'settings.json': # Don't want to override this
	        						writeFileWithStructure(zip.read(file), file, baseDir=targetDir)
	        					else:
	        						settingsData = json.loads(zip.read(file))
	        						overwriteSettings = settingsData.get('forceOverwrite', False)

	        						if overwriteSettings:
	        							writeFileWithStructure(zip.read(file), file, baseDir=targetDir)
	        						else: # Line by line merge
	        							targetSettings = open(changeBaseDir(file, targetDir), 'w+')
	        							mergedJson = mergeJsonFiles(json.loads(zip.open(file)), json.loads(targetSettings))

	        							targetSettings.write(mergedJson)

	        		except urllib2.URLError, e:
	        			hou.ui.displayMessage('Error when downloading new version: {}'.format(e), title='SDMTools Updates', severity=hou.severityType.Error)
	        			return
	        	else:
	        		hou.ui.displayMessage('Error loading version from selection. Please try again.', title='SDMTools Updates', severity=hou.severityType.Error)
	        		return
	else:
		hou.ui.displayMessage('No updates available', title='SDMTools Updates')
