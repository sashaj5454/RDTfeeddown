import json
from qtpy.QtWidgets import QApplication, QMessageBox
from .analysis import group_datasets

def load_selected_files(parent):
		parent.plot_progress.show()
		QApplication.processEvents()
		# Load selected file paths from the validation files list into the loaded files list
		selected_files = [parent.validation_files_list.item(i).text() for i in range(parent.validation_files_list.count()) 
						if parent.validation_files_list.item(i).isSelected()]
		parent.loaded_files_list.clear()
		loaded_output_data = []
		for file in selected_files:
			parent.loaded_files_list.addItem(file)
			data = load_RDTdata(file)
			loaded_output_data.append(data)
		results = group_datasets(loaded_output_data, parent.log_error)
		if len(results) < 4:
			QMessageBox.critical(parent, "Error", "Not enough data from group_datasets.")
			return
		parent.b1rdtdata, parent.b2rdtdata, parent.rdt, parent.rdt_plane = results
		if parent.b1rdtdata is None and parent.b2rdtdata is None:
			parent.loaded_files_list.clear()
			return
		
def _convert_for_json(obj):
    import numpy as np
    if isinstance(obj, np.ndarray):
        return obj.tolist()
    if isinstance(obj, tuple):
        return list(obj)
    raise TypeError(f"Type {type(obj)} not JSON serializable")

def save_RDTdata(data, filename):
    with open(filename, 'w') as fout:
        json.dump(data, fout, default=_convert_for_json)

def load_RDTdata(filename):
	with open(filename, 'r') as fin:
		return json.load(fin)