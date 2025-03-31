from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton,
    QFileDialog, QListWidget, QTabWidget, QWidget, QTextEdit, QMessageBox
)
from PyQt5 import QtWidgets
from PyQt5.QtCore import Qt  # Import Qt for the correct constants
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from .utils import check_rdt, initialize_statetracker, rdt_to_order_and_type, getmodelBPMs
from .analysis import write_RDTshifts, getrdt_omc3, fit_BPM
import time  # Import time to get the current timestamp
import re    # Import re for regex substitution

class RDTFeeddownGUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("RDT Feeddown Analysis")

        # Default input and output paths
        self.default_input_path = "/afs/cern.ch/work/s/sahorney/private/LHCoptics/2025_03_a4corr"
        self.default_output_path = "/afs/cern.ch/work/s/sahorney/private/LHCoptics/2025_03_a4corr"

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
        # Reference Folders
        ref_group = QtWidgets.QGroupBox("Reference Folder")
        ref_layout = QHBoxLayout()
        self.beam1_reffolder_label = QLabel("Beam 1 Reference Folder:")
        self.beam1_reffolder_label.setStyleSheet("color: blue;")
        ref_layout.addWidget(self.beam1_reffolder_label)
        self.beam1_reffolder_entry = QLineEdit()
        ref_layout.addWidget(self.beam1_reffolder_entry)
        self.beam1_reffolder_button = QPushButton("Select Folder")
        self.beam1_reffolder_button.clicked.connect(self.select_beam1_reffolder)
        ref_layout.addWidget(self.beam1_reffolder_button)
        self.beam1_reffolder_remove_button = QPushButton("Remove File")
        self.beam1_reffolder_remove_button.clicked.connect(self.remove_beam1_reffolder)
        ref_layout.addWidget(self.beam1_reffolder_remove_button)
        ref_group.setLayout(ref_layout)
        folders_layout.addWidget(ref_group)
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
        param_layout = QHBoxLayout()
        # Parameters (left side)
        param_left = QVBoxLayout()
        self.rdt_label = QLabel("RDT (in form of jklm):")
        param_left.addWidget(self.rdt_label)
        self.rdt_entry = QLineEdit()
        param_left.addWidget(self.rdt_entry)
        self.rdt_plane_label = QLabel("RDT Plane:")
        param_left.addWidget(self.rdt_plane_label)
        self.rdt_plane_dropdown = QtWidgets.QComboBox()
        self.rdt_plane_dropdown.addItems(["x", "y"])
        param_left.addWidget(self.rdt_plane_dropdown)
        param_layout.addLayout(param_left)
        # Knob (right side)
        param_right = QVBoxLayout()
        self.knob_label = QLabel("Knob:")
        param_right.addWidget(self.knob_label)
        self.knob_entry = QLineEdit("LHCBEAM/IP5-XING-H-MURAD")
        param_right.addWidget(self.knob_entry)
        self.validate_knob_button = QPushButton("Validate Knob")
        self.validate_knob_button.clicked.connect(self.validate_knob_button_clicked)
        param_right.addWidget(self.validate_knob_button)
        param_layout.addLayout(param_right)
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

        # Analysis Tab
        self.analysis_tab = QWidget()
        self.tabs.addTab(self.analysis_tab, "Analysis")
        self.analysis_layout = QVBoxLayout(self.analysis_tab)

        self.analysis_text = QTextEdit()
        self.analysis_text.setReadOnly(True)
        self.analysis_layout.addWidget(self.analysis_text)

        self.figure = Figure(figsize=(6, 4))
        self.canvas = FigureCanvas(self.figure)
        self.analysis_layout.addWidget(self.canvas)

        # Updated: File list for analysis outputs now uses SingleSelection.
        self.file_list = QListWidget()
        self.file_list.setSelectionMode(QListWidget.MultiSelection)
        self.analysis_layout.addWidget(self.file_list)
        
        # New buttons for file actions.
        button_layout = QHBoxLayout()
        self.open_files_button = QPushButton("Browse and Open File")
        self.open_files_button.clicked.connect(self.select_analysis_folders)
        button_layout.addWidget(self.open_files_button)
        
        self.plot_files_button = QPushButton("Plot Selected File")
        self.plot_files_button.clicked.connect(self.plot_selected_files)
        button_layout.addWidget(self.plot_files_button)
        
        self.remove_files_button = QPushButton("Remove Selected File")
        self.remove_files_button.clicked.connect(self.remove_selected_files)
        button_layout.addWidget(self.remove_files_button)
        
        self.analysis_layout.addLayout(button_layout)
        
        # Automatically load existing analysis files even when no analysis has been run
        self.populate_file_list(self.default_output_path)

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
        folderpath = QFileDialog.getExistingDirectory(self, "Select Beam 1 Reference Folder", self.default_input_path)
        if folderpath:
            self.beam1_reffolder_entry.setText(folderpath)

    def select_beam2_reffolder(self):
        """
        Open a file dialog to select the Beam 2 reference measurement folder.
        """
        folderpath = QFileDialog.getExistingDirectory(self, "Select Beam 2 Reference Folder", self.default_input_path)
        if folderpath:
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
        self.select_multiple_directories(self.beam1_folders_list)

    def select_beam2_folders(self):
        self.select_multiple_directories(self.beam2_folders_list)

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
        beam1_model = self.beam1_model_entry.text()
        beam2_model = self.beam2_model_entry.text()
        beam1_reffolder = self.beam1_reffolder_entry.text()
        beam2_reffolder = self.beam2_reffolder_entry.text()
        beam1_folders = [self.beam1_folders_list.item(i).text() for i in range(self.beam1_folders_list.count())]
        beam2_folders = [self.beam2_folders_list.item(i).text() for i in range(self.beam2_folders_list.count())]
        rdt = self.rdt_entry.text()
        rdt_plane = self.rdt_plane_dropdown.currentText()  # Get selected value from dropdown
        knob = self.knob_entry.text()
        output_path = self.default_output_path


        # Validate inputs
        if not beam1_model and not beam2_model:
            QMessageBox.critical(self, "Error", "At least one beam model must be selected!")
            return
        if not rdt or not rdt_plane:
            QMessageBox.critical(self, "Error", "RDT and RDT plane fields must be filled!")
            return
        if not knob:
            QMessageBox.critical(self, "Error", "Knob field must be filled!")
            return
        if not beam1_folders and not beam2_folders:
            QMessageBox.critical(self, "Error", "At least one set of measurement folders must be provided!")
            return

        # Validate RDT and RDT Plane
        is_valid, error_message = self.validate_rdt_and_plane(rdt, rdt_plane)
        if not is_valid:
            QMessageBox.critical(self, "Error", "Invalid RDT or RDT Plane: " + repr(error_message))
            return

        # Validate knob
        is_valid_knob, knob_message = self.validate_knob(initialize_statetracker(), knob)
        if not is_valid_knob:
            QMessageBox.critical(self, "Error", "Invalid Knob: " + repr(knob_message))
            return

        try:
            self.analysis_text.clear()
            self.figure.clear()
            ldb = initialize_statetracker()
            rdtfolder = rdt_to_order_and_type(rdt)

            if beam1_model and beam1_folders:
                b1modelbpmlist, b1bpmdata = getmodelBPMs(beam1_model)
                b1rdtdata = getrdt_omc3(
                            ldb, b1modelbpmlist, b1bpmdata, beam1_reffolder, beam1_folders,
                            knob, output_path, rdt, rdt_plane, rdtfolder,
                            self.analysis_text.append
                        )
                b1rdtdata = fit_BPM(b1rdtdata)
                write_RDTshifts(b1rdtdata, rdt, rdt_plane, "b1", output_path)
                self.analysis_text.append("Beam 1 Analysis Completed Successfully.\n")

            if beam2_model and beam2_folders:
                b2modelbpmlist, b2bpmdata = getmodelBPMs(beam2_model)
                b2rdtdata = getrdt_omc3(
                            ldb, b2modelbpmlist, b2bpmdata, beam2_reffolder, beam2_folders,
                            knob, output_path, rdt, rdt_plane, rdtfolder,
                            self.analysis_text.append
                        )
                b2rdtdata = fit_BPM(b2rdtdata)
                write_RDTshifts(b2rdtdata, rdt, rdt_plane, "b2", output_path)
                self.analysis_text.append("Beam 2 Analysis Completed Successfully.\n")

            self.canvas.draw()
            # Automatically update file list after analysis run
            self.populate_file_list(output_path)

        except Exception as e:
            QMessageBox.critical(self, "Error", "An error occurred: " + repr(e))
            return

        QMessageBox.information(self, "Run Analysis", "Analysis completed successfully!")

    def populate_file_list(self, output_path):
        import glob, os
        pattern = os.path.join(output_path, "data_*")
        files = glob.glob(pattern)
        self.file_list.clear()
        for f in files:
            self.file_list.addItem(f)

    # New helper: Open selected files in one multi-file dialog.
    def select_analysis_folders(self):
        self.select_multiple_files(self.file_list)

    # New helper: Plot data from all selected analysis files together.
    def plot_selected_files(self):
        import csv
        selected_items = self.file_list.selectedItems()
        if not selected_items:
            return
        self.figure.clear()
        ax = self.figure.add_subplot(111)
        for item in selected_items:
            file_path = item.text()
            x, y = [], []
            try:
                with open(file_path, 'r') as f:
                    reader = csv.reader(f, delimiter=' ')
                    header = next(reader)
                    for row in reader:
                        if not row or row[0].startswith("#"):
                            continue
                        try:
                            x.append(float(row[1]))
                            y.append(float(row[2]))
                        except Exception:
                            continue
                ax.plot(x, y, marker='o', label=file_path)
            except Exception as e:
                QMessageBox.critical(self, "Error", "Could not plot file: " + str(e))
                return
        ax.legend()
        ax.set_title("Analysis Files Plot")
        self.canvas.draw()

    # New helper: Remove selected files from the list.
    def remove_selected_files(self):
        for item in self.file_list.selectedItems():
            row = self.file_list.row(item)
            self.file_list.takeItem(row)

    def select_multiple_files(self, list_widget):
        """
        Allow the user to select multiple files and add them to the file list widget.
        """
        dialog = QFileDialog(self)
        dialog.setWindowTitle("Select Files")
        dialog.setDirectory(self.default_output_path)  # Use default output path, adjust if needed
        dialog.setFileMode(QFileDialog.ExistingFiles)
        dialog.setNameFilter("All Files (*)")

        # Enable multiple selection in the dialog
        for view in dialog.findChildren((QtWidgets.QListView, QtWidgets.QTreeView)):
            if isinstance(view.model(), QtWidgets.QFileSystemModel):
                view.setSelectionMode(QtWidgets.QAbstractItemView.ExtendedSelection)

        if dialog.exec_() == QFileDialog.Accepted:
            selected_files = dialog.selectedFiles()
            for file in selected_files:
                if file not in [self.file_list.item(i).text() for i in range(self.file_list.count())]:
                    self.file_list.addItem(file)


