import re
from pathlib import Path

import numpy as np
import tfs
from scipy.optimize import curve_fit
from scipy.stats import zscore

from .utils import csv_to_dict, get_analysis_knobsetting


def filter_outliers(data, threshold=3):
    """
    Filters outliers from data based on Z-scores.

    Parameters
    -  data: list of lists for RDT data
    -  threshold: Z-score threshold for filtering outliers

    Returns
    -  filtered_data: list of lists for RDT data with outliers removed
    """
    data_np = np.array(data, dtype=object)
    amp_values = data_np[:, 1].astype(float)
    re_values = data_np[:, 2].astype(float)
    im_values = data_np[:, 3].astype(float)

    amp_zscores = zscore(amp_values)
    re_zscores = zscore(re_values)
    im_zscores = zscore(im_values)

    return [
        row
        for i, row in enumerate(data)
        if abs(amp_zscores[i]) < threshold
        and abs(re_zscores[i]) < threshold
        and abs(im_zscores[i]) < threshold
    ]


def read_rdt_file(filepath, log_func=None):
    """
    Reads RDT data from a file and returns raw data.
    """
    raw_data = []
    rt = tfs.read(filepath)
    beam_no = rt["Command"][-1]
    rt_filtered = rt[rt["NAME"].str.contains("BPM")]
    if rt_filtered.empty:
        if log_func:
            log_func(f"No BPM data found in file: {filepath}")
        else:
            print(f"No BPM data found in file: {filepath}")
        return None

    for index, row in rt_filtered.iterrows():
        raw_data.append(
            [
                str(row["NAME"]),
                float(row["AMP"]),
                float(row["REAL"]),
                float(row["IMAG"]),
                float(row["ERRAMP"]),
            ]
        )
    return raw_data, beam_no


def ensure_trailing_slash(path):
    """
    Ensure the given folder path ends with a "/".
    """
    return path if path.endswith("/") else path + "/"


def readrdtdatafile(
    cfile, rdt, rdt_plane, rdtfolder, threshold=3, sim=False, log_func=None
):
    """
    Reads RDT data from a file and removes outliers based on Z-scores.
    """
    # Ensure cfile and rdtfolder have trailing slashes
    cfile2 = ensure_trailing_slash(cfile)
    rdtfolder = ensure_trailing_slash(rdtfolder)
    filepath = f"{cfile2}rdt/{rdtfolder}f{rdt}_{rdt_plane}.tfs"
    if sim:
        try:
            df = tfs.read(cfile)
            beam_no = df["Command"][-1]
            df_filtered = df[df["NAME"].str.contains("BPM")]
            if df_filtered.empty:
                if log_func:
                    log_func(f"No BPM data found in file: {filepath}")
                else:
                    print(f"No BPM data found in file: {filepath}")
                return None
            raw_data = []
            for index, row in df_filtered.iterrows():
                row["REAL"] = np.real(row[f"F{rdt}"])
                row["IMAG"] = np.imag(row[f"F{rdt}"])
                row["AMP"] = np.abs(row[f"F{rdt}"])
                raw_data.append(
                    [
                        str(row["NAME"]),
                        float(row["AMP"]),
                        float(row["REAL"]),
                        float(row["IMAG"]),
                        0,
                    ]
                )
        except FileNotFoundError:
            raw_data, beam_no = read_rdt_file(filepath, log_func)
    else:
        raw_data, beam_no = read_rdt_file(filepath, log_func)
    return filter_outliers(raw_data, threshold), beam_no


def update_bpm_data(bpmdata, data, key, knob_setting):
    """
    Updates BPM data dictionary with new data.
    """
    for entry in data:
        name, amp, re, im, amp_err = entry
        bpmdata[name][key].append([knob_setting, amp, re, im, amp_err])


def getrdt_omc3(
    ldb,
    beam,
    modelbpmlist,
    bpmdata,
    ref,
    flist,
    knob,
    rdt,
    rdt_plane,
    rdtfolder,
    sim,
    propfile,
    threshold=3,
    log_func=None,
):
    beam_no = modelbpmlist[0][-1]
    if beam[-1] != beam_no:
        msg = f"Beam number {beam} does not match the model BPM list."
        if log_func:
            log_func(msg)
        else:
            print(msg)
        return None
    mapping_dict = {}
    if sim:
        mapping_dict = csv_to_dict(propfile)

    # Search for ref in mapping_dict and retrieve knob value
    refk = None
    if sim and mapping_dict:
        for entry in mapping_dict:
            regex_str = entry.get("MATCH", "")
            if re.fullmatch(rf"^{regex_str}$", Path(ref).name):
                refk = float(entry.get("KNOB", 0))  # Default to 0 if "KNOB" is missing
                if refk is None:
                    msg = f"Reference knob for {ref} not found in mapping dictionary."
                    if log_func:
                        log_func(msg)
                    raise RuntimeError(msg)
                break
    else:  # Fallback to original method if not found
        refk = get_analysis_knobsetting(ldb, knob, ref, log_func)
        if refk is None:
            msg = f"Reference knob {ref} not found."
            if log_func:
                log_func(msg)
            raise RuntimeError(msg)
    try:
        refdat, beam_no = readrdtdatafile(
            ref, rdt, rdt_plane, rdtfolder, sim=sim, log_func=log_func
        )
        if beam_no != beam[-1]:
            log_func(f"Input is for LHCB{beam_no} not LHCB{beam[-1]}.")
            raise RuntimeError(f"Input is for LHCB{beam_no} not LHCB{beam[-1]}.")
    except FileNotFoundError:
        msg = f"RDT file not found in reference folder: {ref}."
        if log_func:
            log_func(msg)
        raise RuntimeError(msg)
    if refdat is not None and refk is not None:
        update_bpm_data(bpmdata, refdat, "ref", refk)

    updated_count = 0
    ksetting = None
    for f in flist:
        if sim and mapping_dict:
            entry = next(
                (
                    e
                    for e in mapping_dict
                    if re.fullmatch(rf"^{e.get('MATCH', '')}$", Path(f).name)
                    if re.fullmatch(rf"^{e.get('MATCH', '')}$", Path(f).name)
                ),
                None,
            )
            if entry is not None:
                ksetting = float(entry.get("KNOB", 0))
            else:
                msg = f"Measurement knob for {f} not found in mapping dictionary"
                if log_func:
                    log_func(msg)
        else:  # Fallback to original method if not found
            ksetting = get_analysis_knobsetting(ldb, knob, f, log_func)
        try:
            cdat, beam_no = readrdtdatafile(
                f, rdt, rdt_plane, rdtfolder, sim=sim, log_func=log_func
            )
            if beam_no != beam[-1]:
                log_func(f"Input is for LHCB{beam_no} not LHCB{beam[-1]}.")
                raise RuntimeError(f"Input is for LHCB{beam_no} not LHCB{beam[-1]}.")
        except FileNotFoundError:
            msg = f"RDT file not found in measurement folder: {f}."
            if log_func:
                log_func(msg)
            raise RuntimeError(msg)
        if cdat is not None and ksetting is not None:
            update_bpm_data(bpmdata, cdat, "data", ksetting)
            updated_count += 1

    # If no measurement folder updated, throw error and return None
    if updated_count == 0:
        msg = "No BPM data updated for any measurement folder; stopping analysis."
        if log_func:
            log_func(msg)
        raise RuntimeError(msg)
        return None

    intersected_bpm_data = {}
    for bpm in modelbpmlist:
        if len(bpmdata[bpm]["ref"]) != 1 or len(bpmdata[bpm]["data"]) != len(flist):
            continue

        s = bpmdata[bpm]["s"]
        bref = bpmdata[bpm]["ref"]
        dat = bpmdata[bpm]["data"]

        diffdat = [
            [
                dat[k][0] - bref[0][0],
                dat[k][2] - bref[0][2],
                dat[k][3] - bref[0][3],
                dat[k][4],
            ]
            for k in range(len(dat))
        ]
        diffdat.sort(key=lambda x: x[0])
        intersected_bpm_data[bpm] = {"s": s, "diffdata": diffdat}
    if not intersected_bpm_data:
        msg = "No BPM data found after intersection."
        if log_func:
            log_func(msg)
        raise RuntimeError(msg)
        return None

    return {
        "metadata": {
            "beam": beam,
            "ref": ref,
            "rdt": rdt,
            "rdt_plane": rdt_plane,
            "knob": knob,
        },
        "data": intersected_bpm_data,
    }


def polyfunction(x, c, m, n):
    return c + m * x + n * x**2


def fitdata(xdata, ydata, yerrdata, fitfunction):
    popt, pcov = curve_fit(
        fitfunction, xdata, ydata, sigma=yerrdata, absolute_sigma=True
    )
    perr = np.sqrt(np.diag(pcov))
    return popt, pcov, perr


def fitdatanoerrors(xdata, ydata, fitfunction):
    popt, pcov = curve_fit(fitfunction, xdata, ydata)
    perr = np.sqrt(np.diag(pcov))
    return popt, pcov, perr


def fit_bpm(fulldata):
    data = fulldata["data"]
    for bpm in data:
        diffdata = data[bpm]["diffdata"]
        xing = []
        re = []
        im = []
        re_err = []
        im_err = []
        for x in range(len(diffdata)):
            xing.append(diffdata[x][0])
            re.append(diffdata[x][1])
            im.append(diffdata[x][2])
        re_opt, re_cov, re_err = fitdatanoerrors(xing, re, polyfunction)
        im_opt, im_cov, im_err = fitdatanoerrors(xing, im, polyfunction)
        data[bpm]["fitdata"] = [re_opt, re_cov, re_err, im_opt, im_cov, im_err]
    fulldata["data"] = data
    return fulldata


def arc_bpm_check(bpm):
    bpmtype = bpm.partition(".")[0]
    if bpmtype != "BPM":
        is_arc_bpm = False
    else:
        bpmindex = (
            bpm.partition(".")[2].rpartition(".")[0].partition("L")[0].partition("R")[0]
        )
        is_arc_bpm = int(bpmindex) >= 10
    # print(f"{bpm} is arc BPM: {isARCbpm}")
    return is_arc_bpm


def bad_bpm_check(bpm):
    badbpmb1 = ["BPM.13L2.B1"]
    badbpmb2 = ["BPM.25R3.B2", "BPM.26R3.B2"]
    badbpm = False
    for b in badbpmb1:
        if bpm == b:
            badbpm = True
            break
    for b in badbpmb2:
        if bpm == b:
            badbpm = True
            break
    # print(f"{bpm} is bad BPM: {badbpm}")
    return badbpm


def calculate_avg_rdt_shift(data):
    """
    Calculate the average RDT shift and standard deviation over BPMs for given data.
    """
    xing = []  # Get the list of crossing angles measured
    for b in data:
        diffdata = data[b]["diffdata"]
        for x in range(len(diffdata)):
            xing.append(diffdata[x][0])
        break

    ampdat = []
    stddat = []
    for x in xing:
        toavg = []
        for b in data:
            if not arc_bpm_check(b) or bad_bpm_check(b):
                continue
            diffdata = data[b]["diffdata"]
            for y in range(len(diffdata)):
                if diffdata[y][0] == x:
                    re = diffdata[y][1]
                    im = diffdata[y][2]
                    amp = np.sqrt(re**2 + im**2)
                    toavg.append(amp)
        avg_rdt_shift = np.mean(np.array(toavg))
        avg_rdt_shift_err = np.std(np.array(toavg))
        ampdat.append(avg_rdt_shift)
        stddat.append(avg_rdt_shift_err)

    return np.array(xing), np.array(ampdat), np.array(stddat)


def group_datasets(datasets, log_func=None):
    if not datasets:
        return None, None
    rdt, rdt_plane = None, None
    grouped_b1 = {"metadata": None, "data": {}}
    grouped_b2 = {"metadata": None, "data": {}}
    if len(datasets) == 1:
        # If only one dataset, return it as is
        dataset = datasets[0]
        beam_no = dataset["metadata"].get("beam")[-1]
        if beam_no is None:
            if log_func:
                log_func("Dataset metadata missing the 'beam' key.")
            else:
                raise ValueError("Dataset metadata missing the 'beam' key.")
        if beam_no == "1":
            grouped_b1["metadata"] = dataset["metadata"]
            grouped_b1["data"] = dataset["data"]
            return (
                grouped_b1,
                None,
                grouped_b1["metadata"]["rdt"],
                grouped_b1["metadata"]["rdt_plane"],
            )
        if beam_no == "2":
            grouped_b2["metadata"] = dataset["metadata"]
            grouped_b2["data"] = dataset["data"]
            return (
                None,
                grouped_b2,
                grouped_b2["metadata"]["rdt"],
                grouped_b2["metadata"]["rdt_plane"],
            )
    for data in datasets:
        beam_no = data["metadata"].get("beam")[-1]
        if beam_no is None:
            if log_func:
                log_func("Dataset metadata missing the 'beam' key.")
            else:
                raise ValueError("Dataset metadata missing the 'beam' key.")
        # Group by the beam value: for example, "b1" or "b2"
        if beam_no == "1":
            # Set reference metadata if not set
            if grouped_b1["metadata"] is None:
                grouped_b1["metadata"] = data["metadata"]
            # Check for consistency with already grouped metadata:
            elif data["metadata"] != grouped_b1["metadata"]:
                if log_func:
                    log_func(
                        "Datasets for beam LHCB1 have differing metadata; cannot group them together."
                    )
                else:
                    raise ValueError(
                        "Datasets for LHCB2 have differing metadata; cannot group them together."
                    )
                return None, None, None, None
            # Merge the data dictionaries
            grouped_b1["data"].update(data["data"])
        elif beam_no == "2":
            if grouped_b2["metadata"] is None:
                grouped_b2["metadata"] = data["metadata"]
            elif data["metadata"] != grouped_b2["metadata"]:
                if log_func:
                    log_func(
                        "Datasets for LHCB2 have differing metadata; cannot group them together."
                    )
                else:
                    raise ValueError(
                        "Datasets for LHCB2 have differing metadata; cannot group them together."
                    )
                return None, None, None, None
            grouped_b2["data"].update(data["data"])
        else:
            if log_func:
                log_func(f"Unexpected beam value: LHCB{beam_no}")
            else:
                raise ValueError(f"Unexpected beam value: LHCB{beam_no}")
    if {
        k: v for k, v in grouped_b1["metadata"].items() if k != "beam" and k != "ref"
    } != {
        k: v for k, v in grouped_b2["metadata"].items() if k != "beam" and k != "ref"
    }:
        if log_func:
            log_func(
                "Datasets for beam 1 and beam 2 have differing metadata; cannot group them together."
            )
        else:
            raise ValueError(
                "Datasets for beam 1 and beam 2 have differing metadata; cannot group them together."
            )
        return None, None, None, None
    if grouped_b1["metadata"] is not None:
        rdt = grouped_b1["metadata"]["rdt"]
        rdt_plane = grouped_b1["metadata"]["rdt_plane"]
    elif grouped_b2["metadata"] is not None:
        rdt = grouped_b2["metadata"]["rdt"]
        rdt_plane = grouped_b2["metadata"]["rdt_plane"]
    else:
        if log_func:
            log_func("No metadata found for either beam.")
        else:
            raise ValueError("No metadata found for either beam.")
        return None, None, None, None

    return grouped_b1, grouped_b2, rdt, rdt_plane


def getrdt_sim(
    beam,
    ref,
    file,
    xing,
    knob_name,
    knob_strength,
    rdt,
    rdt_plane,
    rdtfolder,
    log_func=None,
):
    bpmdata = {}
    bpmlist = []
    knob_strength = float(knob_strength)
    xing = float(xing)
    # Read the reference data
    rdtfolder = rdtfolder if rdtfolder.endswith("/") else rdtfolder + "/"
    try:
        ref = ref if ref.endswith("/") else ref + "/"
        refdat = tfs.read(f"{ref}rdt/{rdtfolder}f{rdt}_{rdt_plane}.tfs")
        refdat = refdat[refdat["NAME"].str.contains("BPM")]
    except FileNotFoundError:
        msg = f"RDT file not found in reference folder: {ref}."
        if log_func:
            log_func(msg)
        raise RuntimeError(msg)
        return None
    if refdat is not None:
        for index, entry in refdat.iterrows():
            bpm = entry["NAME"]
            if not arc_bpm_check(bpm) or bad_bpm_check(bpm):
                continue
            bpmlist.append(bpm)
            bpmdata[bpm] = {}
            bpmdata[bpm]["s"] = float(entry["S"])
            bpmdata[bpm]["ref"] = []
            bpmdata[bpm]["data"] = []
            bpmdata[bpm]["ref"].append(
                [0, entry["AMP"], entry["REAL"], entry["IMAG"], entry["ERRAMP"]]
            )
    else:
        msg = f"Reference data not found for {ref}."
        if log_func:
            log_func(msg)
        raise RuntimeError(msg)
        return None
    # Read the measurement data
    try:
        file = file if file.endswith("/") else file + "/"
        cdat = tfs.read(f"{file}rdt/{rdtfolder}f{rdt}_{rdt_plane}.tfs")
        cdat = cdat[cdat["NAME"].str.contains("BPM")]
    except FileNotFoundError:
        msg = f"RDT file not found in measurement folder: {file}."
        if log_func:
            log_func(msg)
        raise RuntimeError(msg)
        return None
    if cdat is not None:
        for index, entry in cdat.iterrows():
            bpm = entry["NAME"]
            if not arc_bpm_check(bpm) or bad_bpm_check(bpm):
                continue
            bpmdata[bpm]["data"].append(
                [
                    knob_strength,
                    entry["AMP"],
                    entry["REAL"],
                    entry["IMAG"],
                    entry["ERRAMP"],
                ]
            )
    else:
        msg = f"Measurement data not found for {file}."
        if log_func:
            log_func(msg)
        raise RuntimeError(msg)
        return None
    # Check if the reference and measurement data have the same number of entries
    if len(bpmdata) == 0:
        msg = "No BPM data found."
        if log_func:
            log_func(msg)
        raise RuntimeError(msg)
        return None
    intersected_bpm_data = {}
    # Check if the reference and measurement data have the same number of entries
    for bpm in bpmlist:
        if len(bpmdata[bpm]["ref"]) != 1 or len(bpmdata[bpm]["data"]) != 1:
            msg = f"Reference and measurement data for BPM {bpm} do not match."
            if log_func:
                log_func(msg)
            continue
        # Calculate the RDT shifts
        s = bpmdata[bpm]["s"]
        bref = bpmdata[bpm]["ref"]
        dat = bpmdata[bpm]["data"]
        diffdat = [
            ((dat[0][2] - bref[0][2]) / xing) / knob_strength,
            ((dat[0][3] - bref[0][3]) / xing) / knob_strength,
        ]
        intersected_bpm_data[bpm] = {"s": s, "diffdata": diffdat}
    if not intersected_bpm_data:
        msg = "No BPM data found after intersection."
        if log_func:
            log_func(msg)
        raise RuntimeError(msg)
        return None
    return {
        "metadata": {
            "beam": beam,
            "ref": ref,
            "rdt": rdt,
            "rdt_plane": rdt_plane,
            "knob_name": knob_name,
        },
        "data": intersected_bpm_data,
    }
