import wx
from Controllers import dicom_controller

class App(wx.App):
    """subclass of wx.App necessary for main event loop"""
    def onInit(self):
        return True

if __name__ == '__main__':
    """Starts the main event loop for the app"""
    app = App(redirect=False)
    mainFrame = dicom_controller.Controller()
    app.MainLoop()