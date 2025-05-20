import json
from qtpy.QtWidgets import QApplication, QMessageBox, QFileDialog, QTreeWidgetItem
from .analysis import getrdt_omc3, getrdt_sim, fit_BPM, group_datasets
from .validation_utils import validate_rdt_and_plane, validate_knob
from .utils import initialize_statetracker, rdt_to_order_and_type, getmodelBPMs
from .data_handler import load_RDTdata, save_RDTdata, save_b1_rdtdata, save_b2_rdtdata
from .validation_utils import validate_file_structure

def run_analysis(parent):
	parent.input_progress.show()
	QApplication.processEvents()
	ldb = None
	
	# Validate RDT and RDT plane
	rdt = parent.rdt_entry.text().strip()
	rdt_plane = parent.rdt_plane_dropdown.currentText().strip()
	if not rdt or not rdt_plane:
		parent.log_error("RDT and RDT plane must be specified!")
		parent.input_progress.hide()
		return
	is_valid_rdt, rdt_message = validate_rdt_and_plane(rdt, rdt_plane)
	if not is_valid_rdt:
		parent.log_error(f"Invalid RDT or RDT plane: {rdt_message}")
		parent.input_progress.hide()
		return
	rdt_folder = rdt_to_order_and_type(rdt)
	# Validate knob
	knob = parent.knob_entry.text().strip()
	if not knob:
		parent.log_error("Knob must be specified!")
		parent.input_progress.hide()
		return
	if not parent.simulation_checkbox.isChecked():
		ldb = initialize_statetracker()
		is_valid_knob, knob_message = validate_knob(ldb, knob)
		if not is_valid_knob:
			parent.log_error(f"Invalid Knob: {knob_message}")
			parent.input_progress.hide()
			return
	if not is_valid_knob:
		parent.log_error(f"Invalid Knob: {knob_message}")
		parent.input_progress.hide()
		return
	# Validate models
	beam1_model = parent.beam1_model_entry.text().strip()
	beam2_model = parent.beam2_model_entry.text().strip()
	if not beam1_model and not beam2_model:
		parent.log_error("At least one beam model must be specified!")
		parent.input_progress.hide()
		return
	# Validate reference folders
	beam1_reffolder = parent.beam1_reffolder_entry.text().strip()
	beam2_reffolder = parent.beam2_reffolder_entry.text().strip()
	if not beam1_reffolder and not beam2_reffolder:
		parent.log_error("At least one reference folder must be specified!")
		parent.input_progress.hide()
		return
	# Validate measurement folders
	beam1_folders = [parent.beam1_folders_list.item(i).text() for i in range(parent.beam1_folders_list.count())]
	beam2_folders = [parent.beam2_folders_list.item(i).text() for i in range(parent.beam2_folders_list.count())]
	if not beam1_folders and not beam2_folders:
		parent.log_error("At least one measurement folder must be specified!")
		parent.input_progress.hide()
		return

	# Run analysis
	try:
		run_analysis_logic(
			parent, ldb, beam1_model, beam2_model, beam1_reffolder, beam2_reffolder, beam1_folders, beam2_folders, rdt, rdt_plane, rdt_folder, knob
		)
		parent.update_validation_files_widget()
		QMessageBox.information(parent, "Analysis Complete", "Analysis completed successfully.")
	except Exception as e:
		parent.log_error(f"Error running analysis: {e}")
		parent.input_progress.hide()
	parent.input_progress.hide()

def run_analysis_logic(parent, ldb, beam1_model, beam2_model, beam1_reffolder, beam2_reffolder, beam1_folders, beam2_folders, rdt, rdt_plane, rdt_folder, knob):
	if beam1_model and beam1_folders:
			b1modelbpmlist, b1bpmdata = getmodelBPMs(beam1_model)
			parent.b1rdtdata = getrdt_omc3(ldb, "LHCB1", b1modelbpmlist, b1bpmdata,
										  beam1_reffolder, beam1_folders,
										  knob, rdt, rdt_plane, 
										  rdt_folder,
										  parent.simulation_checkbox.isChecked(), 
										  parent.simulation_file_entry.text(),
										#   parent.threshold,
										  log_func=parent.log_error)
			parent.b1rdtdata = fit_BPM(parent.b1rdtdata)
	QApplication.processEvents()
	if beam2_model and beam2_folders:
		b2modelbpmlist, b2bpmdata = getmodelBPMs(beam2_model)
		parent.b2rdtdata = getrdt_omc3(ldb, "LHCB2", b2modelbpmlist, b2bpmdata,
										beam2_reffolder, beam2_folders,
										knob, rdt, rdt_plane, 
										rdt_folder, 
										parent.simulation_checkbox.isChecked(), 
										parent.simulation_file_entry.text(),
										# parent.threshold,
										log_func=parent.log_error)
		parent.b2rdtdata = fit_BPM(parent.b2rdtdata)
	QApplication.processEvents()
	# Prompt to save LHCB1 RDT data just before calling write_RDTshifts
	parent.analysis_output_files = []
	if beam1_model and beam1_folders:
		save_b1_rdtdata(parent)
	if beam2_model and beam2_folders:
		save_b2_rdtdata(parent)

	loaded_output_data = []
	parent.loaded_files_list.clear()
	# Check if the file is already in the TreeWidget
	existing_files = [
		parent.loaded_files_list.topLevelItem(i).text(0)  # Assuming column 0 contains the file name
		for i in range(parent.loaded_files_list.topLevelItemCount())
	]
	for f in parent.analysis_output_files:
		if f not in existing_files:
			data = load_RDTdata(f)
			valid = validate_file_structure(data, ['beam', 'ref', 'rdt', 'rdt_plane', 'knob'], parent.log_error)
			if not valid:
				parent.log_error(f"Invalid file structure for {f}.")
				continue
			parent.rdt = data.get("metadata", {}).get("rdt", "Unknown RDT")
			parent.rdt_plane = data.get("metadata", {}).get("rdt_plane", "Unknown Plane")
			parent.corrector = data.get("metadata", {}).get("knob", "Unknown Corrector")
			beam = data.get("metadata", {}).get("beam", "Unknown Beam")
			item = QTreeWidgetItem([f, beam, parent.rdt, parent.rdt_plane, parent.corrector])
			parent.loaded_files_list.addTopLevelItem(item)
		loaded_output_data.append(data)
	results = group_datasets(loaded_output_data, parent.log_error)
	if len(results) < 4:
		parent.log_error("Not enough data from group_datasets.")
		parent.input_progress.hide()
		return
	parent.b1rdtdata, parent.b2rdtdata, parent.rdt, parent.rdt_plane = results
	if parent.b1rdtdata is None and parent.b2rdtdata is None:
		parent.loaded_files_list.clear()
		parent.input_progress.hide()
		return
	parent.input_progress.hide()
pass

def run_response(parent):
	parent.simcorr_progress.show()
	QApplication.processEvents()
	# Validate RDT and RDT plane
	rdt = parent.corr_rdt_entry.text().strip()
	rdt_plane = parent.corr_rdt_plane_dropdown.currentText().strip()
	parent.rdt = rdt
	parent.rdt_plane = rdt_plane
	if not parent.rdt or not parent.rdt_plane:
		parent.log_error("RDT and RDT plane must be specified!")
		parent.simcorr_progress.hide()
		return
	is_valid_rdt, rdt_message = validate_rdt_and_plane(rdt, rdt_plane)
	if not is_valid_rdt:
		parent.log_error(f"Invalid RDT or RDT plane: {rdt_message}")
		parent.simcorr_progress.hide()
		return
	rdt_folder = rdt_to_order_and_type(rdt)
	# Validate reference folders
	beam1_reffolder = parent.corr_beam1_reffolder_entry.text().strip()
	beam2_reffolder = parent.corr_beam2_reffolder_entry.text().strip()
	if not beam1_reffolder and not beam2_reffolder:
		parent.log_error("At least one reference folder must be specified!")
		parent.simcorr_progress.hide()
		return
	# Validate measurement folders
	beam1_measfolder = parent.corr_beam1_measfolder_entry.text().strip()
	beam2_measfolder = parent.corr_beam2_measfolder_entry.text().strip()
	if not beam1_measfolder and not beam2_measfolder:
		parent.log_error("At least one measurement folder must be specified!")
		parent.simcorr_progress.hide()
		return
	# Validate knobs
	if parent.b1andb2same_checkbox.isChecked():
		b1_knob_name = parent.corr_knobname_entry.text().strip()
		b2_knob_name = b1_knob_name
		b1_knob_value = parent.corr_knob_entry.text().strip()
		b2_knob_value = b1_knob_value
		b1_xing = parent.corr_xing_entry.text().strip()
		b2_xing = b1_xing
		if not b1_knob_name or not b1_knob_value or not b1_xing:
			parent.log_error("Knob name, value, and XING must be specified!")
			parent.simcorr_progress.hide()
			return
	else:
		b1_knob_name = parent.b1_corr_knobname_entry.text().strip()
		b1_knob_value = parent.b1_corr_knob_entry.text().strip()
		b1_xing = parent.b1_corr_xing_entry.text().strip()
		b2_knob_name = parent.b2_corr_knobname_entry.text().strip()
		b2_knob_value = parent.b2_corr_knob_entry.text().strip()
		b2_xing = parent.b2_corr_xing_entry.text().strip()
		# Validate LHCB1 fields
		if (b1_knob_name or b1_knob_value or b1_xing) and not (b1_knob_name and b1_knob_value and b1_xing):
			parent.log_error("For LHCB1, if any knob fields are specified, then all (name, value, and XING) must be provided!")
			parent.simcorr_progress.hide()
			return

		# Validate LHCB2 fields
		if (b2_knob_name or b2_knob_value or b2_xing) and not (b2_knob_name and b2_knob_value and b2_xing):
			parent.log_error("For LHCB2, if any knob fields are specified, then all (name, value, and XING) must be provided!")
			parent.simcorr_progress.hide()
			return
	# Run response
	try:
		run_response_logic(
			parent, parent.default_output_path, beam1_reffolder, beam2_reffolder, beam1_measfolder, beam2_measfolder, rdt, 
			rdt_plane, rdt_folder, b1_knob_name, b1_knob_value, b1_xing, b2_knob_name, b2_knob_value, b2_xing, parent.log_error
		)
		QMessageBox.information(parent, "Response Complete", "Response analysis completed successfully.")
	except Exception as e:
		parent.log_error(f"Error running response analysis: {e}")
	parent.simcorr_progress.hide()

def run_response_logic(parent, default_output_path, beam1_reffolder, beam2_reffolder, beam1_measfolder, beam2_measfolder, 
                       rdt, rdt_plane, rdt_folder, b1_knob_name, b1_knob_value, b1_xing, b2_knob_name, b2_knob_value, b2_xing, log_func):
	filenameb1, filenameb2 = "", ""
	if beam1_reffolder and beam1_measfolder:
			filenameb1, _ = QFileDialog.getSaveFileName(
				parent,
				"Save LHCB1 RDT Data",
				default_output_path,
				"JSON Files (*.json)"
			)
	if beam2_reffolder and beam2_measfolder:
		filenameb2, _ = QFileDialog.getSaveFileName(
			parent,
			"Save LHCB2 RDT Data",
			default_output_path,
			"JSON Files (*.json)"
		) 
	if filenameb1 == "" and filenameb2 == "":
		log_func("No output file selected.")
		parent.simcorr_progress.hide()
		return
	if filenameb1:
		if not filenameb1.lower().endswith(".json"):
			filenameb1 += ".json"
		try:
			b1response = getrdt_sim("LHCB1", beam1_reffolder, beam1_measfolder, b1_xing, 
			b1_knob_name, b1_knob_value, rdt, rdt_plane, rdt_folder, 
			log_func=log_func)
			parent.corr_responses[filenameb1] = b1response
			save_RDTdata(b1response, filenameb1)
			item = QTreeWidgetItem([filenameb1, "LHCB1", rdt, rdt_plane, b1_knob_name])
			parent.correction_loaded_files_list.addTopLevelItem(item)
			parent.populate_knob_manager()
		except Exception as e:
			log_func(f"Error in getting RDT: {e}")
	else: 
		log_func("No output file selected for LHCB1.")
		parent.simcorr_progress.hide()
		return
	if filenameb2:
		if not filenameb2.lower().endswith(".json"):
			filenameb2 += ".json"
		try:
			b2response = getrdt_sim("LHCB2", beam2_reffolder, beam2_measfolder, b2_xing, 
			b2_knob_name, b2_knob_value, rdt, rdt_plane, rdt_folder, 
			log_func=log_func)
			parent.corr_responses[filenameb2] = b2response
			save_RDTdata(b2response, filenameb2)
			item = QTreeWidgetItem([filenameb2, "LHCB2", rdt, rdt_plane, b2_knob_name])
			parent.correction_loaded_files_list.addTopLevelItem(item)
			parent.populate_knob_manager()
		except Exception as e:
			log_func(f"Error in getting RDT: {e}")
	else:
		log_func("No output file selected for LHCB2.")
		parent.simcorr_progress.hide()
		return
	parent.rdt, parent.rdt_plane = rdt, rdt_plane
	parent.simcorr_progress.hide()
	pass
