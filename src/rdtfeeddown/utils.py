import os
import sys
import re
import csv
import datetime as dt
import pytimber
from zoneinfo import ZoneInfo 
import tfs
from datetime import datetime
import json
import pyqtgraph as pg
from qtpy.QtCore import Qt
from qtpy.QtCore import QTimer
	

def rdt_to_order_and_type(
	rdt: str
):	
	rdt_j, rdt_k, rdt_l, rdt_m = map(int, rdt)
	rdt_type = "normal" if (rdt_l + rdt_m) % 2 == 0 else "skew"
	orders = dict(((1, "dipole"), 
				(2, "quadrupole"), 
				(3, "sextupole"), 
				(4, "octupole"),
				(5, "decapole"),
				(6, "dodecapole"),
				(7, "tetradecapole"),
				(8, "hexadecapole"),
				))
	return f"{rdt_type}_{orders[rdt_j + rdt_k + rdt_l + rdt_m]}"

def initialize_statetracker():
	ldb = pytimber.LoggingDB()
	return ldb

def getknobsetting_statetracker(ldb,thistimestamp,requested_knob):
	statetrackerknobname = 'LhcStateTracker:'+re.sub('/',':',requested_knob)+':value'
	knob_setting = ldb.get(statetrackerknobname,thistimestamp)[statetrackerknobname][1][0]
	return knob_setting

def get_analysis_knobsetting(ldb,requested_knob,analyfile, log_func=None):
	############-> read the command.run file to generate a list of all the kicks used to produce this results folder	
	fc=analyfile+'/command.run'
	try:
		rc=open(fc,'r')
	except FileNotFoundError:
		if log_func:
			log_func('No command.run file found in the results folder')
		else:
			print('No command.run file found in the results folder')
	for line in rc.readlines():
		if re.search('/afs/cern.ch/eng/sl/lintrack/omc_python3/bin/python -m omc3.hole_in_one --optics',line):
			flist=line.partition('--files')[2].partition('--')[0].split(',') 
			break
	rc.close()
	knobsettings=[]
	try:
		for f in flist:
			kickname=f.rpartition('/')[2]
			kicktime=convert_from_kickfilename(kickname)
			localktime=utctolocal(kicktime)
			knobsetting=getknobsetting_statetracker(ldb,localktime,requested_knob)
			knobsettings.append([kicktime,knobsetting])
	except Exception as e:
		if log_func:
			log_func('Error reading command.run file: '+str(e))
		else:
			print('Error reading command.run file: '+str(e))
		return None

	if len(knobsettings)>1:  #### --> in case multiple files were used for the analysis - check all were performed at timestamp with equal knob settings
		for k in range(len(knobsettings)):
			if knobsettings[k][1]!=knobsettings[0][1]:
				if log_func:
					log_func('Results file '+analyfile+' includes kicks with different knob settings')
				else:
					print('Results file '+analyfile+' includes kicks with different knob settings')
				return None

	knobvalue=knobsetting ### --> in case results folder generated with single kick, or all kicks have the same knob setting, just take the last knobsetting as the value to use moving forward
	return knobvalue

def parse_timestamp(
	thistime,
	log_func=None
):
	accepted_time_input_format = ['%Y-%m-%d %H:%M:%S.%f','%Y-%m-%d %H:%M:%S','%Y-%m-%d_%H:%M:%S.%f','%Y-%m-%d_%H:%M:%S']
	for fmat in accepted_time_input_format:
		try:
			dtobject=dt.datetime.strptime(thistime,fmat)
			return dtobject
		except ValueError:
			pass
	timefmatstring=''
	for fmat in accepted_time_input_format:
		timefmatstring=timefmatstring+'\"'+fmat+'\" ,   '
	sys.tracebacklimit = 0
	if log_func:
		log_func('No appropriate input format found for start time of scan (-s).\n ---> Accepted input formats are:   '+timefmatstring)
	else:
		raise ValueError('No appropriate input format found for start time of scan (-s).\n ---> Accepted input formats are:   '+timefmatstring)

def utctolocal(
	dtutctime, 
	local_tz_str="Europe/Paris"
):
	dtutctime = dtutctime.replace(tzinfo=dt.timezone.utc)
	local_tz = ZoneInfo(local_tz_str)
	return dtutctime.astimezone(local_tz)

def convert_from_kickfilename(kickfilename):
	if re.search('Beam1@Turn@',kickfilename):
		ts=kickfilename.partition('Beam1@Turn@')[2]
	elif re.search('Beam2@Turn@',kickfilename):
		ts=kickfilename.partition('Beam2@Turn@')[2]
	elif re.search('Beam1@BunchTurn@',kickfilename):
		ts=kickfilename.partition('Beam1@BunchTurn@')[2]
	elif re.search('Beam2@BunchTurn@',kickfilename):
		ts=kickfilename.partition('Beam2@BunchTurn@')[2]
	ts=ts.partition('.sdds')[0]
	dtobject=dt.datetime.strptime(ts,'%Y_%m_%d@%H_%M_%S_%f')
	return dtobject

def getmodelBPMs(modelpath):
	modelbpmlist=[]
	bpmdata={}
	twissfile=modelpath+'/twiss.dat'
	rt=tfs.read(twissfile)
	rt_filtered=rt[rt['NAME'].str.contains('BPM')]
	for index, row in rt_filtered.iterrows():
		bpm = row["NAME"]
		modelbpmlist.append(bpm)
		bpmdata[bpm]={}
		bpmdata[bpm]['s']=float(row["S"])
		bpmdata[bpm]['ref']=[]
		bpmdata[bpm]['data']=[]
	return modelbpmlist,bpmdata

def load_defaults(log_func=None):
	# Set built-in defaults
	curr_time = datetime.now().strftime('%Y-%m-%d')
	defaults = {
		"default_input_path": "/user/slops/data/LHC_DATA/OP_DATA/FILL_DATA/FILL_DIR/BPM/",
		"default_output_path": f"/user/slops/data/LHC_DATA/OP_DATA/Betabeat/{curr_time}/",
	}
	# Use current working directory to locate the configuration file
	config_path = f"{os.getcwd()}/defaults.json"
	if os.path.exists(config_path):
		try:
			with open(config_path, "r") as cf:
				user_defaults = json.load(cf)
				defaults.update(user_defaults)
		except Exception as e:
			if log_func:
				log_func(f"Error looking for configuration file: {e}")
			else:
				print(f"Error looking for configuration file: {e}")
			pass
	return defaults

def csv_to_dict(
	file_path: str
):
	"""
	Converts a CSV file to a dictionary
	
	Parameters:
	- file_path: The file path of the CSV file.
	
	Returns:
	- data: The dictionary of the CSV file.
	
	"""
	with open(file_path, mode="r") as infile:
		reader = csv.DictReader(infile, skipinitialspace=True)
		data = [row for row in reader]
	return data

class MyViewBox(pg.ViewBox):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._resetting = False

    def mouseClickEvent(self, ev):
        if ev.button() == Qt.RightButton and not self._resetting:
            self._resetting = True
            self.autoRange()
            ev.accept()  # consume the event
            # Reset the flag after a short delay to avoid continuous resetting.
            QTimer.singleShot(50, self._reset_flag)
        else:
            super().mouseClickEvent(ev)

    def _reset_flag(self):
        self._resetting = False