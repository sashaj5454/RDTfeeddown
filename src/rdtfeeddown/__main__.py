from .gui import RDTFeeddownGUI
from PyQt5.QtCore import qRegisterMetaType
from PyQt5.QtGui import QTextCursor
from PyQt5.QtWidgets import QApplication

if __name__ == "__main__":
    app = QApplication([])
    qRegisterMetaType(QTextCursor, "QTextCursor")
    window = RDTFeeddownGUI()
    window.show()
    app.exec_()