from qtpy.QtGui import QIcon, QPixmap, QPainter, QColor
from qtpy.QtCore import QSize, Qt
DARK_BACKGROUND_COLOR = "#2e2e2e"
plot_colour = "#5C62D6"
run_colour = "green"
remove_colour = "#710C04"
b1_colour = "#0066cc"
b2_colour = "#B90E0A"


dark_stylesheet = f"""
QWidget {{ 
    background-color: {DARK_BACKGROUND_COLOR}; 
    color: #ffffff; 
}}
QPushButton {{ 
    background-color: #3c3c3c; 
    color: #ffffff; 
    border: white;
    padding: 5px;
}}
QPushButton:hover {{ 
    background-color: #484848; 
}}
QLineEdit, QComboBox, QTreeWidget, QListWidget {{
    background-color: #3c3c3c;
    color: #ffffff;
    border: 1px solid #555555;
}}
QGroupBox {{
    border: 1px solid #555555;
    margin-top: 10px;
}}
QGroupBox::title {{
    subcontrol-origin: margin;
    subcontrol-position: top center;
    padding: 0 3px;
}}
QTabWidget::pane {{ 
    border: 1px solid #555555;
}}
QTabBar::tab {{ 
    background: #3c3c3c;
    color: #ffffff;
    padding: 5px;
}}
QTabBar::tab:selected {{ 
    background: #484848; 
}}
QCheckBox::indicator {{
    width: 13px;
    height: 13px;
    border: 1px solid white;
    background-color: #3c3c3c;
}}
QCheckBox::indicator:checked {{
    image: url(:/icons/Images/tick.png);
}}
QToolTip {{
    color: white;
    background-color: #2e2e2e;
    border: 1px solid white;
}}
"""

def recolor_icon(icon, color, size=QSize(28, 28)):
    # Get a pixmap from the icon (using its actual size)
    pixmap = icon.pixmap(icon.actualSize(size))
    
    # Create a new pixmap with a transparent background
    new_pixmap = QPixmap(pixmap.size())
    new_pixmap.fill(Qt.transparent)
    
    # Set up a QPainter to recolor the pixmap
    painter = QPainter(new_pixmap)
    # Draw the original pixmap
    painter.drawPixmap(0, 0, pixmap)
    
    # Set composition mode to tint the pixmap
    painter.setCompositionMode(QPainter.CompositionMode_SourceIn)
    painter.fillRect(new_pixmap.rect(), QColor(color))
    painter.end()
    
    return QIcon(new_pixmap)

minimize_stylesheet = f"""
#minimizeButton {{
			background-color: #3c3c3c;
			color: white;
			border: none;
			padding: 5px;
			border-radius: 3px;
		}}
#minimizeButton:hover {{
    background-color: #484848;
}}
"""

maximize_stylesheet = f"""
#maximizeButton {{
            background-color: #3c3c3c;
            color: white;
            border: none;
            padding: 5px;
            border-radius: 3px;
        }}  
#maximizeButton:hover {{
    background-color: #484848;
}}
"""

close_stylesheet = f"""
#closeButton {{
            background-color: #3c3c3c;
            color: white;
            border: none;
            padding: 5px;
            border-radius: 3px;
        }}
#closeButton:hover {{
    background-color: #484848;
}}
"""

plot_stylesheet = f"""
QPushButton {{
    background-color: {plot_colour};
    color: white;
}}
QPushButton:hover {{
    background-color: #7E85E0;  /* paler variant of plot_colour */
}}
"""

run_stylesheet = f"""
QPushButton {{
    background-color: {run_colour};
    color: white;
}}
QPushButton:hover {{
    background-color: #66ff66;  /* paler variant of run_colour */
}}
"""

remove_stylesheet = f"""
QPushButton {{
    background-color: {remove_colour};
    color: white;
}}
QPushButton:hover {{
    background-color: #a05252;  /* paler variant of remove_colour */
}}
"""

b1_stylesheet = f"""
QLabel {{
    background-color: {b1_colour};
    color: white;
}}
"""

b2_stylesheet = f"""
QLabel {{
    background-color: {b2_colour};
    color: white;
}}
"""