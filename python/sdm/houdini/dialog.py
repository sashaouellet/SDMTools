import os, glob
import logging
import hou
import urllib, json, zipfile, StringIO, uuid, shutil, base64
from datetime import datetime
import smtplib

from PySide2.QtCore import *
from PySide2.QtGui import *
from PySide2.QtWidgets import *
from PySide2.QtUiTools import QUiLoader

import sdm.houdini
from sdm.houdini.fileutils import SettingsFile, getLargerVersions, writeFileWithStructure, changeBaseDir, mergeDict, ValidationType
from sdm.utils import splitByCamelCase
from sdm.houdini.shelves import addShelf

logger = logging.getLogger(__name__)

class PreferencesDialog(QDialog):
	def __init__(self, settings, parent=None):
		QDialog.__init__(self, parent=parent)

		uiPath = os.path.join(sdm.houdini.folder, 'ui', 'MENU_preferences.ui')

		file = QFile(uiPath)
		file.open(QFile.ReadOnly)

		loader = QUiLoader()
		self.ui = loader.load(file)
		self.ui.tools = {}
		self.settings = settings

		self.ui.LBL_version.setText(self.settings.get('version', 'v1.0.0'))
		self.ui.LNE_email.setText(self.settings.get('notificationEmail', ''))
		self.ui.LNE_password.setText(base64.b64decode(self.settings.get('notificationPassword', '')))
		self.ui.CHK_autoCheckUpdates.setChecked(self.settings.get('autoCheckUpdates', False))

		self.ui.LNE_password.setEchoMode(QLineEdit.Password)
		self.ui.BTN_verifyLogin.clicked.connect(self._verifyLogin)
		self.ui.BTN_ok.clicked.connect(self._save)
		self.ui.BTN_cancel.clicked.connect(self.ui.reject)

		shelfToolsDir = os.path.join(sdm.houdini.folder, 'toolbar')
		allTools = glob.glob(os.path.join(shelfToolsDir, '*.shelf'))

		# Add all tools as enabled initially, except for sdm_tools which is the shelf file itself
		for tool in allTools:
			toolName = os.path.splitext(os.path.split(tool)[1])[0]

			if toolName == 'sdm_tools':
				continue

			self._addTool(toolName)

		# No go disable the ones that have been marked as such
		for tool in self.settings.get('disabledTools', []):
			self.ui.tools[tool].setChecked(False)

		self.ui.setStyleSheet(hou.qt.styleSheet())
		self.ui.setWindowModality(Qt.NonModal)

		self.ui.show()

	def _addTool(self, name):
		chk = QCheckBox(' '.join([s.capitalize() for s in splitByCamelCase(name)]))
		chk.setChecked(True)

		self.ui.LAY_tools.addWidget(chk)

		self.ui.tools[name] = chk

	def getSettings(self):
		disabledTools = []
		for tool, chk in self.ui.tools.iteritems():
			if not chk.isChecked():
				disabledTools.append(tool)

		self.settings.set('disabledTools', disabledTools)
		self.settings.set('notificationEmail', self.ui.LNE_email.text(), validation=ValidationType.EMAIL)
		self.settings.set('notificationPassword', base64.b64encode(self.ui.LNE_password.text()))
		self.settings.set('autoCheckUpdates', self.ui.CHK_autoCheckUpdates.isChecked())

		return self.settings

	def _save(self):
		self.getSettings().write()
		addShelf()
		self.ui.close()

		hou.ui.displayMessage('Preferences have been saved', title='SDMTools Preferences')

	def _verifyLogin(self):
		server = smtplib.SMTP('smtp.gmail.com:587')
		user = self.ui.LNE_email.text()
		pw = self.ui.LNE_password.text()

		server.starttls()

		try:
			logger.info('Authenticating user')
			server.login(user, pw)
			hou.ui.displayMessage('Successfully authenticated!', title='Successful Authentication')
			server.quit()
		except smtplib.SMTPAuthenticationError:
			hou.ui.displayMessage('Invalid login. Please check credentials. Also ensure that your account is not setup for 2-step authentication and that you have enabled access from 3rd party apps.', title='Authentication Error', severity=hou.severityType.Error)
			server.quit()
			logger.warning('Error during authentication', exc_info=True)

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

def checkForUpdates(silent=False):
	settings = SettingsFile()

	currVer = settings.get('version', 'v1.0.0')
	autoCheckUpdates = settings.get('autoCheckUpdates', False)

	releasesUrl = 'http://api.github.com/repos/sashaouellet/SDMTools/releases'
	allVersions = []

	try:
		logger.info('Retrieving all releases')
		response = urllib.urlopen(releasesUrl)
		data = json.loads(response.read())

		for release in data:
			allVersions.append(release)
	except urllib2.URLError, e:
		hou.ui.displayMessage('Error when retrieving new versions: {}'.format(e), title='SDMTools Updates', severity=hou.severityType.Error)
		logger.warning('Error in retrieval', exc_info=True)
		return

	newVersions = getLargerVersions(currVer, allVersions)

	logger.debug('Newer versions found: {}'.format(newVersions))

	if len(newVersions) > 0: # Prompt user for new versions
		dialog = CheckForUpdatesDialog(newVersions, autoCheckUpdates)

		if dialog.ret == QDialog.Rejected:
			settings.set('autoCheckUpdates', dialog.ui.CHK_autoCheckUpdates.isChecked())
			settings.write()

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
				logger.info('Installing {}'.format(selectedTag))

				targetDir =  os.path.join(os.path.split(os.path.dirname(sdmtools.folder))[0], 'temp_{}'.format(uuid.uuid4())) # temp SDMTools base directory - to rename after deleting old one
				oldSettings = '{}'

				for dirpath, dirs, files in os.walk(os.path.dirname(sdmtools.folder)):
					for f in files:
						if f == 'settings.json':
							oldSettings = json.load(open(os.path.join(dirpath, f)))

				try:
					logger.info('Obtaining zipball from {}'.format(version['zipball_url']))
					response = urllib2.urlopen(version['zipball_url'])
					s = StringIO.StringIO()

					s.write(response.read())

					with zipfile.ZipFile(s) as zip:
						sourceBase = os.path.split(zip.namelist()[0])[0]

						for file in zip.namelist():
							fileName = os.path.split(file)[1]

							logger.debug('Installing {}'.format(fileName))

							if fileName != 'settings.json': # Don't want to override this
								writeFileWithStructure(zip.read(file), file, baseDir=targetDir)
							else:
								settingsData = json.loads(zip.read(file))
								overwriteSettings = settingsData.get('forceOverwrite', False)

								if overwriteSettings:
									logger.debug('Forced overwrite of settings.json')
									writeFileWithStructure(zip.read(file), file, baseDir=targetDir)
								else: # Line by line merge
									logger.debug('Merging new settings with existing')
									targetSettings = open(changeBaseDir(file, targetDir), 'w+')
									mergedJson = mergeDict(json.load(zip.open(file)), oldSettings)
									mergedJson['version'] = version['tag_name']
									mergedJson['autoCheckUpdates'] = autoCheckUpdates

									json.dump(mergedJson, targetSettings, sort_keys=True, indent=4, separators=(',', ': '))

					oldFolder = os.path.dirname(sdmtools.folder)
					shutil.rmtree(oldFolder) # Delete old folder
					os.rename(targetDir, oldFolder)

					hou.ui.displayMessage('Successfully installed {}!'.format(version['tag_name']), title='SDMTools updates')
					logger.info('Finished installation')

				except urllib2.URLError, e:
					hou.ui.displayMessage('Error when downloading new version: {}'.format(e), title='SDMTools Updates', severity=hou.severityType.Error)
					logger.warning('Error retrieving zipball', exc_info=True)
					return
			else:
				hou.ui.displayMessage('Error loading version from selection. Please try again.', title='SDMTools Updates', severity=hou.severityType.Error)
				logger.warning('Could not get version based on selected tag: {}'.format(selectedTag))
				return
	else:
		logger.debug('No new updates')
		if not silent:
			hou.ui.displayMessage('No updates available', title='SDMTools Updates')

def showPreferences():
	settings = SettingsFile()

	dialog = PreferencesDialog(settings, parent=hou.qt.mainWindow())
	hou.session.dummy = dialog.ui # Keeps the dialog open
