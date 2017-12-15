"""Functions regarding notifying the user about events and their completions

__author__ = Sasha Ouellet (www.sashaouellet.com)
__version__ = 1.0.0
__date__ = 12/10/17
"""

from enum import Enum
import logging
import smtplib, base64
from email.mime.text import MIMEText

from sdm.houdini.fileutils import SettingsFile
from sdm.utils import splitByCamelCase

logger = logging.getLogger(__name__)

class NotificationType(Enum):
	ROP_COMPLETE = 1

def notifyUser(msg, data={}):
	"""Given a message type and optional data, notifies
	the user via the email saved in the settings file

	Args:
	    msg (NotificationType): The type of notification to send, the actual
	    	body of the message is determined by this value
	    data (dict, optional): Optional data that will be parsed into the message
	    	such as where this notification is coming from, time of completion, etc.
	"""
	if not msg:
		return

	server = smtplib.SMTP('smtp.gmail.com:587')

	if msg == NotificationType.ROP_COMPLETE:
		logger.info('Notifying for ROP completion')
		server.starttls()

		settings = SettingsFile()
		user = settings.get('notificationEmail', '')
		pw = base64.b64decode(settings.get('notificationPassword', ''))

		if user and pw:
			message = MIMEText(formatMessage('Cache completed', data))
			message['Subject'] = 'SDMTools - {} has completed'.format(data.get('Node', 'Cache'))

			logger.debug('Authenticating user')
			server.login(user, pw)
			server.sendmail(user, user, message.as_string())
			logger.debug('Sent email')
			server.quit()


def formatMessage(body, data={}):
	"""Formats a message as a string with the given
	body and optional data pieces. The data pieces will
	be separated on new lines by key, alongside their associated
	values.

	Args:
	    body (str): The body of the message
	    data (dict, optional): Optional data pieces to include underneath
	    	the body

	Returns:
	    str: The formatted message with, at minimum, the given body.
	"""
	out = body + '\n'

	for key, val in data.iteritems():
		out += '\n' + '{}: {}'.format(' '.join(splitByCamelCase(key)), val)

	return out