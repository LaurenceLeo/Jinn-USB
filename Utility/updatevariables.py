
import datetime
import os
import shutil

class UpdateVariables:
    def __init__(self, branch: str=None):
    # Used to store variables required by the update process
        self.rootDir = self.setRootDir()
        self.codeDir = "NewCode/"
        self.oldCodeDir = "OldCode"
        self.zipDir = "CodeArchive"
        self.zipFileUrl = "https://github.com/hezmondo/Jinn/archive"
        self.githubBranchName = branch
        self.advancedLogging = False

    def getPath(self, directory):
        return os.path.join(rootDir, directory)

    def setRootDir(self):
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
        return str(rootDir)

    def getZipFile(self):
        return "{}.zip".format(self.githubBranchName)


    def getZipFileUrl(self):
        return "{}/{}".format(self.zipFileUrl, self.getZipFile())


    def getZipExtractedDir(self):
        # Rather than use the branch name we are using "Code" to prevent issues for Ben
        # return "NewCode".format(UpdateVariables.githubBranchName)
        codeDir = self.getPath(self.codeDir)
        return codeDir

    def clearExtractedFolder(self):
        # To prevent any mishaps we clear the "NewCode" folder before each extraction
        directory = self.getZipExtractedDir()
        for file in os.listdir(directory):
            filePath = os.path.join(directory, file)
            try:
                if os.path.isfile(filePath):
                    os.unlink(filePath)
                elif os.path.isdir(filePath):
                    shutil.rmtree(filePath)
            except Exception as ex:
                raise ex

    def getOldCodeDirWithDateTime(self):
        # make legal filename cross-platform; don't bother with seconds
        return "{}-{}".format(self.oldCodeDir, datetime.datetime.now().strftime("%Y-%m-%d_%H-%M"))

