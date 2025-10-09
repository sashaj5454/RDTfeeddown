from pathlib import Path
from typing import Literal

from qtpy.QtWidgets import (
    QApplication,
    QFileDialog,
    QMessageBox,
    QTreeWidgetItem,
    QWidget,
)

from rdtfeeddown.analysis import fit_bpm, getrdt_omc3, getrdt_sim, group_datasets
from rdtfeeddown.data_handler import (
    load_rdtdata,
    save_b1_rdtdata,
    save_b2_rdtdata,
    save_rdtdata,
)
from rdtfeeddown.utils import (
    getmodelbpms,
    initialize_statetracker,
    rdt_to_order_and_type,
)
from rdtfeeddown.validation_utils import (
    validate_file_structure,
    validate_knob,
    validate_rdt_and_plane,
)

# --- Validation helpers ---


def validate_rdt_and_plane_fields(parent=None, rdt=None, rdt_plane=None, log_func=None):
    if parent:
        rdt = parent.rdt_entry.text().strip()
        rdt_plane = parent.rdt_plane_dropdown.currentText().strip()
        log_func = parent.log_error
    if not rdt or not rdt_plane:
        if log_func:
            log_func("RDT and RDT plane must be specified!")
        return None, None, False
    is_valid_rdt, rdt_message = validate_rdt_and_plane(rdt, rdt_plane)
    if not is_valid_rdt:
        if log_func:
            log_func(f"Invalid RDT or RDT plane: {rdt_message}")
        return None, None, False
    return rdt, rdt_plane, True


def validate_knob_field(
    parent=None, ldb=None, knob=None, simulation_checkbox=None, log_func=None
):
    if parent:
        knob = parent.knob_entry.text().strip()
        simulation_checkbox = parent.simulation_checkbox.isChecked()
        log_func = parent.log_error
    if not knob:
        if log_func:
            log_func("Knob must be specified!")
        return None, False
    if not simulation_checkbox:
        is_valid_knob, knob_message = validate_knob(ldb, knob)
        if not is_valid_knob:
            if log_func:
                log_func(f"Invalid Knob: {knob_message}")
            return None, False
    return knob, True


def validate_model_and_ref_fields(
    parent=None,
    beam1_model=None,
    beam2_model=None,
    beam1_reffolder=None,
    beam2_reffolder=None,
    log_func=None,
):
    if parent:
        beam1_model = parent.beam1_model_entry.text().strip()
        beam2_model = parent.beam2_model_entry.text().strip()
        beam1_reffolder = parent.beam1_reffolder_entry.text().strip()
        beam2_reffolder = parent.beam2_reffolder_entry.text().strip()
        log_func = parent.log_error
    if not beam1_model and not beam2_model:
        if log_func:
            log_func("At least one beam model must be specified!")
        return None, None, False
    if not beam1_reffolder and not beam2_reffolder:
        if log_func:
            log_func("At least one reference folder must be specified!")
        return None, None, False
    return (beam1_model, beam2_model, beam1_reffolder, beam2_reffolder, True)


def validate_measurement_folders(
    parent=None, beam1_folders=None, beam2_folders=None, log_func=None
):
    if parent:
        beam1_folders = [
            parent.beam1_folders_list.item(i).text()
            for i in range(parent.beam1_folders_list.count())
        ]
        beam2_folders = [
            parent.beam2_folders_list.item(i).text()
            for i in range(parent.beam2_folders_list.count())
        ]
        log_func = parent.log_error
    if not beam1_folders and not beam2_folders:
        if log_func:
            log_func("At least one measurement folder must be specified!")
        return None, None, False
    return beam1_folders, beam2_folders, True


# --- Analysis logic helpers ---


def handle_beam_analysis(
    parent: QWidget = None,
    ldb: callable = None,
    beam_model: Path = None,
    beam_folders: list[Path] = None,
    beam_reffolder: Path = None,
    knob: str = None,
    rdt: str = None,
    rdt_plane: Literal["x", "y"] = "x",
    rdt_folder: str = None,
    beam_label: str = None,
    simulation_checkbox: bool = None,
    simulation_file: Path = None,
    log_func: callable = None,
):
    if parent:
        simulation_checkbox = parent.simulation_checkbox.isChecked()
        simulation_file = parent.simulation_file_entry.text()
        log_func = parent.log_error
    if beam_model and beam_folders:
        modelbpmlist, bpmdata = getmodelbpms(beam_model)
        return getrdt_omc3(
            ldb,
            beam_label,
            modelbpmlist,
            bpmdata,
            beam_reffolder,
            beam_folders,
            knob,
            rdt,
            rdt_plane,
            rdt_folder,
            simulation_checkbox,
            simulation_file,
            log_func=log_func,
        )
    return None


def save_analysis_outputs(
    parent=None,
    beam1_model=None,
    beam1_folders=None,
    beam2_model=None,
    beam2_folders=None,
    analysis_output_files=None,
):
    if parent:
        parent.analysis_output_files = []
        if beam1_model and beam1_folders:
            save_b1_rdtdata(parent)
        if beam2_model and beam2_folders:
            save_b2_rdtdata(parent)
    else:
        pass


def update_loaded_files_list(
    parent=None, output_files=None, loaded_files_list=None, log_func=None
):
    loaded_output_data = []
    if parent:
        loaded_files_list = parent.loaded_files_list
        log_func = parent.log_error
        output_files = parent.analysis_output_files
        loaded_files_list.clear()
        existing_files = [
            loaded_files_list.topLevelItem(i).text(0)
            for i in range(loaded_files_list.topLevelItemCount())
        ]
    else:
        existing_files = []
    for f in output_files:
        if f not in existing_files:
            data = load_rdtdata(f)
            valid = validate_file_structure(
                data, ["beam", "ref", "rdt", "rdt_plane", "knob"], log_func
            )
            if not valid:
                if log_func:
                    log_func(f"Invalid file structure for {f}.")
                continue
            if parent:
                parent.rdt = data.get("metadata", {}).get("rdt", "Unknown RDT")
                parent.rdt_plane = data.get("metadata", {}).get(
                    "rdt_plane", "Unknown Plane"
                )
                parent.corrector = data.get("metadata", {}).get(
                    "knob", "Unknown Corrector"
                )
                beam = data.get("metadata", {}).get("beam", "Unknown Beam")
                item = QTreeWidgetItem(
                    [f, beam, parent.rdt, parent.rdt_plane, parent.corrector]
                )
                loaded_files_list.addTopLevelItem(item)
            loaded_output_data.append(data)
    return loaded_output_data


def finalize_grouped_results(
    parent: QWidget = None, loaded_output_data=None, log_func=None
):
    if parent:
        log_func = parent.log_error
    results = group_datasets(loaded_output_data, log_func)
    if len(results) < 4:
        if log_func:
            log_func("Not enough data from group_datasets.")
        if parent:
            parent.input_progress.hide()
        return False
    if parent:
        parent.b1rdtdata, parent.b2rdtdata, parent.rdt, parent.rdt_plane = results
        if parent.b1rdtdata is None and parent.b2rdtdata is None:
            parent.loaded_files_list.clear()
            parent.input_progress.hide()
            return False
    return True


# --- Main entry point ---


def run_analysis(parent=None, **kwargs):
    """
    Runs the RDT feeddown analysis.

    :param parent: Parent GUI widget (optional).
    :type parent: QWidget or None

    Keyword Arguments:
        beam1_model (str or Path): Path to the LHCB1 model file.
        beam2_model (str or Path): Path to the LHCB2 model file.
        beam1_reffolder (str or Path): Path to the LHCB1 reference folder.
        beam2_reffolder (str or Path): Path to the LHCB2 reference folder.
        beam1_folders (list[str] or list[Path]): List of LHCB1 measurement folders.
        beam2_folders (list[str] or list[Path]): List of LHCB2 measurement folders.
        knob (str): Knob name for analysis.
        rdt (str): RDT type (in form of "1020" for example).
        rdt_plane (str): RDT plane ("x" or "y").
        rdt_folder (str): Magnet folder in RDT folder.
        simulation_checkbox (bool): Whether simulation data is used.
        simulation_file (str or Path): Path to file for knob values if not available on Timber.
        log_func (callable): Logging function.
        b1filename (str or Path): Output filename for LHCB1.
        b2filename (str or Path): Output filename for LHCB2.

    :returns: Analysis results for LHCB1 and LHCB2 in file usable for plotting and matching with response.
    :rtype: tuple
    """
    if parent:
        parent.input_progress.show()
        QApplication.processEvents()
        ldb = None
        rdt, rdt_plane, ok = validate_rdt_and_plane_fields(parent)
        if not ok:
            parent.input_progress.hide()
            return None
        rdt_folder = rdt_to_order_and_type(rdt)
        if not parent.simulation_checkbox.isChecked():
            ldb = initialize_statetracker()
            knob, ok = validate_knob_field(parent, ldb)
        if not ok:
            parent.input_progress.hide()
            return None
        models_refs = validate_model_and_ref_fields(parent)
        if not models_refs[-1]:
            parent.input_progress.hide()
            return None
        beam1_model, beam2_model, beam1_reffolder, beam2_reffolder, _ = models_refs
        beam1_folders, beam2_folders, ok = validate_measurement_folders(parent)
        if not ok:
            parent.input_progress.hide()
            return None
        try:
            parent.b1rdtdata = handle_beam_analysis(
                parent,
                ldb,
                beam1_model,
                beam1_folders,
                beam1_reffolder,
                knob,
                rdt,
                rdt_plane,
                rdt_folder,
                "LHCB1",
                parent.simulation_checkbox.isChecked(),
                parent.simulation_file_entry.text(),
                parent.log_error,
            )
            QApplication.processEvents()
            parent.b2rdtdata = handle_beam_analysis(
                parent,
                ldb,
                beam2_model,
                beam2_folders,
                beam2_reffolder,
                knob,
                rdt,
                rdt_plane,
                rdt_folder,
                "LHCB2",
                parent.simulation_checkbox.isChecked(),
                parent.simulation_file_entry.text(),
                parent.log_error,
            )
            QApplication.processEvents()
            save_analysis_outputs(
                parent, beam1_model, beam1_folders, beam2_model, beam2_folders
            )
            loaded_output_data = update_loaded_files_list(parent)
            if not finalize_grouped_results(parent, loaded_output_data):
                return None
            parent.update_validation_files_widget()
            QMessageBox.information(
                parent, "Analysis Complete", "Analysis completed successfully."
            )
        except RuntimeError as e:
            parent.log_error(f"Error running analysis: {e}", e)
            parent.input_progress.hide()
        parent.input_progress.hide()
    else:
        ldb = None
        log_func = kwargs.get("log_func", print)
        rdt = kwargs.get("rdt")
        rdt_plane = kwargs.get("rdt_plane")
        rdt_folder = kwargs.get(
            "rdt_folder", rdt_to_order_and_type(rdt) if rdt else None
        )
        knob = kwargs.get("knob")
        beam1_model = kwargs.get("beam1_model")
        beam2_model = kwargs.get("beam2_model")
        beam1_reffolder = kwargs.get("beam1_reffolder")
        beam2_reffolder = kwargs.get("beam2_reffolder")
        beam1_folders = kwargs.get("beam1_folders")
        beam2_folders = kwargs.get("beam2_folders")
        b1filename, b2filename = (
            kwargs.get("b1filename", ""),
            kwargs.get("b2filename", ""),
        )
        simulation_checkbox = kwargs.get("simulation_checkbox", False)
        if not simulation_checkbox:
            ldb = initialize_statetracker()
            is_valid_knob, knob_message = validate_knob(ldb, knob)
            if not is_valid_knob:
                if kwargs.get("log_func"):
                    kwargs["log_func"](f"Invalid Knob: {knob_message}")
                return None, None
        simulation_file = kwargs.get("simulation_file", "")
        b1rdtdata = handle_beam_analysis(
            None,
            ldb,
            Path(beam1_model) if beam1_model is not None else None,
            [Path(f) for f in beam1_folders] if beam1_folders is not None else None,
            Path(beam1_reffolder) if beam1_reffolder is not None else None,
            knob,
            knob,
            rdt,
            rdt_plane,
            rdt_folder,
            "LHCB1",
            simulation_checkbox,
            simulation_file,
            log_func,
        )
        b2rdtdata = handle_beam_analysis(
            None,
            ldb,
            beam2_model,
            beam2_folders,
            beam2_reffolder,
            knob,
            rdt,
            rdt_plane,
            rdt_folder,
            "LHCB2",
            simulation_checkbox,
            simulation_file,
            log_func,
        )
        save_rdtdata(b1rdtdata, b1filename)
        save_rdtdata(b2rdtdata, b2filename)
        return b1rdtdata, b2rdtdata
    return None


# --- Response validation helpers ---


def validate_corr_rdt_and_plane(parent=None, rdt=None, rdt_plane=None, log_func=None):
    if parent:
        rdt = parent.corr_rdt_entry.text().strip()
        rdt_plane = parent.corr_rdt_plane_dropdown.currentText().strip()
        parent.rdt = rdt
        parent.rdt_plane = rdt_plane
        log_func = parent.log_error
    if not rdt or not rdt_plane:
        if log_func:
            log_func("RDT and RDT plane must be specified!")
        return None, None, False
    is_valid_rdt, rdt_message = validate_rdt_and_plane(rdt, rdt_plane)
    if not is_valid_rdt:
        if log_func:
            log_func(f"Invalid RDT or RDT plane: {rdt_message}")
        return None, None, False
    return rdt, rdt_plane, True


def validate_corr_ref_and_meas_folders(
    parent=None,
    beam1_reffolder=None,
    beam2_reffolder=None,
    beam1_measfolder=None,
    beam2_measfolder=None,
    log_func=None,
):
    if parent:
        beam1_reffolder = parent.corr_beam1_reffolder_entry.text().strip()
        beam2_reffolder = parent.corr_beam2_reffolder_entry.text().strip()
        beam1_measfolder = parent.corr_beam1_measfolder_entry.text().strip()
        beam2_measfolder = parent.corr_beam2_measfolder_entry.text().strip()
        log_func = parent.log_error
    if not beam1_reffolder and not beam2_reffolder:
        if log_func:
            log_func("At least one reference folder must be specified!")
        return None, None, None, None, False
    if not beam1_measfolder and not beam2_measfolder:
        if log_func:
            log_func("At least one measurement folder must be specified!")
        return None, None, None, None, False
    return beam1_reffolder, beam2_reffolder, beam1_measfolder, beam2_measfolder, True


def validate_corr_knobs(
    parent=None,
    b1_knob_name=None,
    b1_knob_value=None,
    b1_xing=None,
    b2_knob_name=None,
    b2_knob_value=None,
    b2_xing=None,
    b1andb2same=None,
    log_func=None,
):
    if parent:
        b1andb2same = parent.b1andb2same_checkbox.isChecked()
        log_func = parent.log_error
    if b1andb2same:
        if parent:
            b1_knob_name = parent.corr_knobname_entry.text().strip()
            b2_knob_name = b1_knob_name
            b1_knob_value = parent.corr_knob_entry.text().strip()
            b2_knob_value = b1_knob_value
            b1_xing = parent.corr_xing_entry.text().strip()
            b2_xing = b1_xing
        if not b1_knob_name or not b1_knob_value or not b1_xing:
            if log_func:
                log_func("Knob name, value, and XING must be specified!")
            return None, None, None, None, None, None, False
    else:
        if parent:
            b1_knob_name = parent.b1_corr_knobname_entry.text().strip()
            b1_knob_value = parent.b1_corr_knob_entry.text().strip()
            b1_xing = parent.b1_corr_xing_entry.text().strip()
            b2_knob_name = parent.b2_corr_knobname_entry.text().strip()
            b2_knob_value = parent.b2_corr_knob_entry.text().strip()
            b2_xing = parent.b2_corr_xing_entry.text().strip()
        if (b1_knob_name or b1_knob_value or b1_xing) and not (
            b1_knob_name and b1_knob_value and b1_xing
        ):
            if log_func:
                log_func(
                    "For LHCB1, if any knob fields are specified, then all (name, value, and XING) must be provided!"
                )
            return None, None, None, None, None, None, False
        if (b2_knob_name or b2_knob_value or b2_xing) and not (
            b2_knob_name and b2_knob_value and b2_xing
        ):
            if log_func:
                log_func(
                    "For LHCB2, if any knob fields are specified, then all (name, value, and XING) must be provided!"
                )
            return None, None, None, None, None, None, False
    return (
        b1_knob_name,
        b1_knob_value,
        b1_xing,
        b2_knob_name,
        b2_knob_value,
        b2_xing,
        True,
    )


def get_save_filenames(
    parent=None,
    beam1_reffolder=None,
    beam2_reffolder=None,
    beam1_measfolder=None,
    beam2_measfolder=None,
):
    filenameb1 = None
    filenameb2 = None
    default_output_path = parent.default_output_path
    if beam1_reffolder and beam1_measfolder:
        filenameb1, _ = QFileDialog.getSaveFileName(
            parent, "Save LHCB1 RDT Data", default_output_path, "JSON Files (*.json)"
        )
    if beam2_reffolder and beam2_measfolder:
        filenameb2, _ = QFileDialog.getSaveFileName(
            parent, "Save LHCB2 RDT Data", default_output_path, "JSON Files (*.json)"
        )
    return filenameb1, filenameb2


# --- Modular run_response ---


def run_response(parent=None, **kwargs):
    """
    Runs the RDT feeddown response analysis.

    :param parent: Parent GUI widget (optional).
    :type parent: QWidget or None

    Keyword Arguments:
        rdt (str): RDT type (in form of "1020" for example).
        rdt_plane (str): RDT plane ("x" or "y").
        rdt_folder (str): Magnet folder in RDT folder.
        beam1_reffolder (str or Path): Path to the LHCB1 reference folder.
        beam2_reffolder (str or Path): Path to the LHCB2 reference folder.
        beam1_measfolder (str or Path): Path to the LHCB1 measurement folder.
        beam2_measfolder (str or Path): Path to the LHCB2 measurement folder.
        b1_knob_name (str): Corrector name for LHCB1.
        b1_knob_value (str): Corrector value for LHCB1.
        b1_xing (str): Difference in crossing angle value for LHCB1.
        b2_knob_name (str): Corrector name for LHCB2.
        b2_knob_value (str): Corrector value for LHCB2.
        b2_xing (str): Difference in crossing angle value for LHCB2.
        filenameb1 (str or Path): Output filename for LHCB1.
        filenameb2 (str or Path): Output filename for LHCB2.
        log_func (callable): Logging function.

    :returns: Response results for LHCB1 and LHCB2 in file usable for plotting and matching the measurement.
    :rtype: dict or None
    """
    if parent:
        parent.simcorr_progress.show()
        QApplication.processEvents()
        rdt, rdt_plane, ok = validate_corr_rdt_and_plane(parent)
        if not ok:
            parent.simcorr_progress.hide()
            return None
        rdt_folder = rdt_to_order_and_type(rdt)
        beam1_reffolder, beam2_reffolder, beam1_measfolder, beam2_measfolder, ok = (
            validate_corr_ref_and_meas_folders(parent)
        )
        if not ok:
            parent.simcorr_progress.hide()
            return None
        (
            b1_knob_name,
            b1_knob_value,
            b1_xing,
            b2_knob_name,
            b2_knob_value,
            b2_xing,
            ok,
        ) = validate_corr_knobs(parent)
        if not ok:
            parent.simcorr_progress.hide()
            return None
        try:
            run_response_logic(
                parent,
                parent.default_output_path,
                beam1_reffolder,
                beam2_reffolder,
                beam1_measfolder,
                beam2_measfolder,
                rdt,
                rdt_plane,
                rdt_folder,
                b1_knob_name,
                b1_knob_value,
                b1_xing,
                b2_knob_name,
                b2_knob_value,
                b2_xing,
                parent.log_error,
            )
            QMessageBox.information(
                parent, "Response Complete", "Response analysis completed successfully."
            )
        except RuntimeError as e:
            parent.log_error(f"Error running response analysis: {e}", e)
        parent.simcorr_progress.hide()
    else:
        log_func = kwargs.get("log_func", print)
        rdt = kwargs.get("rdt")
        rdt_plane = kwargs.get("rdt_plane")
        rdt_folder = kwargs.get(
            "rdt_folder", rdt_to_order_and_type(rdt) if rdt else None
        )
        beam1_reffolder = kwargs.get("beam1_reffolder")
        beam2_reffolder = kwargs.get("beam2_reffolder")
        beam1_measfolder = kwargs.get("beam1_measfolder")
        beam2_measfolder = kwargs.get("beam2_measfolder")
        b1_knob_name = kwargs.get("b1_knob_name")
        b1_knob_value = kwargs.get("b1_knob_value")
        b1_xing = kwargs.get("b1_xing")
        b2_knob_name = kwargs.get("b2_knob_name")
        b2_knob_value = kwargs.get("b2_knob_value")
        b2_xing = kwargs.get("b2_xing")
        filenameb1, filenameb2 = (
            kwargs.get("filenameb1", ""),
            kwargs.get("filenameb2", ""),
        )
        results = {}
        if filenameb1:
            if not filenameb1.lower().endswith(".json"):
                filenameb1 += ".json"
            b1response = getrdt_sim(
                "LHCB1",
                beam1_reffolder,
                beam1_measfolder,
                b1_xing,
                b1_knob_name,
                b1_knob_value,
                rdt,
                rdt_plane,
                rdt_folder,
                log_func=log_func,
            )
            save_rdtdata(b1response, filenameb1)
            results["LHCB1"] = b1response
        if filenameb2:
            if not filenameb2.lower().endswith(".json"):
                filenameb2 += ".json"
            b2response = getrdt_sim(
                "LHCB2",
                beam2_reffolder,
                beam2_measfolder,
                b2_xing,
                b2_knob_name,
                b2_knob_value,
                rdt,
                rdt_plane,
                rdt_folder,
                log_func=log_func,
            )
            save_rdtdata(b2response, filenameb2)
            results["LHCB2"] = b2response
        return results
    return None


def run_response_logic(
    parent,
    default_output_path,
    beam1_reffolder,
    beam2_reffolder,
    beam1_measfolder,
    beam2_measfolder,
    rdt,
    rdt_plane,
    rdt_folder,
    b1_knob_name,
    b1_knob_value,
    b1_xing,
    b2_knob_name,
    b2_knob_value,
    b2_xing,
    log_func,
):
    filenameb1, filenameb2 = get_save_filenames(
        parent,
        beam1_reffolder,
        beam2_reffolder,
        beam1_measfolder,
        beam2_measfolder,
    )
    if filenameb1 == "" and filenameb2 == "":
        log_func("No output file selected.")
        if parent:
            parent.simcorr_progress.hide()
        return
    if filenameb1:
        if not filenameb1.lower().endswith(".json"):
            filenameb1 += ".json"
        try:
            b1response = getrdt_sim(
                "LHCB1",
                beam1_reffolder,
                beam1_measfolder,
                b1_xing,
                b1_knob_name,
                b1_knob_value,
                rdt,
                rdt_plane,
                rdt_folder,
                log_func=log_func,
            )
            if parent:
                parent.corr_responses[filenameb1] = b1response
                save_rdtdata(b1response, filenameb1)
                item = QTreeWidgetItem(
                    [filenameb1, "LHCB1", rdt, rdt_plane, b1_knob_name]
                )
                parent.correction_loaded_files_list.addTopLevelItem(item)
                parent.populate_knob_manager()
            else:
                save_rdtdata(b1response, filenameb1)
        except RuntimeError as e:
            log_func(f"Error in getting RDT: {e}")
    else:
        log_func("No output file selected for LHCB1.")
        if parent:
            parent.simcorr_progress.hide()
        return
    if filenameb2:
        if not filenameb2.lower().endswith(".json"):
            filenameb2 += ".json"
        try:
            b2response = getrdt_sim(
                "LHCB2",
                beam2_reffolder,
                beam2_measfolder,
                b2_xing,
                b2_knob_name,
                b2_knob_value,
                rdt,
                rdt_plane,
                rdt_folder,
                log_func=log_func,
            )
            if parent:
                parent.corr_responses[filenameb2] = b2response
                save_rdtdata(b2response, filenameb2)
                item = QTreeWidgetItem(
                    [filenameb2, "LHCB2", rdt, rdt_plane, b2_knob_name]
                )
                parent.correction_loaded_files_list.addTopLevelItem(item)
                parent.populate_knob_manager()
            else:
                save_rdtdata(b2response, filenameb2)
        except RuntimeError as e:
            log_func(f"Error in getting RDT: {e}")
    else:
        log_func("No output file selected for LHCB2.")
        if parent:
            parent.simcorr_progress.hide()
        return
    if parent:
        parent.rdt, parent.rdt_plane = rdt, rdt_plane
        parent.simcorr_progress.hide()
    pass
