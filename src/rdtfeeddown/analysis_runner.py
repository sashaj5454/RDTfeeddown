import json
from qtpy.QtWidgets import QApplication, QMessageBox
from .analysis import group_datasets
from .data_handler import load_RDTdata, save_RDTdata

def run_analysis(parent):
    parent.input_progress.show()
    QApplication.processEvents()
    # Validate RDT and RDT plane
    rdt = parent.rdt_entry.text().strip()
    rdt_plane = parent.rdt_plane_dropdown.currentText().strip()
    if not rdt or not rdt_plane:
        QMessageBox.critical(parent, "Error", "RDT and RDT plane must be specified!")
        parent.input_progress.hide()
        return
    is_valid_rdt, rdt_message = validate_rdt_and_plane(rdt, rdt_plane)
    if not is_valid_rdt:
        QMessageBox.critical(parent, "Error", f"Invalid RDT or RDT plane: {rdt_message}")
        parent.input_progress.hide()
        return
    # Validate knob
    knob = parent.knob_entry.text().strip()
    if not knob:
        QMessageBox.critical(parent, "Error", "Knob must be specified!")
        parent.input_progress.hide()
        return
    is_valid_knob, knob_message = validate_knob(initialize_statetracker(), knob)
    if not is_valid_knob:
        QMessageBox.critical(parent, "Error", f"Invalid Knob: {knob_message}")
        parent.input_progress.hide()
        return
    # Validate models
    beam1_model = parent.beam1_model_entry.text().strip()
    beam2_model = parent.beam2_model_entry.text().strip()
    if not beam1_model and not beam2_model:
        QMessageBox.critical(parent, "Error", "At least one beam model must be specified!")
        parent.input_progress.hide()
        return
    # Validate reference folders
    beam1_reffolder = parent.beam1_reffolder_entry.text().strip()
    beam2_reffolder = parent.beam2_reffolder_entry.text().strip()
    if not beam1_reffolder and not beam2_reffolder:
        QMessageBox.critical(parent, "Error", "At least one reference folder must be specified!")
        parent.input_progress.hide()
        return
    # Validate measurement folders
    beam1_folders = [parent.beam1_folders_list.item(i).text() for i in range(parent.beam1_folders_list.count())]
    beam2_folders = [parent.beam2_folders_list.item(i).text() for i in range(parent.beam2_folders_list.count())]
    if not beam1_folders and not beam2_folders:
        QMessageBox.critical(parent, "Error", "At least one measurement folder must be specified!")
        parent.input_progress.hide()
        return
    # Run analysis
    try:
        parent.b1rdtdata, parent.b2rdtdata, parent.rdt, parent.rdt_plane = run_analysis_logic(
            beam1_model, beam2_model, beam1_reffolder, beam2_reffolder, beam1_folders, beam2_folders, rdt, rdt_plane, knob, parent.log_error
        )
        parent.update_validation_files_widget()
        QMessageBox.information(parent, "Analysis Complete", "Analysis completed successfully.")
    except Exception as e:
        parent.log_error(f"Error running analysis: {e}")
    parent.input_progress.hide()

def run_analysis_logic(beam1_model, beam2_model, beam1_reffolder, beam2_reffolder, beam1_folders, beam2_folders, rdt, rdt_plane, knob, log_func):
    # Placeholder for the actual analysis logic
    # This function should contain the core logic for running the analysis
    # and return the results (b1rdtdata, b2rdtdata, rdt, rdt_plane)
    pass

def run_response(parent):
    parent.simcorr_progress.show()
    QApplication.processEvents()
    # Validate RDT and RDT plane
    rdt = parent.corr_rdt_entry.text().strip()
    rdt_plane = parent.corr_rdt_plane_dropdown.currentText().strip()
    if not rdt or not rdt_plane:
        QMessageBox.critical(parent, "Error", "RDT and RDT plane must be specified!")
        parent.simcorr_progress.hide()
        return
    is_valid_rdt, rdt_message = validate_rdt_and_plane(rdt, rdt_plane)
    if not is_valid_rdt:
        QMessageBox.critical(parent, "Error", f"Invalid RDT or RDT plane: {rdt_message}")
        parent.simcorr_progress.hide()
        return
    # Validate reference folders
    beam1_reffolder = parent.corr_beam1_reffolder_entry.text().strip()
    beam2_reffolder = parent.corr_beam2_reffolder_entry.text().strip()
    if not beam1_reffolder and not beam2_reffolder:
        QMessageBox.critical(parent, "Error", "At least one reference folder must be specified!")
        parent.simcorr_progress.hide()
        return
    # Validate measurement folders
    beam1_measfolder = parent.corr_beam1_measfolder_entry.text().strip()
    beam2_measfolder = parent.corr_beam2_measfolder_entry.text().strip()
    if not beam1_measfolder and not beam2_measfolder:
        QMessageBox.critical(parent, "Error", "At least one measurement folder must be specified!")
        parent.simcorr_progress.hide()
        return
    # Validate knobs
    if parent.b1andb2same_checkbox.isChecked():
        knob_name = parent.corr_knobname_entry.text().strip()
        knob_value = parent.corr_knob_entry.text().strip()
        xing = parent.corr_xing_entry.text().strip()
        if not knob_name or not knob_value or not xing:
            QMessageBox.critical(parent, "Error", "Knob name, value, and XING must be specified!")
            parent.simcorr_progress.hide()
            return
    else:
        b1_knob_name = parent.b1_corr_knobname_entry.text().strip()
        b1_knob_value = parent.b1_corr_knob_entry.text().strip()
        b1_xing = parent.b1_corr_xing_entry.text().strip()
        b2_knob_name = parent.b2_corr_knobname_entry.text().strip()
        b2_knob_value = parent.b2_corr_knob_entry.text().strip()
        b2_xing = parent.b2_corr_xing_entry.text().strip()
        if not b1_knob_name or not b1_knob_value or not b1_xing or not b2_knob_name or not b2_knob_value or not b2_xing:
            QMessageBox.critical(parent, "Error", "Knob names, values, and XINGs must be specified for both beams!")
            parent.simcorr_progress.hide()
            return
    # Run response
    try:
        parent.b1_response_meas, parent.b2_response_meas = run_response_logic(
            beam1_reffolder, beam2_reffolder, beam1_measfolder, beam2_measfolder, rdt, rdt_plane, parent.b1andb2same_checkbox.isChecked(),
            knob_name, knob_value, xing, b1_knob_name, b1_knob_value, b1_xing, b2_knob_name, b2_knob_value, b2_xing, parent.log_error
        )
        parent.plot_loaded_correction_files()
        QMessageBox.information(parent, "Response Complete", "Response analysis completed successfully.")
    except Exception as e:
        parent.log_error(f"Error running response analysis: {e}")
    parent.simcorr_progress.hide()

def run_response_logic(beam1_reffolder, beam2_reffolder, beam1_measfolder, beam2_measfolder, rdt, rdt_plane, b1andb2same, knob_name, knob_value, xing, b1_knob_name, b1_knob_value, b1_xing, b2_knob_name, b2_knob_value, b2_xing, log_func):
    # Placeholder for the actual response logic
    # This function should contain the core logic for running the response analysis
    # and return the results (b1_response_meas, b2_response_meas)
    pass
