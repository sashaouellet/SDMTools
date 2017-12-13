import os, json, inspect
import logging, logging.config
from logging.handlers import RotatingFileHandler

# Installation directory for Houdini SDM Tools
folder = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))), 'houdini')
logDir = os.path.join(folder, 'logs')

if not os.path.exists(logDir):
	os.makedirs(logDir)

logHandler = RotatingFileHandler(os.path.join(logDir, 'sdm_tools.log'), maxBytes=10485760, backupCount=5, encoding='utf8')

# Setup logging
loggingConfig = os.path.join(folder, 'logging.json')

if os.path.exists(loggingConfig):
	with open(loggingConfig, 'rt') as f:
		config = json.load(f)

	logging.config.dictConfig(config)
else:
	logging.basicConfig(level=logging.DEBUG)

def getLogger():
	frm = inspect.stack()[1]
	mod = inspect.getmodule(frm[0])

	logger = logging.getLogger(mod.__name__)
	formatter = logging.Formatter('%(asctime)s [%(levelname)s]: %(name)s:%(funcName)s: %(message)s', '%Y-%m-%d %H:%M:%S')

	logHandler.setFormatter(formatter)
	logger.addHandler(logHandler)

	return logger


logger = getLogger()

logger.debug('Init SDMTool Houdini library in folder: {}'.format(folder))