import tkinter as tk
from tkinter import filedialog, messagebox
from tkinter import ttk
from .utils import check_rdt, initialize_statetracker, rdt_to_order_and_type, getmodelBPMs, getrdt_omc3
from .analysis import write_RDTshifts
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.pyplot as plt

class RDTFeeddownGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("RDT Feeddown Analysis")

        # Default input and output paths
        self.default_input_path = "/afs/cern.ch/work/s/sahorney/private/LHCoptics/2025_03_a4corr"
        self.default_output_path = "/afs/cern.ch/work/s/sahorney/private/LHCoptics/2025_03_a4corr"
        
        # Create Notebook for tabs
        self.notebook = ttk.Notebook(root)
        self.notebook.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")

        # Input Tab
        self.input_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.input_tab, text="Input")

        # Analysis Tab
        self.analysis_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.analysis_tab, text="Analysis")

        # Input folder selection
        self.input_frame = ttk.LabelFrame(self.input_tab, text="Input and Output Paths")
        self.input_frame.grid(row=0, column=0, padx=10, pady=10, sticky="ew")

        # Default Input Path Display and Change Button
        self.default_input_path_label = ttk.Label(self.input_frame, text=f"Default Input Path: {self.default_input_path}")
        self.default_input_path_label.grid(row=0, column=0, columnspan=3, padx=5, pady=5, sticky="w")
        self.change_input_path_button = ttk.Button(self.input_frame, text="Change Input Path", command=self.change_default_input_path)
        self.change_input_path_button.grid(row=0, column=3, padx=5, pady=5)

        # Default Output Path Display and Change Button
        self.default_output_path_label = ttk.Label(self.input_frame, text=f"Default Output Path: {self.default_output_path}")
        self.default_output_path_label.grid(row=1, column=0, columnspan=3, padx=5, pady=5, sticky="w")
        self.change_output_path_button = ttk.Button(self.input_frame, text="Change Output Path", command=self.change_default_output_path)
        self.change_output_path_button.grid(row=1, column=3, padx=5, pady=5)

        # Beam 1 Model Selection
        self.beam1_model_label = ttk.Label(self.input_frame, text="Beam 1 Model:")
        self.beam1_model_label.grid(row=2, column=0, padx=5, pady=5, sticky="w")
        self.beam1_model_entry = ttk.Entry(self.input_frame, width=50)
        self.beam1_model_entry.grid(row=2, column=1, padx=5, pady=5)
        self.beam1_model_button = ttk.Button(self.input_frame, text="Select Model", command=self.select_beam1_model)
        self.beam1_model_button.grid(row=2, column=2, padx=5, pady=5)
        self.beam1_model_delete = ttk.Button(self.input_frame, text="Delete", command=self.delete_beam1_model)
        self.beam1_model_delete.grid(row=2, column=3, padx=5, pady=5)

        # Beam 1 Reference Folder
        self.beam1_ref_label = ttk.Label(self.input_frame, text="Beam 1 Reference Folder:")
        self.beam1_ref_label.grid(row=3, column=0, padx=5, pady=5, sticky="w")
        self.beam1_ref_entry = ttk.Entry(self.input_frame, width=50)
        self.beam1_ref_entry.grid(row=3, column=1, padx=5, pady=5)
        self.beam1_ref_button = ttk.Button(self.input_frame, text="Browse", command=self.select_beam1_ref_folder)
        self.beam1_ref_button.grid(row=3, column=2, padx=5, pady=5)
        self.beam1_ref_delete = ttk.Button(self.input_frame, text="Delete", command=self.delete_beam1_ref_folder)
        self.beam1_ref_delete.grid(row=3, column=3, padx=5, pady=5)

        # Beam 2 Model Selection
        self.beam2_model_label = ttk.Label(self.input_frame, text="Beam 2 Model:")
        self.beam2_model_label.grid(row=5, column=0, padx=5, pady=5, sticky="w")
        self.beam2_model_entry = ttk.Entry(self.input_frame, width=50)
        self.beam2_model_entry.grid(row=5, column=1, padx=5, pady=5)
        self.beam2_model_button = ttk.Button(self.input_frame, text="Select Model", command=self.select_beam2_model)
        self.beam2_model_button.grid(row=5, column=2, padx=5, pady=5)
        self.beam2_model_delete = ttk.Button(self.input_frame, text="Delete", command=self.delete_beam2_model)
        self.beam2_model_delete.grid(row=5, column=3, padx=5, pady=5)

        # Beam 2 Reference Folder
        self.beam2_ref_label = ttk.Label(self.input_frame, text="Beam 2 Reference Folder:")
        self.beam2_ref_label.grid(row=6, column=0, padx=5, pady=5, sticky="w")
        self.beam2_ref_entry = ttk.Entry(self.input_frame, width=50)
        self.beam2_ref_entry.grid(row=6, column=1, padx=5, pady=5)
        self.beam2_ref_button = ttk.Button(self.input_frame, text="Browse", command=self.select_beam2_ref_folder)
        self.beam2_ref_button.grid(row=6, column=2, padx=5, pady=5)
        self.beam2_ref_delete = ttk.Button(self.input_frame, text="Delete", command=self.delete_beam2_ref_folder)
        self.beam2_ref_delete.grid(row=6, column=3, padx=5, pady=5)

        # Beam 1 Folders
        self.beam1_label = ttk.Label(self.input_frame, text="Beam 1 Folders:")
        self.beam1_label.grid(row=7, column=0, padx=5, pady=5, sticky="w")
        self.beam1_listbox = tk.Listbox(self.input_frame, selectmode=tk.MULTIPLE, height=5, width=50)
        self.beam1_listbox.grid(row=7, column=1, padx=5, pady=5)
        self.beam1_button = ttk.Button(self.input_frame, text="Add Folders", command=self.select_beam1_folders)
        self.beam1_button.grid(row=7, column=2, padx=5, pady=5)
        self.beam1_delete = ttk.Button(self.input_frame, text="Delete Selected", command=self.delete_beam1_folders)
        self.beam1_delete.grid(row=7, column=3, padx=5, pady=5)

        # Beam 2 Folders
        self.beam2_label = ttk.Label(self.input_frame, text="Beam 2 Folders:")
        self.beam2_label.grid(row=8, column=0, padx=5, pady=5, sticky="w")
        self.beam2_listbox = tk.Listbox(self.input_frame, selectmode=tk.MULTIPLE, height=5, width=50)
        self.beam2_listbox.grid(row=8, column=1, padx=5, pady=5)
        self.beam2_button = ttk.Button(self.input_frame, text="Add Folders", command=self.select_beam2_folders)
        self.beam2_button.grid(row=8, column=2, padx=5, pady=5)
        self.beam2_delete = ttk.Button(self.input_frame, text="Delete Selected", command=self.delete_beam2_folders)
        self.beam2_delete.grid(row=8, column=3, padx=5, pady=5)

        # Parameters
        self.param_frame = ttk.LabelFrame(self.input_tab, text="Parameters")
        self.param_frame.grid(row=1, column=0, padx=10, pady=10, sticky="ew")

        self.rdt_label = ttk.Label(self.param_frame, text="RDT:")
        self.rdt_label.grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.rdt_entry = ttk.Entry(self.param_frame, width=20)
        self.rdt_entry.grid(row=0, column=1, padx=5, pady=5)

        self.rdt_plane_label = ttk.Label(self.param_frame, text="RDT Plane:")
        self.rdt_plane_label.grid(row=1, column=0, padx=5, pady=5, sticky="w")
        self.rdt_plane_entry = ttk.Entry(self.param_frame, width=20)
        self.rdt_plane_entry.grid(row=1, column=1, padx=5, pady=5)

        self.knob_label = ttk.Label(self.param_frame, text="Knob:")
        self.knob_label.grid(row=2, column=0, padx=5, pady=5, sticky="w")
        self.knob_entry = ttk.Entry(self.param_frame, width=20)
        self.knob_entry.grid(row=2, column=1, padx=5, pady=5)
        self.knob_entry.insert(0, "LHCBEAM/IP5-XING-H-MURAD")  # Set default knob value

        # Run button
        self.run_button = ttk.Button(self.input_tab, text="Run Analysis", command=self.run_analysis)
        self.run_button.grid(row=2, column=0, padx=10, pady=10)

        # Analysis Results
        self.analysis_text = tk.Text(self.analysis_tab, wrap="word", height=10, width=80)
        self.analysis_text.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")

        # Interactive Plot
        self.figure = plt.Figure(figsize=(6, 4), dpi=100)
        self.plot_ax = self.figure.add_subplot(111)
        self.canvas = FigureCanvasTkAgg(self.figure, self.analysis_tab)
        self.canvas.get_tk_widget().grid(row=1, column=0, padx=10, pady=10, sticky="nsew")

    def change_default_input_path(self):
        # Allow the user to select a new default input path
        new_path = filedialog.askdirectory(title="Select Default Input Path", initialdir=self.default_input_path)
        if new_path:
            self.default_input_path = new_path
            self.default_input_path_label.config(text=f"Default Input Path: {self.default_input_path}")

    def change_default_output_path(self):
        # Allow the user to select a new default output path
        new_path = filedialog.askdirectory(title="Select Default Output Path", initialdir=self.default_output_path)
        if new_path:
            self.default_output_path = new_path
            self.default_output_path_label.config(text=f"Default Output Path: {self.default_output_path}")

    def select_beam1_model(self):
        modelpath = filedialog.askopenfilename(title="Select Beam 1 Model", initialdir=self.default_input_path)
        if modelpath:
            self.beam1_model_entry.delete(0, tk.END)
            self.beam1_model_entry.insert(0, modelpath)

    def delete_beam1_model(self):
        self.beam1_model_entry.delete(0, tk.END)

    def select_beam2_model(self):
        modelpath = filedialog.askopenfilename(title="Select Beam 2 Model", initialdir=self.default_input_path)
        if modelpath:
            self.beam2_model_entry.delete(0, tk.END)
            self.beam2_model_entry.insert(0, modelpath)

    def delete_beam2_model(self):
        self.beam2_model_entry.delete(0, tk.END)

    def select_beam1_ref_folder(self):
        folderpath = filedialog.askdirectory(title="Select Beam 1 Reference Folder", initialdir=self.default_input_path)
        if folderpath:
            self.beam1_ref_entry.delete(0, tk.END)
            self.beam1_ref_entry.insert(0, folderpath)

    def select_beam2_ref_folder(self):
        folderpath = filedialog.askdirectory(title="Select Beam 2 Reference Folder", initialdir=self.default_input_path)
        if folderpath:
            self.beam2_ref_entry.delete(0, tk.END)
            self.beam2_ref_entry.insert(0, folderpath)

    def select_beam1_folders(self):
        folderpath = filedialog.askdirectory(title="Select Beam 1 Measurement Folders", initialdir=self.default_input_path)
        if folderpath:
            if folderpath not in self.beam1_listbox.get(0, tk.END):
                self.beam1_listbox.insert(tk.END, folderpath)

    def select_beam2_folders(self):
        folderpath = filedialog.askdirectory(title="Select Beam 2 Measurement Folders", initialdir=self.default_input_path)
        if folderpath:
            if folderpath not in self.beam2_listbox.get(0, tk.END):
                self.beam2_listbox.insert(tk.END, folderpath)

    def delete_beam1_ref_folder(self):
        self.beam1_ref_entry.delete(0, tk.END)

    def delete_beam2_ref_folder(self):
        self.beam2_ref_entry.delete(0, tk.END)

    def delete_beam1_folders(self):
        selected = self.beam1_listbox.curselection()
        for index in reversed(selected):
            self.beam1_listbox.delete(index)

    def delete_beam2_folders(self):
        selected = self.beam2_listbox.curselection()
        for index in reversed(selected):
            self.beam2_listbox.delete(index)

    def validate_rdt_and_plane(self, rdt, rdt_plane):
        """Validate the RDT and RDT Plane combination."""
        check_rdt(rdt, rdt_plane)
        return True, ""

    def run_analysis(self):
        beam1_model = self.beam1_model_entry.get()
        beam2_model = self.beam2_model_entry.get()
        beam1_ref_folder = self.beam1_ref_entry.get()
        beam2_ref_folder = self.beam2_ref_entry.get()
        beam1_folders = list(self.beam1_listbox.get(0, tk.END))
        beam2_folders = list(self.beam2_listbox.get(0, tk.END))
        rdt = self.rdt_entry.get()
        rdt_plane = self.rdt_plane_entry.get()
        knob = self.knob_entry.get()
        output_path = self.default_output_path

        # Validate inputs
        if not beam1_model:
            messagebox.showerror("Error", "Beam 1 model must be selected!")
            return
        if not beam2_model:
            messagebox.showerror("Error", "Beam 2 model must be selected!")
            return
        if not rdt or not rdt_plane:
            messagebox.showerror("Error", "RDT and RDT plane fields must be filled!")
            return

        # Validate RDT and RDT Plane
        is_valid, error_message = self.validate_rdt_and_plane(rdt, rdt_plane)
        if not is_valid:
            messagebox.showerror("Error", error_message)
            return

        if not knob:
            messagebox.showerror("Error", "Knob field must be filled!")
            return

        if not (beam1_ref_folder or beam2_ref_folder):
            messagebox.showerror("Error", "At least one reference folder must be provided!")
            return

        if beam1_ref_folder and not beam1_folders:
            messagebox.showerror("Error", "Beam 1 reference folder provided but no Beam 1 measurement folders!")
            return

        if beam2_ref_folder and not beam2_folders:
            messagebox.showerror("Error", "Beam 2 reference folder provided but no Beam 2 measurement folders!")
            return

        try:
            self.analysis_text.delete(1.0, tk.END)
            self.plot_ax.clear()
            ldb=initialize_statetracker()
            rdtfolder = rdt_to_order_and_type(rdt, rdt_plane)
            if beam1_ref_folder and beam1_folders:
                b1modelbpmlist,b1bpmdata=getmodelBPMs(beam1_model)
                b1rdtdata=getrdt_omc3(ldb,b1modelbpmlist,b1bpmdata,beam1_ref_folder,beam1_folders,knob,output_path,rdt,rdt_plane,rdtfolder)
                write_RDTshifts(b1rdtdata, rdt, rdt_plane, "b1", output_path)
                self.analysis_text.insert(tk.END, "Beam 1 Analysis Completed Successfully.\n")

            if beam2_ref_folder and beam2_folders:
                b2modelbpmlist,b2bpmdata=getmodelBPMs(beam2_model)
                b2rdtdata=getrdt_omc3(ldb,b2modelbpmlist,b2bpmdata,beam2_ref_folder,beam2_folders,knob,output_path,rdt,rdt_plane,rdtfolder)
                write_RDTshifts(b2rdtdata, rdt, rdt_plane, "b2", output_path)
                self.analysis_text.insert(tk.END, "Beam 2 Analysis Completed Successfully.\n")

            self.canvas.draw()
            self.notebook.select(self.analysis_tab)

        except Exception as e:
            messagebox.showerror("Error", f"An error occurred: {e}")

if __name__ == "__main__":
    root = tk.Tk()
    app = RDTFeeddownGUI(root)
    root.mainloop()
