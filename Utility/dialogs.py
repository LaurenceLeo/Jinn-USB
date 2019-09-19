from PyQt5 import QtCore, QtGui
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QVBoxLayout, QDialog, QSizePolicy

from widgets import JLabel, JTextEdit, JPushButton




class JDialog(QDialog):
    """Simply a QDialog to use in Jinn which we can add attributes/methods to if needed"""
    """ *** ALL JINN DIALOGS SHOULD INHERIT FROM THIS INSTEAD OF FROM QDialog *** """

    _ignoreReturnKey = False

    def __init__(self, parent=None, dialog=None):
        super().__init__(parent)


        self.initaliseWindowIcon(dialog)
        # To avoid possible memory leaks, we make the default be to auto-delete dialogs on close.
        # See https://github.com/hezmondo/Jinn/issues/76
        # If we find this must not be done on some dialog
        # (e.g. we want to access its content after the user has closed it?)
        # the caller will need to go JDialog.setAttribute(QtCore.Qt.WA_DeleteOnClose, False) after creation
        # and will need to call JDialog.deleteLater() after retrieving any information from the (closed) dialog
        # (see class DelayedDeleteOnClose below, code can use: "with JDialog.delayedDeleteOnClose():")
        # I have gone through code and gotten rid of some occurences where references were not being released
        # to allow Python garbage collection to proceed
        # but not all (e.g. infamous dialog.widget.connect(lambda: func(self)),
        # see my https://forum.qt.io/topic/92825/python-pyqt-qdialog-with-connect-lambda-leaks)
        # so the next line still deals with those remaining
        self.setDeleteOnClose(True)

        # None of our dialogs support Windows context help "?" button
        # (next line shows a PyCharm "type" error --- can't be helped)
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowContextHelpButtonHint)

        # Default is to allow Return/Enter key on dialog
        self._ignoreReturnKey = False

    def initaliseWindowIcon(self, dialog):
        if dialog == "Updater":
            self.setWindowIcon(QtGui.QIcon('GUI\jinnup.ico'))
        elif dialog == "Downloader":
            self.setWindowIcon(QtGui.QIcon('GUI\jinndl.ico'))
        else:
            self.setWindowIcon(QtGui.QIcon('GUI\jinn.ico'))

    class DelayedDeleteOnClose:
        # Helper class to neatly support temporarily clearing the default JDialog.setDeleteOnClose(True)
        # and instead doing a JDialog.deleteLater() at the end
        # This helper class allows you to simply write:
        #     dlg = JDialog()
        #     with DelayedDeleteOnClose(dlg):
        #         dlg.exec()
        #         something = dlg.getValues()
        # instead of having to type in "try: ... finally: ..."
        # as per https://www.python.org/dev/peps/pep-0343/

        def __init__(self, dlg: 'JDialog'):
            self.dlg = dlg

        def __enter__(self):
            # Clear the Qt.WA_DeleteOnClose attribute...
            self.dlg.setDeleteOnClose(False)

        def __exit__(self, type, value, tb):
            # ...and instead destroy it now explicitly at end of block
            self.dlg.destroy()

    def delayedDeleteOnClose(self):
        # Convenince method to allow outside world to go:
        #     dlg = JDialog()
        #     with dlg.delayedDeleteOnClose():
        #         dlg.exec()
        #         something = dlg.getValues()
        return self.DelayedDeleteOnClose(self)

    def setDeleteOnClose(self, delete: bool):
        # Set the "auto-delete QDialog on closing it" attribute
        self.setAttribute(QtCore.Qt.WA_DeleteOnClose, delete)

    def setIgnoreReturnKey(self, ignore: bool=True):
        # Set to ignore/accept Return/Enter key
        self._ignoreReturnKey = ignore

    def keyPressEvent(self, event: QtGui.QKeyEvent):
        # see whether this dialog ignores Return/Enter key
        if self._ignoreReturnKey:
            if event.key() in (QtCore.Qt.Key_Return, QtCore.Qt.Key_Enter):
                return
        # pass to base handler
        super().keyPressEvent(event)

    def setInitialSize(self, width: int=0, height: int=0):
        # convenience method for calling QDialog.resize()
        # defined so we can pick up where a dialog has an initial size
        # if width or height == -1 preserve current width/height, so you can change just one of them
        if width == 0:
            width = self.width()
        if height == 0:
            height = self.height()
        self.resize(width, height)

class JMessageBox(JDialog):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.setInitialSize(500, 200)

        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(20, 20, 20, 20)
        self.layout.setSpacing(15)

        self.text = JLabel("Default text", self)
        self.text.setProperty("class", "fontSizeBigger")
        self.informativeText = JTextEdit("", self)
        self.informativeText.setProperty("class", "backgroundColorTransparent")
        self.informativeText.setReadOnly(True)
        self.informativeText.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.MinimumExpanding)
        self.informativeText.hide()
        self.btnOK = JPushButton("Ok", self)
        self.btnOK.setObjectName("btnOK")

        self.text.setAlignment(QtCore.Qt.AlignHCenter)
        self.informativeText.setAlignment(QtCore.Qt.AlignHCenter)

        self.layout.addWidget(self.text)
        self.layout.addWidget(self.informativeText)
        self.layout.addWidget(self.btnOK)

        self.layout.setAlignment(self.btnOK, QtCore.Qt.AlignHCenter)

        self.btnOK.clicked.connect(self.accept)

    def setText(self, message):
        self.text.setText(message)

    def resizeForInformativeText(self):
        length = len(self.informativeText.toPlainText())
        if length > 500:
            self.setInitialSize(800, 600)
        elif length > 100:
            self.setInitialSize(650, 400)
        elif length > 50:
            self.setInitialSize(500, 300)
        else:
            self.setInitialSize(500, 200)

    def setInformativeText(self, message: str):
        self.informativeText.show()
        self.informativeText.setText(message)
        self.resizeForInformativeText()


class InfoMsgBox(JMessageBox):
    def __init__(self, text=None, infotext=None, title=None, parent=None):
        super().__init__(parent)

        if text:
            self.setText(text)
        if infotext:
            self.setInformativeText(infotext)
        if title:
            self.setWindowTitle(title)

