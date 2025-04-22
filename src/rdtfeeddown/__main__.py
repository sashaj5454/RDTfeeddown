from .gui import RDTFeeddownGUI
from qtpy.QtWidgets import QApplication
from .config import dark_stylesheet
import rdtfeeddown.resources_rc


if __name__ == "__main__":
    try:
        app = QApplication([])
        app.setStyleSheet(dark_stylesheet)
        window = RDTFeeddownGUI()
        window.show()
        app.exec_()
    except Exception as e:
        print(f"Error starting the GUI: {e}")
        exit(1)