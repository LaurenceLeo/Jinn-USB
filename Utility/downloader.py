import os
import shutil
import sys
import urllib.request
import zipfile

from PyQt5.QtGui import QTextCursor, QIcon
from PyQt5.QtWidgets import QVBoxLayout, QHBoxLayout, QApplication, QFrame, QPushButton
from dialogs import JDialog, InfoMsgBox
from widgets import JPushButton, JCancelButton, LabelledComboBox, JTextEdit
from updatevariables import UpdateVariables

class DownloaderDialog(JDialog):
    def __init__(self):
        super().__init__()
        self.setWindowIcon(QIcon('GUI\jinndl.ico'))
        self.setInitialSize(800,800)

        self.initUi()
        self.setActions()

    def initUi(self):
        self.setWindowTitle("Download Jinn")
        self.windowLayout = QVBoxLayout(self)

        # Advanced options
        # Stored in a QFrame, this is hidden or shown by self.btnAdvancedOptions
        self.topBar = QHBoxLayout()
        self.btnAdvancedOptions = QPushButton("Show advanced options")

        self.comboBranch = LabelledComboBox("Choose branch:")
        self.comboBranch.cb.addItems(["HJinn", "LJinn", "master"])
        self.advancedOptionsLayout = QHBoxLayout()
        self.advancedOptionsLayout.addWidget(self.comboBranch)

        self.advancedOptionsFrame = QFrame()
        self.advancedOptionsFrame.setHidden(True)
        self.advancedOptionsFrame.setLayout(self.advancedOptionsLayout)
        self.topBar.addWidget(self.btnAdvancedOptions)
        self.topBar.addWidget(self.advancedOptionsFrame)

        self.updateLog = JTextEdit("Press 'Download' below to download the latest Jinn code to the USB memory stick")

        self.statusLayout = QVBoxLayout()
        self.statusLayout.addWidget(self.updateLog)

        self.btnDownload = JPushButton("Download")
        self.btnCancel = JCancelButton("Cancel")
        self.buttonBtm = QHBoxLayout()
        self.buttonBtm.addWidget(self.btnDownload)
        self.buttonBtm.addWidget(self.btnCancel)

        self.windowLayout.addLayout(self.topBar)
        self.windowLayout.addLayout(self.statusLayout)
        self.windowLayout.addLayout(self.buttonBtm)

    def setActions(self):
        self.btnAdvancedOptions.clicked.connect(self.showAdvancedOptions)
        self.btnDownload.clicked.connect(self.doDownload)
        self.btnCancel.clicked.connect(self.reject)

    def showAdvancedOptions(self):
        if self.advancedOptionsFrame.isHidden():
            self.advancedOptionsFrame.show()
            self.btnAdvancedOptions.setText("Hide advanced options")
        else:
            self.advancedOptionsFrame.hide()
            self.btnAdvancedOptions.setText("Show advanced options")

    def getBranch(self):
        return self.comboBranch.cb.currentText()

    def doDownload(self):
        branch = self.getBranch()
        updateVariables = UpdateVariables(branch)
        try:
            cwd = os.getcwd()
            dirname = os.path.basename(cwd)
            if dirname.upper() == updateVariables.codeDir.upper():
                raise Exception("This script must not be run with the current directory being \"{}\""
                                ", because it needs to replace that directory".format(cwd))

            # compute the root directory (`Jinn`) via where this script is being run from
            stdOut = setRootDir()

            updateJTextEdit(self.updateLog, stdOut)
            # download the zip file from github to the `Jinn` directory
            downloadZipFile(self.updateLog, updateVariables)

            # extract from the zip file to create `Jinn-master` directory in `Jinn` directory
            extractFromZipFile(self.updateLog, updateVariables)

            updateJTextEdit(self.updateLog,"Finished downloading and extracting latest Jinn code. Please insert the USB into your "
                            "work computer and run the installer.")
        except Exception as ex:
            raise ex
        InfoMsgBox("Finished","Download has finished. You can now close the downloader and remove the USB stick. To continue "
                   "upgrading Jinn plug this USB stick into your work PC and run the 'Jinn updater' shortcut",
                   "Download finished").exec()


def updateJTextEdit(jTextEdit: JTextEdit, newText):
    Text = jTextEdit.toPlainText() + "\n" + newText
    jTextEdit.moveCursor(QTextCursor.End)
    jTextEdit.setText(Text)
    jTextEdit.moveCursor(QTextCursor.End)

def setRootDir():
    # Store the parent of the directory this module is executing from in rootDir
    # this will be used as the root/parent of where the "Code" directory resides
    from inspect import currentframe, getframeinfo
    filename = getframeinfo(currentframe()).filename
    # get "Code" directory
    dir = os.path.dirname(os.path.realpath(filename))
    # set rootDir as *parent* of "Code" directory, i.e. "Jinn" directory
    global rootDir
    rootDir = os.path.dirname(dir)
    # Return output as string
    UpdateVariables.rootDir = rootDir
    return str(rootDir)


def checkProceed() -> bool:
    while True:
        sys.stderr.write("Proceed? [y/n]")
        sys.stderr.flush()
        answer = sys.stdin.readline().lower()
        if answer.startswith("y"):
            return True
        elif answer.startswith("n"):
            return False
        else:
            sys.stderr.write("Please type 'y' or 'n', followed by the RETURN/ENTER key\n")


def downloadZipFile(updateLog: JTextEdit, updateVariables: UpdateVariables):
    # First clear old zip files

    zipFilePath = updateVariables.getPath(updateVariables.zipDir)
    zipFile = updateVariables.getZipFile()
    zipFileTarget = os.path.join(zipFilePath, zipFile)
    zipFileUrl = updateVariables.getZipFileUrl()
    updateJTextEdit(updateLog, "Downloading Zip file from \"{}\" to \"{}\"\n".format(zipFileUrl, zipFileTarget))
    # taken from https://stackoverflow.com/a/7244263/489865
    # Download the file from `url` and save it locally under `file_name`:

    req = urllib.request.Request(zipFileUrl)
    with urllib.request.urlopen(req) as response, open(zipFileTarget, 'wb') as out_file:

        shutil.copyfileobj(response, out_file)
        out_file.close()
        updateJTextEdit(updateLog,"Download finished.")
    if not os.path.exists(zipFileTarget):
        raise Exception("Something went wrong: expected to create \"{}\"".format(zipFileTarget))


def extractFromZipFile(updateLog: JTextEdit, updateVariables: UpdateVariables):
    updateJTextEdit(updateLog, "Clearing old extracted code")
    updateVariables.clearExtractedFolder()
    zipFileDir = updateVariables.getPath(updateVariables.zipDir)
    zipFile = updateVariables.getZipFile()
    zipFilePath = os.path.join(zipFileDir, zipFile)
    zipExtractedDirPath = updateVariables.getZipExtractedDir()
    updateJTextEdit(updateLog, "Extracting from Zip file \"{}\" to \"{}\"\n".format(zipFilePath, zipExtractedDirPath))
    # taken from https://stackoverflow.com/a/3451150
    with zipfile.ZipFile(zipFilePath, 'r') as zip_ref:
        nameList = zip_ref.namelist()

        for x, name in enumerate(nameList):
            updateJTextEdit(updateLog, "Extracting: {}".format(name))
            zip_ref.extract(name, zipExtractedDirPath)

    if not os.path.exists(zipExtractedDirPath):
        raise Exception("Something went wrong: expected to create \"{}\"".format(zipExtractedDirPath))
    if os.path.exists(zipFilePath):
        os.unlink(zipFilePath)


def renameCodeDirectory(updateLog: JTextEdit, updateVariables: UpdateVariables):
    updateJTextEdit(updateLog, "Renaming Code directory")
    codeDirPath = os.path.join(rootDir, updateVariables.codeDir)
    zipExtractedDirPath = updateVariables.getZipExtractedDir()
    codeDirAlreadyExists = os.path.exists(codeDirPath)
    if codeDirAlreadyExists:
        updateJTextEdit(updateLog, "Rename existing \"{}\" directory to \"{}\", and ".format(updateVariables.codeDir, updateVariables.oldCodeDir))
    updateJTextEdit(updateLog, "Rename \"{}\" to \"{}\"\n".format(updateVariables.getZipExtractedDir, updateVariables.codeDir))
    # rename existing `Code` directory to `OldCode`

    if codeDirAlreadyExists:
        oldCodeDirPath = updateVariables.getOldCodeDirWithDateTime()
        updateJTextEdit(updateLog,"Renaming \"{}\" to \"{}\"\n".format(codeDirPath, oldCodeDirPath))
        os.rename(codeDirPath, oldCodeDirPath)
    # rename directory from extracted zip file to `Code`
        updateJTextEdit(updateLog,"Renaming \"{}\" to \"{}\"\n".format(zipExtractedDirPath, codeDirPath))
    os.rename(zipExtractedDirPath, codeDirPath)



if __name__ == '__main__':
    # -*- coding: utf-8 -*-

    app = QApplication(sys.argv)
    updateDialog = DownloaderDialog()
    sys.exit(updateDialog.exec_())