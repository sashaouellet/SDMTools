import hou

def createFloatingIPR():
	desktop = hou.ui.curDesktop()
	ipr = desktop.createFloatingPaneTab(hou.paneTabType.IPRViewer, size=(800, 600))