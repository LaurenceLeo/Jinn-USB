import os
import shutil
import sys
import pathlib

from PyQt5.QtGui import QTextCursor, QIcon
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QVBoxLayout, QHBoxLayout, QApplication, QFrame, QSizePolicy, QListWidget
from dialogs import JDialog, InfoMsgBox
from widgets import JPushButton, JCancelButton, JTextEdit, DirectorySelector
from updatevariables import UpdateVariables
from createshortcut import createShortcut

class UpdaterDialog(JDialog):
    def __init__(self):
        super().__init__()

        self.setInitialSize(800, 800)
        self.initUi()
        self.setActions()

    def initUi(self):
        self.setWindowTitle("Update Jinn")

        self.windowLayout = QVBoxLayout(self)
        self.topBar = QHBoxLayout()
        self.middleLayout = QHBoxLayout()
        self.advancedOptionsLayout = QVBoxLayout()
        self.advancedButtonLayout = QHBoxLayout()
        self.buttonBtm = QHBoxLayout()

        self.advancedOptionsFrame = QFrame()
        self.advancedOptionsFrame.setHidden(True)

        self.updateLog = JTextEdit("Use this on your work PC. Press 'Update' to copy the Jinn code on this USB stick to "
                                 "this PC. The old code will be saved incase it is needed.")
        self.updateLog.setReadOnly(True)

        self.btnAdvancedOptions = JPushButton("Show advanced options")
        self.btnLocateJinn = JPushButton("Locate Jinn installation")
        self.btnUpdate = JPushButton("Update")
        self.btnCreateShortcut = JPushButton("Create desktop shortcut")
        self.btnCancel = JCancelButton("Cancel")

        self.codeDir = DirectorySelector(caption="Select Code directory")
        self.codeDir.leDirname.setText("C:/Jinn/Code")


        self.advancedOptionsLayout.addWidget(self.codeDir)
        self.advancedButtonLayout.addWidget(self.btnCreateShortcut)
        self.advancedButtonLayout.addWidget(self.btnLocateJinn)
        self.advancedOptionsLayout.addLayout(self.advancedButtonLayout)
        self.advancedOptionsFrame.setLayout(self.advancedOptionsLayout)

        self.buttonBtm.addWidget(self.btnUpdate)
        self.buttonBtm.addWidget(self.btnCancel)

        self.topBar.addWidget(self.btnAdvancedOptions)
        self.middleLayout.addWidget(self.advancedOptionsFrame)

        self.windowLayout.addLayout(self.topBar)

        self.windowLayout.addLayout(self.middleLayout)
        self.windowLayout.addStretch()
        self.windowLayout.addWidget(self.updateLog)
        self.windowLayout.addLayout(self.buttonBtm)

    def setActions(self):
        self.btnLocateJinn.clicked.connect(self.locateCodeFolder)
        self.btnUpdate.clicked.connect(self.updateCode)
        self.btnCreateShortcut.clicked.connect(self.createShortcut)
        self.btnCancel.clicked.connect(self.reject)
        self.btnAdvancedOptions.clicked.connect(self.showAdvancedOptions)

    def showAdvancedOptions(self):
        if self.advancedOptionsFrame.isHidden():
            self.advancedOptionsFrame.show()
            self.btnAdvancedOptions.setText("Hide advanced options")
        else:
            self.advancedOptionsFrame.hide()
            self.btnAdvancedOptions.setText("Show advanced options")

    def createShortcut(self):
        path = self.codeDir.leDirname.text()
        try:
            print("Attempting shortcut to path variable 'python3'")
            createShortcut(path, 'python3')
        except:
            print("'python3' failed using 'python'")
            createShortcut(path, 'python')

    def locateCodeFolder(self):
        root = "C:\\"
        pattern = '..\Jinn\Code\home.py'
        # Want to find all Jinn\Code paths
        # Performs a walk through operating system paths and looks for the match "Jinn\Code"
        # Potential for failure if user has multiple Jinns for some reason
        try:
            possibleDirs = []
            for path, dirs, files in os.walk(os.path.abspath(root)):
                if pathlib.PurePath(path).match('*/Jinn/Code'):
                    possibleDirs.append(path)

            print(possibleDirs)
        except Exception as ex:
            raise ex

        if len(possibleDirs) > 1:
            multipleJinnDialog = MultipleJinnDialog(possibleDirs)
            with multipleJinnDialog.delayedDeleteOnClose():
                multipleJinnDialog.exec()
                path = multipleJinnDialog.getPath()
        else:
            path = possibleDirs[0]

        self.codeDir.leDirname.setText(str(path))

    def updateCode(self):
        updateVariables = UpdateVariables()
        # Rename old code directory and then move new code and rename it
        codeDirPath = self.codeDir.leDirname.text()
        codeDirPath = os.path.abspath(codeDirPath)
        oldCodeFolder = updateVariables.getOldCodeDirWithDateTime()

        jinnDirPath = os.path.join(codeDirPath, "..")

        codeDirAlreadyExists = os.path.exists(codeDirPath)
        if codeDirAlreadyExists:
            updateJTextEdit(self.updateLog,
                            "Rename existing \"{}\" directory to \"{}\", and ".format(codeDirPath,
                                                                                      oldCodeFolder))
        updateJTextEdit(self.updateLog, "Rename \"{}\" to \"{}\"\n".format(codeDirPath, updateVariables.codeDir))
        # rename existing `Code` directory to `OldCode`
        if codeDirAlreadyExists:
            oldCodeDirPath = os.path.join(jinnDirPath, oldCodeFolder)
            updateJTextEdit(self.updateLog, "Renaming \"{}\" to \"{}\"\n".format(codeDirPath, oldCodeDirPath))
            os.rename(codeDirPath, oldCodeDirPath)
            # rename directory from extracted zip file to `Code`
            updateJTextEdit(self.updateLog, "Renaming \"{}\" to \"{}\"\n".format(codeDirPath, codeDirPath))
        # Old code folder is renamed. Now we need to move the newCode and rename it
        # New code is in UpdateVariables.getPath(newCode), unfortunately there is an unknown folder name here from Git
        # First work out the Git hub zip extracted name
        gitFolder = getImmediateSubdirectories(updateVariables.getPath(updateVariables.codeDir))[0]
        print(gitFolder)
        newCode = os.path.join(updateVariables.getPath(updateVariables.codeDir), gitFolder)
        try:
            os.chdir(newCode)
            shutil.copytree(newCode, codeDirPath)
            dialog = InfoMsgBox("Update Finished", "Update finished with no faults. Code has been updated to the USB "
                                                   "copy", "Finished")
            dialog.exec()
        except Exception as e:
            raise e

class MultipleJinnDialog(JDialog):
    def __init__(self, paths=list, parent=None):
        super().__init__(parent)
        self.path =  None

        self.setInitialSize(500, 200)

        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(20, 20, 20, 20)
        self.layout.setSpacing(15)

        self.informativeText = JTextEdit("More than one Jinn installation has been found on this PC. Please select the one you wish to use", self)
        self.informativeText.setProperty("class", "backgroundColorTransparent")
        self.informativeText.setReadOnly(True)
        self.informativeText.setSizePolicy(QSizePolicy.Preferred,
                                           QSizePolicy.MinimumExpanding)
        self.pathList = QListWidget()
        self.pathList.addItems(paths)

        self.btnOK = JPushButton("Ok", self)
        self.btnCancel = JCancelButton("Cancel", self)

        self.informativeText.setAlignment(Qt.AlignHCenter)

        self.layout.addWidget(self.informativeText)
        self.layout.addWidget(self.pathList)
        self.layout.addWidget(self.btnOK)
        self.layout.addWidget(self.btnCancel)

        self.layout.setAlignment(self.btnOK, Qt.AlignHCenter)

        self.btnOK.clicked.connect(self.selectPath)
        self.btnCancel.clicked.connect(self.reject)

    def selectPath(self):
        path = self.pathList.selectedItems()[0]
        if self.pathList.selectedItems():
            self.path =  path.data(0)
            self.accept()

    def getPath(self):
        return self.path

def updateJTextEdit(jTextEdit: JTextEdit, newText):
    Text = jTextEdit.toPlainText() + "\n" + newText
    jTextEdit.moveCursor(QTextCursor.End)
    jTextEdit.setText(Text)
    jTextEdit.moveCursor(QTextCursor.End)

def getImmediateSubdirectories(dir):
    return [name for name in os.listdir(dir) if os.path.isdir(os.path.join(dir, name))]

if __name__ == '__main__':
    # -*- coding: utf-8 -*-

    app = QApplication(sys.argv)
    updateDialog = UpdaterDialog()
    sys.exit(updateDialog.exec_())