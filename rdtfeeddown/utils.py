import os
import sys
import re
import datetime as dt
from optparse import OptionParser
import pytimber
from zoneinfo import ZoneInfo 

# ...existing code for parse_options, initialize_statetracker, get_analysis_knobsetting, getmodelBPMs...
def parse_options():
    """
    Parse command-line options for the script.
    """
    parser = OptionParser()
    
    # Model paths
    parser.add_option("-m", "--model1",
                      help="Path to Beam1 model",
                      metavar="MODEL1", default="./2025-03-10/LHCB1/", dest="model1")
    parser.add_option("-n", "--model2",
                      help="Path to Beam2 model",
                      metavar="MODEL2", default="./2025-03-11/LHCB2/", dest="model2")
    
    # Reference measurements
    parser.add_option("-r", "--ref1",
                      help="Reference measurement for Beam1",
                      metavar="REF1", default="./2025-03-11/LHCB1/", dest="ref1", type=str)
    parser.add_option("-s", "--ref2",
                      help="Reference measurement for Beam2",
                      metavar="REF2", default="./2025-03-11/LHCB2/", dest="ref2", type=str)
    
    # Analysis folders
    parser.add_option("-f", "--file1",
                      help="Comma-separated list of analysis folders for Beam1",
                      metavar="FILE1", default="./2025-03-11/LHCB1/", dest="file1", type=str)
    parser.add_option("-g", "--file2",
                      help="Comma-separated list of analysis folders for Beam2",
                      metavar="FILE2", default="./2025-03-11/LHCB2/", dest="file2", type=str)
    
    # Knob and output path
    parser.add_option("-k", "--knob",
                      help="Knob name",
                      metavar="KNOB", default="LHCBEAM/IP5-XING-H-MURAD", dest="knob")
    parser.add_option("-o", "--outputpath",
                      help="Path to output results and extracted data",
                      metavar="OUTPUTPATH", default="./", dest="outputpath")
    
    # Time offset and RDT
    parser.add_option("-t", "--timeoffset",
                      help="Offset in hours between UTC/ACD kick times and state tracker acquisition",
                      metavar="TIMEOFFSET", default=1.0, dest="timeoffset", type=float)
    parser.add_option("-u", "--rdt",
                      help="RDT to analyze in format jklm followed by plane (e.g., 0030y)",
                      metavar="RDT", default="0030y", dest="rdtchosen")
    
    # Parse options
    options, _ = parser.parse_args()
    
    # Resolve paths
    model1 = os.path.abspath(options.model1) + '/'
    model2 = os.path.abspath(options.model2) + '/'
    ref1 = os.path.abspath(options.ref1) + '/'
    ref2 = os.path.abspath(options.ref2) + '/'
    outputpath = os.path.abspath(options.outputpath) + '/'
    
    # Parse file lists
    f_lhcb1 = [os.path.abspath(f) for f in options.file1.split(',')]
    f_lhcb2 = [os.path.abspath(f) for f in options.file2.split(',')]
    
    # Validate output path
    if not os.path.exists(outputpath):
        sys.exit(f"Error: Output path does not exist: {outputpath}")
    
    # Parse RDT
    rdtchosen = options.rdtchosen
    rdt = check_rdt(rdtchosen[:-1], rdtchosen[-1])
    rdt_plane = rdtchosen[-1]
    rdtfolder = rdt_to_order_and_type(rdt)
    rdt = "".join(map(str, rdt))
    
    # Return parsed options
    return model1, model2, ref1, ref2, f_lhcb1, f_lhcb2, outputpath, options.knob, int(options.timeoffset), rdt, rdt_plane, rdtfolder

def check_rdt(
	rdt:str, 
	rdtplane:str
):
	if len(rdt) != 4:
		raise ValueError("The rdt must be exactly 4 characters long.")

	# Check if all characters are digits
	if not rdt.isdigit():
		raise ValueError("The rdt must contain only numeric characters.")

	# Split the string into j, k, l, and m
	j, k, l, m = [int(char) for char in rdt]

	if j == 0 and l == 0:  # the RDT can't be seen on any plane
		raise ValueError("The rdt does not exist on any plane")
	if l+m == 0 and j !=0 and rdtplane != "x":
		raise ValueError("The rdt does not exist on the vertical plane") 
	elif j+k == 0 and l !=0 and rdtplane != "y":
		raise ValueError("The rdt does not exist on the horizontal plane")
	elif j ==0 and rdtplane != "y":
		raise ValueError("The rdt does not exist on the horizontal plane")
	elif l ==0 and rdtplane != "x":
		raise ValueError("The rdt does not exist on the vertical plane")
	

	return j, k, l, m

def rdt_to_order_and_type(
    rdt: tuple
):
    j, k, l, m = rdt 
    rdt_type = "normal" if (l + m) % 2 == 0 else "skew"
    orders = dict(((1, "dipole"), 
                   (2, "quadrupole"), 
                   (3, "sextupole"), 
                   (4, "octupole"),
                   (5, "decapole"),
                   (6, "dodecapole"),
                   (7, "tetradecapole"),
                   (8, "hexadecapole"),
                 ))
    return f"{rdt_type}_{orders[j + k + l + m]}"

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

def parse_timestamp(thistime):
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
    twissfile=modelpath+'twiss.dat'
    rt=open(twissfile,'r')
    csvrt=csv.reader(rt,delimiter=' ',skipinitialspace=True)
    for row in csvrt:
        if row[0]=='@' or row[0]=='*' or row[0]=='$':
            continue
        elif re.search('BPM',row[0]):
            modelbpmlist.append(row[0])
            bpmdata[row[0]]={}
            bpmdata[row[0]]['s']=float(row[1])
            bpmdata[row[0]]['ref']=[]
            bpmdata[row[0]]['data']=[]
    rt.close()
    return modelbpmlist,bpmdata