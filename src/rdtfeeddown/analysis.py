import numpy as np
from scipy.optimize import curve_fit
from scipy.stats import zscore
import csv
from .utils import get_analysis_knobsetting
import tfs
import glob
import numpy as np
import json

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

def readrdtdatafile(cfile, rdt, rdt_plane, rdtfolder, log_func=None):
	"""
	Reads RDT data from a file and removes outliers based on Z-scores.
	"""
	# Ensure cfile and rdtfolder have trailing slashes
	cfile = ensure_trailing_slash(cfile)
	rdtfolder = ensure_trailing_slash(rdtfolder)
	filepath = f'{cfile}rdt/{rdtfolder}f{rdt}_{rdt_plane}.tfs'
	raw_data = read_rdt_file(filepath)
	return filter_outliers(raw_data)

def update_bpm_data(bpmdata, data, key, knob_setting):
	"""
	Updates BPM data dictionary with new data.
	"""
	for entry in data:
		name, amp, re, im = entry
		bpmdata[name][key].append([knob_setting, amp, re, im])

def getrdt_omc3(ldb, modelbpmlist, bpmdata, ref, flist, knob, outputpath, rdt, rdt_plane, rdtfolder, log_func=None):
	"""
	Processes RDT data and updates BPM data dictionary.
	"""
	refk = get_analysis_knobsetting(ldb, knob, ref)
	try:
		refdat = readrdtdatafile(ref, rdt, rdt_plane, rdtfolder, log_func)
	except FileNotFoundError:
		if log_func:
			log_func(f"RDT file not found in reference folder: {ref}. Skipping reference data.")
		else:
			print(f"RDT file not found in reference folder: {ref}. Skipping reference data.")
		refdat = []
	update_bpm_data(bpmdata, refdat, 'ref', refk)

	for f in flist:
		ksetting = get_analysis_knobsetting(ldb, knob, f)
		try:
			cdat = readrdtdatafile(f, rdt, rdt_plane, rdtfolder, log_func)
		except FileNotFoundError:
			if log_func:
				log_func(f"RDT file not found in measurement folder: {f}. Skipping.")
			else:
				print(f"RDT file not found in measurement folder: {f}. Skipping.")
			continue
		update_bpm_data(bpmdata, cdat, 'data', ksetting)

	intersectedBPMdata = {}
	for bpm in modelbpmlist:
		if len(bpmdata[bpm]['ref']) != 1 or len(bpmdata[bpm]['data']) != len(flist):
			continue

		s = bpmdata[bpm]['s']
		ref = bpmdata[bpm]['ref']
		dat = bpmdata[bpm]['data']

		diffdat = [
			[dat[k][0] - ref[0][0], dat[k][2] - ref[0][2], dat[k][3] - ref[0][3]]
			for k in range(len(dat))
		]
		diffdat.sort(key=lambda x: x[0])

		intersectedBPMdata[bpm] = {'s': s, 'diffdata': diffdat}

	return intersectedBPMdata

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

def fit_BPM(data):
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
	return data

def arcBPMcheck(bpm):
	bpmtype=bpm.partition('.')[0]
	if bpmtype!='BPM':
		isARCbpm=False
	else:
		bpmindex=bpm.partition('.')[2].rpartition('.')[0].partition('L')[0].partition('R')[0]
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




