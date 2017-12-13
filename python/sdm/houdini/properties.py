"""Utility functions regarding property and parameter interfaces

__author__ = Sasha Ouellet (www.sashaouellet.com)
__version__ = 1.0.0
__date__ = 12/10/17
"""

import hou

def initRopNotificationProperty(node):
	parmTemplate = node.parmTemplateGroup()
	folderParm = parmTemplate.containingFolder('execute')
	allParms = folderParm.parmTemplates()
	newParms = ()

	for parm in allParms:
		if parm.name() == 'renderdialog':
			parm.setJoinWithNext(True)

			newParms += (parm,)

			notifyParm = hou.ToggleParmTemplate('notify', 'Notify on Completion', help='Receive a notification when this ROP output operation completes. Notifications are based on settings in SDMTools > Preferences.')
			newParms += (notifyParm,)
		elif parm.name() == 'execute':
			execCache = parm.clone()

			parm.hide(True)

			newParms += (parm,)
			callback = execCache.scriptCallback()
			callback = 'import time; start = time.time(); ' + callback
			callback += "; from sdm.houdini.notifications import notifyUser, NotificationType;" \
			"seconds = time.time() - start;" \
			"m, s = divmod(seconds, 60);" \
			"h, m = divmod(m, 60);" \
			"p = hou.pwd().parm('notify');" \
			"data = {'Node':hou.pwd().name(), 'Duration':'%d:%02d:%02d' % (h, m, s)};" \
			"notifyUser(NotificationType.ROP_COMPLETE if p and p.eval() else None, data=data)"

			execCache.setScriptCallback(callback)
			execCache.setName('executeWithNotification')

			newParms += (execCache,)
		else:
			newParms += (parm,)

	folderParm.setParmTemplates(newParms)
	parmTemplate.replace(folderParm.name(), folderParm)

	node.setParmTemplateGroup(parmTemplate)