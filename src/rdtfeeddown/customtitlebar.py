from .style import recolor_icon, minimize_stylesheet, maximize_stylesheet, close_stylesheet
from qtpy.QtWidgets import QWidget, QHBoxLayout, QToolButton, QLabel, QMessageBox, QStyle, QDialog, QVBoxLayout, QTextEdit, QPushButton
from qtpy.QtCore import Qt, QSize

def create_custom_title_bar(parent):
	# Create a custom title bar widget
	title_bar = QWidget()
	title_bar_layout = QHBoxLayout()
	title_bar_layout.setContentsMargins(0, 0, 0, 0)

	# Add the help button
	help_button = QToolButton()
	help_button.setObjectName("helpButton")  # Set a unique object name
	help_button.setIcon(parent.style().standardIcon(QStyle.SP_MessageBoxQuestion))
	help_button.setToolTip("Click for Help")
	help_button.clicked.connect(lambda: show_help(parent))
	title_bar_layout.addWidget(help_button)

	error_log_button = QToolButton()
	error_log_button.setObjectName("errorLogButton")  # Set a unique object name
	error_log_button.setIcon(parent.style().standardIcon(QStyle.SP_FileDialogDetailedView))
	error_log_button.setToolTip("Click to view error log")
	error_log_button.clicked.connect(lambda:show_error_log_window(parent))
	title_bar_layout.addWidget(error_log_button)

	title_bar_layout.addStretch()

	# Add the title text
	title_label = QLabel("RDT Feeddown Analysis")
	title_label.setStyleSheet("color: white; font-weight: bold;")
	title_bar_layout.addWidget(title_label)

	title_bar_layout.addStretch()

	# Add minimize button
	minimize_button = QToolButton()
	minimize_button.setObjectName("minimizeButton")  # Set a unique object name
	style = parent.style().standardIcon(QStyle.SP_TitleBarMinButton)
	cust_style = recolor_icon(style, "white",QSize(30,30))
	minimize_button.setIcon(cust_style)
	minimize_button.setToolTip("Minimize")
	minimize_button.clicked.connect(lambda: parent.showMinimized())
	minimize_button.setStyleSheet(minimize_stylesheet)
	title_bar_layout.addWidget(minimize_button)

	# Add maximize/restore button
	parent.maximize_button = QToolButton()
	parent.maximize_button.setObjectName("maximizeButton")  # Set a unique object name
	style2 = parent.style().standardIcon(QStyle.SP_TitleBarMaxButton)
	cust_style2 = recolor_icon(style2, "white")
	parent.maximize_button.setIcon(cust_style2)
	parent.maximize_button.clicked.connect(lambda: toggle_maximize_restore(parent))
	parent.maximize_button.setToolTip("Maximize/Restore")
	parent.maximize_button.setStyleSheet(maximize_stylesheet)
	title_bar_layout.addWidget(parent.maximize_button)

	# Add close button
	close_button = QToolButton()
	close_button.setObjectName("closeButton")  # Set a unique object name
	style3 = parent.style().standardIcon(QStyle.SP_TitleBarCloseButton)
	cust_style3 = recolor_icon(style3, "white", QSize(30,30))
	close_button.setIcon(cust_style3)
	close_button.setToolTip("Close")
	close_button.clicked.connect(parent.close)
	close_button.setStyleSheet(close_stylesheet)
	title_bar_layout.addWidget(close_button)

	# Set the layout for the title bar
	title_bar.setLayout(title_bar_layout)
	title_bar.setStyleSheet("background-color: #2e2e2e;")
	parent.central_widget.mousePressEvent = lambda event: mousePressEvent(parent, event)
	parent.central_widget.mouseMoveEvent = lambda event: mouseMoveEvent(parent, event)
	parent.central_widget.mouseReleaseEvent = lambda event: mouseReleaseEvent(parent, event)

	return title_bar

def show_help(parent):
	help_text = """
<html>
<body>
<p><b>RDT Feeddown Analysis Help:</b></p>
<ul style="padding-left: 0;">
<li style="margin-bottom: 1em;">To change the default input/output paths before launching, create a file called "defaults.json" in the cwd, formatted as follows:.</li>
<div style="background-color: #252526; font-family: monospace; padding: 10px; border-radius: 5px;">
	<pre>
<span style="color: #9cdcfe;">{</span>
<span style="color: #ce9178;">"default_input_path"</span>: <span style="color: #dcdCAA;">"[insert input path here]"</span>,
<span style="color: #ce9178;">"default_output_path"</span>: <span style="color: #dcdCAA;">"[insert output path here]"</span>
<span style="color: #9cdcfe;">}</span>
	</pre>
</div>
<li style="margin-bottom: 1em;">To create a <span style="font-weight: bold;">properties file</span> (i.e. if in simulation mode in the <span style="font-weight: bold;">Input tab</span> since no Timber data) it must be saved in <span style="font-weight: bold;">.csv format</span>, set out as shown below:</li>
<div style="background-color: #252526; font-family: monospace; padding: 10px; border-radius: 5px;">
<pre>
<span style="color:#569cd6">MATCH,</span> <span style="color:#dcdcaa">KNOB</span>
<span style="color:#569cd6">[insert regex string corresponding to chosen folder paths],</span> <span style="color:#dcdcaa">[insert XING knob value]</span>
</pre>
</div>
</ul>
<hr>
<p><b>Plot Shortcuts:</b></p>
<table style="width:100%; border-collapse:collapse; font-family: monospace; font-size:90%; margin-bottom:20px;">
  <tr>
    <td style="width:35%; vertical-align:top;">
      <span style="display:inline-block; padding:4px 8px; background-color:#444; color:#ddd; border:1px solid #666; border-radius:4px; margin-right:4px;">
        Ctrl</span> 
		+ 
      <span style="display:inline-block; padding:4px 8px; background-color:#444; color:#ddd; border:1px solid #666; border-radius:4px; margin-left:4px;">
        Left Click</span>
    </td>
    <td style="vertical-align:top;">Drag to pan the plot</td>
  </tr>
  <tr>
    <td style="vertical-align:top;">
      <span style="display:inline-block; padding:4px 8px; background-color:#444; color:#ddd; border:1px solid #666; border-radius:4px;">
        Right Click
      </span>
    </td>
    <td style="vertical-align:top;">Auto-scale a plot</td>
  </tr>
</table>

<li style="margin-bottom: 1em;">Use the <span style="font-weight: bold;">Input</span> tab to input results of crossing angle scans either from simulation or measurement.</li>
<li style="margin-bottom: 1em;">Use the <span style="font-weight: bold;">Validation</span> tab to see results of analysis on file selections and to to view BPM, RDT, and RDT shift plots.</li>
<li style="margin-bottom: 1em;">Use the <span style="font-weight: bold;">Graph</span> sub-tab of the <span style="font-weight: bold;">Correction</span> tab use output of the response tab to match with analysis of measurement.</li>
<li style="margin-bottom: 1em;">Use the <span style="font-weight: bold;">Response (optional)</span> sub-tab of the <span style="font-weight: bold;">Correction</span> tab to quantify RDT response caused by changing XING angle for a specific corrector - this can either be simulation or measurement result.</li>
</ul>
</body>
</html>
	"""
	QMessageBox.information(parent, "Help", help_text)

def show_error_log_window(self):
        """
        Open a pop-up window displaying all logged error messages.
        """
        dialog = QDialog(self)
        dialog.setWindowTitle("Error Log")
        layout = QVBoxLayout()
        text_edit = QTextEdit()
        text_edit.setReadOnly(True)
        text_edit.setHtml("<br><br>".join(self.error_log))
        layout.addWidget(text_edit)
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(dialog.accept)
        layout.addWidget(close_btn)
        dialog.setLayout(layout)
        dialog.exec_()

def mousePressEvent(parent, event):
	if event.button() == Qt.LeftButton:
		# Convert global position to the widget's local coordinate system
		local_pos = parent.mapFromGlobal(event.globalPos())
		if isNearEdge(parent, local_pos):
			parent._resizing = True
			parent._resize_start_pos = event.globalPos()  # keep global for delta calculations
			parent._resize_start_geom = parent.geometry()
			parent._resize_direction = getResizeDirection(parent, local_pos)
		else:
			parent.drag_position = event.globalPos() - parent.frameGeometry().topLeft()
		event.accept()

def mouseMoveEvent(parent, event):
	if parent._resizing:
		handleResize(parent, event.globalPos())
		event.accept()
	elif event.buttons() == Qt.LeftButton:
		if hasattr(parent, "drag_position"):
			parent.move(event.globalPos() - parent.drag_position)
		event.accept()
	else:
		# Convert the global position to local coordinates
		local_pos = parent.mapFromGlobal(event.globalPos())
		direction = getResizeDirection(parent, local_pos)
		if direction in ['left', 'right']:
			parent.setCursor(Qt.SizeHorCursor)
		elif direction in ['top', 'bottom']:
			parent.setCursor(Qt.SizeVerCursor)
		elif direction in ['top-left', 'bottom-right']:
			parent.setCursor(Qt.SizeFDiagCursor)
		elif direction in ['top-right', 'bottom-left']:
			parent.setCursor(Qt.SizeBDiagCursor)
		else:
			parent.setCursor(Qt.ArrowCursor)

def mouseReleaseEvent(parent, event):
	parent._resizing = False
	parent._resize_direction = None
	parent.setCursor(Qt.ArrowCursor)

def isNearEdge(parent, pos):
	rect = parent.rect()
	margin = parent._resize_margin
	return (
		pos.x() < margin or pos.x() > rect.width() - margin or
		pos.y() < margin or pos.y() > rect.height() - margin
	)

def getResizeDirection(parent, pos):
	rect = parent.rect()
	margin = parent._resize_margin
	left = pos.x() < margin
	right = pos.x() > rect.width() - margin
	top = pos.y() < margin
	bottom = pos.y() > rect.height() - margin

	if top and left:
		return 'top-left'
	elif top and right:
		return 'top-right'
	elif bottom and left:
		return 'bottom-left'
	elif bottom and right:
		return 'bottom-right'
	elif left:
		return 'left'
	elif right:
		return 'right'
	elif top:
		return 'top'
	elif bottom:
		return 'bottom'
	return None

def handleResize(parent, global_pos):
	if not parent._resize_direction:
		return
	delta = global_pos - parent._resize_start_pos
	geom = parent._resize_start_geom
	dir = parent._resize_direction

	if dir == 'right':
		new_width = max(geom.width() + delta.x(), parent.minimumWidth())
		parent.setGeometry(geom.x(), geom.y(), new_width, geom.height())
	elif dir == 'bottom':
		new_height = max(geom.height() + delta.y(), parent.minimumHeight())
		parent.setGeometry(geom.x(), geom.y(), geom.width(), new_height)
	elif dir == 'left':
		new_x = geom.x() + delta.x()
		new_width = max(geom.width() - delta.x(), parent.minimumWidth())
		parent.setGeometry(new_x, geom.y(), new_width, geom.height())
	elif dir == 'top':
		new_y = geom.y() + delta.y()
		new_height = max(geom.height() - delta.y(), parent.minimumHeight())
		parent.setGeometry(geom.x(), new_y, geom.width(), new_height)
	elif dir == 'top-left':
		new_x = geom.x() + delta.x()
		new_y = geom.y() + delta.y()
		new_width = max(geom.width() - delta.x(), parent.minimumWidth())
		new_height = max(geom.height() - delta.y(), parent.minimumHeight())
		parent.setGeometry(new_x, new_y, new_width, new_height)
	elif dir == 'top-right':
		new_y = geom.y() + delta.y()
		new_width = max(geom.width() + delta.x(), parent.minimumWidth())
		new_height = max(geom.height() - delta.y(), parent.minimumHeight())
		parent.setGeometry(geom.x(), new_y, new_width, new_height)
	elif dir == 'bottom-left':
		new_x = geom.x() + delta.x()
		new_width = max(geom.width() - delta.x(), parent.minimumWidth())
		new_height = max(geom.height() + delta.y(), parent.minimumHeight())
		parent.setGeometry(new_x, geom.y(), new_width, new_height)
	elif dir == 'bottom-right':
		new_width = max(geom.width() + delta.x(), parent.minimumWidth())
		new_height = max(geom.height() + delta.y(), parent.minimumHeight())
		parent.setGeometry(geom.x(), geom.y(), new_width, new_height)

def toggle_maximize_restore(parent):
	style = parent.style().standardIcon(QStyle.SP_TitleBarMaxButton)
	cust_style = recolor_icon(style, "white")
	style2 = parent.style().standardIcon(QStyle.SP_TitleBarNormalButton)
	cust_style2 = recolor_icon(style2, "white", QSize(30,30))
	if parent.isMaximized():
		parent.showNormal()
		parent.maximize_button.setIcon(cust_style)
	else:
		parent.showMaximized()
		parent.maximize_button.setIcon(cust_style2)

def eventFilter(parent, obj, event):
	# If you receive a MouseMove even from a child, call the mouseMoveEvent method.
	if event.type() == event.MouseMove:
		parent.mouseMoveEvent(event)
	return super().eventFilter(obj, event)

def install_event_filters(parent, widget):
	widget.installEventFilter(parent)
	for child in widget.findChildren(QWidget):
		child.installEventFilter(parent)

def enable_mouse_tracking(parent, widget):
	widget.setMouseTracking(True)
	for child in widget.findChildren(QWidget):
		child.setMouseTracking(True)