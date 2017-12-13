import os, json
import logging, logging.config
from logging.handlers import RotatingFileHandler

# Installation directory for Houdini SDM Tools
folder = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))), 'houdini')
logDir = os.path.join(folder, 'logs')

# Setup logging
if not os.path.exists(logDir):
	os.makedirs(logDir)

logHandler = RotatingFileHandler(os.path.join(logDir, 'sdm_tools.log'), maxBytes=10485760, backupCount=5, encoding='utf8')

def getLogger(moduleName):
	logger = logging.getLogger(moduleName)
	formatter = logging.Formatter('%(asctime)s [%(levelname)s]: %(name)s:%(funcName)s: %(message)s', '%Y-%m-%d %H:%M:%S')

	logHandler.setFormatter(formatter)
	logger.addHandler(logHandler)

	logger.propagate = False

	return logger

logger = getLogger(__name__)

logger.debug('Init SDMTool Houdini library in folder: {}'.format(folder))