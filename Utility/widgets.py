import typing

from PyQt5 import QtWidgets, QtGui, QtCore
from PyQt5.QtWidgets import QSizePolicy, QWidget, QHBoxLayout, QFileDialog

def widgetPropertyChanged(widget: QWidget):
    # Whenever a widget property is changed
    # (widget.setProperty() or something like QLineEdit.setReadOnly()) called to alter a property after initialisation)
    # we have to "alter" widget's stylesheet to cause Qt to refresh for the property change
    # ss = widget.styleSheet()
    # widget.setStyleSheet("/* */" + (ss if ss is not None else ""))
    # widget.setStyleSheet(ss)
    widget.style().unpolish(widget)
    widget.style().polish(widget)

def widgetEvent(widget: QWidget, e: QtCore.QEvent):
    # All of our widgets should call this in a def event() override
    # to allow for dynamic property changes etc.
    if e.type() == QtCore.QEvent.DynamicPropertyChange:
        if isinstance(e, QtCore.QDynamicPropertyChangeEvent):
            name = e.propertyName().data().decode('utf8')
            if name in ["class"]:
                widgetPropertyChanged(widget)
    elif e.type() == QtCore.QEvent.ReadOnlyChange:
        widgetPropertyChanged(widget)


def widgetSetFixedSizePolicy(widget: QWidget):
    widget.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)


class JLabel(QtWidgets.QLabel):
    def setFixedSizePolicy(self):
        widgetSetFixedSizePolicy(self)

    def event(self, e: QtCore.QEvent):
        widgetEvent(self, e)
        return super().event(e)



class JPushButton(QtWidgets.QPushButton):
    def __init__(self, text=None, parent=None):
        super().__init__(text, parent)

    def event(self, e: QtCore.QEvent):
        widgetEvent(self, e)
        return super().event(e)

class JCancelButton(JPushButton):
    """A subclassed button to allow different attributes such as colour to be set in stylesheet"""
    def __init__(self, text=None, parent=None):
        super().__init__(text, parent)

class JLineEdit(QtWidgets.QLineEdit):
    def setText(self, text: str):
        # Qt places the text cursor at the *end* of line edits
        # When the line is wider than than the widget this means that user sees it as right-scrolled
        # Under Windows at least the convention in other (non-Qt) apps seems to be to show it left-scrolled
        # and that is what we prefer
        # so here we set the cursor at the start so it's always left-scrolled if the length happens to exceed the width
        # I don't think this will cause any problems anywhere, but keep an eye out...
        super().setText(text)
        self.setCursorPosition(0)

    def setFixedSizePolicy(self):
        widgetSetFixedSizePolicy(self)

    def event(self, e: QtCore.QEvent):
        widgetEvent(self, e)
        return super().event(e)

class LabelledWidget(QtWidgets.QWidget):
    def __init__(self, labelText: str=None, valueWidget: QtWidgets.QWidget=None, parent=None):
        super().__init__(parent)

        if not labelText:
            labelText = "Generic text"
        self.label = JLabel(labelText, self)

        self.valueWidget = valueWidget

        self.horLayout = QtWidgets.QHBoxLayout(self)
        self.horLayout.setContentsMargins(10, 0, 10, 0)
        self.horLayout.addWidget(self.label, 1)
        self.horLayout.addWidget(self.valueWidget, 6)

    def setFixedSizePolicy(self):
        widgetSetFixedSizePolicy(self)

class JComboBox(QtWidgets.QComboBox):
    # class variable for a new "popupAboutToBeShown" signal
    # Qt does not emit a signal when the dropdown/popup of a combobox is about to be shown
    # we add this signal, which can be used for e.g. dynamically populating the items
    popupAboutToBeShown = QtCore.pyqtSignal(name='popupAboutToBeShown')

    def __init__(self, parent=None):
        super().__init__(parent)

    def setFixedSizePolicy(self):
        widgetSetFixedSizePolicy(self)

    def showPopup(self):
        # emit the new signal
        # Note: as per https://forum.qt.io/topic/93063/qcombobox-showpopup-override-timing-problem
        # this only works correctly provided the (synchronously-executed) slot
        # only takes a "short" amount of time to execute
        # (e.g. in my tests 100 milliseconds was OK, but 500 milliseconds was too long)
        # if it takes too long the list is populated but the popup does not get shown
        # so use with caution
        self.popupAboutToBeShown.emit()

        # we like the popup to always show the full contents
        # we only need to do work for this when the combo has had a maximum width specified
        maxWidth = self.maximumWidth()
        # see https://doc.qt.io/qt-5/qwidget.html#maximumWidth-prop for the 16777215 value
        if (maxWidth and maxWidth < 16777215) or self.sizeAdjustPolicy() == JComboBox.AdjustToMinimumContentsLength:
            self.setPopupMinimumWidthForItems()

        # call the base method now to display the popup
        super().showPopup()

    def setPopupMinimumWidthForItems(self):
        # we like the popup to always show the full contents
        # under Linux/GNOME popups always do this
        # but under Windows they get truncated/ellipsised
        # here we calculate the maximum width among the items
        # and set QComboBox.view() to accomodate this
        # which makes items show full width under Windows
        view = self.view()
        fm = self.fontMetrics()
        maxWidth = max([fm.width(self.itemText(i)) for i in range(self.count())])
        if maxWidth:
            view.setMinimumWidth(maxWidth)

    def event(self, e: QtCore.QEvent):
        widgetEvent(self, e)
        return super().event(e)

    def setCurrentText(self, text: str):
        super().setCurrentText(text)
        if self.isEditable():
            # On an editable combobox, QComboBox.setCurrentText() sets *only* the editable text
            # We like it so it also selects any corresponding list item
            index = self.findText(text)
            if index >= 0:
                self.setCurrentIndex(index)

    def setCurrentData(self, data: typing.Any):
        index = self.findData(data)
        self.setCurrentIndex(index)

class LabelledComboBox(LabelledWidget):
    def __init__(self, labelText: str=None, parent=None, editable=False, readOnly=False):
        self.cb = JComboBox()
        super().__init__(labelText, self.cb, parent)

        self.horLayout.setAlignment(self.valueWidget, QtCore.Qt.AlignLeft)
        self.cb.setFixedSizePolicy()
        if editable:
            self.cb.setEditable(True)
        if readOnly:
            self.cb.setEnabled(False)

    def setText(self, text):
        self.cb.setCurrentText(text)

    def text(self):
        return self.cb.currentText()



class JTextEdit(QtWidgets.QTextEdit):
    def event(self, e: QtCore.QEvent):
        widgetEvent(self, e)
        return super().event(e)

    def setHeightFromContent(self):
        # See https://forum.qt.io/topic/96392/qtextedit-minimal-height-but-expanding-problem
        # size = self.document().size().toSize()
        # self.setFixedHeight(size.height())
        font = self.document().defaultFont()
        fontMetrics = QtGui.QFontMetrics(font)
        textSize = fontMetrics.size(0, self.toPlainText())
        textHeight = textSize.height() + 40  # Need to tweak
        self.setFixedHeight(textHeight)

class JProgressBar(QtWidgets.QProgressBar):
    def event(self, e: QtCore.QEvent):
        widgetEvent(self, e)
        return super().event(e)

class LabelledProgressBar(LabelledWidget):
    def __init__(self, labelText: str=None, parent=None):
        self.pb = JProgressBar()
        super().__init__(labelText, self.pb, parent)

class DirectorySelector(QWidget):
    def __init__(self, parent: typing.Optional[QWidget] = None, caption: str = None, directory: str = None):
        super().__init__(parent)

        self.caption = caption if caption else "Select directory"
        self.directory = directory

        self.layout = QHBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)

        self.btnSelectDir = JPushButton(self.caption, self)
        self.btnSelectDir.clicked.connect(self.selectDirectory)
        self.leDirname = JLineEdit("", self)
        self.layout.addWidget(self.btnSelectDir)
        self.layout.addWidget(self.leDirname)

    def selectDirectory(self):
        dirname = fileDialogGetExistingDirectory(self, self.caption, self.directory)
        self.leDirname.setText(dirname)

def fileDialogGetExistingDirectory(parent: typing.Optional[QWidget] = None, caption: str = None,
                                   directory: str = None
                                   ) -> str:
    # Replacement (sort of) for QFileDialog.getExistingDirectory()
    if not caption:
        caption = "Choose directory"
    fileDialog = QFileDialog(parent, caption, directory)
    # directory only
    fileDialog.setFileMode(QFileDialog.DirectoryOnly)
    # just list mode is quite sufficient for choosing a diectory
    fileDialog.setViewMode(QFileDialog.List)
    # only want to to show directories
    fileDialog.setOption(QFileDialog.ShowDirsOnly)
    # native dialog, at least under Ubuntu GNOME is a bit naff for choosing a directory
    # (shows files but greyed out), so going for Qt's own cross-plaform chooser
    fileDialog.setOption(QFileDialog.DontUseNativeDialog)
    # get rid of (or at least grey out) file-types selector
    fileDialog.setOption(QFileDialog.HideNameFilterDetails)
    # DontResolveSymlinks seemingly recommended by http://doc.qt.io/qt-5/qfiledialog.html#getExistingDirectory
    # but I found it didn't make any difference (symlinks resolved anyway)
    # fileDialog.setOption(QtWidgets.QFileDialog.DontResolveSymlinks)
    if not fileDialog.exec():
        return ""
    return fileDialog.selectedFiles()[0]





