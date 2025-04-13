from .gui import RDTFeeddownGUI
from qtpy.QtWidgets import QApplication

if __name__ == "__main__":
    try:
        app = QApplication([])
        window = RDTFeeddownGUI()
        window.show()
        app.exec_()
    except Exception as e:
        print(f"Error starting the GUI: {e}")
        exit(1)