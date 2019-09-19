import os
from win32com.client import Dispatch

# This is flawed if used on a system with an altered desktop location
# Also will probably fail on a non-Windows environment
# desktop = os.path.join(os.environ["HOMEPATH"], "Desktop")


def createShortcut(codeFolder='', python=''):
    python = ''
    codeFolder = codeFolder
    # print(codeFolder)
    # print("creating shortcut")
    try:
        shell = Dispatch('WScript.Shell')
        desktop = shell.SpecialFolders('Desktop')
        # print(desktop)
        path = os.path.join(desktop, 'Jinnww.lnk')
        # print(path)
        argument = 'home.py'
        # print(argument)
        icon =  os.path.join(codeFolder, 'GUI\jinn.ico')
        # print(icon)
        #
        # print("creating shortcut")
        shortcut = shell.CreateShortCut(path)
        # print("creating shortcut")
        shortcut.IconLocation = icon
        shortcut.Targetpath = "python"
        shortcut.Arguments = argument
        # print("creating shortcut")
        shortcut.WorkingDirectory = codeFolder

        shortcut.save()
    except Exception as e:
        raise e