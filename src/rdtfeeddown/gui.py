import json
from PyQt5.QtWidgets import (
	QApplication, QMainWindow, QGridLayout, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton, QCheckBox,
	QFileDialog, QListWidget, QTabWidget, QWidget, QTextEdit, QMessageBox, QProgressBar, QSizePolicy, QToolButton, QGroupBox
)
import pyqtgraph as pg
from PyQt5 import QtWidgets
from PyQt5.QtCore import Qt, QTimer  # Import Qt for the correct constants and QTimer
from matplotlib.figure import Figure
from .validation_utils import validate_rdt_and_plane, validate_knob, validate_metas
from .utils import load_defaults, initialize_statetracker, rdt_to_order_and_type, getmodelBPMs, MyViewBox
from .analysis import write_RDTshifts, getrdt_omc3, fit_BPM, save_RDTdata, load_RDTdata, group_datasets, getrdt_sim
from .plotting import plot_BPM, plot_RDT, plot_RDTshifts, plot_dRDTdknob, clear_layout, setup_blankcanvas  # Assuming you have a plotting module for BPM plotting
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
		# LHCB1
		beam1_layout = QVBoxLayout()
		self.beam1_model_label = QLabel("LHCB1 Model:")
		self.beam1_model_label.setStyleSheet("color: blue;")
		beam1_layout.addWidget(self.beam1_model_label)
		self.beam1_model_entry = QLineEdit()
		beam1_layout.addWidget(self.beam1_model_entry)
		self.beam1_model_button = QPushButton("Select Model")
		self.beam1_model_button.clicked.connect(self.select_beam1_model)
		beam1_layout.addWidget(self.beam1_model_button)
		beam_model_layout.addLayout(beam1_layout)
		# LHCB2
		beam2_layout = QVBoxLayout()
		self.beam2_model_label = QLabel("LHCB2 Model:")
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

		# LHCB1 Reference Folder (vertical layout)
		beam1_ref_layout = QVBoxLayout()
		self.beam1_reffolder_label = QLabel("LHCB1 Reference Measurement Folder:")
		self.beam1_reffolder_label.setStyleSheet("color: blue;")
		beam1_ref_layout.addWidget(self.beam1_reffolder_label)
		self.beam1_reffolder_entry = QLineEdit()
		beam1_ref_layout.addWidget(self.beam1_reffolder_entry)
		beam1_buttons_layout = QHBoxLayout()
		self.beam1_reffolder_button = QPushButton("Select Folder")
		self.beam1_reffolder_button.clicked.connect(lambda: self.select_singleitem("LHCB1",
													"Select LHCB1 Reference Measurement Folder",
													"LHCB1 folders (Beam1BunchTurn*);;All Folders (*)",
													self.beam1_reffolder_entry, self.beam2_reffolder_entry,
													True))
		beam1_buttons_layout.addWidget(self.beam1_reffolder_button)
		self.beam1_reffolder_remove_button = QPushButton("Remove File")
		self.beam1_reffolder_remove_button.clicked.connect(lambda: self.remove_singlefolder("LHCB1",
													self.beam1_reffolder_entry, self.beam2_reffolder_entry))
		beam1_buttons_layout.addWidget(self.beam1_reffolder_remove_button)  # Added the remove button to the layout
		beam1_ref_layout.addLayout(beam1_buttons_layout)
		ref_folders_layout.addLayout(beam1_ref_layout)

		# LHCB2 Reference Folder (vertical layout)
		beam2_ref_layout = QVBoxLayout()
		self.beam2_reffolder_label = QLabel("LHCB2 Reference Measurement Folder:")
		self.beam2_reffolder_label.setStyleSheet("color: red;")
		beam2_ref_layout.addWidget(self.beam2_reffolder_label)
		self.beam2_reffolder_entry = QLineEdit()
		beam2_ref_layout.addWidget(self.beam2_reffolder_entry)
		beam2_buttons_layout = QHBoxLayout()
		self.beam2_reffolder_button = QPushButton("Select Folder")
		self.beam2_reffolder_button.clicked.connect(lambda: self.select_singleitem("LHCB2", 
													"Select LHCB2 Reference Measurement Folder", 
													"LHCB2 folders (Beam2BunchTurn*);;All Folders (*)", 
													self.beam1_reffolder_entry, self.beam2_reffolder_entry,
													True))
		beam2_buttons_layout.addWidget(self.beam2_reffolder_button)
		self.beam2_reffolder_remove_button = QPushButton("Remove File")
		self.beam2_reffolder_remove_button.clicked.connect(lambda: self.remove_singlefolder("LHCB2",
													self.beam1_reffolder_entry, self.beam2_reffolder_entry))
		beam2_buttons_layout.addWidget(self.beam2_reffolder_remove_button)
		beam2_ref_layout.addLayout(beam2_buttons_layout)
		ref_folders_layout.addLayout(beam2_ref_layout)

		ref_folders_group.setLayout(ref_folders_layout)
		# Insert the new reference folders group at the top of the folders layout.
		folders_layout.insertWidget(0, ref_folders_group)

		# Measurement Folders for LHCB1 and LHCB2
		measure_group = QtWidgets.QGroupBox("Measurement Folders")
		measure_layout = QHBoxLayout()
		# LHCB1 Measurement Folders
		beam1_folders_layout = QVBoxLayout()
		self.beam1_folders_label = QLabel("LHCB1 Measurement Folders:")
		self.beam1_folders_label.setStyleSheet("color: blue;")
		beam1_folders_layout.addWidget(self.beam1_folders_label)
		self.beam1_folders_list = QListWidget()
		self.beam1_folders_list.setSelectionMode(QListWidget.ExtendedSelection)
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
		# LHCB2 Measurement Folders (similar)
		beam2_folders_layout = QVBoxLayout()
		self.beam2_folders_label = QLabel("LHCB2 Measurement Folders:")
		self.beam2_folders_label.setStyleSheet("color: red;")
		beam2_folders_layout.addWidget(self.beam2_folders_label)
		self.beam2_folders_list = QListWidget()
		self.beam2_folders_list.setSelectionMode(QListWidget.ExtendedSelection)
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
		self.knob_entry = QLineEdit("LHCBEAM/IP2-XING-V-MURAD")
		param_layout.addWidget(self.knob_entry)
		# New simulation mode checkbox
		self.simulation_checkbox = QtWidgets.QCheckBox("Simulation Mode")
		param_layout.addWidget(self.simulation_checkbox)
		self.simulation_checkbox.stateChanged.connect(self.toggle_simulation_mode)
		# New properties file input and browse button (hidden by default)
		self.simulation_file_entry = QLineEdit()
		self.simulation_file_entry.setPlaceholderText("Select properties file")
		self.simulation_file_entry.hide()
		param_layout.addWidget(self.simulation_file_entry)
		self.simulation_file_button = QPushButton("Browse Properties")
		self.simulation_file_button.clicked.connect(self.select_properties_file)
		self.simulation_file_button.hide()
		param_layout.addWidget(self.simulation_file_button)
		self.validate_knob_button = QPushButton("Validate Knob")
		self.validate_knob_button.clicked.connect(self.validate_knob_button_clicked)
		param_layout.addWidget(self.validate_knob_button)
		# Unified fields (hidden by default)
		self.corr_knobname_entry = QLineEdit()
		self.corr_knobname_entry.setPlaceholderText("Unified Knob Name")
		self.corr_knobname_entry.hide()
		param_layout.addWidget(self.corr_knobname_entry)
		self.corr_knob_entry = QLineEdit()
		self.corr_knob_entry.setPlaceholderText("Unified Knob Value")
		self.corr_knob_entry.hide()
		param_layout.addWidget(self.corr_knob_entry)
		self.corr_xing_entry = QLineEdit()
		self.corr_xing_entry.setPlaceholderText("Unified XING")
		self.corr_xing_entry.hide()
		param_layout.addWidget(self.corr_xing_entry)
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

		 # Progress bar for plotting
		self.input_progress = QProgressBar()
		self.input_progress.setRange(0, 0)
		self.input_progress.hide()
		self.layout.addWidget(self.input_progress)

		 # Validation Tab
		self.validation_tab = QWidget()
		self.tabs.addTab(self.validation_tab, "Validation")
		self.validation_layout = QVBoxLayout(self.validation_tab)

		 # Keep only the new validation_files_list layout
		validation_files_layout = QVBoxLayout()
		self.validation_files_label = QLabel("Validation Files:")
		validation_files_layout.addWidget(self.validation_files_label)

		self.validation_files_list = QListWidget()
		self.validation_files_list.setSelectionMode(QtWidgets.QAbstractItemView.ExtendedSelection)
		validation_files_layout.addWidget(self.validation_files_list)

		validation_buttons_layout = QHBoxLayout()
		self.validation_files_button = QPushButton("Add Folders")
		self.validation_files_button.clicked.connect(self.select_analysis_files)
		validation_buttons_layout.addWidget(self.validation_files_button)

		self.validation_files_remove_button = QPushButton("Remove Selected")
		self.validation_files_remove_button.clicked.connect(lambda: self.remove_selected_items(self.validation_files_list))
		validation_buttons_layout.addWidget(self.validation_files_remove_button)

		self.validation_select_all_checkbox = QCheckBox("Select All")
		self.validation_select_all_checkbox.stateChanged.connect(self.toggle_select_all_validation_files)
		validation_buttons_layout.addWidget(self.validation_select_all_checkbox)

		validation_files_layout.addLayout(validation_buttons_layout)
		self.validation_layout.addLayout(validation_files_layout)

		self.load_selected_files_button = QPushButton("Load Selected Files")
		self.load_selected_files_button.clicked.connect(self.load_selected_files)
		self.validation_layout.addWidget(self.load_selected_files_button)

		self.loaded_files_list = QListWidget()
		self.loaded_files_list.setSelectionMode(QtWidgets.QAbstractItemView.NoSelection)
		self.validation_layout.addWidget(self.loaded_files_list)

		# --- Replace Beam Tabs with a Beam Selector and Single Plotting Canvas ---
		self.graph_tabs = QTabWidget()
		self.bpm_tab = QWidget()
		bpm_tab_layout = QVBoxLayout(self.bpm_tab)

		beam_selector_layout = QHBoxLayout()
		beam_label = QLabel("Select Beam:")
		beam_selector_layout.addWidget(beam_label)
		self.beam_selector = QtWidgets.QComboBox()
		self.beam_selector.addItems(["LHCB1", "LHCB2"])
		self.beam_selector.currentIndexChanged.connect(self.update_bpm_search_entry)
		beam_selector_layout.addWidget(self.beam_selector)
		bpm_tab_layout.addLayout(beam_selector_layout)

		self.bpm_search_entry = QLineEdit()
		self.update_bpm_search_entry()  # initialize with the correct default
		self.bpm_search_entry.setPlaceholderText("Enter BPM search term")
		bpm_layout = QHBoxLayout()
		bpm_layout.addWidget(self.bpm_search_entry)
		self.search_bpm_button = QPushButton("Search BPM")
		self.search_bpm_button.clicked.connect(self.search_bpm)
		bpm_layout.addWidget(self.search_bpm_button)
		self.graph_bpm_button = QPushButton("Graph BPM")
		self.graph_bpm_button.clicked.connect(self.graph_bpm)
		bpm_layout.addWidget(self.graph_bpm_button)
		bpm_tab_layout.addLayout(bpm_layout)

		# BPM plotting widget
		self.bpmWidget = pg.PlotWidget()
		setup_blankcanvas(self.bpmWidget)
		bpm_tab_layout.addWidget(self.bpmWidget)

		# Add graph tabs for RDT and RDT shifts
		self.graph_tabs.addTab(self.bpm_tab, "BPM")
		self.rdt_tab = QWidget()
		self.rdt_shift_tab = QWidget()
		self.graph_tabs.addTab(self.rdt_tab, "RDT")
		self.graph_tabs.addTab(self.rdt_shift_tab, "RDT shift")
		self.validation_layout.addWidget(self.graph_tabs)

		rdt_layout = QVBoxLayout(self.rdt_tab)
		self.plot_rdt_button = QPushButton("Plot RDT")
		self.plot_rdt_button.clicked.connect(self.plot_rdt)
		rdt_layout.addWidget(self.plot_rdt_button)
		self.rdtWidget = pg.PlotWidget()
		setup_blankcanvas(self.rdtWidget)
		rdt_layout.addWidget(self.rdtWidget)

		rdt_shift_layout = QVBoxLayout(self.rdt_shift_tab)
		self.plot_rdt_shifts_button = QPushButton("Plot RDT Shifts")
		self.plot_rdt_shifts_button.clicked.connect(self.plot_rdt_shifts)
		rdt_shift_layout.addWidget(self.plot_rdt_shifts_button)
		self.rdtShiftwidget = pg.PlotWidget()
		setup_blankcanvas(self.rdtShiftwidget)
		rdt_shift_layout.addWidget(self.rdtShiftwidget)

		 # Progress bar for plotting
		self.plot_progress = QProgressBar()
		self.plot_progress.setRange(0, 0)
		self.plot_progress.hide()
		self.layout.addWidget(self.plot_progress)

		# Correction Tab
		self.correction_tab = QWidget()
		self.tabs.addTab(self.correction_tab, "Correction")
		correction_main_layout = QVBoxLayout(self.correction_tab)

		# Create a header container for the toggle button.
		header_container = QWidget()
		header_layout = QHBoxLayout(header_container)
		header_layout.setContentsMargins(0, 0, 0, 0)
		self.corr_toggle_button = QToolButton()
		self.corr_toggle_button.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)  # force text display
		self.corr_toggle_button.setText("Collapse Section")
		self.corr_toggle_button.setCheckable(True)
		self.corr_toggle_button.setChecked(True)
		self.corr_toggle_button.setArrowType(Qt.DownArrow)
		self.corr_toggle_button.setFixedHeight(30)
		self.corr_toggle_button.clicked.connect(self.toggle_correction_content)
		header_layout.addWidget(self.corr_toggle_button)
		header_layout.addStretch()  # keep the header at the top
		correction_main_layout.addWidget(header_container)

		# Collapsible content container – remains below the fixed header.
		self.correction_content = QWidget()
		self.correction_layout = QVBoxLayout(self.correction_content)
		self.correction_content.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum)
		correction_main_layout.addWidget(self.correction_content)

		# Reference correction folders
		corr_folders_group = QtWidgets.QGroupBox("Reference and Measurement Folders")
		corr_folders_group.setSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Fixed)
		corr_folders_layout = QVBoxLayout(corr_folders_group)

		# Replace the individual reference folder groups with a combined horizontal group:
		corr_ref_folders_group = QtWidgets.QGroupBox("Reference Folders")
		corr_ref_folders_group.setSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Fixed)
		corr_ref_folders_layout = QHBoxLayout()

		# LHCB1 Reference Folder (vertical layout)
		corr_beam1_ref_layout = QVBoxLayout()
		self.corr_beam1_reffolder_label = QLabel("LHCB1 Reference Folder:")
		self.corr_beam1_reffolder_label.setStyleSheet("color: blue;")
		corr_beam1_ref_layout.addWidget(self.corr_beam1_reffolder_label)
		self.corr_beam1_reffolder_entry = QLineEdit()
		corr_beam1_ref_layout.addWidget(self.corr_beam1_reffolder_entry)
		corr_beam1_buttons_layout = QHBoxLayout()
		self.corr_beam1_reffolder_button = QPushButton("Select Folder")
		self.corr_beam1_reffolder_button.clicked.connect(lambda: self.select_singleitem("LHCB1", 
													"Select LHCB1 Reference File", 
													"All Folders (*)", 
													self.corr_beam1_reffolder_entry, None,
													True))
		corr_beam1_buttons_layout.addWidget(self.corr_beam1_reffolder_button)
		self.corr_beam1_reffolder_remove_button = QPushButton("Remove File")
		self.corr_beam1_reffolder_remove_button.clicked.connect(lambda: self.remove_singlefolder("LHCB1",
													self.beam1_reffolder_entry, self.beam2_reffolder_entry,))
		corr_beam1_buttons_layout.addWidget(self.corr_beam1_reffolder_remove_button)
		corr_beam1_ref_layout.addLayout(corr_beam1_buttons_layout)
		corr_ref_folders_layout.addLayout(corr_beam1_ref_layout)

		# LHCB2 Reference Folder (vertical layout)
		corr_beam2_ref_layout = QVBoxLayout()
		self.corr_beam2_reffolder_label = QLabel("LHCB2 Reference Folder:")
		self.corr_beam2_reffolder_label.setStyleSheet("color: red;")
		corr_beam2_ref_layout.addWidget(self.corr_beam2_reffolder_label)
		self.corr_beam2_reffolder_entry = QLineEdit()
		corr_beam2_ref_layout.addWidget(self.corr_beam2_reffolder_entry)
		corr_beam2_buttons_layout = QHBoxLayout()
		self.corr_beam2_reffolder_button = QPushButton("Select Folder")
		self.corr_beam2_reffolder_button.clicked.connect(lambda: self.select_singleitem("LHCB2", 
													"Select LHCB2 Reference Folder", 
													"All Folders (*)", 
													None, self.corr_beam2_reffolder_entry,
													True))
		corr_beam2_buttons_layout.addWidget(self.corr_beam2_reffolder_button)
		self.corr_beam2_reffolder_remove_button = QPushButton("Remove File")
		self.corr_beam2_reffolder_remove_button.clicked.connect(lambda: self.remove_singlefolder("LHCB2",
													self.beam2_reffolder_entry, self.beam2_reffolder_entry))
		corr_beam2_buttons_layout.addWidget(self.corr_beam2_reffolder_remove_button)
		corr_beam2_ref_layout.addLayout(corr_beam2_buttons_layout)
		corr_ref_folders_layout.addLayout(corr_beam2_ref_layout)

		corr_ref_folders_group.setLayout(corr_ref_folders_layout)
		# Insert the new reference folders group at the top of the folders layout.
		corr_folders_layout.insertWidget(0, corr_ref_folders_group)

		# Replace the individual measurement folder groups with a combined horizontal group:
		corr_meas_folders_group = QtWidgets.QGroupBox("Response Folders")
		corr_meas_folders_group.setSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Fixed)
		corr_meas_folders_layout = QHBoxLayout()

		# LHCB1 Measurement Folder (vertical layout)
		corr_beam1_meas_layout = QVBoxLayout()
		self.corr_beam1_measfolder_label = QLabel("LHCB1 Response Folder:")
		self.corr_beam1_measfolder_label.setStyleSheet("color: blue;")
		corr_beam1_meas_layout.addWidget(self.corr_beam1_measfolder_label)
		self.corr_beam1_measfolder_entry = QLineEdit()
		corr_beam1_meas_layout.addWidget(self.corr_beam1_measfolder_entry)
		corr_beam1_buttons_layout = QHBoxLayout()
		self.corr_beam1_measfolder_button = QPushButton("Select Folder")
		self.corr_beam1_measfolder_button.clicked.connect(lambda: self.select_singleitem("LHCB1", 
													"Select LHCB1 Response Folder", 
													"All Folders (*)", 
													self.corr_beam1_measfolder_entry, None,
													True))
		corr_beam1_buttons_layout.addWidget(self.corr_beam1_measfolder_button)
		self.corr_beam1_measfolder_remove_button = QPushButton("Remove File")
		self.corr_beam1_measfolder_remove_button.clicked.connect(lambda: self.remove_singlefolder("LHCB1",
													self.beam1_measfolder_entry, self.beam2_measfolder_entry))
		corr_beam1_buttons_layout.addWidget(self.corr_beam1_measfolder_remove_button)
		corr_beam1_meas_layout.addLayout(corr_beam1_buttons_layout)
		corr_meas_folders_layout.addLayout(corr_beam1_meas_layout)

		# LHCB2 Measurement Folder (vertical layout)
		corr_beam2_meas_layout = QVBoxLayout()
		self.corr_beam2_measfolder_label = QLabel("LHCB2 Response Folder:")
		self.corr_beam2_measfolder_label.setStyleSheet("color: red;")
		corr_beam2_meas_layout.addWidget(self.corr_beam2_measfolder_label)
		self.corr_beam2_measfolder_entry = QLineEdit()
		corr_beam2_meas_layout.addWidget(self.corr_beam2_measfolder_entry)
		corr_beam2_buttons_layout = QHBoxLayout()
		self.corr_beam2_measfolder_button = QPushButton("Select Folder")
		self.corr_beam2_measfolder_button.clicked.connect(lambda: self.select_singleitem("LHCB2", 
													"Select LHCB2 Response Folder", 
													"All Files (*)", 
													None, self.corr_beam2_measfolder_entry,
													True))
		corr_beam2_buttons_layout.addWidget(self.corr_beam2_measfolder_button)
		self.corr_beam2_measfolder_remove_button = QPushButton("Remove File")
		self.corr_beam2_measfolder_remove_button.clicked.connect(lambda: self.remove_singlefolder("LHCB1",
													None, self.beam2_measfolder_entry))
		corr_beam2_buttons_layout.addWidget(self.corr_beam2_measfolder_remove_button)
		corr_beam2_meas_layout.addLayout(corr_beam2_buttons_layout)
		corr_meas_folders_layout.addLayout(corr_beam2_meas_layout)

		corr_meas_folders_group.setLayout(corr_meas_folders_layout)
		# Insert the new measured folders group at the top of the folders layout.
		corr_folders_layout.insertWidget(1, corr_meas_folders_group)
		self.correction_layout.addWidget(corr_folders_group)

		# --- Parameters and Knob Group (Correction Tab) ---
		corr_param_group = QtWidgets.QGroupBox("Parameters and Knob")
		corr_param_layout = QVBoxLayout()
		self.corr_rdt_label = QLabel("RDT (in form of jklm):")
		corr_param_layout.addWidget(self.corr_rdt_label)
		self.corr_rdt_entry = QLineEdit()
		corr_param_layout.addWidget(self.corr_rdt_entry)
		self.corr_rdt_plane_label = QLabel("RDT Plane:")
		corr_param_layout.addWidget(self.corr_rdt_plane_label)
		self.corr_rdt_plane_dropdown = QtWidgets.QComboBox()
		self.corr_rdt_plane_dropdown.addItems(["x", "y"])
		corr_param_layout.addWidget(self.corr_rdt_plane_dropdown)

		# Common checkbox above knob entries
		self.b1andb2same_checkbox = QtWidgets.QCheckBox("LHCB1 same as LHCB2 mode")
		corr_param_layout.addWidget(self.b1andb2same_checkbox)
		self.b1andb2same_checkbox.stateChanged.connect(self.toggle_b1andb2same_mode)

		# --- Add separate LHCB1 and LHCB2 knob fields ---
		separate_knob_layout = QHBoxLayout()
		# LHCB1 widgets
		lhcb1_layout = QVBoxLayout()
		self.b1_corr_knobname_label = QLabel("LHCB1 Knob name:")
		self.b1_corr_knobname_label.setStyleSheet("color: blue;")
		lhcb1_layout.addWidget(self.b1_corr_knobname_label)
		self.b1_corr_knobname_entry = QLineEdit()
		lhcb1_layout.addWidget(self.b1_corr_knobname_entry)
		self.b1_corr_knob_label = QLabel("LHCB1 Knob value:")
		self.b1_corr_knob_label.setStyleSheet("color: blue;")
		lhcb1_layout.addWidget(self.b1_corr_knob_label)
		self.b1_corr_knob_entry = QLineEdit()
		lhcb1_layout.addWidget(self.b1_corr_knob_entry)
		self.b1_corr_xing_label = QLabel("LHCB1 XING angle:")
		self.b1_corr_xing_label.setStyleSheet("color: blue;")
		lhcb1_layout.addWidget(self.b1_corr_xing_label)
		self.b1_corr_xing_entry = QLineEdit()
		lhcb1_layout.addWidget(self.b1_corr_xing_entry)
		separate_knob_layout.addLayout(lhcb1_layout)
		# LHCB2 widgets
		lhcb2_layout = QVBoxLayout()
		self.b2_corr_knobname_label = QLabel("LHCB2 Knob name:")
		self.b2_corr_knobname_label.setStyleSheet("color: red;")
		lhcb2_layout.addWidget(self.b2_corr_knobname_label)
		self.b2_corr_knobname_entry = QLineEdit()
		lhcb2_layout.addWidget(self.b2_corr_knobname_entry)
		self.b2_corr_knob_label = QLabel("LHCB2 Knob value:")
		self.b2_corr_knob_label.setStyleSheet("color: red;")
		lhcb2_layout.addWidget(self.b2_corr_knob_label)
		self.b2_corr_knob_entry = QLineEdit()
		lhcb2_layout.addWidget(self.b2_corr_knob_entry)
		self.b2_corr_xing_label = QLabel("LHCB2 XING angle:")
		self.b2_corr_xing_label.setStyleSheet("color: red;")
		lhcb2_layout.addWidget(self.b2_corr_xing_label)
		self.b2_corr_xing_entry = QLineEdit()
		lhcb2_layout.addWidget(self.b2_corr_xing_entry)
		separate_knob_layout.addLayout(lhcb2_layout)
		corr_param_layout.addLayout(separate_knob_layout)
		# By default show separate fields
		self.b1_corr_knobname_label.show()
		self.b1_corr_knobname_entry.show()
		self.b1_corr_knob_label.show()
		self.b1_corr_knob_entry.show()
		self.b1_corr_xing_label.show()
		self.b1_corr_xing_entry.show()
		self.b2_corr_knobname_label.show()
		self.b2_corr_knobname_entry.show()
		self.b2_corr_knob_label.show()
		self.b2_corr_knob_entry.show()
		self.b2_corr_xing_label.show()
		self.b2_corr_xing_entry.show()

		# --- Unified knob fields (for same mode) ---
		self.corr_knobname_entry_label = QLabel("Shared Knob name:")
		self.corr_knobname_entry = QLineEdit()
		self.corr_knob_entry_label = QLabel("Shared Knob value:")
		self.corr_knob_entry = QLineEdit()
		self.corr_xing_entry_label = QLabel("Shared XING angle:")
		self.corr_xing_entry = QLineEdit()
		# Initially hide unified fields
		self.corr_knobname_entry_label.hide()
		self.corr_knobname_entry.hide()
		self.corr_knob_entry_label.hide()
		self.corr_knob_entry.hide()
		self.corr_xing_entry_label.hide()
		self.corr_xing_entry.hide()
		corr_param_layout.addWidget(self.corr_knobname_entry_label)
		corr_param_layout.addWidget(self.corr_knobname_entry)
		corr_param_layout.addWidget(self.corr_knob_entry_label)
		corr_param_layout.addWidget(self.corr_knob_entry)
		corr_param_layout.addWidget(self.corr_xing_entry_label)
		corr_param_layout.addWidget(self.corr_xing_entry)

		corr_param_group.setLayout(corr_param_layout)
		self.correction_layout.addWidget(corr_param_group)

		# --- Run Button Group ---
		run_response_group = QtWidgets.QGroupBox("Find Response")
		run_response_layout = QVBoxLayout()
		self.run_response_button = QPushButton("Find response")
		self.run_response_button.clicked.connect(self.run_response)
		run_response_layout.addWidget(self.run_response_button)
		run_response_group.setLayout(run_response_layout)
		self.correction_layout.addWidget(run_response_group)

		# Existing: add the collapsible content
		correction_main_layout.addWidget(self.correction_content)
		
		# NEW: Loaded Files section (outside the collapsible content)
		loaded_files_group = QGroupBox("Loaded Files")
		loaded_files_group.setFixedHeight(150)
		loaded_files_layout = QVBoxLayout()
		self.correction_loaded_files_list = QtWidgets.QTreeWidget()
		self.correction_loaded_files_list.setColumnCount(4)  # 4 columns: Filename and RDT and RDT plane and CORRECTOR
		self.correction_loaded_files_list.setHeaderLabels(["Filename", "RDT", "RDT plane", "Corrector"])  # Set column headers
		loaded_files_layout.addWidget(self.correction_loaded_files_list)

		btn_layout = QHBoxLayout()
		self.load_file_button = QPushButton("Load File")
		self.load_file_button.clicked.connect(self.load_selected_correction_files)  # New method to implement
		btn_layout.addWidget(self.load_file_button)
		self.remove_file_button = QPushButton("Remove Selected Files")
		self.remove_file_button.clicked.connect(lambda: self.remove_selected_items(self.correction_loaded_files_list, True))
		btn_layout.addWidget(self.remove_file_button)
		self.select_all_files_checkbox = QCheckBox("Select All Files")
		self.select_all_files_checkbox.stateChanged.connect(lambda state: self._toggle_select_all(self.correction_loaded_files_list, state))
		btn_layout.addWidget(self.select_all_files_checkbox)
		loaded_files_layout.addLayout(btn_layout)
		loaded_files_group.setLayout(loaded_files_layout)
		correction_main_layout.addWidget(loaded_files_group)
		
		# Create the measurement_match_group widget
		measurement_match_group = QGroupBox("Measurement to be matched")
		match_layout = QHBoxLayout(measurement_match_group)

		# LHCB1
		b1_container = QWidget()
		b1_vlayout = QVBoxLayout(b1_container)
		b1_label = QLabel("LHCB1 Single Measurement:")
		b1_label.setStyleSheet("color: blue;")
		self.b1_match_entry = QLineEdit()
		b1_button = QPushButton("Browse File")
		b1_button.clicked.connect(lambda: self.select_singleitem("LHCB1",
															"Select LHCB1 Match File",
															"JSON Files (*.json);;All Files (*)", 
															self.b1_match_entry, None))
		b1_vlayout.addWidget(b1_label)
		b1_vlayout.addWidget(self.b1_match_entry)
		b1_vlayout.addWidget(b1_button)
		match_layout.addWidget(b1_container)

		# LHCB2
		b2_container = QWidget()
		b2_vlayout = QVBoxLayout(b2_container)
		b2_label = QLabel("LHCB2 Single Measurement:")
		b2_label.setStyleSheet("color: red;")
		self.b2_match_entry = QLineEdit()
		b2_button = QPushButton("Browse File")
		b2_button.clicked.connect(lambda: self.select_singleitem("LHCB2",
															"Select LHCB2 Match File",
															"JSON Files (*.json);;Select LHCB2 Match File",
															None, self.b2_match_entry))
		b2_vlayout.addWidget(b2_label)
		b2_vlayout.addWidget(self.b2_match_entry)
		b2_vlayout.addWidget(b2_button)
		match_layout.addWidget(b2_container)

		# Insert the measurement_match_group widget below the loaded files widget and buttons
		correction_main_layout.addWidget(measurement_match_group)

		# Add a Plot button below the measurement_match_group (if desired, below the graph)
		self.corr_plot_button = QPushButton("Plot")
		self.corr_plot_button.clicked.connect(self.plot_loaded_correction_files)
		correction_main_layout.addWidget(self.corr_plot_button)

		graph_and_knob_layout = QHBoxLayout()
		self.corrFigure = pg.PlotWidget()
		setup_blankcanvas(self.corrFigure)
		graph_and_knob_layout.addWidget(self.corrFigure, stretch=3)
		# Knob Manager group
		self.knob_manager_group = QGroupBox("Knob Manager")
		knob_manager_layout = QVBoxLayout()
		self.knob_widgets = {}
		self.update_knobs_button = QPushButton("Update Knobs and Re-Plot")
		self.update_knobs_button.clicked.connect(self.update_knobs_and_replot)
		knob_manager_layout.addWidget(self.update_knobs_button)
		self.knob_manager_group.setLayout(knob_manager_layout)
		graph_and_knob_layout.addWidget(self.knob_manager_group)
		correction_main_layout.addLayout(graph_and_knob_layout, stretch=1)

		# Progress bar for correction tab remains below everything
		self.simcorr_progress = QProgressBar()
		self.simcorr_progress.setRange(0, 0)
		self.simcorr_progress.hide()
		self.layout.addWidget(self.simcorr_progress)

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
		Open a file dialog to select the LHCB1 model directory, starting from the default input path.
		"""
		modelpath = QFileDialog.getExistingDirectory(self, "Select LHCB1 Model", self.default_input_path)
		if modelpath:
			self.beam1_model_entry.setText(modelpath)
		
	def select_beam2_model(self):
		"""
		Open a file dialog to select the LHCB2 model directory, starting from the default input path.
		"""
		modelpath = QFileDialog.getExistingDirectory(self, "Select LHCB2 Model", self.default_input_path)
		if modelpath:
			self.beam2_model_entry.setText(modelpath)

	def select_singleitem(self, beam, title_text, filter_text, b1entry, b2entry, folder=False):
		"""
		Open a file dialog to select the reference measurement folder for the specified beam.
		"""
		dialog = QFileDialog(self)
		dialog.setWindowTitle(title_text)
		dialog.setDirectory(self.default_input_path)
		if folder:
			dialog.setFileMode(QFileDialog.Directory)
			dialog.setOption(QFileDialog.ShowDirsOnly, True)
		else:
			dialog.setFileMode(QFileDialog.ExistingFiles)
		dialog.setNameFilter(filter_text)
		if dialog.exec_() == QFileDialog.Accepted:
			folderpath = dialog.selectedFiles()[0]
			if beam == "LHCB1":
				b1entry.setText(folderpath)
			else:
				b2entry.setText(folderpath)

	def remove_singlefolder(self, beam, b1entry, b2entry):
		"""
		Clear the reference folder entry for the specified beam.
		"""
		if beam == "LHCB1":
			b1entry.clear()
		else:
			b2entry.clear()

	def validate_knob_button_clicked(self):
		"""
		Validate the knob when the "Validate Knob" button is clicked.
		"""
		knob = self.knob_entry.text()
		if not knob:
			QMessageBox.critical(self, "Error", "Knob field must be filled!")
			return
		is_valid_knob, knob_message = validate_knob(initialize_statetracker(), knob)
		if is_valid_knob:
			QMessageBox.information(self, "Knob Validation", "Knob is valid. Setting: " + repr(knob_message))
		else:
			QMessageBox.critical(self, "Knob Validation", "Invalid Knob: " + repr(knob_message))

	def run_analysis(self):
		# Divide heavy processing into steps for better UI responsiveness:
		self.current_step = 0
		self.analysis_steps = [
			self.analysis_step1,  # e.g., initialization and first data processing
			self.analysis_step2,  # e.g., fitting/BPM processing
			self.analysis_step3,   # e.g., fitting/BPM processing
			self.analysis_step4,  # e.g., writing output files
		]
		self.run_next_step()

	def update_validation_files_widget(self):
		# Update the validation_files_list widget with analysis_output_files
		for f in self.analysis_output_files:
			if f not in [self.validation_files_list.item(i).text() for i in range(self.validation_files_list.count())]:
				self.validation_files_list.addItem(f)

	def run_next_step(self):
		try:
			if self.current_step < len(self.analysis_steps):
				self.analysis_steps[self.current_step]()  # execute current step
				self.current_step += 1
				QTimer.singleShot(0, self.run_next_step)     # schedule next step ASAP
			else:
				self.update_validation_files_widget()  # show analysis output files in the widget
				QMessageBox.information(self, "Run Analysis", "Analysis completed successfully!")
		except Exception as e:
			self.input_progress.hide()
			QMessageBox.critical(self, "Analysis Error", f"Step {self.current_step+1} failed: {e}")

	def analysis_step1(self):
		self.input_progress.show()
		QtWidgets.QApplication.processEvents()
		# Initialize variables and validate inputs
		if self.simulation_checkbox.isChecked():
			self.ldb = None
		else:
			self.ldb = initialize_statetracker()
		self.rdt = self.rdt_entry.text()
		self.rdt_plane = self.rdt_plane_dropdown.currentText()
		is_valid_rdt, rdt_message = validate_rdt_and_plane(self.rdt, self.rdt_plane)
		if not is_valid_rdt:
			QMessageBox.critical(self, "Error", "Invalid RDT: " + repr(rdt_message))
			self.input_progress.hide()
			return
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
		# Process LHCB1 data
		if self.beam1_model and self.beam1_folders:
			b1modelbpmlist, b1bpmdata = getmodelBPMs(self.beam1_model)
			self.b1rdtdata = getrdt_omc3(self.ldb, "b1", b1modelbpmlist, b1bpmdata,
										  self.beam1_reffolder, self.beam1_folders,
										  self.knob, self.rdt, self.rdt_plane, 
										  self.rdtfolder,
										  self.simulation_checkbox.isChecked(), 
										  self.simulation_file_entry.text(),
										  self.log_error)
			self.b1rdtdata = fit_BPM(self.b1rdtdata)

	def analysis_step3(self):
		# Process LHCB2 data and write output files:
		if self.beam2_model and self.beam2_folders:
			b2modelbpmlist, b2bpmdata = getmodelBPMs(self.beam2_model)
			self.b2rdtdata = getrdt_omc3(self.ldb, "b2", b2modelbpmlist, b2bpmdata,
										  self.beam2_reffolder, self.beam2_folders,
										  self.knob, self.rdt, self.rdt_plane, 
										  self.rdtfolder, 
										  self.simulation_checkbox.isChecked(), 
										  self.simulation_file_entry.text(),
										  self.log_error)
			self.b2rdtdata = fit_BPM(self.b2rdtdata)
	
	def analysis_step4(self):			
		# Prompt to save LHCB1 RDT data just before calling write_RDTshifts
		self.analysis_output_files = []
		if self.beam1_model and self.beam1_folders:
			self.save_b1_rdtdata()
			# write_RDTshifts(self.b1rdtdata, self.rdt, self.rdt_plane, "b1", self.output_path, self.log_error)
		if self.beam2_model and self.beam2_folders:
			self.save_b2_rdtdata()
			# write_RDTshifts(self.b2rdtdata, self.rdt, self.rdt_plane, "b2", self.output_path, self.log_error)

		loaded_output_data = []
		self.loaded_files_list.clear()
		for f in self.analysis_output_files:
			if f not in [self.loaded_files_list.item(i).text() for i in range(self.loaded_files_list.count())]:
				self.loaded_files_list.addItem(f)
			data = load_RDTdata(f)
			loaded_output_data.append(data)
		results = group_datasets(loaded_output_data, self.log_error)
		if len(results) < 4:
			QMessageBox.critical(self, "Error", "Not enough data from group_datasets.")
			self.input_progress.hide()
			return
		self.b1rdtdata, self.b2rdtdata, self.rdt, self.rdt_plane = results
		if self.b1rdtdata is None and self.b2rdtdata is None:
			self.loaded_files_list.clear()
			self.input_progress.hide()
			return
		self.input_progress.hide()

	def log_error(self, error_msg):
		QMessageBox.critical(self, "Error", error_msg)

	def toggle_select_all_validation_files(self, state):
		"""
		Toggle selection for all items in the validation files list based on the checkbox state.
		"""
		for i in range(self.validation_files_list.count()):
			self.validation_files_list.item(i).setSelected(state == Qt.Checked)
	
	def select_multiple_files(self, list_widget, title="Select Files", filter="JSON Files (*.json)"):
		"""
		Allow the user to select multiple files and add them to the file list widget.
		"""
		dialog = QFileDialog(self)
		dialog.setWindowTitle(title)
		dialog.setDirectory(self.default_input_path)  # Use default output path, adjust if needed
		dialog.setFileMode(QFileDialog.ExistingFiles)
		dialog.setNameFilter(filter)

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
					item = QtWidgets.QListWidgetItem(file)
					item.setSelected(True)
					list_widget.addItem(item)
		return dialog.selectedFiles()

	def select_multiple_treefiles(self, tree_widget, title="Select Files", filter="JSON Files (*.json)"):
		"""
		Allow the user to select multiple files and add them to the file tree widget.
		"""
		dialog = QFileDialog(self)
		dialog.setWindowTitle(title)
		dialog.setDirectory(self.default_input_path)  # Use default output path, adjust if needed
		dialog.setFileMode(QFileDialog.ExistingFiles)
		dialog.setNameFilter(filter)

		# Enable multiple selection in the dialog
		for view in dialog.findChildren((QtWidgets.QListView, QtWidgets.QTreeView)):
			if isinstance(view.model(), QtWidgets.QFileSystemModel):
				view.setSelectionMode(QtWidgets.QAbstractItemView.ExtendedSelection)

		if dialog.exec_() == QFileDialog.Accepted:
			selected_files = dialog.selectedFiles()
			existing_files = [
				tree_widget.topLevelItem(i).text(0)  # Get the filename from the first column
				for i in range(tree_widget.topLevelItemCount())
			]
			for file in selected_files:
				if file not in existing_files:
					self.corr_responses[file] = load_RDTdata(file)
					self.rdt = self.corr_responses[file].get("metadata", {}).get("rdt", "Unknown RDT")
					self.rdt_plane = self.corr_responses[file].get("metadata", {}).get("rdt_plane", "Unknown Plane")
					self.corrector = self.corr_responses[file].get("metadata", {}).get("knob_name", "Unknown Corrector")
					item = QtWidgets.QTreeWidgetItem([file, self.rdt, self.rdt_plane, self.corrector])
					tree_widget.addTopLevelItem(item)
		return dialog.selectedFiles()

	def select_analysis_files(self):
		selected_files = self.select_multiple_files(self.validation_files_list, "Select Analysis Files")
		if self.validation_files_list.count() > 0:
			reply = QMessageBox.question(
				self, 
				"Load Files?", 
				"Would you like to load these files now?", 
				QMessageBox.Yes | QMessageBox.No
			)
			if reply == QMessageBox.Yes:
				loaded_output_data = []
				self.loaded_files_list.clear()
				for file in selected_files:
					self.loaded_files_list.addItem(file)
					data = load_RDTdata(file)
					loaded_output_data.append(data)
				results = group_datasets(loaded_output_data, self.log_error)
				if len(results) < 4:
					QMessageBox.critical(self, "Error", "Not enough data from group_datasets.")
					return
				self.b1rdtdata, self.b2rdtdata, self.rdt, self.rdt_plane = results
				if self.b1rdtdata is None and self.b2rdtdata is None:
					self.loaded_files_list.clear()
					return

	def search_bpm(self):
		search_term = self.bpm_search_entry.text().strip()
		if not search_term:
			QMessageBox.information(self, "BPM Search", "No BPM specified.")
			return
		beam = self.beam_selector.currentText()
		if beam == "LHCB1":
			data = getattr(self, 'b1rdtdata', None)
		else:
			data = getattr(self, 'b2rdtdata', None)
		if data is None:
			QMessageBox.information(self, "BPM Search", f"No data available for {beam}.")
			return
		if search_term in data["data"]:
			QMessageBox.information(self, "BPM Search", f"Found BPM '{search_term}' in {beam}.")
		else:
			QMessageBox.information(self, "BPM Search", f"BPM '{search_term}' not found in {beam}.")

	def graph_bpm(self):
		BPM = self.bpm_search_entry.text().strip()
		if not BPM:
			QMessageBox.information(self, "BPM Graph", "No BPM specified.")
			return
		beam = self.beam_selector.currentText()
		data = getattr(self, 'b1rdtdata', None) if beam == "LHCB1" else getattr(self, 'b2rdtdata', None)
		if data is None:
			QMessageBox.information(self, "BPM Graph", f"No data available for {beam}.")
			return
		# Search for the BPM in the data before plotting (assuming data["data"] holds BPM keys)
		if BPM not in data.get("data", {}):
			QMessageBox.information(self, "BPM Graph", f"BPM '{BPM}' not found in {beam}.")
			return
		(ax1, ax2), grid = self.setup_figure(self.bpmWidget, data, None, 2)
		plot_BPM(BPM, data, self.rdt, self.rdt_plane, ax1=ax1, ax2=ax2, log_func=self.log_error)
		self.plot_progress.hide()
	
	def save_b1_rdtdata(self):
		filename, _ = QFileDialog.getSaveFileName(
			self,
			"Save LHCB1 RDT Data",
			self.default_output_path,
			"JSON Files (*.json)"
		)
		if filename:
			if not filename.lower().endswith(".json"):
				filename += ".json"
			save_RDTdata(self.b1rdtdata, filename)
			self.analysis_output_files.append(filename)

	def save_b2_rdtdata(self):
		filename, _ = QFileDialog.getSaveFileName(
			self,
			"Save LHCB2 RDT Data",
			self.default_output_path,
			"JSON Files (*.json)"
		)
		if filename:
			if not filename.lower().endswith(".json"):
				filename += ".json"
			save_RDTdata(self.b2rdtdata, filename)
			self.analysis_output_files.append(filename)

	def load_selected_files(self):
		self.plot_progress.show()
		QtWidgets.QApplication.processEvents()
		# Load selected file paths from the validation files list into the loaded files list
		selected_files = [self.validation_files_list.item(i).text() for i in range(self.validation_files_list.count()) 
						if self.validation_files_list.item(i).isSelected()]
		self.loaded_files_list.clear()
		loaded_output_data = []
		for file in selected_files:
			self.loaded_files_list.addItem(file)
			data = load_RDTdata(file)
			loaded_output_data.append(data)
		results = group_datasets(loaded_output_data, self.log_error)
		if len(results) < 4:
			QMessageBox.critical(self, "Error", "Not enough data from group_datasets.")
			return
		self.b1rdtdata, self.b2rdtdata, self.rdt, self.rdt_plane = results
		if self.b1rdtdata is None and self.b2rdtdata is None:
			self.loaded_files_list.clear()
			return

	def update_bpm_search_entry(self):
		# Set default BPM value based on the selected beam.
		if self.beam_selector.currentText() == "LHCB1":
			self.bpm_search_entry.setText("BPM.30L2.B1")
		else:
			self.bpm_search_entry.setText("BPM.30L1.B2")

	def get_selected_validation_files(self):
		return [
			self.validation_files_list.item(i).text()
			for i in range(self.validation_files_list.count())
			if self.validation_files_list.item(i).isSelected()
		]

	def plot_rdt(self):
		self.plot_progress.show()
		QtWidgets.QApplication.processEvents()
		datab1, datab2 = None, None
		try:
			datab1 = self.b1rdtdata["data"]
		except Exception as e:
			self.log_error(f"Error accessing LHCB1 RDT data: {e}")
		try:
			datab2 = self.b2rdtdata["data"]
		except Exception as e:
			self.log_error(f"Error accessing LHCB2 RDT data: {e}")

		self.rdt_axes, self.rdt_axes_layout = self.setup_figure(self.rdtWidget, datab1, datab2, 3)
		
		try:
			plot_RDT(datab1, datab2, self.rdt, self.rdt_plane, self.rdt_axes, log_func=self.log_error)
		except Exception as e:
			self.log_error(f"Error plotting RDT data: {e}")
			self.plot_progress.hide()
			return
		self.plot_progress.hide()

	def plot_rdt_shifts(self):
		self.plot_progress.show()
		QtWidgets.QApplication.processEvents()
		datab1, datab2 = None, None
		try:
			datab1 = self.b1rdtdata["data"]
		except Exception as e:
			self.log_error(f"Error accessing LHCB1 RDT data: {e}")
		try:
			datab2 = self.b2rdtdata["data"]
		except Exception as e:
			self.log_error(f"Error accessing LHCB2 RDT data: {e}")

		self.rdtshift_axes, self.rdtshift_axes_layout = self.setup_figure(self.rdtShiftwidget, datab1, datab2, 3)

		try:
			plot_RDTshifts(datab1, datab2, self.rdt, self.rdt_plane, self.rdtshift_axes, log_func=self.log_error)
		except Exception as e:
			self.log_error(f"Error plotting RDT shifts: {e}")
			self.plot_progress.hide()
			return
		self.plot_progress.hide()

	# New method to toggle simulation mode UI changes
	def toggle_simulation_mode(self, state):
		if state == Qt.Checked:
			self.knob_entry.hide()
			self.knob_label.hide()
			self.validate_knob_button.hide()
			self.simulation_file_entry.show()
			self.simulation_file_button.show()
		else:
			self.knob_entry.show()
			self.knob_label.show()
			self.validate_knob_button.show()
			self.simulation_file_entry.hide()
			self.simulation_file_button.hide()

	# New method to select a properties file
	def select_properties_file(self):
		filename, _ = QFileDialog.getOpenFileName(
			self, "Select Properties File", self.default_input_path, "Properties Files (*.csv);;All Files (*)"
		)
		if filename:
			self.simulation_file_entry.setText(filename)

	def _select_folders(self, name_filter, list_widget):
		dialog = QFileDialog(self)
		dialog.setOption(QFileDialog.DontUseNativeDialog, True)
		dialog.setFileMode(QFileDialog.Directory)
		dialog.setOption(QFileDialog.ShowDirsOnly, True)
		dialog.setDirectory(self.default_input_path)
		dialog.setNameFilter(name_filter)
		for view in dialog.findChildren((QtWidgets.QListView, QtWidgets.QTreeView)):
			if isinstance(view.model(), QtWidgets.QFileSystemModel):
				view.setSelectionMode(QtWidgets.QAbstractItemView.ExtendedSelection)
		if dialog.exec_() == QFileDialog.Accepted:
			selected_dirs = dialog.selectedFiles()
			for directory in selected_dirs:
				if directory not in [list_widget.item(i).text() for i in range(list_widget.count())]:
					list_widget.addItem(directory)

	def remove_selected_items(self, widget, corr_responses=False):
		"""
		Remove selected items from either a QListWidget or QTreeWidget.
		Optionally delete corresponding entries in corr_responses.
		"""
		if isinstance(widget, QtWidgets.QListWidget):
			# Handle QListWidget
			for item in widget.selectedItems():
				if corr_responses:
					filename = item.text()  # Get the filename from the list widget item
					if filename in self.corr_responses:
						del self.corr_responses[filename]
				widget.takeItem(widget.row(item))
		elif isinstance(widget, QtWidgets.QTreeWidget):
			# Handle QTreeWidget
			for item in widget.selectedItems():
				if corr_responses:
					filename = item.text(0)  # Get the filename from the first column
					if filename in self.corr_responses:
						del self.corr_responses[filename]
				index = widget.indexOfTopLevelItem(item)
				widget.takeTopLevelItem(index)
		else:
			self.log_error("Unsupported widget type for remove_selected_items.")
			raise TypeError("Unsupported widget type. Only QListWidget and QTreeWidget are supported.")

	def _toggle_select_all(self, widget, state):
		"""
		Toggle selection for all items in either a QTreeWidget or QListWidget based on the checkbox state.
		"""
		if isinstance(widget, QtWidgets.QTreeWidget):
			# Handle QTreeWidget
			for i in range(widget.topLevelItemCount()):
				widget.topLevelItem(i).setSelected(state == Qt.Checked)
		elif isinstance(widget, QtWidgets.QListWidget):
			# Handle QListWidget
			for i in range(widget.count()):
				widget.item(i).setSelected(state == Qt.Checked)
		else:
			self.log_error("Unsupported widget type for toggle_select_all.")
			raise TypeError("Unsupported widget type. Only QTreeWidget and QListWidget are supported.")

	def select_beam1_folders(self):
		self._select_folders("Beam1BunchTurn (Beam1BunchTurn*);;All Folders (*)", self.beam1_folders_list)

	def select_beam2_folders(self):
		self._select_folders("Beam2BunchTurn (Beam2BunchTurn)*;;All Folders (*)", self.beam2_folders_list)

	def remove_selected_beam1_folders(self):
		self.remove_selected_items(self.beam1_folders_list)

	def remove_selected_beam2_folders(self):
		self.remove_selected_items(self.beam2_folders_list)

	def toggle_select_all_beam1_folders(self, state):
		self._toggle_select_all(self.beam1_folders_list, state)

	def toggle_select_all_beam2_folders(self, state):
		self._toggle_select_all(self.beam2_folders_list, state)

	def run_response(self):
		self.simcorr_progress.show()
		QtWidgets.QApplication.processEvents()
		# self.corr_b1_reffile = self.corr_beam1_reffolder_entry.text()
		# self.corr_b2_reffile = self.corr_beam2_reffolder_entry.text()
		# self.corr_b1_measfile = self.corr_beam1_measfolder_entry.text()
		# self.corr_b2_measfile = self.corr_beam2_measfolder_entry.text()
		self.corr_responses = {}
		filenameb1 = ""
		filenameb2 = ""
		# Debugging logs
		self.corr_b1_reffile = "/afs/cern.ch/work/s/sahorney/private/LHCoptics/2025_03_a4corr/2025-04-03/LHCB1/Results/trackone_b1_R5_0.sdds"
		self.corr_b2_reffile = "/afs/cern.ch/work/s/sahorney/private/LHCoptics/2025_03_a4corr/2025-04-03/LHCB2/Results/trackone_b2_R5_0.sdds"
		self.corr_b1_measfile = "/afs/cern.ch/work/s/sahorney/private/LHCoptics/2025_03_a4corr/2025-04-03/LHCB1/Results/trackone_b1_R5_160.sdds"
		self.corr_b2_measfile = "/afs/cern.ch/work/s/sahorney/private/LHCoptics/2025_03_a4corr/2025-04-03/LHCB2/Results/trackone_b2_R5_160.sdds"
		# Updated knob assignment based on b1andb2same_checkbox toggle
		# if self.b1andb2same_checkbox.isChecked():
		# 	self.b1_corr_knobname = self.corr_knobname_entry.text()
		# 	self.b2_corr_knobname = self.corr_knobname_entry.text()
		# 	self.b1_corr_knob = self.corr_knob_entry.text()
		# 	self.b2_corr_knob = self.corr_knob_entry.text()
		# 	self.b1_corr_xing = self.corr_xing_entry.text()
		# 	self.b2_corr_xing = self.corr_xing_entry.text()
		# else:
		# 	self.b1_corr_knobname = self.b1_corr_knobname_entry.text()
		# 	self.b1_corr_knob = self.b1_corr_knob_entry.text()
		# 	self.b2_corr_knobname = self.b2_corr_knobname_entry.text()
		# 	self.b2_corr_knob = self.b2_corr_knob_entry.text() 
		# 	self.b1_corr_xing = self.b1_corr_xing_entry.text()
		# 	self.b2_corr_xing = self.b2_corr_xing_entry.text()
		# self.rdt = self.corr_rdt_entry.text()
		# self.rdt_plane = self.corr_rdt_plane_dropdown.currentText()
		# self.rdtfolder = rdt_to_order_and_type(self.rdt)
		self.b1_corr_knobname = "MCOSX_R5"
		self.b1_corr_knob = "2"
		self.b2_corr_knobname = "MCOSX_R5"
		self.b2_corr_knob = "2" 
		self.b1_corr_xing = "160"
		self.b2_corr_xing = "160"
		self.rdt = "1020"
		self.rdt_plane = "x"
		self.rdtfolder = rdt_to_order_and_type(self.rdt)
		is_valid_rdt, rdt_message = validate_rdt_and_plane(self.rdt, self.rdt_plane)
		if not is_valid_rdt:
			QMessageBox.critical(self, "Error", "Invalid RDT: " + repr(rdt_message))
			self.simcorr_progress.hide()
			return
		# if self.corr_b1_reffile and self.corr_b1_measfile:
		# 	filenameb1, _ = QFileDialog.getSaveFileName(
		# 		self,
		# 		"Save LHCB1 RDT Data",
		# 		self.default_output_path,
		# 		"JSON Files (*.json)"
		# 	)
		# if self.corr_b2_reffile and self.corr_b2_measfile:
		# 	filenameb2, _ = QFileDialog.getSaveFileName(
		# 		self,
		# 		"Save LHCB2 RDT Data",
		# 		self.default_output_path,
		# 		"JSON Files (*.json)"
		# 	)
		filenameb1 =  "/afs/cern.ch/work/s/sahorney/private/LHCoptics/2025_03_a4corr/b1_MCOSX_R5.json"
		filenameb2 =  "/afs/cern.ch/work/s/sahorney/private/LHCoptics/2025_03_a4corr/b2_MCOSX_R5.json"
		if filenameb1 == "" and filenameb2 == "":
			self.log_error("No output file selected.")
			self.simcorr_progress.hide()
			return

		if filenameb1:
			if not filenameb1.lower().endswith(".json"):
				filenameb1 += ".json"
			try:
				b1response = getrdt_sim("LHCB1", self.corr_b1_reffile, self.corr_b1_measfile, self.b1_corr_xing, 
				self.b1_corr_knobname, self.b1_corr_knob, self.rdt, self.rdt_plane, self.rdtfolder, 
				log_func=self.log_error)
				self.corr_responses[filenameb1] = b1response
				save_RDTdata(b1response, filenameb1)
				item = QtWidgets.QTreeWidgetItem([filenameb1, self.rdt, self.rdt_plane, self.b1_corr_knobname])
				self.correction_loaded_files_list.addTopLevelItem(item)
				self.populate_knob_manager()
			except Exception as e:
				self.log_error(f"Error in getting RDT: {e}")
		if filenameb2:
			if not filenameb2.lower().endswith(".json"):
				filenameb2 += ".json"
			try:
				b2response = getrdt_sim("LHCB2", self.corr_b2_reffile, self.corr_b2_measfile, self.b2_corr_xing, 
				self.b2_corr_knobname, self.b2_corr_knob, self.rdt, self.rdt_plane, self.rdtfolder, 
				log_func=self.log_error)
				self.corr_responses[filenameb2] = b2response
				save_RDTdata(b2response, filenameb2)
				item = QtWidgets.QTreeWidgetItem([filenameb2, self.rdt, self.rdt_plane, self.b2_corr_knobname])
				self.correction_loaded_files_list.addTopLevelItem(item)
				self.populate_knob_manager()
			except Exception as e:
				self.log_error(f"Error in getting RDT: {e}")
		self.simcorr_progress.hide()

	def toggle_b1andb2same_mode(self, state):
		is_checked = (state == Qt.Checked)
		 # For sections with separate knob fields, only toggle if they exist.

		self.b1_corr_knobname_label.setVisible(not is_checked)
		self.b1_corr_knobname_entry.setVisible(not is_checked)
		self.b1_corr_knob_label.setVisible(not is_checked)
		self.b1_corr_knob_entry.setVisible(not is_checked)
		self.b1_corr_xing_label.setVisible(not is_checked)
		self.b1_corr_xing_entry.setVisible(not is_checked)
		self.b2_corr_knobname_label.setVisible(not is_checked)
		self.b2_corr_knobname_entry.setVisible(not is_checked)
		self.b2_corr_knob_label.setVisible(not is_checked)
		self.b2_corr_knob_entry.setVisible(not is_checked)
		self.b2_corr_xing_label.setVisible(not is_checked)
		self.b2_corr_xing_entry.setVisible(not is_checked)
		# Always toggle the unified fields in the correction parameters layout
		self.corr_knobname_entry_label.setVisible(is_checked)
		self.corr_knobname_entry.setVisible(is_checked)
		self.corr_knob_entry_label.setVisible(is_checked)
		self.corr_knob_entry.setVisible(is_checked)
		self.corr_xing_entry_label.setVisible(is_checked)
		self.corr_xing_entry.setVisible(is_checked)

	# New method to toggle the Correction content visibility
	def toggle_correction_content(self):
		visible = self.corr_toggle_button.isChecked()
		self.correction_content.setVisible(visible)
		if visible:
			self.corr_toggle_button.setArrowType(Qt.DownArrow)
			self.corr_toggle_button.setText("Collapse Section")
		else:
			self.corr_toggle_button.setArrowType(Qt.RightArrow)
			self.corr_toggle_button.setText("Expand Section")

	# NEW: New method to plot loaded correction files into the unified graph widget
	def plot_loaded_correction_files(self):
		self.corr_toggle_button.setChecked(False)
		self.correction_content.setVisible(False)
		self.corr_toggle_button.setArrowType(Qt.RightArrow)
		self.corr_toggle_button.setText("Expand Section")
		self.simcorr_progress.show()
		QtWidgets.QApplication.processEvents()
		self.b1_response_meas = None
		self.b2_response_meas = None
		# try:
		# 	self.b1_response_meas = load_RDTdata(self.b1_match_entry.text())
		# except Exception as e:
		# 	self.log_error(f"Error loading LHCB1 response measurement: {e}")
		# try:
		# 	self.b2_response_meas = load_RDTdata(self.b2_match_entry.text())
		# except Exception as e:
		# 	self.log_error(f"Error loading LHCB2 response measurement: {e}")

		self.b1_response_meas = load_RDTdata("/afs/cern.ch/work/s/sahorney/private/LHCoptics/2025_03_a4corr/b1_xingsim.json")
		self.b2_response_meas = load_RDTdata("/afs/cern.ch/work/s/sahorney/private/LHCoptics/2025_03_a4corr/b2_xingsim.json")
		QtWidgets.QApplication.processEvents()
		if not self.b1_response_meas and not self.b2_response_meas:
			self.log_error("No data loaded for reference measurement.")
			self.simcorr_progress.hide()
			return
		if self.b1_response_meas:
			if (
				self.b1_response_meas.get('metadata', {}).get('rdt') == self.rdt and
				self.b1_response_meas.get('metadata', {}).get('rdt_plane') == self.rdt_plane
			):
				self.b1_response_meas['data'] = {
					key: value for key, value in self.b1_response_meas['data'].items()
				}
			else:
				self.b1_response_meas['data'] = {}  # Clear data if metadata doesn't match
		if self.b2_response_meas:
			if (
				self.b2_response_meas.get('metadata', {}).get('rdt') == self.rdt and
				self.b2_response_meas.get('metadata', {}).get('rdt_plane') == self.rdt_plane
			):
				self.b2_response_meas['data'] = {
					key: value for key, value in self.b2_response_meas['data'].items()
				}
			else:
				self.b2_response_meas['data'] = {}
		if not self.b1_response_meas and not self.b2_response_meas:
			self.b1_match_entry.clear()
			self.b2_match_entry.clear()
			self.log_error("No data loaded for reference measurement.")
			self.simcorr_progress.hide()
			return
		if self.b1andb2same_checkbox.isChecked():
			if not self.b1_response_meas or not self.b2_response_meas:
				self.log_error("Both beams must be loaded for reference measurement.")

		for plot_widget in getattr(self, 'corr_axes', []):
			plot_widget.clear()
		self.b1data, self.b2data = None, None
		try:
			self.b1data = {
				file: response
				for file, response in self.corr_responses.items()
				if "LHCB1" in response.get("metadata", {}).get('beam')
			}
		except Exception as e:
			self.log_error(f"Error extracting LHCB1 data: {e}")
		try:
			self.b2data = {
				file: response
				for file, response in self.corr_responses.items()
				if "LHCB2" in response.get("metadata", {}).get("beam", "")
			}
		except Exception as e:
			self.log_error(f"Error extracting LHCB2 data: {e}")
		if self.b1andb2same_checkbox.isChecked():
			if self.b1data is None or self.b2data is None:
				self.log_error("Both beams must be loaded for reference measurement.")
				self.simcorr_progress.hide()
				return

		self.corr_axes, grid = self.setup_figure(self.corrFigure, self.b1data, self.b2data, 2)
		QtWidgets.QApplication.processEvents()

		def both_plot():
			plot_dRDTdknob(self.b1_response_meas, self.b2_response_meas, self.rdt, self.rdt_plane,
							self.corr_axes, log_func=self.log_error)
			for ax in self.corr_axes:
				ax.getViewBox().enableAutoRange(False)
				y_min, y_max = ax.viewRange()[1]
				ax.setYRange(y_min, y_max)
			plot_dRDTdknob(self.b1data, self.b2data, self.rdt, self.rdt_plane, 
							self.corr_axes, self.knob_widgets.items(), 
							log_func=self.log_error)

		both_plot()
		QtWidgets.QApplication.processEvents()

		self.simcorr_progress.hide()

	def load_selected_correction_files(self):
		self.simcorr_progress.show()
		if not hasattr(self, 'corr_responses') or self.corr_responses is None:
			self.corr_responses = {}

		selected_files = self.select_multiple_treefiles(self.correction_loaded_files_list, title="Select Response Files")
		# Validate metadata and update the UI
		samemetadata, metadata = validate_metas(self.corr_responses)
		if samemetadata:
			for file in selected_files:
				if file not in self.corr_responses.keys():
					self.corr_responses[file] = load_RDTdata(file)
			self.populate_knob_manager()
			self.simcorr_progress.hide()
		else:
			self.log_error("Metadata differs so not loading data.")
			self.simcorr_progress.hide()

	def populate_knob_manager(self):
		"""
		Extract knobnames from metadata and create fields for the user to edit knob values.
		"""
		layout = self.knob_manager_group.layout()
		# Clear old input fields
		for i in reversed(range(layout.count() - 1)):  # leave update button
			item = layout.itemAt(i).widget()
			if item:
				item.deleteLater()
		self.knob_widgets.clear()
		# Gather all knobs from loaded metadata
		all_knobs = set()
		for file, response in self.corr_responses.items():
			meta = response.get("metadata", {})
			knobname = meta.get("knob_name")
			if knobname:
				all_knobs.add(knobname)
		# Create QLineEdit for each knob
		for knobname in all_knobs:
			row_container = QWidget()
			row_layout = QHBoxLayout(row_container)
			label = QLabel(f"{knobname}")
			val_input = QLineEdit("0")  # default
			self.knob_widgets[knobname] = val_input
			row_layout.addWidget(label)
			row_layout.addWidget(val_input)
			layout.insertWidget(layout.count() - 1, row_container)

	def update_knobs_and_replot(self):
		"""
		Read knob edits, apply them, and replot using these values.
		"""
		self.simcorr_progress.show()

		for ax in self.corr_axes:
			for item in ax.listDataItems():
				print(item, item.name())
				if hasattr(item, 'name') and item.name() == 'Simulation':
					ax.removeItem(item)
		plot_dRDTdknob(self.b1data, self.b2data, self.rdt, self.rdt_plane, self.corr_axes, self.knob_widgets.items(), 
								log_func=self.log_error)
		self.simcorr_progress.hide()


	def setup_figure(self, container, b1data, b2data, rows):
		"""
		Set up the container with subplots using pyqtgraph.
		Safely removes any previous layout before setting up a new one.
		"""
		clear_layout(container)
		# Create a new QGridLayout for subplots.
		grid = QGridLayout()
		grid.setSpacing(20)
		grid.setContentsMargins(5, 5, 5, 5)
		container.setLayout(grid)
		axes = []

		# Create the subplots based on available data.
		if b1data and b2data:
			# Create a 2x2 grid of subplots.
			axes = []
			for row in range(rows):
				for col in range(2):
					# Create a PlotWidget with a custom ViewBox.
					view_box = MyViewBox()
					plot_widget = pg.PlotWidget(viewBox=view_box)
					plot_widget.setBackground('w')
					plot_widget.showGrid(x=True, y=True)
					grid.addWidget(plot_widget, row, col)
					axes.append(plot_widget)
					view_box.setMouseMode(pg.ViewBox.RectMode)  # Enable click-and-drag zoom
					view_box.menu = None  # Disable default context menu
		else:
			# Create a 2x1 grid of subplots.
			axes = []
			for row in range(rows):
				view_box = MyViewBox()
				plot_widget = pg.PlotWidget(viewBox=view_box)
				plot_widget.setBackground('w')
				plot_widget.showGrid(x=True, y=True)
				grid.addWidget(plot_widget, row, 0)
				axes.append(plot_widget)
				view_box.setMouseMode(pg.ViewBox.RectMode)  # Enable click-and-drag zoom
				view_box.menu = None  # Disable default context menu
		QtWidgets.QApplication.processEvents()  # Force the UI to update.
		return axes, grid

	def reset_zoom_on_right_click(self, event, axes):
		"""
		Reset zoom when the right mouse button is clicked.
		"""
		if event.button() == Qt.RightButton:
			for plot_widget in axes:
				plot_widget.getViewBox().autoRange()