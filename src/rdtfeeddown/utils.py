import os
import sys
import re
import datetime as dt
from optparse import OptionParser
import pytimber
from zoneinfo import ZoneInfo 
import csv
import tfs
from datetime import datetime
import json

def check_rdt(
	rdt:str, 
	rdtplane:str
):
	if len(rdt) != 4:
		return False, "The rdt must be exactly 4 characters long."

	# Check if all characters are digits
	if not rdt.isdigit():
		return False, "The rdt must contain only numeric characters."

	# Split the string into j, k, l, and m
	j, k, l, m = [int(char) for char in rdt]

	if j == 0 and l == 0:  # the RDT can't be seen on any plane
		return False, "The rdt does not exist on any plane"
	if l+m == 0 and j !=0 and rdtplane != "x":
		return False, "The rdt does not exist on the vertical plane"
	elif j+k == 0 and l !=0 and rdtplane != "y":
		return False, "The rdt does not exist on the horizontal plane"
	elif j ==0 and rdtplane != "y":
		return False, "The rdt does not exist on the horizontal plane"
	elif l ==0 and rdtplane != "x":
		return False, "The rdt does not exist on the vertical plane"
	

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

def get_analysis_knobsetting(ldb,requested_knob,analyfile):
	############-> read the command.run file to generate a list of all the kicks used to produce this results folder
	fc=analyfile+'/command.run'
	rc=open(fc,'r')
	for line in rc.readlines():
		if re.search('/afs/cern.ch/eng/sl/lintrack/omc_python3/bin/python -m omc3.hole_in_one --optics',line):
			flist=line.partition('--files')[2].partition('--')[0].split(',') 
			break
	rc.close()
	knobsettings=[]
	for f in flist:
		kickname=f.rpartition('/')[2]
		kicktime=convert_from_kickfilename(kickname)
		localktime=utctolocal(kicktime)
		knobsetting=getknobsetting_statetracker(ldb,localktime,requested_knob)
		knobsettings.append([kicktime,knobsetting])

	if len(knobsettings)>1:  #### --> in case multiple files were used for the analysis - check all were performed at timestamp with equal knob settings
		for k in range(len(knobsettings)):
			if knobsettings[k][1]!=knobsettings[0][1]:
				print('Results file '+analyfile+' includes kicks with different knob settings')
				for k in range(len(knobsettings)):
					print(knobsettings[k])
				sys.exit('Terminating')

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
				if log_func:
					log_func(f"Loading configuration file from: {cf}")
				user_defaults = json.load(cf)
				defaults.update(user_defaults)
		except Exception as e:
			if log_func:
				log_func(f"Looking for configuration file at: {e}")
			pass
	return defaults