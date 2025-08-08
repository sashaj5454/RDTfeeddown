from qtpy.QtCore import QEvent, QObject
from qtpy.QtWidgets import QApplication

import rdtfeeddown.resources_rc  # noqa: F401 - needed for resource loading

from rdtfeeddown.gui import RDTFeeddownGUI
from rdtfeeddown.style import dark_stylesheet


class CursorResetFilter(QObject):
    def eventFilter(self, obj, event):  # noqa: N802
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
    except (ImportError, RuntimeError) as e:
        print(f"Error starting the GUI: {e}")
        exit(1)
