import tkinter as tk
from .gui import RDTFeeddownGUI
from PyQt5.QtWidgets import QApplication

if __name__ == "__main__":
    app = QApplication([])
    window = RDTFeeddownGUI()
    window.show()
    app.exec_()