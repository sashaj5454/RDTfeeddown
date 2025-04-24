import json
import traceback
from qtpy.QtWidgets import (
	QApplication, QMainWindow, QGridLayout, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton, QCheckBox,
	QFileDialog, QListWidget, QTabWidget, QWidget, QMessageBox, QProgressBar, QSizePolicy, QGroupBox, QComboBox,
	QAbstractItemView, QTreeWidget, QTreeWidgetItem
)
import pyqtgraph as pg
from qtpy.QtCore import Qt   # Import Qt for the correct constants and QTimer
from .validation_utils import validate_knob, validate_metas, validate_file_structure
from .utils import load_defaults, initialize_statetracker, MyViewBox
from .analysis_runner import run_analysis, run_response
from .analysis import group_datasets
from .plotting import plot_BPM, plot_RDT, plot_RDTshifts, plot_dRDTdknob, setup_blankcanvas
from .file_dialog_helpers import select_singleitem, select_multiple_files, select_folders, select_multiple_treefiles
from .data_handler import load_selected_files, load_RDTdata
from .style import DARK_BACKGROUND_COLOR, plot_stylesheet, run_stylesheet, remove_stylesheet, b1_stylesheet, b2_stylesheet
from .customtitlebar import create_custom_title_bar, install_event_filters, enable_mouse_tracking
pg.setConfigOption('foreground', 'w')

class RDTFeeddownGUI(QMainWindow):
	def __init__(self):
		super().__init__()
		self.setWindowFlags(Qt.FramelessWindowHint | Qt.Window)
		self._resizing = False
		self._resize_margin = 8
		self._resize_direction = None
		# Main layout
		self.central_widget = QWidget()
		self.setCentralWidget(self.central_widget)
		self.layout = QVBoxLayout(self.central_widget)
		self.layout.setContentsMargins(0, 0, 0, 0)
		self.error_log = []
		# Add the custom title bar
		self.layout.addWidget(create_custom_title_bar(self))

		# Add the rest of the GUI
		self.tabs = QTabWidget()
		self.layout.addWidget(self.tabs)
		self.buildInputTab()
		self.buildValidationTab()
		self.buildCorrectionTab()
		self.setMouseTracking(True)
		self.central_widget.setMouseTracking(True)
		self.central_widget.installEventFilter(self)
		install_event_filters(self, self.central_widget)
		enable_mouse_tracking(self, self.central_widget)

	def buildPathsSection(self):
		# Load defaults from the special file
		config = load_defaults(self.log_error)
		self.default_input_path = config.get("default_input_path")
		self.default_output_path = config.get("default_output_path")
		paths_group = QGroupBox("Paths")
		paths_layout = QVBoxLayout()
		self.input_path_label = QLabel(f"Default Input Path: {self.default_input_path}")
		paths_layout.addWidget(self.input_path_label)
		self.change_input_path_button = QPushButton("Change Input Path")
		self.change_input_path_button.clicked.connect(self.change_default_input_path)
		self.change_input_path_button.setToolTip("Select the default input path for analysis files, see Help for how to set it before launch")
		paths_layout.addWidget(self.change_input_path_button)
		self.output_path_label = QLabel(f"Default Output Path: {self.default_output_path}")
		paths_layout.addWidget(self.output_path_label)
		self.change_output_path_button = QPushButton("Change Output Path")
		self.change_output_path_button.clicked.connect(self.change_default_output_path)
		self.change_output_path_button.setToolTip("Select the default output path for analysis files, see Help for how to set it before launch")
		paths_layout.addWidget(self.change_output_path_button)
		paths_group.setLayout(paths_layout)
		self.input_layout.addWidget(paths_group)

	def buildInputTab(self):
		# Add an attribute to store the list of analysis output files
		self.analysis_output_files = []

		# ===== Input Tab with separated sections =====
		self.input_tab = QWidget()
		self.tabs.addTab(self.input_tab, "Input")
		self.input_layout = QVBoxLayout(self.input_tab)
		self.buildPathsSection()

		# --- Beam Models Group ---
		beam_model_group = QGroupBox("Beam Model Selection")
		beam_model_layout = QHBoxLayout()
		# LHCB1
		beam1_layout = QVBoxLayout()
		self.beam1_model_label = QLabel("LHCB1 Model:")
		self.beam1_model_label.setStyleSheet(b1_stylesheet)
		beam1_layout.addWidget(self.beam1_model_label)
		self.beam1_model_entry = QLineEdit()
		beam1_layout.addWidget(self.beam1_model_entry)
		self.beam1_model_button = QPushButton("Select Model")
		self.beam1_model_button.clicked.connect(lambda: select_singleitem(self, "LHCB1",
													"Select LHCB1 Model",
													self.beam1_model_entry, None,
													folder=True))
		self.beam1_model_button.setToolTip("Select LHCB1 model folder - needed only for valid BPM list")
		beam1_layout.addWidget(self.beam1_model_button)
		beam_model_layout.addLayout(beam1_layout)
		# LHCB2
		beam2_layout = QVBoxLayout()
		self.beam2_model_label = QLabel("LHCB2 Model:")
		self.beam2_model_label.setStyleSheet(b2_stylesheet)
		beam2_layout.addWidget(self.beam2_model_label)
		self.beam2_model_entry = QLineEdit()
		beam2_layout.addWidget(self.beam2_model_entry)
		self.beam2_model_button = QPushButton("Select Model")
		self.beam2_model_button.clicked.connect(lambda: select_singleitem(self, "LHCB2",
													"Select LHCB2 Model",
													None, self.beam2_model_entry,
													folder=True))
		self.beam2_model_button.setToolTip("Select LHCB2 model folder - needed only for valid BPM list")
		beam2_layout.addWidget(self.beam2_model_button)
		beam_model_layout.addLayout(beam2_layout)
		beam_model_group.setLayout(beam_model_layout)
		self.input_layout.addWidget(beam_model_group)

		# --- Reference and Measurement Folders Group ---
		folders_group = QGroupBox("Reference and Measurement Folders")
		folders_layout = QVBoxLayout()

		# --- Ref Models Group ---
		ref_folders_group = QGroupBox("Reference Folders")
		ref_folders_layout = QHBoxLayout()

		# LHCB1 Reference Folder
		beam1_ref_layout = QVBoxLayout()
		self.beam1_reffolder_label = QLabel("LHCB1 Reference Measurement Folder:")
		self.beam1_reffolder_label.setStyleSheet(b1_stylesheet)
		beam1_ref_layout.addWidget(self.beam1_reffolder_label)
		self.beam1_reffolder_entry = QLineEdit()
		beam1_ref_layout.addWidget(self.beam1_reffolder_entry)
		beam1_buttons_layout = QHBoxLayout()
		self.beam1_reffolder_button = QPushButton("Select Folder")
		self.beam1_reffolder_button.clicked.connect(lambda: select_singleitem(self, "LHCB1",
													"Select LHCB1 Reference Measurement Folder",
													self.beam1_reffolder_entry, self.beam2_reffolder_entry,
													"LHCB1 folders (Beam1BunchTurn*);;All Folders (*)",
													folder = True))
		self.beam1_reffolder_button.setToolTip("Select LHCB1 OMC analysis folder to be used as the reference")
		beam1_buttons_layout.addWidget(self.beam1_reffolder_button)
		self.beam1_reffolder_remove_button = QPushButton("Remove File")
		self.beam1_reffolder_remove_button.setStyleSheet(remove_stylesheet)
		self.beam1_reffolder_remove_button.clicked.connect(lambda: self.remove_singlefolder("LHCB1",
													self.beam1_reffolder_entry, self.beam2_reffolder_entry))
		beam1_buttons_layout.addWidget(self.beam1_reffolder_remove_button)  # Added the remove button to the layout
		beam1_ref_layout.addLayout(beam1_buttons_layout)
		ref_folders_layout.addLayout(beam1_ref_layout)

		# LHCB2 Reference Folder
		beam2_ref_layout = QVBoxLayout()
		self.beam2_reffolder_label = QLabel("LHCB2 Reference Measurement Folder:")
		self.beam2_reffolder_label.setStyleSheet(b2_stylesheet)
		beam2_ref_layout.addWidget(self.beam2_reffolder_label)
		self.beam2_reffolder_entry = QLineEdit()
		beam2_ref_layout.addWidget(self.beam2_reffolder_entry)
		beam2_buttons_layout = QHBoxLayout()
		self.beam2_reffolder_button = QPushButton("Select Folder")
		self.beam2_reffolder_button.clicked.connect(lambda: select_singleitem(self, "LHCB2", 
													"Select LHCB2 Reference Measurement Folder", 
													self.beam1_reffolder_entry, self.beam2_reffolder_entry,
													"LHCB2 folders (Beam2BunchTurn*);;All Folders (*)",
													folder = True))
		self.beam2_reffolder_button.setToolTip("Select LHCB2 OMC analysis folder to be used as the reference")
		beam2_buttons_layout.addWidget(self.beam2_reffolder_button)
		self.beam2_reffolder_remove_button = QPushButton("Remove File")
		self.beam2_reffolder_remove_button.setStyleSheet(remove_stylesheet)
		self.beam2_reffolder_remove_button.clicked.connect(lambda: self.remove_singlefolder("LHCB2",
													self.beam1_reffolder_entry, self.beam2_reffolder_entry))
		beam2_buttons_layout.addWidget(self.beam2_reffolder_remove_button)
		beam2_ref_layout.addLayout(beam2_buttons_layout)
		ref_folders_layout.addLayout(beam2_ref_layout)

		ref_folders_group.setLayout(ref_folders_layout)
		folders_layout.addWidget(ref_folders_group)

		# --- Measurements Group ---
		measure_group = QGroupBox("Measurement Folders")
		measure_layout = QHBoxLayout()

		# LHCB1 Measurement Folders
		beam1_folders_layout = QVBoxLayout()
		self.beam1_folders_label = QLabel("LHCB1 Measurement Folders:")
		self.beam1_folders_label.setStyleSheet(b1_stylesheet)
		beam1_folders_layout.addWidget(self.beam1_folders_label)
		self.beam1_folders_list = QListWidget()
		self.beam1_folders_list.setSelectionMode(QListWidget.ExtendedSelection)
		beam1_folders_layout.addWidget(self.beam1_folders_list)
		self.beam1_folders_list.itemSelectionChanged.connect(lambda: self.update_select_all_checkbox(self.beam1_folders_list, self.beam1_select_all_checkbox))
		beam1_buttons_layout = QHBoxLayout()
		self.beam1_folders_button = QPushButton("Add Folders")
		self.beam1_folders_button.clicked.connect(self.select_beam1_folders)
		self.beam1_folders_button.setToolTip("Select LHCB1 OMC analysis folders to be used as comparison with reference - needs more than 3 different xing angles")
		beam1_buttons_layout.addWidget(self.beam1_folders_button)
		self.beam1_remove_button = QPushButton("Remove Selected")
		self.beam1_remove_button.setStyleSheet(remove_stylesheet)
		self.beam1_remove_button.clicked.connect(self.remove_selected_beam1_folders)
		beam1_buttons_layout.addWidget(self.beam1_remove_button)
		self.beam1_select_all_checkbox = QCheckBox("Select All")
		self.beam1_select_all_checkbox.stateChanged.connect(self.toggle_select_all_beam1_folders)
		beam1_buttons_layout.addWidget(self.beam1_select_all_checkbox)
		beam1_folders_layout.addLayout(beam1_buttons_layout)
		measure_layout.addLayout(beam1_folders_layout)

		# LHCB2 Measurement Folders
		beam2_folders_layout = QVBoxLayout()
		self.beam2_folders_label = QLabel("LHCB2 Measurement Folders:")
		self.beam2_folders_label.setStyleSheet(b2_stylesheet)
		beam2_folders_layout.addWidget(self.beam2_folders_label)
		self.beam2_folders_list = QListWidget()
		self.beam2_folders_list.setSelectionMode(QListWidget.ExtendedSelection)
		beam2_folders_layout.addWidget(self.beam2_folders_list)
		self.beam2_folders_list.itemSelectionChanged.connect(lambda: self.update_select_all_checkbox(self.beam2_folders_list, self.beam2_select_all_checkbox))
		beam2_buttons_layout = QHBoxLayout()
		self.beam2_folders_button = QPushButton("Add Folders")
		self.beam2_folders_button.clicked.connect(self.select_beam2_folders)
		self.beam2_folders_button.setToolTip("Select LHCB2 OMC analysis folders to be used as comparison with reference - needs more than 3 different xing angles")
		beam2_buttons_layout.addWidget(self.beam2_folders_button)
		self.beam2_remove_button = QPushButton("Remove Selected")
		self.beam2_remove_button.setStyleSheet(remove_stylesheet)
		self.beam2_remove_button.clicked.connect(self.remove_selected_beam2_folders)
		beam2_buttons_layout.addWidget(self.beam2_remove_button)
		self.beam2_select_all_checkbox = QCheckBox("Select All")
		self.beam2_select_all_checkbox.stateChanged.connect(self.toggle_select_all_beam2_folders)
		beam2_buttons_layout.addWidget(self.beam2_select_all_checkbox)
		beam2_folders_layout.addLayout(beam2_buttons_layout)
		measure_layout.addLayout(beam2_folders_layout)
		measure_group.setLayout(measure_layout)
		folders_layout.addWidget(measure_group)
		folders_group.setLayout(folders_layout)
		self.input_layout.addWidget(folders_group)

		# --- Parameters and Knob Group ---
		param_group = QGroupBox("Parameters and Knob")
		param_layout = QVBoxLayout()
		self.rdt_label = QLabel("RDT (in form of jklm):")
		param_layout.addWidget(self.rdt_label)       # "RDT (in form of jklm):"
		self.rdt_entry = QLineEdit()
		param_layout.addWidget(self.rdt_entry)
		self.rdt_plane_label = QLabel("RDT Plane:")
		param_layout.addWidget(self.rdt_plane_label)   # "RDT Plane:"
		self.rdt_plane_dropdown = QComboBox()
		self.rdt_plane_dropdown.addItems(["x", "y"])
		param_layout.addWidget(self.rdt_plane_dropdown)
		self.knob_label = QLabel("Xing Knob Name:")
		param_layout.addWidget(self.knob_label)          # "Knob:"
		self.knob_entry = QLineEdit("LHCBEAM/IP2-XING-V-MURAD")
		param_layout.addWidget(self.knob_entry)
		self.simulation_checkbox = QCheckBox("Simulation Mode")
		param_layout.addWidget(self.simulation_checkbox)
		self.simulation_checkbox.stateChanged.connect(self.toggle_simulation_mode)
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
		self.validate_knob_button.setToolTip("Only required if want to check if knob exists in Timber!!!")
		param_layout.addWidget(self.validate_knob_button)
		param_group.setLayout(param_layout)
		self.input_layout.addWidget(param_group)

		# --- Run Button Group ---
		run_group = QGroupBox("Execute Analysis")
		run_layout = QVBoxLayout()
		self.run_button = QPushButton("Run Analysis")
		self.run_button.setStyleSheet(run_stylesheet)
		self.run_button.clicked.connect(lambda: run_analysis(self))
		run_layout.addWidget(self.run_button)
		run_group.setLayout(run_layout)
		self.input_layout.addWidget(run_group)

		 # Progress bar for plotting
		self.input_progress = QProgressBar()
		self.input_progress.setRange(0, 0)
		self.input_progress.hide()
		self.layout.addWidget(self.input_progress)

	def buildValidationTab(self):
		# ===== Validation Tab with separated sections =====
		self.validation_tab = QWidget()
		self.tabs.addTab(self.validation_tab, "Validation")
		self.validation_layout = QVBoxLayout(self.validation_tab)

		 # Keep only the new validation_files_list layout
		validation_files_layout = QVBoxLayout()
		self.validation_files_label = QLabel("Analysis Files:")
		validation_files_layout.addWidget(self.validation_files_label)

		self.validation_files_list = QListWidget()
		self.validation_files_list.setFixedHeight(100)
		self.validation_files_list.setSelectionMode(QAbstractItemView.ExtendedSelection)
		validation_files_layout.addWidget(self.validation_files_list, stretch=1)
		self.validation_files_list.itemSelectionChanged.connect(lambda: self.update_select_all_checkbox(self.validation_files_list, self.validation_select_all_checkbox))

		validation_buttons_layout = QHBoxLayout()
		self.validation_files_button = QPushButton("Add Folders")
		self.validation_files_button.clicked.connect(self.select_analysis_files)
		validation_buttons_layout.addWidget(self.validation_files_button)

		self.validation_files_remove_button = QPushButton("Remove Selected")
		self.validation_files_remove_button.setStyleSheet(remove_stylesheet)
		self.validation_files_remove_button.clicked.connect(lambda: self.remove_selected_items(self.validation_files_list))
		validation_buttons_layout.addWidget(self.validation_files_remove_button)

		self.validation_select_all_checkbox = QCheckBox("Select All")
		self.validation_select_all_checkbox.stateChanged.connect(lambda state: self._toggle_select_all(self.validation_files_list, state))
		validation_buttons_layout.addWidget(self.validation_select_all_checkbox)

		validation_files_layout.addLayout(validation_buttons_layout)
		self.validation_layout.addLayout(validation_files_layout)

		load_selected_files_button = QPushButton("Load Selected Files For Plotting")
		load_selected_files_button.clicked.connect(lambda: load_selected_files(self))
		load_selected_files_button.setToolTip("Load selected analysis files for plotting (if files are not loaded, plotting of them is not possible)")
		self.validation_layout.addWidget(load_selected_files_button)

		self.loaded_files_list = QTreeWidget()
		self.loaded_files_list.setHeaderLabels(["Filename", "Beam", "RDT", "RDT plane", "Xing Knob Name"])
		self.loaded_files_list.setFixedHeight(100) 
		self.loaded_files_list.setSelectionMode(QAbstractItemView.NoSelection)
		self.validation_layout.addWidget(self.loaded_files_list, stretch=1)

		# --- Graphing sub tabs ---
		self.graph_tabs = QTabWidget()
		self.bpm_tab = QWidget()
		bpm_tab_layout = QVBoxLayout(self.bpm_tab)

		beam_selector_layout = QHBoxLayout()
		beam_label = QLabel("Select Beam:")
		beam_selector_layout.addWidget(beam_label)
		self.beam_selector = QComboBox()
		self.beam_selector.addItems(["LHCB1", "LHCB2"])
		self.beam_selector.currentIndexChanged.connect(self.update_bpm_search_entry)
		beam_selector_layout.addWidget(self.beam_selector)
		bpm_tab_layout.addLayout(beam_selector_layout)

		self.bpm_search_entry = QLineEdit()
		self.update_bpm_search_entry() 
		self.bpm_search_entry.setPlaceholderText("Enter BPM search term")
		self.bpm_search_entry.returnPressed.connect(self.graph_bpm)
		bpm_layout = QHBoxLayout()
		bpm_layout.addWidget(self.bpm_search_entry)
		self.search_bpm_button = QPushButton("Search BPM")
		self.search_bpm_button.clicked.connect(self.search_bpm)
		self.search_bpm_button.setToolTip("Only required if want to check if BPM exists in data")
		bpm_layout.addWidget(self.search_bpm_button)
		self.graph_bpm_button = QPushButton("Plot BPM")
		self.graph_bpm_button.setStyleSheet(plot_stylesheet)
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
		self.validation_layout.addWidget(self.graph_tabs, stretch=3)

		rdt_layout = QVBoxLayout(self.rdt_tab)
		self.plot_rdt_button = QPushButton("Plot RDT")
		self.plot_rdt_button.setStyleSheet(plot_stylesheet)
		self.plot_rdt_button.clicked.connect(self.plot_rdt)
		rdt_layout.addWidget(self.plot_rdt_button)
		self.rdtWidget = pg.PlotWidget()
		setup_blankcanvas(self.rdtWidget)
		rdt_layout.addWidget(self.rdtWidget)

		rdt_shift_layout = QVBoxLayout(self.rdt_shift_tab)
		self.plot_rdt_shifts_button = QPushButton("Plot RDT Shifts")
		self.plot_rdt_shifts_button.setStyleSheet(plot_stylesheet)
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
	
	def buildCorrectionTab(self):
		# ===== Correction Tab with separated sections =====
		self.correction_tab = QWidget()
		self.tabs.addTab(self.correction_tab, "Correction")
		correction_main_layout = QVBoxLayout(self.correction_tab)

		# Create a QTabWidget for the sub-tabs
		self.correction_sub_tabs = QTabWidget()
		correction_main_layout.addWidget(self.correction_sub_tabs)
		
		# ------------------- Response Tab -------------------
		self.response_tab = QWidget()
		response_tab_layout = QVBoxLayout(self.response_tab)

		# Group for reference and reponse folders
		corr_folders_group = QGroupBox("Reference and Reponse Folders")
		corr_folders_group.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)
		corr_folders_layout = QVBoxLayout(corr_folders_group)

		# Reference Folders group
		corr_ref_folders_group = QGroupBox("Reference Folders")
		corr_ref_folders_group.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)
		corr_ref_folders_layout = QHBoxLayout()

		# LHCB1 Reference Folder (vertical layout)
		corr_beam1_ref_layout = QVBoxLayout()
		self.corr_beam1_reffolder_label = QLabel("LHCB1 Reference Folder:")
		self.corr_beam1_reffolder_label.setStyleSheet(b1_stylesheet)
		corr_beam1_ref_layout.addWidget(self.corr_beam1_reffolder_label)
		self.corr_beam1_reffolder_entry = QLineEdit()
		corr_beam1_ref_layout.addWidget(self.corr_beam1_reffolder_entry)
		beam1_ref_buttons_layout = QHBoxLayout()
		self.corr_beam1_reffolder_button = QPushButton("Select Folder")
		self.corr_beam1_reffolder_button.clicked.connect(lambda: select_singleitem(self, "LHCB1", 
															"Select LHCB1 Reference File", 
															self.corr_beam1_reffolder_entry, None,
															folder=True))
		self.corr_beam1_reffolder_button.setToolTip("Select LHCB1 OMC analysis folder to be used as the reference")
		beam1_ref_buttons_layout.addWidget(self.corr_beam1_reffolder_button)
		self.corr_beam1_reffolder_remove_button = QPushButton("Remove File")
		self.corr_beam1_reffolder_remove_button.setStyleSheet(remove_stylesheet)
		self.corr_beam1_reffolder_remove_button.clicked.connect(lambda: self.remove_singlefolder("LHCB1",
															self.corr_beam1_reffolder_entry, self.corr_beam2_reffolder_entry))
		beam1_ref_buttons_layout.addWidget(self.corr_beam1_reffolder_remove_button)
		corr_beam1_ref_layout.addLayout(beam1_ref_buttons_layout)
		corr_ref_folders_layout.addLayout(corr_beam1_ref_layout)

		# LHCB2 Reference Folder (vertical layout)
		corr_beam2_ref_layout = QVBoxLayout()
		self.corr_beam2_reffolder_label = QLabel("LHCB2 Reference Folder:")
		self.corr_beam2_reffolder_label.setStyleSheet(b2_stylesheet)
		corr_beam2_ref_layout.addWidget(self.corr_beam2_reffolder_label)
		self.corr_beam2_reffolder_entry = QLineEdit()
		corr_beam2_ref_layout.addWidget(self.corr_beam2_reffolder_entry)
		beam2_ref_buttons_layout = QHBoxLayout()
		self.corr_beam2_reffolder_button = QPushButton("Select Folder")
		self.corr_beam2_reffolder_button.clicked.connect(lambda: select_singleitem(self, "LHCB2", 
															"Select LHCB2 Reference Folder", 
															None, self.corr_beam2_reffolder_entry,
															folder=True))
		self.corr_beam2_reffolder_button.setToolTip("Select LHCB2 OMC analysis folder to be used as the reference")
		beam2_ref_buttons_layout.addWidget(self.corr_beam2_reffolder_button)
		self.corr_beam2_reffolder_remove_button = QPushButton("Remove File")
		self.corr_beam2_reffolder_remove_button.setStyleSheet(remove_stylesheet)
		self.corr_beam2_reffolder_remove_button.clicked.connect(lambda: self.remove_singlefolder("LHCB2",
															self.corr_beam2_reffolder_entry, self.corr_beam2_reffolder_entry))
		beam2_ref_buttons_layout.addWidget(self.corr_beam2_reffolder_remove_button)
		corr_beam2_ref_layout.addLayout(beam2_ref_buttons_layout)
		corr_ref_folders_layout.addLayout(corr_beam2_ref_layout)

		corr_ref_folders_group.setLayout(corr_ref_folders_layout)
		# Insert the Reference Folders group at the top
		corr_folders_layout.insertWidget(0, corr_ref_folders_group)

		# Measurement (Response) Folders group
		corr_meas_folders_group = QGroupBox("Response Folders")
		corr_meas_folders_group.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)
		corr_meas_folders_layout = QHBoxLayout()

		# LHCB1 Measurement Folder (vertical layout)
		corr_beam1_meas_layout = QVBoxLayout()
		self.corr_beam1_measfolder_label = QLabel("LHCB1 Response Folder:")
		self.corr_beam1_measfolder_label.setStyleSheet(b1_stylesheet)
		corr_beam1_meas_layout.addWidget(self.corr_beam1_measfolder_label)
		self.corr_beam1_measfolder_entry = QLineEdit()
		corr_beam1_meas_layout.addWidget(self.corr_beam1_measfolder_entry)
		beam1_meas_buttons_layout = QHBoxLayout()
		self.corr_beam1_measfolder_button = QPushButton("Select Folder")
		self.corr_beam1_measfolder_button.clicked.connect(lambda: select_singleitem(self, "LHCB1", 
															"Select LHCB1 Response Folder", 
															self.corr_beam1_measfolder_entry, None,
															folder=True))
		self.corr_beam1_measfolder_button.setToolTip("Select LHCB1 OMC analysis folder which only has a different XING angle to the reference")
		beam1_meas_buttons_layout.addWidget(self.corr_beam1_measfolder_button)
		self.corr_beam1_measfolder_remove_button = QPushButton("Remove File")
		self.corr_beam1_measfolder_remove_button.setStyleSheet(remove_stylesheet)
		self.corr_beam1_measfolder_remove_button.clicked.connect(lambda: self.remove_singlefolder("LHCB1",
															self.corr_beam1_measfolder_entry, self.corr_beam2_measfolder_entry))
		beam1_meas_buttons_layout.addWidget(self.corr_beam1_measfolder_remove_button)
		corr_beam1_meas_layout.addLayout(beam1_meas_buttons_layout)
		corr_meas_folders_layout.addLayout(corr_beam1_meas_layout)

		# LHCB2 Measurement Folder (vertical layout)
		corr_beam2_meas_layout = QVBoxLayout()
		self.corr_beam2_measfolder_label = QLabel("LHCB2 Response Folder:")
		self.corr_beam2_measfolder_label.setStyleSheet(b2_stylesheet)
		corr_beam2_meas_layout.addWidget(self.corr_beam2_measfolder_label)
		self.corr_beam2_measfolder_entry = QLineEdit()
		corr_beam2_meas_layout.addWidget(self.corr_beam2_measfolder_entry)
		beam2_meas_buttons_layout = QHBoxLayout()
		self.corr_beam2_measfolder_button = QPushButton("Select Folder")
		self.corr_beam2_measfolder_button.clicked.connect(lambda: select_singleitem(self, "LHCB2", 
															"Select LHCB2 Response Folder", 
															None, self.corr_beam2_measfolder_entry,
															folder=True))
		self.corr_beam2_measfolder_button.setToolTip("Select LHCB2 OMC analysis folder which only has a different XING angle to the reference")
		beam2_meas_buttons_layout.addWidget(self.corr_beam2_measfolder_button)
		self.corr_beam2_measfolder_remove_button = QPushButton("Remove File")
		self.corr_beam2_measfolder_remove_button.setStyleSheet(remove_stylesheet)
		self.corr_beam2_measfolder_remove_button.clicked.connect(lambda: self.remove_singlefolder("LHCB2",
															self.corr_beam2_measfolder_entry, self.corr_beam2_measfolder_entry))
		beam2_meas_buttons_layout.addWidget(self.corr_beam2_measfolder_remove_button)
		corr_beam2_meas_layout.addLayout(beam2_meas_buttons_layout)
		corr_meas_folders_layout.addLayout(corr_beam2_meas_layout)

		corr_meas_folders_group.setLayout(corr_meas_folders_layout)
		# Insert the Measurement (Response) Folders group as second widget
		corr_folders_layout.insertWidget(1, corr_meas_folders_group)
		corr_folders_group.setLayout(corr_folders_layout)
		response_tab_layout.addWidget(corr_folders_group)

		# --- Parameters and Knob Group ---
		corr_param_group = QGroupBox("Parameters and Corrector")
		corr_param_layout = QVBoxLayout()
		self.corr_rdt_label = QLabel("RDT (in form of jklm):")
		corr_param_layout.addWidget(self.corr_rdt_label)
		self.corr_rdt_entry = QLineEdit()
		corr_param_layout.addWidget(self.corr_rdt_entry)
		self.corr_rdt_plane_label = QLabel("RDT Plane:")
		corr_param_layout.addWidget(self.corr_rdt_plane_label)
		self.corr_rdt_plane_dropdown = QComboBox()
		self.corr_rdt_plane_dropdown.addItems(["x", "y"])
		corr_param_layout.addWidget(self.corr_rdt_plane_dropdown)

		self.b1andb2same_checkbox = QCheckBox("LHCB1 same as LHCB2 mode")
		corr_param_layout.addWidget(self.b1andb2same_checkbox)
		self.b1andb2same_checkbox.stateChanged.connect(self.toggle_b1andb2same_mode)

		separate_knob_layout = QHBoxLayout()
		# LHCB1 knob fields
		lhcb1_layout = QVBoxLayout()
		h_layout = QHBoxLayout()
		self.b1_corr_knobname_label = QLabel("LHCB1 Corrector name:")
		self.b1_corr_knobname_label.setStyleSheet(b1_stylesheet)
		lhcb1_layout.addWidget(self.b1_corr_knobname_label)
		self.b1_corr_knobname_entry = QLineEdit()
		lhcb1_layout.addWidget(self.b1_corr_knobname_entry)
		self.b1_corr_knob_label = QLabel("LHCB1 Corrector value:")
		self.b1_corr_knob_label.setStyleSheet(b1_stylesheet)
		lhcb1_layout.addWidget(self.b1_corr_knob_label)
		self.b1_corr_knob_entry = QLineEdit()
		self.b1_corr_knob_entry.setToolTip("Enter the corrector value for LHCB1 (should be same for both reference and response)")
		lhcb1_layout.addWidget(self.b1_corr_knob_entry)
		self.b1_corr_xing_label = QLabel("LHCB1 difference in XING angle:")
		self.b1_corr_xing_label.setStyleSheet(b1_stylesheet)
		lhcb1_layout.addWidget(self.b1_corr_xing_label)
		self.b1_corr_xing_entry = QLineEdit()
		self.b1_corr_xing_entry.setToolTip("Enter the difference in xing angle for LHCB1 (between reference and response)")
		lhcb1_layout.addWidget(self.b1_corr_xing_entry)
		separate_knob_layout.addLayout(lhcb1_layout)
		# LHCB2 knob fields
		lhcb2_layout = QVBoxLayout()
		self.b2_corr_knobname_label = QLabel("LHCB2 Corrector name:")
		self.b2_corr_knobname_label.setStyleSheet(b2_stylesheet)
		lhcb2_layout.addWidget(self.b2_corr_knobname_label)
		self.b2_corr_knobname_entry = QLineEdit()
		lhcb2_layout.addWidget(self.b2_corr_knobname_entry)
		self.b2_corr_knob_label = QLabel("LHCB2 Corrector value:")
		self.b2_corr_knob_label.setStyleSheet(b2_stylesheet)
		lhcb2_layout.addWidget(self.b2_corr_knob_label)
		self.b2_corr_knob_entry = QLineEdit()
		self.b2_corr_knob_entry.setToolTip("Enter the corrector value for LHCB2 (should be same for both reference and response)")
		lhcb2_layout.addWidget(self.b2_corr_knob_entry)
		self.b2_corr_xing_label = QLabel("LHCB2 difference in XING angle:")
		self.b2_corr_xing_label.setStyleSheet(b2_stylesheet)
		lhcb2_layout.addWidget(self.b2_corr_xing_label)
		self.b2_corr_xing_entry = QLineEdit()
		self.b2_corr_xing_entry.setToolTip("Enter the difference in xing angle for LHCB2 (between reference and response)")
		lhcb2_layout.addWidget(self.b2_corr_xing_entry)
		separate_knob_layout.addLayout(lhcb2_layout)
		corr_param_layout.addLayout(separate_knob_layout)
		# Unified knob fields
		self.corr_knobname_entry_label = QLabel("Shared Corrector name:")
		self.corr_knobname_entry = QLineEdit()
		self.corr_knob_entry_label = QLabel("Shared Corrector value:")
		self.corr_knob_entry = QLineEdit()
		self.corr_knob_entry.setToolTip("Enter the corrector value (should be same for both reference and response)")
		self.corr_xing_entry_label = QLabel("Shared difference in XING angle:")
		self.corr_xing_entry = QLineEdit()
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
		response_tab_layout.addWidget(corr_param_group)

		# --- Run Button Group ---
		run_response_group = QGroupBox("Find Response")
		run_response_layout = QVBoxLayout()
		self.run_response_button = QPushButton("Find Response")
		self.run_response_button.setStyleSheet(run_stylesheet)
		self.run_response_button.clicked.connect(self.run_response)
		run_response_layout.addWidget(self.run_response_button)
		run_response_group.setLayout(run_response_layout)
		response_tab_layout.addWidget(run_response_group)

		self.response_tab.setLayout(response_tab_layout)
		self.correction_sub_tabs.addTab(self.response_tab, "Response")

		# ------------------- Graph Tab -------------------
		self.graph_tab = QWidget()
		graph_tab_layout = QVBoxLayout(self.graph_tab)
		# Loaded Files section
		loaded_files_group = QGroupBox("Loaded Corrector Response Files")
		loaded_files_group.setFixedHeight(150)
		loaded_files_layout = QVBoxLayout()
		self.correction_loaded_files_list = QTreeWidget()
		self.correction_loaded_files_list.setColumnCount(4)
		self.correction_loaded_files_list.setHeaderLabels(["Filename", "Beam", "RDT", "RDT plane", "Corrector"])
		self.correction_loaded_files_list.setSelectionMode(QAbstractItemView.ExtendedSelection)
		loaded_files_layout.addWidget(self.correction_loaded_files_list)
		self.correction_loaded_files_list.itemSelectionChanged.connect(lambda: self.update_select_all_checkbox(self.correction_loaded_files_list, self.select_all_files_checkbox))

		btn_layout = QHBoxLayout()
		self.load_file_button = QPushButton("Load Files")
		self.load_file_button.clicked.connect(self.load_selected_correction_files)
		self.load_file_button.setToolTip("Load selected response files to use to match to the analysis files")
		btn_layout.addWidget(self.load_file_button)
		self.remove_file_button = QPushButton("Remove Selected Files")
		self.remove_file_button.setStyleSheet(remove_stylesheet)
		self.remove_file_button.clicked.connect(lambda: self.remove_selected_items(self.correction_loaded_files_list, self.corr_responses, True))
		btn_layout.addWidget(self.remove_file_button)
		self.select_all_files_checkbox = QCheckBox("Select All Files")
		self.select_all_files_checkbox.stateChanged.connect(lambda state: self._toggle_select_all(self.correction_loaded_files_list, state))
		btn_layout.addWidget(self.select_all_files_checkbox)
		loaded_files_layout.addLayout(btn_layout)
		loaded_files_group.setLayout(loaded_files_layout)
		graph_tab_layout.addWidget(loaded_files_group)
				
		# Measurement to be matched group
		measurement_match_group = QGroupBox("Measurements to be matched")
		match_layout = QHBoxLayout(measurement_match_group)

		# LHCB1 Single Measurement
		b1_container = QWidget()
		b1_vlayout = QVBoxLayout(b1_container)
		b1_label = QLabel("LHCB1 Analysis File To Match:")
		b1_label.setStyleSheet(b1_stylesheet)
		b1_vlayout.addWidget(b1_label)
		self.b1_match_entry = QLineEdit()
		b1_vlayout.addWidget(self.b1_match_entry)
		b1_button = QPushButton("Browse File")
		b1_button.clicked.connect(lambda: select_singleitem(self, "LHCB1",
															"Select LHCB1 Analysis File",
															self.b1_match_entry, None,
															"JSON Files (*.json)" 
															))
		b1_button.setToolTip("Select LHCB1 analysis file outputted in the Validation tab from the measurements to be matched to with the response files")
		b1_vlayout.addWidget(b1_button)
		match_layout.addWidget(b1_container)

		# LHCB2 Single Measurement
		b2_container = QWidget()
		b2_vlayout = QVBoxLayout(b2_container)
		b2_label = QLabel("LHCB2 Analysis File To Match:")
		b2_label.setStyleSheet(b2_stylesheet)
		b2_vlayout.addWidget(b2_label)
		self.b2_match_entry = QLineEdit()
		b2_vlayout.addWidget(self.b2_match_entry)
		b2_button = QPushButton("Browse File")
		b2_button.clicked.connect(lambda: select_singleitem(self, "LHCB2",
															"Select LHCB2 Analysis File",
															None, self.b2_match_entry,
															"JSON Files (*.json)"
															))
		b2_button.setToolTip("Select LHCB2 analysis file outputted in the Validation tab from the measurements to be matched to with the response files")
		b2_vlayout.addWidget(b2_button)
		match_layout.addWidget(b2_container)

		graph_tab_layout.addWidget(measurement_match_group)

		# Plot button
		self.corr_plot_button = QPushButton("Plot")
		self.corr_plot_button.setStyleSheet(plot_stylesheet)
		self.corr_plot_button.clicked.connect(self.plot_loaded_correction_files)
		graph_tab_layout.addWidget(self.corr_plot_button)

		# Graph and Knob Manager layout
		graph_and_knob_layout = QHBoxLayout()
		self.figureContainer = QWidget()
		container_layout = QVBoxLayout(self.figureContainer)
		self.corrFigure = pg.PlotWidget()
		setup_blankcanvas(self.corrFigure)
		container_layout.addWidget(self.corrFigure)
		graph_and_knob_layout.addWidget(self.figureContainer, stretch=3)
		self.knob_manager_group = QGroupBox("Knob Manager")
		knob_manager_layout = QVBoxLayout()
		self.knob_widgets = {}
		self.update_knobs_button = QPushButton("Update Knobs and Re-Plot")
		self.update_knobs_button.setStyleSheet(plot_stylesheet)
		self.update_knobs_button.clicked.connect(self.update_knobs_and_replot)
		knob_manager_layout.addWidget(self.update_knobs_button)
		self.knob_manager_group.setLayout(knob_manager_layout)
		graph_and_knob_layout.addWidget(self.knob_manager_group)
		graph_tab_layout.addLayout(graph_and_knob_layout, stretch=1)

		self.graph_tab.setLayout(graph_tab_layout)
		self.correction_sub_tabs.addTab(self.graph_tab, "Graph")

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
			self.log_error("Knob field must be filled!")
			return
		is_valid_knob, knob_message = validate_knob(initialize_statetracker(), knob)
		if is_valid_knob:
			QMessageBox.information(self, "Knob Validation", "Knob is valid. Setting: " + repr(knob_message))
		else:
			self.log_error("Knob Validation", "Invalid Knob: " + repr(knob_message))

	def update_validation_files_widget(self):
		# Update the validation_files_list widget with analysis_output_files
		for f in self.analysis_output_files:
			if f not in [self.validation_files_list.item(i).text() for i in range(self.validation_files_list.count())]:
				self.validation_files_list.addItem(f)

	def log_error(self, error_msg):
		tb = traceback.format_exc()
		formatted = f"<p style='color:white;'>{error_msg}</p>"
		if tb and tb.strip() and tb.strip() != "None":
			formatted += f"<p style='color:red;'>{tb}</p>"
		self.error_log.append(formatted)
		QMessageBox.critical(self, "Error", error_msg)

	def toggle_select_all_validation_files(self, state):
		"""
		Toggle selection for all items in the validation files list based on the checkbox state.
		"""
		for i in range(self.validation_files_list.count()):
			self.validation_files_list.item(i).setSelected(state == Qt.Checked)
	
	def select_analysis_files(self):
		selected_files = select_multiple_files(self, self.default_input_path, self.validation_files_list, "Select Analysis Files")
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
					# self.loaded_files_list.addItem(file)
					data = load_RDTdata(file)
					valid = validate_file_structure(data, ['beam', 'ref', 'rdt', 'rdt_plane', 'knob'], self.log_error)
					if not valid:
						matches = self.validation_files_list.findItems(file, Qt.MatchExactly)
						if matches:
							for item in matches: 
								row = self.validation_files_list.row(item)
								self.validation_files_list.takeItem(row)
							continue
					loaded_output_data.append(data)
					metadata = data.get("metadata", {})
					beam     = metadata.get("beam", "")
					rdt_val  = metadata.get("rdt", "")
					rdt_plane= metadata.get("rdt_plane", "")
					knob     = metadata.get("knob", "")
					item = QTreeWidgetItem([file, beam, rdt_val, rdt_plane, knob])
					self.loaded_files_list.addTopLevelItem(item)
				if not loaded_output_data:
					self.loaded_files_list.clear()
					self.log_error("No valid data loaded.")
					return
				results = group_datasets(loaded_output_data, self.log_error)
				if len(results) < 4:
					self.log_error("Not enough data from group_datasets.")
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
		QApplication.processEvents()
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
		QApplication.processEvents()
		datab1, datab2, knob = None, None, None
		try:
			datab1 = self.b1rdtdata["data"]
			knob = self.b1rdtdata["metadata"]["knob"]
		except Exception as e:
			self.log_error(f"Error accessing LHCB1 RDT data: {e}")
		try:
			datab2 = self.b2rdtdata["data"]
			knob = self.b2rdtdata["metadata"]["knob"]
		except Exception as e:
			self.log_error(f"Error accessing LHCB2 RDT data: {e}")

		self.rdtshift_axes, self.rdtshift_axes_layout = self.setup_figure(self.rdtShiftwidget, datab1, datab2, 3)

		try:
			plot_RDTshifts(datab1, datab2, self.rdt, self.rdt_plane, self.rdtshift_axes, knob, log_func=self.log_error)
		except Exception as e:
			self.log_error(f"Error plotting RDT shifts: {e}")
			self.plot_progress.hide()
			return
		self.plot_progress.hide()

	# New method to toggle simulation mode UI changes
	def toggle_simulation_mode(self, state):
		if state == Qt.Checked:
			self.validate_knob_button.hide()
			self.simulation_file_entry.show()
			self.simulation_file_button.show()
		else:
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

	def remove_selected_items(self, widget, saved_data=None, corr_responses=False):
		"""
		Remove selected items from either a QListWidget or QTreeWidget.
		Optionally delete corresponding entries in corr_responses.
		"""
		if isinstance(widget, QListWidget):
			# Handle QListWidget
			for item in widget.selectedItems():
				if saved_data:
					filename = item.text()  # Get the filename from the list widget item
					if filename in saved_data:
						del saved_data[filename]
				widget.takeItem(widget.row(item))
		elif isinstance(widget, QTreeWidget):
			# Handle QTreeWidget
			for item in widget.selectedItems():
				if saved_data:
					filename = item.text(0)  # Get the filename from the first column
					if filename in saved_data:
						del saved_data[filename]
				index = widget.indexOfTopLevelItem(item)
				widget.takeTopLevelItem(index)
		else:
			self.log_error("Unsupported widget type for remove_selected_items.")
			raise TypeError("Unsupported widget type. Only QListWidget and QTreeWidget are supported.")
		
		if corr_responses:
			self.populate_knob_manager()

	def _toggle_select_all(self, widget, state):
		"""
		Toggle selection for all items in either a QTreeWidget or QListWidget based on the checkbox state.
		"""
		if isinstance(widget, QTreeWidget):
			# Handle QTreeWidget
			for i in range(widget.topLevelItemCount()):
				widget.topLevelItem(i).setSelected(state == Qt.Checked)
		elif isinstance(widget, QListWidget):
			# Handle QListWidget
			for i in range(widget.count()):
				widget.item(i).setSelected(state == Qt.Checked)
		else:
			self.log_error("Unsupported widget type for toggle_select_all.")
			raise TypeError("Unsupported widget type. Only QTreeWidget and QListWidget are supported.")
	
	def update_select_all_checkbox(self, file_list, check_box):
		"""
		Update the 'Select All' checkbox.
		Uncheck it if not all items are selected.
		"""
		if isinstance(file_list, QTreeWidget):
			total = file_list.topLevelItemCount()
			selected = len(file_list.selectedItems())
		else:
			total = file_list.count()
			selected = len(file_list.selectedItems())
		check_box.blockSignals(True)
		check_box.setChecked(selected == total and total > 0)
		check_box.blockSignals(False)

	def select_beam1_folders(self):
		select_folders(self, self.default_input_path, "Beam1BunchTurn (Beam1BunchTurn*);;All Folders (*)", self.beam1_folders_list)

	def select_beam2_folders(self):
		select_folders(self, self.default_input_path, "Beam2BunchTurn (Beam2BunchTurn)*;;All Folders (*)", self.beam2_folders_list)

	def remove_selected_beam1_folders(self):
		self.remove_selected_items(self.beam1_folders_list)

	def remove_selected_beam2_folders(self):
		self.remove_selected_items(self.beam2_folders_list)

	def toggle_select_all_beam1_folders(self, state):
		self._toggle_select_all(self.beam1_folders_list, state)

	def toggle_select_all_beam2_folders(self, state):
		self._toggle_select_all(self.beam2_folders_list, state)

	def run_response(self):
		run_response(self)

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

	# NEW: New method to plot loaded correction files into the unified graph widget
	def plot_loaded_correction_files(self):
		self.simcorr_progress.show()
		QApplication.processEvents()
		self.b1_response_meas = None
		self.b2_response_meas = None
		try:
			self.b1_response_meas = load_RDTdata(self.b1_match_entry.text())
		except Exception as e:
			self.log_error(f"Error loading LHCB1 response measurement: {e}")
		try:
			self.b2_response_meas = load_RDTdata(self.b2_match_entry.text())
		except Exception as e:
			self.log_error(f"Error loading LHCB2 response measurement: {e}")
			
		QApplication.processEvents()
		if not self.b1_response_meas and not self.b2_response_meas:
			self.log_error("No data loaded for reference measurement.")
			self.simcorr_progress.hide()
			return
		if self.b1_response_meas:
			if (
				self.b1_response_meas.get('metadata', {}).get('rdt') == self.rdt and
				self.b1_response_meas.get('metadata', {}).get('rdt_plane') == self.rdt_plane and
				self.b1_response_meas.get('metadata', {}).get('beam')[-1] == "1"
			):
				self.b1_response_meas['data'] = {
					key: value for key, value in self.b1_response_meas['data'].items()
				}
			else:
				self.b1_response_meas['data'] = {}  # Clear data if metadata doesn't match
				self.log_error("LHCB1 response measurement metadata does not match.")
				self.simcorr_progress.hide()
				return
		if self.b2_response_meas:
			if (
				self.b2_response_meas.get('metadata', {}).get('rdt') == self.rdt and
				self.b2_response_meas.get('metadata', {}).get('rdt_plane') == self.rdt_plane and
				self.b2_response_meas.get('metadata', {}).get('beam')[-1] == "2"
			):
				self.b2_response_meas['data'] = {
					key: value for key, value in self.b2_response_meas['data'].items()
				}
			else:
				self.b2_response_meas['data'] = {}
				self.log_error("LHCB2 response measurement metadata does not match.")
				self.simcorr_progress.hide()
				return
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
			
		self.corr_axes, grid = self.setup_figure(self.figureContainer, self.b1data, self.b2data, 2)
		QApplication.processEvents()

		def both_plot():
			plot_dRDTdknob(self.b1_response_meas, self.b2_response_meas, self.rdt, self.rdt_plane,
							self.corr_axes, log_func=self.log_error)
			plot_dRDTdknob(self.b1data, self.b2data, self.rdt, self.rdt_plane, 
							self.corr_axes, log_func=self.log_error)

		both_plot()
		QApplication.processEvents()

		self.simcorr_progress.hide()

	def load_selected_correction_files(self):
		self.simcorr_progress.show()
		if not hasattr(self, 'corr_responses') or self.corr_responses is None:
			self.corr_responses = {}
		if not hasattr(self, 'rdt'):
			self.rdt = {}
		if not hasattr(self, 'rdt_plane'):
			self.rdt_plane = {}

		selected_files = select_multiple_treefiles(self, self.correction_loaded_files_list, title="Select Response Files", saved_data=self.corr_responses)
		# Validate metadata and update the UI
		samemetadata, metadata = validate_metas(self.corr_responses)
		if samemetadata:
			for file in selected_files:
				if file not in self.corr_responses.keys():
					self.corr_responses[file] = load_RDTdata(file)
					validate_file_structure(self.corr_responses[file], ['beam', 'ref', 'rdt', 'rdt_plane', 'knob_name'], self.log_error)
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
			row_layout.setContentsMargins(0, 0, 0, 0)
			label = QLabel(f"{knobname}")
			val_input = QLineEdit("0")  # default
			val_input.returnPressed.connect(self.update_knobs_and_replot)
			self.knob_widgets[knobname] = val_input
			row_layout.addWidget(label)
			row_layout.addWidget(val_input)
			layout.insertWidget(layout.count() - 1, row_container)

	def update_knobs_and_replot(self):
		"""
		Read knob edits, apply them, and replot using these values.
		"""
		self.simcorr_progress.show()
		QApplication.processEvents()

		if not hasattr(self, "corr_axes"):
			self.log_error("Correction axes not defined. Please plot the correction files first.")
			self.simcorr_progress.hide()
			return

		for ax in self.corr_axes:
			for item in ax.listDataItems():
				if hasattr(item, 'name') and item.name() == 'Simulation':
					ax.removeItem(item)
		 # Extract updated knob values.
		knob_values = {knob: widget.text() for knob, widget in self.knob_widgets.items()}
		plot_dRDTdknob(self.b1data, self.b2data, self.rdt, self.rdt_plane, self.corr_axes, knob_values, 
								log_func=self.log_error)
		self.simcorr_progress.hide()


	def setup_figure(self, container, b1data, b2data, rows):
		"""
		Set up the container with subplots using pyqtgraph.
		Safely removes any previous layout before setting up a new one.
		"""
		# Create a new QGridLayout for subplots.
		grid = QGridLayout()
		grid.setSpacing(10)
		existing_layout = container.layout()
		if existing_layout:
			QWidget().setLayout(existing_layout)
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
					view_box.setMouseEnabled(x=True, y=True)
					plot_widget = pg.PlotWidget(viewBox=view_box)
					plot_widget.setBackground(DARK_BACKGROUND_COLOR)
					plot_widget.showGrid(x=True, y=True)
					plot_widget.setMouseTracking(True)
					grid.addWidget(plot_widget, row, col)
					axes.append(plot_widget)
					view_box.setMouseMode(pg.ViewBox.RectMode)  # Enable click-and-drag zoom
					view_box.menu = None  # Disable default context menu
		else:
			# Create a 2x1 grid of subplots.
			axes = []
			for row in range(rows):
				view_box = MyViewBox()
				view_box.setMouseEnabled(x=True, y=True)
				plot_widget = pg.PlotWidget(viewBox=view_box)
				plot_widget.setBackground(DARK_BACKGROUND_COLOR)
				plot_widget.showGrid(x=True, y=True)
				plot_widget.setMouseTracking(True)
				grid.addWidget(plot_widget, row, 0)
				axes.append(plot_widget)
				view_box.setMouseMode(pg.ViewBox.RectMode)  # Enable click-and-drag zoom
				view_box.menu = None  # Disable default context menu

		QApplication.processEvents()  # Force the UI to update.
		return axes, grid

	def reset_zoom_on_right_click(self, event, axes):
		"""
		Reset zoom when the right mouse button is clicked.
		"""
		if event.button() == Qt.RightButton:
			for plot_widget in axes:
				plot_widget.getViewBox().autoRange()
