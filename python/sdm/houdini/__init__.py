import hou
import os, json
import logging, logging.config

# Installation directory for Houdini SDM Tools
folder = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))), 'houdini')
logDir = os.path.join(folder, 'logs')

# Setup logging
if not os.path.exists(logDir):
	os.makedirs(logDir)

logConfigPath = os.path.join(folder, 'logging.json')

if os.path.exists(logConfigPath):
	with open(logConfigPath) as logConfig:
		config = json.load(logConfig)
		config['handlers']['file_handler']['filename'] = os.path.join(logDir, 'sdm_tools.log')

		logging.config.dictConfig(config)
else:
	logging.basicConfig(level=logging.DEBUG)

logger = logging.getLogger(__name__)

logger.info('Houdini version: {}'.format(hou.applicationVersionString()))
logger.info('Init SDMTool Houdini library in folder: {}'.format(folder))