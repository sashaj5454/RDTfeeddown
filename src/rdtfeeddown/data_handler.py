import json
from pathlib import Path

from qtpy.QtWidgets import QApplication, QFileDialog, QMessageBox, QTreeWidgetItem

from rdtfeeddown.analysis import group_datasets
from rdtfeeddown.validation_utils import validate_file_structure


def load_selected_files(parent):
    parent.plot_progress.show()
    QApplication.processEvents()
    selected_files = [
        parent.validation_files_list.item(i).text()
        for i in range(parent.validation_files_list.count())
        if parent.validation_files_list.item(i).isSelected()
    ]

    # Clear the loaded files tree widget
    parent.loaded_files_list.clear()
    loaded_output_data = []
    for file in selected_files:
        data = load_rdtdata(file)
        valid = validate_file_structure(
            data, ["beam", "ref", "rdt", "rdt_plane", "knob"], parent.log_error
        )
        if not valid:
            continue
        loaded_output_data.append(data)
        # Extract metadata for columns
        metadata = data.get("metadata", {})
        beam = metadata.get("beam", "")
        rdt_val = metadata.get("rdt", "")
        rdt_plane = metadata.get("rdt_plane", "")
        knob = metadata.get("knob", "")

        # Create a tree widget item with all columns
        item = QTreeWidgetItem([file, beam, rdt_val, rdt_plane, knob])
        parent.loaded_files_list.addTopLevelItem(item)

    if not loaded_output_data:
        QMessageBox.critical(parent, "Error", "No valid data found.")
        parent.plot_progress.hide()
        return

    results = group_datasets(loaded_output_data, parent.log_error)
    if len(results) < 4:
        QMessageBox.critical(parent, "Error", "Not enough data from group_datasets.")
        parent.plot_progress.hide()
        return

    parent.b1rdtdata, parent.b2rdtdata, parent.rdt, parent.rdt_plane = results
    if parent.b1rdtdata is None and parent.b2rdtdata is None:
        parent.loaded_files_list.clear()
    parent.plot_progress.hide()


def _convert_for_json(obj):
    import numpy as np

    if isinstance(obj, np.ndarray):
        return obj.tolist()
    if isinstance(obj, tuple):
        return list(obj)
    raise TypeError(f"Type {type(obj)} not JSON serializable")


def save_rdtdata(data, filename):
    with Path.open(filename, "w") as fout:
        json.dump(data, fout, default=_convert_for_json)


def load_rdtdata(filename):
    with Path.open(filename, "r") as fin:
        return json.load(fin)


def save_b1_rdtdata(parent):
    filename, _ = QFileDialog.getSaveFileName(
        parent, "Save LHCB1 RDT Data", parent.default_output_path, "JSON Files (*.json)"
    )
    if filename:
        if not filename.lower().endswith(".json"):
            filename += ".json"
        save_rdtdata(parent.b1rdtdata, filename)
        parent.analysis_output_files.append(filename)


def save_b2_rdtdata(parent):
    filename, _ = QFileDialog.getSaveFileName(
        parent, "Save LHCB2 RDT Data", parent.default_output_path, "JSON Files (*.json)"
    )
    if filename:
        if not filename.lower().endswith(".json"):
            filename += ".json"
        save_rdtdata(parent.b2rdtdata, filename)
        parent.analysis_output_files.append(filename)
