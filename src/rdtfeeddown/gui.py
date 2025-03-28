from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton,
    QFileDialog, QListWidget, QTabWidget, QWidget, QTextEdit, QMessageBox
)
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from .utils import check_rdt, initialize_statetracker, rdt_to_order_and_type, getmodelBPMs
from .analysis import write_RDTshifts, getrdt_omc3

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

        # Input Tab
        self.input_tab = QWidget()
        self.tabs.addTab(self.input_tab, "Input")
        self.input_layout = QVBoxLayout(self.input_tab)

        # Input and Output Paths
        self.input_path_label = QLabel(f"Default Input Path: {self.default_input_path}")
        self.input_layout.addWidget(self.input_path_label)
        self.change_input_path_button = QPushButton("Change Input Path")
        self.change_input_path_button.clicked.connect(self.change_default_input_path)
        self.input_layout.addWidget(self.change_input_path_button)

        self.output_path_label = QLabel(f"Default Output Path: {self.default_output_path}")
        self.input_layout.addWidget(self.output_path_label)
        self.change_output_path_button = QPushButton("Change Output Path")
        self.change_output_path_button.clicked.connect(self.change_default_output_path)
        self.input_layout.addWidget(self.change_output_path_button)

        # Beam 1 Model
        self.beam1_model_label = QLabel("Beam 1 Model:")
        self.input_layout.addWidget(self.beam1_model_label)
        self.beam1_model_entry = QLineEdit()
        self.input_layout.addWidget(self.beam1_model_entry)
        self.beam1_model_button = QPushButton("Select Model")
        self.beam1_model_button.clicked.connect(self.select_beam1_model)
        self.input_layout.addWidget(self.beam1_model_button)

        # Beam 2 Model
        self.beam2_model_label = QLabel("Beam 2 Model:")
        self.input_layout.addWidget(self.beam2_model_label)
        self.beam2_model_entry = QLineEdit()
        self.input_layout.addWidget(self.beam2_model_entry)
        self.beam2_model_button = QPushButton("Select Model")
        self.beam2_model_button.clicked.connect(self.select_beam2_model)
        self.input_layout.addWidget(self.beam2_model_button)

        # Beam 1 Folders
        self.beam1_folders_label = QLabel("Beam 1 Folders:")
        self.input_layout.addWidget(self.beam1_folders_label)
        self.beam1_folders_list = QListWidget()
        self.input_layout.addWidget(self.beam1_folders_list)
        self.beam1_folders_button = QPushButton("Add Folders")
        self.beam1_folders_button.clicked.connect(self.select_beam1_folders)
        self.input_layout.addWidget(self.beam1_folders_button)

        # Beam 2 Folders
        self.beam2_folders_label = QLabel("Beam 2 Folders:")
        self.input_layout.addWidget(self.beam2_folders_label)
        self.beam2_folders_list = QListWidget()
        self.input_layout.addWidget(self.beam2_folders_list)
        self.beam2_folders_button = QPushButton("Add Folders")
        self.beam2_folders_button.clicked.connect(self.select_beam2_folders)
        self.input_layout.addWidget(self.beam2_folders_button)

        # Parameters
        self.rdt_label = QLabel("RDT:")
        self.input_layout.addWidget(self.rdt_label)
        self.rdt_entry = QLineEdit()
        self.input_layout.addWidget(self.rdt_entry)

        self.rdt_plane_label = QLabel("RDT Plane:")
        self.input_layout.addWidget(self.rdt_plane_label)
        self.rdt_plane_entry = QLineEdit()
        self.input_layout.addWidget(self.rdt_plane_entry)

        self.knob_label = QLabel("Knob:")
        self.input_layout.addWidget(self.knob_label)
        self.knob_entry = QLineEdit("LHCBEAM/IP5-XING-H-MURAD")
        self.input_layout.addWidget(self.knob_entry)

        # Run Button
        self.run_button = QPushButton("Run Analysis")
        self.run_button.clicked.connect(self.run_analysis)
        self.input_layout.addWidget(self.run_button)

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
        modelpath = QFileDialog.getExistingDirectory(self, "Select Beam 1 Model", self.default_input_path)
        if modelpath:
            self.beam1_model_entry.setText(modelpath)

    def select_beam2_model(self):
        modelpath = QFileDialog.getExistingDirectory(self, "Select Beam 2 Model", self.default_input_path)
        if modelpath:
            self.beam2_model_entry.setText(modelpath)

    def select_beam1_folders(self):
        folderpath = QFileDialog.getExistingDirectory(self, "Select Beam 1 Folder", self.default_input_path)
        if folderpath and folderpath not in [self.beam1_folders_list.item(i).text() for i in range(self.beam1_folders_list.count())]:
            self.beam1_folders_list.addItem(folderpath)

    def select_beam2_folders(self):
        folderpath = QFileDialog.getExistingDirectory(self, "Select Beam 2 Folder", self.default_input_path)
        if folderpath and folderpath not in [self.beam2_folders_list.item(i).text() for i in range(self.beam2_folders_list.count())]:
            self.beam2_folders_list.addItem(folderpath)

    def run_analysis(self):
        beam1_model = self.beam1_model_entry.text()
        beam2_model = self.beam2_model_entry.text()
        beam1_folders = [self.beam1_folders_list.item(i).text() for i in range(self.beam1_folders_list.count())]
        beam2_folders = [self.beam2_folders_list.item(i).text() for i in range(self.beam2_folders_list.count())]
        rdt = self.rdt_entry.text()
        rdt_plane = self.rdt_plane_entry.text()
        knob = self.knob_entry.text()
        output_path = self.default_output_path

        # Validate inputs
        if not beam1_model:
            QMessageBox.critical(self, "Error", "Beam 1 model must be selected!")
            return
        if not beam2_model:
            QMessageBox.critical(self, "Error", "Beam 2 model must be selected!")
            return
        if not rdt or not rdt_plane:
            QMessageBox.critical(self, "Error", "RDT and RDT plane fields must be filled!")
            return

        # Validate RDT and RDT Plane
        try:
            check_rdt(rdt, rdt_plane)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Invalid RDT or RDT Plane: {e}")
            return

        if not knob:
            QMessageBox.critical(self, "Error", "Knob field must be filled!")
            return

        if not beam1_folders and not beam2_folders:
            QMessageBox.critical(self, "Error", "At least one set of measurement folders must be provided!")
            return

        try:
            self.analysis_text.clear()
            self.figure.clear()
            ldb = initialize_statetracker()
            rdtfolder = rdt_to_order_and_type(rdt, rdt_plane)

            if beam1_folders:
                b1modelbpmlist, b1bpmdata = getmodelBPMs(beam1_model)
                b1rdtdata = getrdt_omc3(ldb, b1modelbpmlist, b1bpmdata, None, beam1_folders, knob, output_path, rdt, rdt_plane, rdtfolder)
                write_RDTshifts(b1rdtdata, rdt, rdt_plane, "b1", output_path)
                self.analysis_text.append("Beam 1 Analysis Completed Successfully.\n")

            if beam2_folders:
                b2modelbpmlist, b2bpmdata = getmodelBPMs(beam2_model)
                b2rdtdata = getrdt_omc3(ldb, b2modelbpmlist, b2bpmdata, None, beam2_folders, knob, output_path, rdt, rdt_plane, rdtfolder)
                write_RDTshifts(b2rdtdata, rdt, rdt_plane, "b2", output_path)
                self.analysis_text.append("Beam 2 Analysis Completed Successfully.\n")

            self.canvas.draw()

        except Exception as e:
            QMessageBox.critical(self, "Error", f"An error occurred: {e}")
            return

        QMessageBox.information(self, "Run Analysis", "Analysis completed successfully!")

if __name__ == "__main__":
    app = QApplication([])
    window = RDTFeeddownGUI()
    window.show()
    app.exec_()


