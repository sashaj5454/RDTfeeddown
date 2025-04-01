import os
import json
import csv
from PyQt5.QtWidgets import (
	QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton,
	QFileDialog, QListWidget, QTabWidget, QWidget, QTextEdit, QMessageBox
)
from PyQt5 import QtWidgets
from PyQt5.QtCore import Qt, pyqtSignal, QTimer  # Import Qt for the correct constants and QTimer
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from .utils import load_defaults, check_rdt, initialize_statetracker, rdt_to_order_and_type, getmodelBPMs
from .analysis import write_RDTshifts, getrdt_omc3, fit_BPM, save_RDTdata, load_RDTdata
from .plotting import plot_BPM  # Assuming you have a plotting module for BPM plotting
import time  # Import time to get the current timestamp
import re    # Import re for regex substitution

class RDTFeeddownGUI(QMainWindow):
	def __init__(self):
		super().__init__()
		self.setWindowTitle("RDT Feeddown Analysis")

		# Load defaults from the special file
		config = load_defaults(self.log_error)
		self.default_input_path = config.get("default_input_path")
		self.default_output_path = config.get("default_output_path")

		# Add an attribute to store the list of analysis output files
		self.analysis_output_files = []

		# Main layout
		self.central_widget = QWidget()
		self.setCentralWidget(self.central_widget)
		self.layout = QVBoxLayout(self.central_widget)

		# Tabs
		self.tabs = QTabWidget()
		self.layout.addWidget(self.tabs)

		# ===== Input Tab with separated sections =====
		self.input_tab = QWidget()
		self.tabs.addTab(self.input_tab, "Input")
		self.input_layout = QVBoxLayout(self.input_tab)

		# --- Paths Group ---
		paths_group = QtWidgets.QGroupBox("Paths")
		paths_layout = QVBoxLayout()
		self.input_path_label = QLabel(f"Default Input Path: {self.default_input_path}")
		paths_layout.addWidget(self.input_path_label)
		self.change_input_path_button = QPushButton("Change Input Path")
		self.change_input_path_button.clicked.connect(self.change_default_input_path)
		paths_layout.addWidget(self.change_input_path_button)
		self.output_path_label = QLabel(f"Default Output Path: {self.default_output_path}")
		paths_layout.addWidget(self.output_path_label)
		self.change_output_path_button = QPushButton("Change Output Path")
		self.change_output_path_button.clicked.connect(self.change_default_output_path)
		paths_layout.addWidget(self.change_output_path_button)
		paths_group.setLayout(paths_layout)
		self.input_layout.addWidget(paths_group)

		# --- Beam Models Group ---
		beam_model_group = QtWidgets.QGroupBox("Beam Model Selection")
		beam_model_layout = QHBoxLayout()
		# Beam 1
		beam1_layout = QVBoxLayout()
		self.beam1_model_label = QLabel("Beam 1 Model:")
		self.beam1_model_label.setStyleSheet("color: blue;")
		beam1_layout.addWidget(self.beam1_model_label)
		self.beam1_model_entry = QLineEdit()
		beam1_layout.addWidget(self.beam1_model_entry)
		self.beam1_model_button = QPushButton("Select Model")
		self.beam1_model_button.clicked.connect(self.select_beam1_model)
		beam1_layout.addWidget(self.beam1_model_button)
		beam_model_layout.addLayout(beam1_layout)
		# Beam 2
		beam2_layout = QVBoxLayout()
		self.beam2_model_label = QLabel("Beam 2 Model:")
		self.beam2_model_label.setStyleSheet("color: red;")
		beam2_layout.addWidget(self.beam2_model_label)
		self.beam2_model_entry = QLineEdit()
		beam2_layout.addWidget(self.beam2_model_entry)
		self.beam2_model_button = QPushButton("Select Model")
		self.beam2_model_button.clicked.connect(self.select_beam2_model)
		beam2_layout.addWidget(self.beam2_model_button)
		beam_model_layout.addLayout(beam2_layout)
		beam_model_group.setLayout(beam_model_layout)
		self.input_layout.addWidget(beam_model_group)

		# --- Folders Group ---
		folders_group = QtWidgets.QGroupBox("Reference and Measurement Folders")
		folders_layout = QVBoxLayout()

		# Replace the individual reference folder groups with a combined horizontal group:
		ref_folders_group = QtWidgets.QGroupBox("Reference Folders")
		ref_folders_layout = QHBoxLayout()

		# Beam 1 Reference Folder (vertical layout)
		beam1_ref_layout = QVBoxLayout()
		self.beam1_reffolder_label = QLabel("Beam 1 Reference Folder:")
		self.beam1_reffolder_label.setStyleSheet("color: blue;")
		beam1_ref_layout.addWidget(self.beam1_reffolder_label)
		self.beam1_reffolder_entry = QLineEdit()
		beam1_ref_layout.addWidget(self.beam1_reffolder_entry)
		beam1_buttons_layout = QHBoxLayout()
		self.beam1_reffolder_button = QPushButton("Select Folder")
		self.beam1_reffolder_button.clicked.connect(self.select_beam1_reffolder)
		beam1_buttons_layout.addWidget(self.beam1_reffolder_button)
		self.beam1_reffolder_remove_button = QPushButton("Remove File")
		self.beam1_reffolder_remove_button.clicked.connect(self.remove_beam1_reffolder)
		beam1_buttons_layout.addWidget(self.beam1_reffolder_remove_button)
		beam1_ref_layout.addLayout(beam1_buttons_layout)
		ref_folders_layout.addLayout(beam1_ref_layout)

		# Beam 2 Reference Folder (vertical layout)
		beam2_ref_layout = QVBoxLayout()
		self.beam2_reffolder_label = QLabel("Beam 2 Reference Folder:")
		self.beam2_reffolder_label.setStyleSheet("color: red;")
		beam2_ref_layout.addWidget(self.beam2_reffolder_label)
		self.beam2_reffolder_entry = QLineEdit()
		beam2_ref_layout.addWidget(self.beam2_reffolder_entry)
		beam2_buttons_layout = QHBoxLayout()
		self.beam2_reffolder_button = QPushButton("Select Folder")
		self.beam2_reffolder_button.clicked.connect(self.select_beam2_reffolder)
		beam2_buttons_layout.addWidget(self.beam2_reffolder_button)
		self.beam2_reffolder_remove_button = QPushButton("Remove File")
		self.beam2_reffolder_remove_button.clicked.connect(self.remove_beam2_reffolder)
		beam2_buttons_layout.addWidget(self.beam2_reffolder_remove_button)
		beam2_ref_layout.addLayout(beam2_buttons_layout)
		ref_folders_layout.addLayout(beam2_ref_layout)

		ref_folders_group.setLayout(ref_folders_layout)
		# Insert the new reference folders group at the top of the folders layout.
		folders_layout.insertWidget(0, ref_folders_group)

		# Measurement Folders for Beam 1 and Beam 2
		measure_group = QtWidgets.QGroupBox("Measurement Folders")
		measure_layout = QHBoxLayout()
		# Beam 1 Measurement Folders
		beam1_folders_layout = QVBoxLayout()
		self.beam1_folders_label = QLabel("Beam 1 Measurement Folders:")
		self.beam1_folders_label.setStyleSheet("color: blue;")
		beam1_folders_layout.addWidget(self.beam1_folders_label)
		self.beam1_folders_list = QListWidget()
		self.beam1_folders_list.setSelectionMode(QListWidget.MultiSelection)
		beam1_folders_layout.addWidget(self.beam1_folders_list)
		beam1_buttons_layout = QHBoxLayout()
		self.beam1_folders_button = QPushButton("Add Folders")
		self.beam1_folders_button.clicked.connect(self.select_beam1_folders)
		beam1_buttons_layout.addWidget(self.beam1_folders_button)
		self.beam1_remove_button = QPushButton("Remove Selected")
		self.beam1_remove_button.clicked.connect(self.remove_selected_beam1_folders)
		beam1_buttons_layout.addWidget(self.beam1_remove_button)
		self.beam1_select_all_checkbox = QtWidgets.QCheckBox("Select All")
		self.beam1_select_all_checkbox.stateChanged.connect(self.toggle_select_all_beam1_folders)
		beam1_buttons_layout.addWidget(self.beam1_select_all_checkbox)
		beam1_folders_layout.addLayout(beam1_buttons_layout)
		measure_layout.addLayout(beam1_folders_layout)
		# Beam 2 Measurement Folders (similar)
		beam2_folders_layout = QVBoxLayout()
		self.beam2_folders_label = QLabel("Beam 2 Measurement Folders:")
		self.beam2_folders_label.setStyleSheet("color: red;")
		beam2_folders_layout.addWidget(self.beam2_folders_label)
		self.beam2_folders_list = QListWidget()
		self.beam2_folders_list.setSelectionMode(QListWidget.MultiSelection)
		beam2_folders_layout.addWidget(self.beam2_folders_list)
		beam2_buttons_layout = QHBoxLayout()
		self.beam2_folders_button = QPushButton("Add Folders")
		self.beam2_folders_button.clicked.connect(self.select_beam2_folders)
		beam2_buttons_layout.addWidget(self.beam2_folders_button)
		self.beam2_remove_button = QPushButton("Remove Selected")
		self.beam2_remove_button.clicked.connect(self.remove_selected_beam2_folders)
		beam2_buttons_layout.addWidget(self.beam2_remove_button)
		self.beam2_select_all_checkbox = QtWidgets.QCheckBox("Select All")
		self.beam2_select_all_checkbox.stateChanged.connect(self.toggle_select_all_beam2_folders)
		beam2_buttons_layout.addWidget(self.beam2_select_all_checkbox)
		beam2_folders_layout.addLayout(beam2_buttons_layout)
		measure_layout.addLayout(beam2_folders_layout)
		measure_group.setLayout(measure_layout)
		folders_layout.addWidget(measure_group)
		folders_group.setLayout(folders_layout)
		self.input_layout.addWidget(folders_group)

		# --- Parameters and Knob Group ---
		param_group = QtWidgets.QGroupBox("Parameters and Knob")
		param_layout = QVBoxLayout()
		self.rdt_label = QLabel("RDT (in form of jklm):")
		param_layout.addWidget(self.rdt_label)       # "RDT (in form of jklm):"
		self.rdt_entry = QLineEdit()
		param_layout.addWidget(self.rdt_entry)
		self.rdt_plane_label = QLabel("RDT Plane:")
		param_layout.addWidget(self.rdt_plane_label)   # "RDT Plane:"
		self.rdt_plane_dropdown = QtWidgets.QComboBox()
		self.rdt_plane_dropdown.addItems(["x", "y"])
		param_layout.addWidget(self.rdt_plane_dropdown)
		self.knob_label = QLabel("Knob:")
		param_layout.addWidget(self.knob_label)          # "Knob:"
		self.knob_entry = QLineEdit("LHCBEAM/IP5-XING-H-MURAD")
		param_layout.addWidget(self.knob_entry)
		self.validate_knob_button = QPushButton("Validate Knob")
		self.validate_knob_button.clicked.connect(self.validate_knob_button_clicked)
		param_layout.addWidget(self.validate_knob_button)
		param_group.setLayout(param_layout)
		self.input_layout.addWidget(param_group)

		# --- Run Button Group ---
		run_group = QtWidgets.QGroupBox("Execute Analysis")
		run_layout = QVBoxLayout()
		self.run_button = QPushButton("Run Analysis")
		self.run_button.clicked.connect(self.run_analysis)
		run_layout.addWidget(self.run_button)
		run_group.setLayout(run_layout)
		self.input_layout.addWidget(run_group)

		# Graph Tab
		self.graph_tab = QWidget()
		self.tabs.addTab(self.graph_tab, "Graphing")
		self.graph_layout = QVBoxLayout(self.graph_tab)

		 # Keep only the new graph_files_list layout
		graph_files_layout = QVBoxLayout()
		self.graph_files_label = QLabel("Graph Files:")
		graph_files_layout.addWidget(self.graph_files_label)

		self.graph_files_list = QListWidget()
		self.graph_files_list.setSelectionMode(QtWidgets.QAbstractItemView.ExtendedSelection)
		graph_files_layout.addWidget(self.graph_files_list)

		graph_buttons_layout = QHBoxLayout()
		self.graph_files_button = QPushButton("Add Folders")
		self.graph_files_button.clicked.connect(self.select_analysis_files)
		graph_buttons_layout.addWidget(self.graph_files_button)

		self.graph_files_remove_button = QPushButton("Remove Selected")
		self.graph_files_remove_button.clicked.connect(lambda: self.remove_selected_items(self.graph_files_list))
		graph_buttons_layout.addWidget(self.graph_files_remove_button)

		self.graph_select_all_checkbox = QtWidgets.QCheckBox("Select All")
		self.graph_select_all_checkbox.stateChanged.connect(self.toggle_select_all_graph_files)
		graph_buttons_layout.addWidget(self.graph_select_all_checkbox)

		graph_files_layout.addLayout(graph_buttons_layout)
		self.graph_layout.addLayout(graph_files_layout)

		# BPM Search Group
		bpm_search_group = QtWidgets.QGroupBox("BPM Search")
		bpm_search_layout = QHBoxLayout()
		self.bpm_search_entry = QLineEdit()
		bpm_search_layout.addWidget(self.bpm_search_entry)
		self.bpm_search_button = QPushButton("Search BPM")
		self.bpm_search_button.clicked.connect(self.search_bpm)
		bpm_search_layout.addWidget(self.bpm_search_button)
		self.bpm_graph_button = QPushButton("Graph BPM")
		self.bpm_graph_button.clicked.connect(self.graph_bpm)
		bpm_search_layout.addWidget(self.bpm_graph_button)
		bpm_search_group.setLayout(bpm_search_layout)
		self.graph_layout.addWidget(bpm_search_group)

		# Graph text and canvas below file management
		self.graph_text = QTextEdit()
		self.graph_text.setReadOnly(True)
		self.graph_layout.addWidget(self.graph_text)

		self.figure = Figure(figsize=(6, 4))
		self.canvas = FigureCanvas(self.figure)
		self.graph_layout.addWidget(self.canvas)

	def change_default_input_path(self):
		new_path = QFileDialog.getExistingDirectory(self, "Select Default Input Path", self.default_input_path)
		if new_path:
			self.default_input_path = new_path
			self.input_path_label.setText(f"Default Input Path: {self.default_input_path}")

	def change_default_output_path(self):
		new_path = QFileDialog.getExistingDirectory(self, "Select Default Output Path", self.default_output_path)
		if new_path:
			self.default_output_path = new_path
			self.output_path_label.setText(f"Default Output Path: {self.default_output_path}")

	def select_beam1_model(self):
		"""
		Open a file dialog to select the Beam 1 model directory, starting from the default input path.
		"""
		modelpath = QFileDialog.getExistingDirectory(self, "Select Beam 1 Model", self.default_input_path)
		if modelpath:
			self.beam1_model_entry.setText(modelpath)
		
	def select_beam2_model(self):
		"""
		Open a file dialog to select the Beam 2 model directory, starting from the default input path.
		"""
		modelpath = QFileDialog.getExistingDirectory(self, "Select Beam 2 Model", self.default_input_path)
		if modelpath:
			self.beam2_model_entry.setText(modelpath)
		
	def select_beam1_reffolder(self):
		"""
		Open a file dialog to select the Beam 1 reference measurement folder.
		"""
		dialog = QFileDialog(self)
		dialog.setWindowTitle("Select Beam 1 Reference Measurement Folder")
		dialog.setDirectory(self.default_input_path)
		dialog.setFileMode(QFileDialog.Directory)
		dialog.setOption(QFileDialog.ShowDirsOnly, True)
		dialog.setNameFilter("Beam1BunchTurn*;;All Folders (*)")
		if dialog.exec_() == QFileDialog.Accepted:
			folderpath = dialog.selectedFiles()[0]
			self.beam1_reffolder_entry.setText(folderpath)

	def select_beam2_reffolder(self):
		"""
		Open a file dialog to select the Beam 2 reference measurement folder.
		"""
		dialog = QFileDialog(self)
		dialog.setWindowTitle("Select Beam 2 Reference Measurement Folder")
		dialog.setDirectory(self.default_input_path)
		dialog.setFileMode(QFileDialog.Directory)
		dialog.setOption(QFileDialog.ShowDirsOnly, True)
		dialog.setNameFilter("Beam2BunchTurn*;;All Folders (*)")
		if dialog.exec_() == QFileDialog.Accepted:
			folderpath = dialog.selectedFiles()[0]
			self.beam2_reffolder_entry.setText(folderpath)

	def remove_beam1_reffolder(self):
		"""
		Clear the Beam 1 reference folder entry.
		"""
		self.beam1_reffolder_entry.clear()

	def remove_beam2_reffolder(self):
		"""
		Clear the Beam 2 reference folder entry.
		"""
		self.beam2_reffolder_entry.clear()

	def select_multiple_directories(self, list_widget):
		"""
		Allow the user to select multiple directories and add them to the provided list widget.
		"""
		dialog = QFileDialog(self)
		dialog.setWindowTitle('Choose Directories')
		dialog.setDirectory(self.default_input_path)  # Set the default input path
		dialog.setOption(QFileDialog.DontUseNativeDialog, True)
		dialog.setFileMode(QFileDialog.Directory)
		dialog.setOption(QFileDialog.ShowDirsOnly, True)

		# Enable multiple selection in the dialog
		for view in dialog.findChildren((QtWidgets.QListView, QtWidgets.QTreeView)):
			if isinstance(view.model(), QtWidgets.QFileSystemModel):
				view.setSelectionMode(QtWidgets.QAbstractItemView.ExtendedSelection)

		if dialog.exec_() == QFileDialog.Accepted:
			selected_dirs = dialog.selectedFiles()
			for directory in selected_dirs:
				if directory not in [list_widget.item(i).text() for i in range(list_widget.count())]:
					list_widget.addItem(directory)

	def select_beam1_folders(self):
		dialog = QFileDialog(self)
		dialog.setWindowTitle('Choose Directories')
		dialog.setDirectory(self.default_input_path)  # Set the default input path
		dialog.setOption(QFileDialog.DontUseNativeDialog, True)
		dialog.setFileMode(QFileDialog.Directory)
		dialog.setOption(QFileDialog.ShowDirsOnly, True)
		dialog.setNameFilter("Beam1BunchTurn*;;All Folders (*)")

		# Enable multiple selection in the dialog
		for view in dialog.findChildren((QtWidgets.QListView, QtWidgets.QTreeView)):
			if isinstance(view.model(), QtWidgets.QFileSystemModel):
				view.setSelectionMode(QtWidgets.QAbstractItemView.ExtendedSelection)

		if dialog.exec_() == QFileDialog.Accepted:
			selected_dirs = dialog.selectedFiles()
			for directory in selected_dirs:
				self.beam1_folders_list.addItem(directory)

	def select_beam2_folders(self):
		dialog = QFileDialog(self)
		dialog.setWindowTitle('Choose Directories')
		dialog.setDirectory(self.default_input_path)  # Set the default input path
		dialog.setOption(QFileDialog.DontUseNativeDialog, True)
		dialog.setFileMode(QFileDialog.Directory)
		dialog.setOption(QFileDialog.ShowDirsOnly, True)
		dialog.setNameFilter("Beam2BunchTurn*;;All Folders (*)")

		# Enable multiple selection in the dialog
		for view in dialog.findChildren((QtWidgets.QListView, QtWidgets.QTreeView)):
			if isinstance(view.model(), QtWidgets.QFileSystemModel):
				view.setSelectionMode(QtWidgets.QAbstractItemView.ExtendedSelection)

		if dialog.exec_() == QFileDialog.Accepted:
			selected_dirs = dialog.selectedFiles()
			for directory in selected_dirs:
				self.beam2_folders_list.addItem(directory)

	def remove_selected_beam1_folders(self):
		"""
		Remove selected items from the Beam 1 folders list.
		"""
		for item in self.beam1_folders_list.selectedItems():
			self.beam1_folders_list.takeItem(self.beam1_folders_list.row(item))

	def remove_selected_beam2_folders(self):
		"""
		Remove selected items from the Beam 2 folders list.
		"""
		for item in self.beam2_folders_list.selectedItems():
			self.beam2_folders_list.takeItem(self.beam2_folders_list.row(item))

	def toggle_select_all_beam1_folders(self, state):
		"""
		Toggle selection for all items in the Beam 1 folders list based on the checkbox state.
		"""
		for i in range(self.beam1_folders_list.count()):
			self.beam1_folders_list.item(i).setSelected(state == Qt.Checked)

	def toggle_select_all_beam2_folders(self, state):
		"""
		Toggle selection for all items in the Beam 2 folders list based on the checkbox state.
		"""
		for i in range(self.beam2_folders_list.count()):
			self.beam2_folders_list.item(i).setSelected(state == Qt.Checked)

	def validate_rdt_and_plane(self, rdt, rdt_plane):
		"""
		Validate the RDT and RDT Plane combination.
		"""
		try:
			check_rdt(rdt, rdt_plane)
			return True, ""
		except Exception as e:
			return False, str(e)

	def validate_knob(self, ldb, knob):
		"""
		Validate the knob by checking its existence in the state tracker.
		Returns a tuple: (True, knob_setting) if valid, otherwise (False, error_message).
		"""
		try:
			current_timestamp = time.time()  # Get the current timestamp
			statetracker_knob_name = f"LhcStateTracker:{re.sub('/', ':', knob)}:value"
			knob_data = ldb.get(statetracker_knob_name, current_timestamp)
			if statetracker_knob_name not in knob_data:
				return False, f"Knob '{knob}' not found in the state tracker."
			knob_setting = knob_data[statetracker_knob_name][1][0]
			return True, knob_setting
		except Exception as e:
			# Log the exception if needed, and return an error without forcing a quit.
			return False, str(e)

	def validate_knob_button_clicked(self):
		"""
		Validate the knob when the "Validate Knob" button is clicked.
		"""
		knob = self.knob_entry.text()
		if not knob:
			QMessageBox.critical(self, "Error", "Knob field must be filled!")
			return

		is_valid_knob, knob_message = self.validate_knob(initialize_statetracker(), knob)
		if is_valid_knob:
			QMessageBox.information(self, "Knob Validation", "Knob is valid. Setting: " + repr(knob_message))
		else:
			QMessageBox.critical(self, "Knob Validation", "Invalid Knob: " + repr(knob_message))

	def run_analysis(self):
		self.figure.clear()
		# Divide heavy processing into steps for better UI responsiveness:
		self.current_step = 0
		self.analysis_steps = [
			self.analysis_step1,  # e.g., initialization and first data processing
			self.analysis_step2,  # e.g., fitting/BPM processing
			self.analysis_step3   # e.g., finalizing and drawing results
		]
		self.run_next_step()

	def update_graph_files_widget(self):
		# Update the graph_files_list widget with analysis_output_files
		self.graph_files_list.clear()
		for f in self.analysis_output_files:
			self.graph_files_list.addItem(f)

	def run_next_step(self):
		if self.current_step < len(self.analysis_steps):
			self.analysis_steps[self.current_step]()  # execute current step
			self.current_step += 1
			QTimer.singleShot(0, self.run_next_step)     # schedule next step ASAP
		else:
			self.canvas.draw()
			self.update_graph_files_widget()  # show analysis output files in the widget
			QMessageBox.information(self, "Run Analysis", "Analysis completed successfully!")

	def analysis_step1(self):
		# Initialize variables and validate inputs
		self.ldb = initialize_statetracker()
		self.rdt = self.rdt_entry.text()
		self.rdt_plane = self.rdt_plane_dropdown.currentText()
		self.validate_rdt_and_plane(self.rdt, self.rdt_plane)
		self.rdtfolder = rdt_to_order_and_type(self.rdt)
		self.beam1_model = self.beam1_model_entry.text()
		self.beam2_model = self.beam2_model_entry.text()
		self.beam1_reffolder = self.beam1_reffolder_entry.text()
		self.beam2_reffolder = self.beam2_reffolder_entry.text()
		self.beam1_folders = [self.beam1_folders_list.item(i).text() for i in range(self.beam1_folders_list.count())]
		self.beam2_folders = [self.beam2_folders_list.item(i).text() for i in range(self.beam2_folders_list.count())]
		self.knob = self.knob_entry.text()
		self.output_path = self.default_output_path

	def analysis_step2(self):
		# Process Beam 1 data
		if self.beam1_model and self.beam1_folders:
			b1modelbpmlist, b1bpmdata = getmodelBPMs(self.beam1_model)
			self.b1rdtdata = getrdt_omc3(self.ldb, b1modelbpmlist, b1bpmdata,
										  self.beam1_reffolder, self.beam1_folders,
										  self.knob, self.output_path,
										  self.rdt, self.rdt_plane, self.rdtfolder, self.log_error)
			self.b1rdtdata = fit_BPM(self.b1rdtdata)

	def analysis_step3(self):
		# Process Beam 2 data and write output files:
		if self.beam2_model and self.beam2_folders:
			b2modelbpmlist, b2bpmdata = getmodelBPMs(self.beam2_model)
			self.b2rdtdata = getrdt_omc3(self.ldb, b2modelbpmlist, b2bpmdata,
										  self.beam2_reffolder, self.beam2_folders,
										  self.knob, self.output_path,
										  self.rdt, self.rdt_plane, self.rdtfolder, self.log_error)
			self.b2rdtdata = fit_BPM(self.b2rdtdata)
			
		# Prompt to save Beam 1 RDT data just before calling write_RDTshifts
		self.analysis_output_files = []
		if self.beam1_model and self.beam1_folders:
			self.save_b1_rdtdata()
			write_RDTshifts(self.b1rdtdata, self.rdt, self.rdt_plane, "b1", self.output_path, self.log_error)
		if self.beam2_model and self.beam2_folders:
			self.save_b2_rdtdata()
			write_RDTshifts(self.b2rdtdata, self.rdt, self.rdt_plane, "b2", self.output_path, self.log_error)

	def log_error(self, error_msg):
		QMessageBox.critical(self, "Error", error_msg)

	def remove_selected_items(self, list_widget):
		"""
		Remove selected items from a given list widget.
		"""
		for item in list_widget.selectedItems():
			list_widget.takeItem(list_widget.row(item))

	def toggle_select_all_graph_files(self, state):
		"""
		Toggle selection for all items in the graph files list based on the checkbox state.
		"""
		for i in range(self.graph_files_list.count()):
			self.graph_files_list.item(i).setSelected(state == Qt.Checked)
	
	def select_multiple_files(self, list_widget):
		"""
		Allow the user to select multiple files and add them to the file list widget.
		"""
		dialog = QFileDialog(self)
		dialog.setWindowTitle("Select Analysis Files")
		dialog.setDirectory(self.default_input_path)  # Use default output path, adjust if needed
		dialog.setFileMode(QFileDialog.ExistingFiles)
		dialog.setNameFilter("All Files (*)")

		# Enable multiple selection in the dialog
		for view in dialog.findChildren((QtWidgets.QListView, QtWidgets.QTreeView)):
			if isinstance(view.model(), QtWidgets.QFileSystemModel):
				view.setSelectionMode(QtWidgets.QAbstractItemView.ExtendedSelection)

		if dialog.exec_() == QFileDialog.Accepted:
			selected_files = dialog.selectedFiles()
			for file in selected_files:
				if file not in [
					list_widget.item(i).text()
					for i in range(list_widget.count())
				]:
					list_widget.addItem(file)

	def select_analysis_files(self):
		self.select_multiple_files(self.graph_files_list)

	def search_bpm(self):
		search_term = self.bpm_search_entry.text().strip()
		if not search_term:
			QMessageBox.information(self, "BPM Search", "No BPM specified.")
			return
		results = []
		for i in range(self.graph_files_list.count()):
			file_path = self.graph_files_list.item(i).text()
			try:
				with open(file_path, "r") as f:
					content = f.read()
				if search_term in content:
					results.append(file_path)
			except Exception:
				pass
		if results:
			QMessageBox.information(self, "BPM Search", f"Found BPM '{search_term}' in:\n" + "\n".join(results))
		else:
			QMessageBox.information(self, "BPM Search", f"BPM '{search_term}' not found.")

	def graph_bpm(self):
		plot_BPM(BPM, data, rdt, rdt_plane, filename)
		pass

	def save_b1_rdtdata(self):
		filename, _ = QFileDialog.getSaveFileName(
			self,
			"Save Beam 1 RDT Data",
			self.default_output_path,
			"JSON Files (*.json)"
		)
		if filename:
			if not filename.lower().endswith(".json"):
				filename += ".json"
			save_RDTdata(self.b1rdtdata, filename)

	def load_b1_rdtdata(self):
		filename, _ = QFileDialog.getOpenFileName(
			self,
			"Load Beam 1 RDT Data",
			self.default_output_path,
			"JSON Files (*.json)"
		)
		if filename:
			self.b1rdtdata = load_RDTdata(filename)

	def save_b2_rdtdata(self):
		filename, _ = QFileDialog.getSaveFileName(
			self,
			"Save Beam 2 RDT Data",
			self.default_output_path,
			"JSON Files (*.json)"
		)
		if filename:
			if not filename.lower().endswith(".json"):
				filename += ".json"
			save_RDTdata(self.b2rdtdata, filename)
			self.analysis_output_files.append(f"{self.output_path}/{filename}")

	def load_b2_rdtdata(self):
		filename, _ = QFileDialog.getOpenFileName(
			self,
			"Load Beam 2 RDT Data",
			self.default_output_path,
			"JSON Files (*.json)"
		)
		if filename:
			self.b2rdtdata = load_RDTdata(filename)
