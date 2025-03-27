import tkinter as tk
from tkinter import filedialog, messagebox
from tkinter import ttk
import os
from analysis import readrdtdatafile, write_RDTshifts, calculate_avg_rdt_shift

class RDTFeeddownGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("RDT Feeddown Analysis")

        # Input file selection
        self.input_frame = ttk.LabelFrame(root, text="Input Files")
        self.input_frame.grid(row=0, column=0, padx=10, pady=10, sticky="ew")

        self.ref_label = ttk.Label(self.input_frame, text="Reference File:")
        self.ref_label.grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.ref_entry = ttk.Entry(self.input_frame, width=50)
        self.ref_entry.grid(row=0, column=1, padx=5, pady=5)
        self.ref_button = ttk.Button(self.input_frame, text="Browse", command=self.select_ref_file)
        self.ref_button.grid(row=0, column=2, padx=5, pady=5)

        self.data_label = ttk.Label(self.input_frame, text="Data Files:")
        self.data_label.grid(row=1, column=0, padx=5, pady=5, sticky="w")
        self.data_entry = ttk.Entry(self.input_frame, width=50)
        self.data_entry.grid(row=1, column=1, padx=5, pady=5)
        self.data_button = ttk.Button(self.input_frame, text="Browse", command=self.select_data_files)
        self.data_button.grid(row=1, column=2, padx=5, pady=5)

        # Parameters
        self.param_frame = ttk.LabelFrame(root, text="Parameters")
        self.param_frame.grid(row=1, column=0, padx=10, pady=10, sticky="ew")

        self.rdt_label = ttk.Label(self.param_frame, text="RDT:")
        self.rdt_label.grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.rdt_entry = ttk.Entry(self.param_frame, width=20)
        self.rdt_entry.grid(row=0, column=1, padx=5, pady=5)

        self.rdt_plane_label = ttk.Label(self.param_frame, text="RDT Plane:")
        self.rdt_plane_label.grid(row=1, column=0, padx=5, pady=5, sticky="w")
        self.rdt_plane_entry = ttk.Entry(self.param_frame, width=20)
        self.rdt_plane_entry.grid(row=1, column=1, padx=5, pady=5)

        self.beam_label = ttk.Label(self.param_frame, text="Beam (b1/b2):")
        self.beam_label.grid(row=2, column=0, padx=5, pady=5, sticky="w")
        self.beam_entry = ttk.Entry(self.param_frame, width=20)
        self.beam_entry.grid(row=2, column=1, padx=5, pady=5)

        # Run button
        self.run_button = ttk.Button(root, text="Run Analysis", command=self.run_analysis)
        self.run_button.grid(row=2, column=0, padx=10, pady=10)

    def select_ref_file(self):
        filepath = filedialog.askopenfilename(title="Select Reference File")
        if filepath:
            self.ref_entry.delete(0, tk.END)
            self.ref_entry.insert(0, filepath)

    def select_data_files(self):
        filepaths = filedialog.askopenfilenames(title="Select Data Files")
        if filepaths:
            self.data_entry.delete(0, tk.END)
            self.data_entry.insert(0, ";".join(filepaths))

    def run_analysis(self):
        ref_file = self.ref_entry.get()
        data_files = self.data_entry.get().split(";")
        rdt = self.rdt_entry.get()
        rdt_plane = self.rdt_plane_entry.get()
        beam = self.beam_entry.get()

        if not ref_file or not data_files or not rdt or not rdt_plane or not beam:
            messagebox.showerror("Error", "All fields must be filled!")
            return

        try:
            # Example: Call the analysis functions
            ref_data = readrdtdatafile(ref_file, rdt, rdt_plane, "folder")
            for data_file in data_files:
                data = readrdtdatafile(data_file, rdt, rdt_plane, "folder")
                # Process data (e.g., write_RDTshifts or other functions)
                write_RDTshifts(data, rdt, rdt_plane, beam)

            messagebox.showinfo("Success", "Analysis completed successfully!")
        except Exception as e:
            messagebox.showerror("Error", f"An error occurred: {e}")

if __name__ == "__main__":
    root = tk.Tk()
    app = RDTFeeddownGUI(root)
    root.mainloop()
