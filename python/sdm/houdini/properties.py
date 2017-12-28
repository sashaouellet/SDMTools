"""Utility functions regarding property and parameter interfaces

__author__ = Sasha Ouellet (www.sashaouellet.com)
__version__ = 1.0.0
__date__ = 12/10/17
"""

import hou

def initRopNotificationProperty(node):
	"""Given a ROP node, replaces the execute button with an identical
	button that launches a notification after the cache/render process
	if the newly added checkbox is checked.

	Args:
	    node (hou.Node): The ROP node to add the new button and notifications
	    	checkbox to
	"""
	parmTemplate = node.parmTemplateGroup()
	notifyParm = hou.ToggleParmTemplate('notify', 'Notify on Completion', help='Receive a notification when this ROP output operation completes. Notifications are based on settings in SDMTools > Preferences.')
	notifyScript = "; from sdm.houdini.notifications import notifyUser, NotificationType;" \
				"seconds = time.time() - start;" \
				"m, s = divmod(seconds, 60);" \
				"h, m = divmod(m, 60);" \
				"p = hou.pwd().parm('notify');" \
				"data = {'Node':hou.pwd().name(), 'Duration':'%d:%02d:%02d' % (h, m, s)};" \
				"notifyUser(NotificationType.ROP_COMPLETE if p and p.eval() else None, data=data)"

	if node.type() == 'filecache':
		folderParm = parmTemplate.containingFolder('execute')
		allParms = folderParm.parmTemplates()
		newParms = ()

		for parm in allParms:
			if parm.name() == 'renderdialog':
				parm.setJoinWithNext(True)

				newParms += (parm,)
				newParms += (notifyParm,)
			elif parm.name() == 'execute':
				execCache = parm.clone()

				parm.hide(True)

				newParms += (parm,)
				callback = execCache.scriptCallback()
				callback = 'import time; start = time.time(); ' + callback
				callback += notifyScript

				execCache.setScriptCallback(callback)
				execCache.setName('executeWithNotification')

				newParms += (execCache,)
			else:
				newParms += (parm,)

		folderParm.setParmTemplates(newParms)
		parmTemplate.replace(folderParm.name(), folderParm)
	else:
		renderButton = parmTemplate.find('execute')

		if renderButton:
			renderNotify = renderButton.clone()

			renderButton.hide(True)

			callback = renderButton.scriptCallback() or 'import hou; hou.pwd().render()'
			callback = 'import time; start = time.time(); ' + callback
			callback += notifyScript

			renderNotify.setScriptCallback(callback)
			renderNotify.setName('executeWithNotification')
			parmTemplate.replace('execute', renderButton)
			parmTemplate.insertAfter('execute', renderNotify)
			parmTemplate.insertAfter('renderdialog', notifyParm)

	node.setParmTemplateGroup(parmTemplate)


def getMainParm(node, parm):
	"""Given a node and a name of a parameter on the node,
	returns the parameter at the end of any potential reference
	chains.

	Args:
	    node (hou.Node): The node to search for the parameter on
	    parm (str): The name of the parameter on the given node to
	    	find the final referenced parameter of

	Returns:
	    hou.Parm: The final parm in the chain of referenced parms

	Raises:
	    ValueError: When the given node is not of type hou.Node
	"""
	parm = node.parm(parm)

	assert isinstance(node, hou.Node), 'Must specify a node (hou.Node)'

	if not parm:
		raise ValueError('Specified parm: {} is not present on given node {}'.format(parm, node))
		return None

	otherParm = parm.getReferencedParm()

	while otherParm != parm:
		parm = otherParm

	return otherParm