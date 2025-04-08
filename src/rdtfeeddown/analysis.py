import numpy as np
from scipy.optimize import curve_fit
from scipy.stats import zscore
import csv
from .utils import get_analysis_knobsetting, csv_to_dict
import tfs
import json
import os
import re

def filter_outliers(
	data, 
	threshold=3
):
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

	filtered_data = [
		row for i, row in enumerate(data)
		if abs(amp_zscores[i]) < threshold and abs(re_zscores[i]) < threshold and abs(im_zscores[i]) < threshold
	]
	return filtered_data

def read_rdt_file(filepath, log_func=None):
	"""
	Reads RDT data from a file and returns raw data.
	"""
	raw_data = []
	rt = tfs.read(filepath)
	rt_filtered = rt[rt['NAME'].str.contains('BPM')]
	if rt_filtered.empty:
		if log_func:
			log_func(f"No BPM data found in file: {filepath}")
		else:
			print(f"No BPM data found in file: {filepath}")
		return None

	for index, row in rt_filtered.iterrows():
			raw_data.append([str(row["NAME"]), float(row["AMP"]), float(row["REAL"]), float(row["IMAG"])])
	return raw_data

def ensure_trailing_slash(path):
	"""
	Ensure the given folder path ends with a "/".
	"""
	return path if path.endswith('/') else path + '/'

def readrdtdatafile(cfile, rdt, rdt_plane, rdtfolder, sim=False, log_func=None):
	"""
	Reads RDT data from a file and removes outliers based on Z-scores.
	"""
	# Ensure cfile and rdtfolder have trailing slashes
	cfile2 = ensure_trailing_slash(cfile)
	rdtfolder = ensure_trailing_slash(rdtfolder)
	filepath = f'{cfile2}rdt/{rdtfolder}f{rdt}_{rdt_plane}.tfs'
	if sim:
		try:
			df = tfs.read(cfile)
			df_filtered = df[df['NAME'].str.contains('BPM')]
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
				raw_data.append([str(row["NAME"]), float(row["AMP"]), float(row["REAL"]), float(row["IMAG"])])
		except Exception:
			raw_data = read_rdt_file(filepath, log_func)
	else:
		raw_data = read_rdt_file(filepath, log_func)
	return filter_outliers(raw_data)

def update_bpm_data(bpmdata, data, key, knob_setting):
	"""
	Updates BPM data dictionary with new data.
	"""
	for entry in data:
		name, amp, re, im = entry
		bpmdata[name][key].append([knob_setting, amp, re, im])

def getrdt_omc3(ldb, beam, modelbpmlist, bpmdata, ref, flist, knob, rdt, rdt_plane, rdtfolder, sim, propfile, log_func=None):
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
			if re.fullmatch(fr"^{regex_str}$", os.path.basename(ref)):
				refk = float(entry.get("KNOB", 0))  # Default to 0 if "KNOB" is missing
				break
		if refk is None:
			msg = f"Reference knob for {ref} not found in mapping dictionary."
			if log_func:
				log_func(msg)
			raise RuntimeError(msg)
	else:  # Fallback to original method if not found
		refk = get_analysis_knobsetting(ldb, knob, ref, log_func)
		if refk is None:
			msg = f"Reference knob {ref} not found."
			if log_func:
				log_func(msg)
			raise RuntimeError(msg)
	try:
		refdat = readrdtdatafile(ref, rdt, rdt_plane, rdtfolder, log_func)
	except FileNotFoundError:
		msg = f"RDT file not found in reference folder: {ref}."
		if log_func:
			log_func(msg)
		raise RuntimeError(msg)
	if refdat is not None and refk is not None:
		update_bpm_data(bpmdata, refdat, 'ref', refk)

	updated_count = 0
	ksetting = None
	for f in flist:
		if sim and mapping_dict:
			entry = next((e for e in mapping_dict if re.fullmatch(fr'^{e.get("MATCH", "")}$', os.path.basename(f))), None)
			if entry is not None:
				ksetting = float(entry.get("KNOB", 0))
			else:
				msg = f"Measurement knob for {f} not found in mapping dictionary"
				if log_func:
					log_func(msg)
		else:  # Fallback to original method if not found
			ksetting = get_analysis_knobsetting(ldb, knob, f, log_func)
		try:
			cdat = readrdtdatafile(f, rdt, rdt_plane, rdtfolder, log_func)
		except FileNotFoundError:
			msg = f"RDT file not found in measurement folder: {f}."
			if log_func:
				log_func(msg)
			raise RuntimeError(msg)
		if cdat is not None and ksetting is not None:
			update_bpm_data(bpmdata, cdat, 'data', ksetting)
			updated_count += 1

	# If no measurement folder updated, throw error and return None
	if updated_count == 0:
		msg = "No BPM data updated for any measurement folder; stopping analysis."
		if log_func:
			log_func(msg)
		raise RuntimeError(msg)
		return None

	intersectedBPMdata = {}
	for bpm in modelbpmlist:
		if len(bpmdata[bpm]['ref']) != 1 or len(bpmdata[bpm]['data']) != len(flist):
			continue

		s = bpmdata[bpm]['s']
		bref = bpmdata[bpm]['ref']
		dat = bpmdata[bpm]['data']

		diffdat = [
			[dat[k][0] - bref[0][0], dat[k][2] - bref[0][2], dat[k][3] - bref[0][3]]
			for k in range(len(dat))
		]
		diffdat.sort(key=lambda x: x[0])
		intersectedBPMdata[bpm] = {'s': s, 'diffdata': diffdat}
	if not intersectedBPMdata:
		msg = "No BPM data found after intersection."
		if log_func:
			log_func(msg)
		raise RuntimeError(msg)
		return None

	return {'metadata': {'beam' : beam, 'ref' : ref, 'rdt': rdt, 'rdt_plane': rdt_plane, 'knob': knob}, 'data': intersectedBPMdata}

def polyfunction(x,c,m,n):
	y=c+m*x+n*x**2
	return y

def fitdata(xdata,ydata,yerrdata,fitfunction):
	popt,pcov = curve_fit(fitfunction,xdata,ydata,sigma=yerrdata,absolute_sigma=True)
	perr = np.sqrt(np.diag(pcov))
	return popt,pcov,perr

def fitdatanoerrors(xdata,ydata,fitfunction):
	popt,pcov = curve_fit(fitfunction,xdata,ydata)
	perr = np.sqrt(np.diag(pcov))
	return popt,pcov,perr

def fit_BPM(fulldata):
	data = fulldata['data']
	for bpm in data.keys():
		diffdata=data[bpm]['diffdata']
		xing=[]
		re=[]
		im=[]
		re_err=[]
		im_err=[]
		for x in range(len(diffdata)):
			xing.append(diffdata[x][0])
			re.append(diffdata[x][1])
			im.append(diffdata[x][2])
		re_opt,re_cov,re_err = fitdatanoerrors(xing,re,polyfunction)
		im_opt,im_cov,im_err = fitdatanoerrors(xing,im,polyfunction)
		data[bpm]['fitdata']=[re_opt,re_cov,re_err,im_opt,im_cov,im_err]
	fulldata['data'] = data
	return fulldata

def arcBPMcheck(bpm):
	bpmtype=bpm.partition('.')[0]
	if bpmtype!='BPM':
		print(bpmtype)
		isARCbpm=False
	else:
		bpmindex=bpm.partition('.')[2].rpartition('.')[0].partition('L')[0].partition('R')[0]
		print(bpmindex)
		if int(bpmindex)>=10:
			isARCbpm=True
		else:
			isARCbpm=False
	return isARCbpm

def badBPMcheck(bpm):
	badbpmb1=['BPM.13L2.B1']
	badbpmb2=['BPM.25R3.B2','BPM.26R3.B2']
	badbpm=False
	for b in badbpmb1:
		if bpm==b:
			badbpm=True
			break
	for b in badbpmb2:
		if bpm==b:
			badbpm=True
			break
	return badbpm

def write_RDTshifts_for_beam(data, rdt, rdt_plane, beam, output_path):
	"""
	Generalized function to write RDT shifts for a given beam (b1 or b2).
	"""
	# Ensure output_path has a trailing slash.
	output_path = ensure_trailing_slash(output_path)
	# Gradients
	fout = f'{output_path}data_{beam}_f{rdt}{rdt_plane}rdtgradient.csv'
	with open(fout, 'w') as wout:
		csvwout = csv.writer(wout, delimiter=' ')
		header = ['#name', 's', f'd(Ref{rdt}_{rdt_plane})/dknob', f'd(Imf{rdt}_{rdt_plane})/dknob', 're fit error', 'im fit error']
		csvwout.writerow(header)
		for b in data.keys():
			if not arcBPMcheck(b) or badBPMcheck(b):
				continue
			s = data[b]['s']
			dredk = data[b]['fitdata'][0][1]
			dimdk = data[b]['fitdata'][3][1]
			dreerr = data[b]['fitdata'][2][1]
			dimerr = data[b]['fitdata'][5][1]
			csvwout.writerow([b, s, dredk, dimdk, dreerr, dimerr])

	# Average re**2 + im**2
	xing = [diff[0] for diff in next(iter(data.values()))['diffdata']]
	fout = f'{output_path}data_{beam}_f{rdt}{rdt_plane}rdtshiftvsknob.csv'
	with open(fout, 'w') as wout:
		csvwout = csv.writer(wout, delimiter=' ')
		header = ['#xing', 'sqrt(Dre^2+Dim^2)', 'std_dev over BPM']
		csvwout.writerow(header)
		for x in xing:
			toavg = []
			for b in data.keys():
				if not arcBPMcheck(b) or badBPMcheck(b):
					continue
				diffdata = data[b]['diffdata']
				for diff in diffdata:
					if diff[0] == x:
						re, im = diff[1], diff[2]
						amp = np.sqrt(re**2 + im**2)
						toavg.append(amp)
			avgRDTshift = np.mean(toavg)
			avgRDTshifterr = np.std(toavg)
			csvwout.writerow([x, avgRDTshift, avgRDTshifterr])

	# RDT deltas
	for x in xing:
		fout = f'{output_path}data_{beam}_f{rdt}{rdt_plane}rdtdelta_knob_{x}.csv'
		with open(fout, 'w') as wout:
			csvwout = csv.writer(wout, delimiter=' ')
			header = ['#name', 's', 'delta amp', 'delta re', 'delta im']
			csvwout.writerow(header)
			for b in data.keys():
				if not arcBPMcheck(b) or badBPMcheck(b):
					continue
				s = data[b]['s']
				diffdata = data[b]['diffdata']
				for diff in diffdata:
					if diff[0] == x:
						re, im = diff[1], diff[2]
						amp = np.sqrt(re**2 + im**2)
						csvwout.writerow([b, s, amp, re, im])

def write_RDTshifts(data, rdt, rdt_plane, beam, output_path , log_func=None):
	"""
	Writes RDT shifts for a beam
	"""
	try:
		write_RDTshifts_for_beam(data, rdt, rdt_plane, beam, output_path)
	except Exception as e:
		if log_func:
			log_func(f"Error writing RDT shifts for {beam}: {e}")
		else:
			print(f"Error writing RDT shifts for {beam}: {e}")

def calculate_avg_rdt_shift(data):
	"""
	Calculate the average RDT shift and standard deviation over BPMs for given data.
	"""
	xing = []  # Get the list of crossing angles measured
	for b in data.keys():
		diffdata = data[b]['diffdata']
		for x in range(len(diffdata)):
			xing.append(diffdata[x][0])
		break

	ampdat = []
	stddat = []
	for x in xing:
		toavg = []
		for b in data.keys():
			if not arcBPMcheck(b) or badBPMcheck(b):
				continue
			diffdata = data[b]['diffdata']
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

def group_datasets(datasets, log_func=None):
	if not datasets:
		return None, None
	rdt, rdt_plane = None, None
	grouped_b1 = {'metadata': None, 'data': {}}
	grouped_b2 = {'metadata': None, 'data': {}}
	if len(datasets) == 1:
		# If only one dataset, return it as is
		dataset = datasets[0]
		beam = dataset['metadata'].get('beam')
		if beam is None:
			if log_func:
				log_func("Dataset metadata missing the 'beam' key.")
			else:
				raise ValueError("Dataset metadata missing the 'beam' key.")
		if beam.lower() == 'b1':
			grouped_b1['metadata'] = dataset['metadata']
			grouped_b1['data'] = dataset['data']
			return grouped_b1, None, grouped_b1['metadata']['rdt'], grouped_b1['metadata']['rdt_plane']
		elif beam.lower() == 'b2':
			grouped_b2['metadata'] = dataset['metadata']
			grouped_b2['data'] = dataset['data']
			return None, grouped_b2, grouped_b2['metadata']['rdt'], grouped_b2['metadata']['rdt_plane']
	for data in datasets:
		beam = data['metadata'].get('beam')
		if beam is None:
			if log_func:
				log_func("Dataset metadata missing the 'beam' key.")
			else:
				raise ValueError("Dataset metadata missing the 'beam' key.")
		# Group by the beam value: for example, "b1" or "b2"
		if beam.lower() == 'b1':
			# Set reference metadata if not set
			if grouped_b1['metadata'] is None:
				grouped_b1['metadata'] = data['metadata']
			# Check for consistency with already grouped metadata:
			elif data['metadata'] != grouped_b1['metadata']:
				if log_func:
					log_func("Datasets for beam b1 have differing metadata; cannot group them together.")
				else:
					raise ValueError("Datasets for beam 1 have differing metadata; cannot group them together.")
				return None, None, None, None
			# Merge the data dictionaries
			grouped_b1['data'].update(data['data'])
		elif beam.lower() == 'b2':
			if grouped_b2['metadata'] is None:
				grouped_b2['metadata'] = data['metadata']
			elif data['metadata'] != grouped_b2['metadata']:
				if log_func:
					log_func("Datasets for beam b2 have differing metadata; cannot group them together.")
				else:
					raise ValueError("Datasets for beam 2 have differing metadata; cannot group them together.")
				return None, None, None, None
			grouped_b2['data'].update(data['data'])
		else:
			if log_func:
				log_func(f"Unexpected beam value: {beam}")
			else:
				raise ValueError(f"Unexpected beam value: {beam}")
	if {k: v for k, v in grouped_b1['metadata'].items() if k != 'beam' and k != 'ref'} != \
		{k: v for k, v in grouped_b2['metadata'].items() if k != 'beam' and k != 'ref'}:
			if log_func:
				log_func("Datasets for beam 1 and beam 2 have differing metadata; cannot group them together.")
			else:
				raise ValueError("Datasets for beam 1 and beam 2 have differing metadata; cannot group them together.")
			return None, None, None, None
	if grouped_b1['metadata'] is not None:
		rdt = grouped_b1['metadata']['rdt']
		rdt_plane = grouped_b1['metadata']['rdt_plane']
	elif grouped_b2['metadata'] is not None:
		rdt = grouped_b2['metadata']['rdt']
		rdt_plane = grouped_b2['metadata']['rdt_plane']
	else:
		if log_func:
			log_func("No metadata found for either beam.")
		else:
			raise ValueError("No metadata found for either beam.")
		return None, None, None, None

	return grouped_b1, grouped_b2, rdt, rdt_plane

def getrdt_sim(beam, ref, file, xing, knob_name, knob_strength, rdt, rdt_plane, rdtfolder, log_func=None):
	bpmdata = {}
	bpmlist = []
	# Read the reference data
	rdtfolder = rdtfolder if rdtfolder.endswith('/') else rdtfolder + '/'
	try:
		ref = ref if ref.endswith('/') else ref + '/'
		refdat = tfs.read(f"{ref}rdt/{rdtfolder}f{rdt}_{rdt_plane}.tfs")
		refdat = refdat[refdat['NAME'].str.contains('BPM')]
	except FileNotFoundError:
		msg = f"RDT file not found in reference folder: {ref}."
		if log_func:
			log_func(msg)
		raise RuntimeError(msg)
		return None
	if refdat is not None:
		for index,entry in refdat.iterrows():
			bpm = entry["NAME"]
			bpmlist.append(bpm)
			if not arcBPMcheck(bpm) or badBPMcheck(bpm):
				continue
			bpmdata[bpm] = {}
			bpmdata[bpm]['s']=float(entry["S"])
			bpmdata[bpm]['ref']=[]
			bpmdata[bpm]['data']=[]
			bpmdata[bpm]['ref'].append([0, entry["AMP"], entry["REAL"], entry["IMAG"]])
	else:
		msg = f"Reference data not found for {ref}."
		if log_func:
			log_func(msg)
		raise RuntimeError(msg)
		return None
	# Read the measurement data
	try:
		file = file if file.endswith('/') else file + '/'
		cdat = tfs.read(f"{ref}rdt/{rdtfolder}f{rdt}_{rdt_plane}.tfs")
		cdat = cdat[cdat['NAME'].str.contains('BPM')]
	except FileNotFoundError:
		msg = f"RDT file not found in measurement folder: {file}."
		if log_func:
			log_func(msg)
		raise RuntimeError(msg)
		return None
	if cdat is not None:
		for index, entry in cdat.iterrows():
			bpm = entry["NAME"]
			if not arcBPMcheck(bpm) or badBPMcheck(bpm):
				continue
			if bpm not in bpmdata:
				bpmdata[bpm] = {}
				bpmdata[bpm]['s']=float(entry["S"])
				bpmdata[bpm]['ref']=[]
				bpmdata[bpm]['data']=[]
				bpmdata[bpm]['data'].append([knob_strength, entry["AMP"], entry["REAL"], entry["IMAG"]])
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
	intersectedBPMdata = {}
	# Check if the reference and measurement data have the same number of entries
	for bpm in bpmlist:
		if len(bpmdata[bpm]['ref']) != 1 or len(bpmdata[bpm]['data']) != 1:
			msg = f"Reference and measurement data for BPM {bpm} do not match."
			if log_func:
				log_func(msg)
			raise RuntimeError(msg)
			return None
		# Calculate the RDT shifts
		s = bpmdata[bpm]['s']
		bref = bpmdata[bpm]['ref']
		dat = bpmdata[bpm]['data']

		diffdat = [((dat[0][0] - bref[0][0])/xing)/knob_strength, 
					((dat[0][2] - bref[0][2])/xing)/knob_strength, 
					((dat[0][3] - bref[0][3])/xing)/knob_strength]
		intersectedBPMdata[bpm] = {'s': s, 'diffdata': diffdat}
	if not intersectedBPMdata:
		msg = "No BPM data found after intersection."
		if log_func:
			log_func(msg)
		raise RuntimeError(msg)
		return None
	return {'metadata': {'beam' : beam, 'ref' : ref, 'rdt': rdt, 'rdt_plane': rdt_plane, 'knob_name': knob_name}, 'data': intersectedBPMdata}


