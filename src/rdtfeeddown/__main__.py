from .gui import RDTFeeddownGUI
from qtpy.QtWidgets import QApplication
from qtpy.QtCore import QObject, QEvent
from .style import dark_stylesheet
import rdtfeeddown.resources_rc

class CursorResetFilter(QObject):
    def eventFilter(self, obj, event):
        if event.type() == QEvent.MouseButtonRelease:
            # Always restore override cursor on any mouse release
            while QApplication.overrideCursor() is not None:
                QApplication.restoreOverrideCursor()
        return False
    
if __name__ == "__main__":
    try:
        app = QApplication([])
        cursor_filter = CursorResetFilter()
        app.installEventFilter(cursor_filter)
        app.setStyleSheet(dark_stylesheet)
        window = RDTFeeddownGUI()
        window.show()
        app.exec_()
    except Exception as e:
        print(f"Error starting the GUI: {e}")
        exit(1)