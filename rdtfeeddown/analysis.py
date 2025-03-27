import numpy as np
from scipy.optimize import curve_fit

# ...existing code for getrdt_omc3, fit_BPM, write_RDTshifts...

def readrdtdatafile(cfile, rdt, rdt_plane, rdtfolder):
    """
    Reads RDT data from a file and removes outliers based on Z-scores.
    """
    cdat = []
    rf = open(cfile + f'/rdt/{rdtfolder}/f{rdt}_{rdt_plane}.tfs', 'r')
    csvrf = csv.reader(rf, delimiter=' ', skipinitialspace=True)
    raw_data = []

    for row in csvrf:
        if row[0] == '@' or row[0] == '*' or row[0] == '$':
            continue
        print(row)
        name = str(row[0])
        amp = float(row[3])
        re = float(row[7])
        im = float(row[8])
        raw_data.append([name, amp, re, im])

    rf.close()

    # Convert raw data to a NumPy array for Z-score calculation
    raw_data_np = np.array(raw_data, dtype=object)
    amp_values = raw_data_np[:, 1].astype(float)
    re_values = raw_data_np[:, 2].astype(float)
    im_values = raw_data_np[:, 3].astype(float)

    # Calculate Z-scores for amp, re, and im
    amp_zscores = zscore(amp_values)
    re_zscores = zscore(re_values)
    im_zscores = zscore(im_values)

    # Define a threshold for outlier detection (e.g., Z-score > 3)
    threshold = 3
    for i, (name, amp, re, im) in enumerate(raw_data):
        if abs(amp_zscores[i]) < threshold and abs(re_zscores[i]) < threshold and abs(im_zscores[i]) < threshold:
            cdat.append([name, amp, re, im])

    return cdat
###########################################################################################################################################################################
###########################################################################################################################################################################
def getrdt_omc3(ldb,modelbpmlist,bpmdata,ref,flist,knob,outputpath,timeoffset,rdt,rdt_plane,rdtfolder):
    ############### add reference values to bpm dict
    refk=get_analysis_knobsetting(ldb,knob,ref,timeoffset)
    refdat=readrdtdatafile(ref,rdt,rdt_plane,rdtfolder)
    for b in range(len(refdat)):
        name=refdat[b][0]
        amp=refdat[b][1]
        re=refdat[b][2]
        im=refdat[b][3]
        bpmdata[name]['ref'].append([refk,amp,re,im])
    ###############              append all the xing scan to bpm dict
    for f in flist:
        ksetting=get_analysis_knobsetting(ldb,knob,f,timeoffset)
        cdat=readrdtdatafile(f,rdt,rdt_plane,rdtfolder)
        for b in range(len(cdat)):
            name=cdat[b][0]
            amp=cdat[b][1]
            re=cdat[b][2]
            im=cdat[b][3]
            bpmdata[name]['data'].append([ksetting,amp,re,im])            
    ###############           create new dict which only include bpms which present in all files and reference
    intersectedBPMdata={}
    for b in range(len(modelbpmlist)):
        thisBPM=modelbpmlist[b]
        if len(bpmdata[thisBPM]['ref'])!=1:
            continue
        if len(bpmdata[thisBPM]['data'])!=len(flist):
            continue

        intersectedBPMdata[thisBPM]={}
        
        s=bpmdata[thisBPM]['s']
        ref=bpmdata[thisBPM]['ref']
        dat=bpmdata[thisBPM]['data']

        ### calculate the re and im diffs
        diffdat=[]
        for k in range(len(dat)):
            kdiff=dat[k][0]-ref[0][0]
            rediff=dat[k][2]-ref[0][2]
            imdiff=dat[k][3]-ref[0][3]
            diffdat.append([kdiff,rediff,imdiff])
        diffdat=sorted(diffdat,key=lambda x: x[0])
        
        intersectedBPMdata[thisBPM]['s']=s
        intersectedBPMdata[thisBPM]['diffdata']=diffdat
    ################
    return intersectedBPMdata
###########################################################################################################################################################################
###########################################################################################################################################################################
def polyfunction(x,c,m,n):
    y=c+m*x+n*x**2
    return y
###########################################################################################################################################################################
###########################################################################################################################################################################
def fitdata(xdata,ydata,yerrdata,fitfunction):
    popt,pcov = curve_fit(fitfunction,xdata,ydata,sigma=yerrdata,absolute_sigma=True)
    perr = np.sqrt(np.diag(pcov))
    return popt,pcov,perr
###########################################################################################################################################################################
###########################################################################################################################################################################
def fitdatanoerrors(xdata,ydata,fitfunction):
    popt,pcov = curve_fit(fitfunction,xdata,ydata)
    perr = np.sqrt(np.diag(pcov))
    return popt,pcov,perr
###########################################################################################################################################################################
###########################################################################################################################################################################
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
###########################################################################################################################################################################
###########################################################################################################################################################################
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

def write_RDTshifts(b1data,b2data,rdt,rdt_plane):
    #############
    ############# LHCB1 gradients
    #############
    fout=f'data_b1_f{rdt}{rdt_plane}rdtgradient.csv'
    wout=open(fout,'w')
    csvwout=csv.writer(wout,delimiter=' ')
    header=['#name','s',f'd(Ref{rdt}_{rdt_plane})/dknob',f'd(Imf{rdt}_{rdt_plane})/dknob','re fit error','im fit error']
    csvwout.writerow(header)
    for b in b1data.keys():
        if arcBPMcheck(b)==False:
            continue
        if badBPMcheck(b)==True:
            continue
        s=b1data[b]['s']
        dredk=b1data[b]['fitdata'][0][1]
        dimdk=b1data[b]['fitdata'][3][1]
        dreerr=b1data[b]['fitdata'][2][1]
        dimerr=b1data[b]['fitdata'][5][1]
        csvwout.writerow([b,s,dredk,dimdk,dreerr,dimerr])
    wout.close()
    #############
    ############# LHCB2 gradients
    #############
    fout=f'data_b2_f{rdt}{rdt_plane}rdtgradient.csv'
    wout=open(fout,'w')
    csvwout=csv.writer(wout,delimiter=' ')
    header=['#name','s',f'd(Ref{rdt}_{rdt_plane})/dknob',f'd(Imf{rdt}_{rdt_plane})/dknob','re fit error','im fit error']
    csvwout.writerow(header)
    for b in b2data.keys():
        if arcBPMcheck(b)==False:
            continue
        if badBPMcheck(b)==True:
            continue
        s=b2data[b]['s']
        dredk=b2data[b]['fitdata'][0][1]
        dimdk=b2data[b]['fitdata'][3][1]
        dreerr=b2data[b]['fitdata'][2][1]
        dimerr=b2data[b]['fitdata'][5][1]
        csvwout.writerow([b,s,dredk,dimdk,dreerr,dimerr])
    wout.close()
    #############
    ############# LHCB1 avg re**2+im**2
    #############
    xing=[]  ### get the list of crossing angles measured
    for b in b1data.keys():
        diffdata=b1data[b]['diffdata']
        for x in range(len(diffdata)):
            xing.append(diffdata[x][0])
        break
    ######## now loop over xings
    fout=f'data_b1_f{rdt}{rdt_plane}rdtshiftvsknob.csv'
    wout=open(fout,'w')
    csvwout=csv.writer(wout,delimiter=' ')
    header=['#xing','sqrt(Dre^2+Dim^2)','std_dev over BPM']
    csvwout.writerow(header)
    for x in xing:
        toavg=[]
        for b in b1data.keys():
            if arcBPMcheck(b)==False:
                continue
            if badBPMcheck(b)==True:
                continue
            diffdata=b1data[b]['diffdata']
            for y in range(len(diffdata)):
                if diffdata[y][0]==x:
                    re=diffdata[y][1]
                    im=diffdata[y][2]
                    amp=np.sqrt(re**2+im**2)
                    toavg.append(amp)
        avgRDTshift=np.mean(np.array(toavg))
        avgRDTshifterr=np.std(np.array(toavg))
        csvwout.writerow([x,avgRDTshift,avgRDTshifterr])
    wout.close()
    #############
    ############# LHCB2 avg re**2+im**2
    #############
    xing=[]  ### get the list of crossing angles measured
    for b in b2data.keys():
        diffdata=b2data[b]['diffdata']
        for x in range(len(diffdata)):
            xing.append(diffdata[x][0])
        break
    ######## now loop over xings
    fout=f'data_b2_f{rdt}{rdt_plane}rdtshiftvsknob.csv'
    wout=open(fout,'w')
    csvwout=csv.writer(wout,delimiter=' ')
    header=['#xing','sqrt(Dre^2+Dim^2)','std_dev over BPM']
    csvwout.writerow(header)
    for x in xing:
        toavg=[]
        for b in b2data.keys():
            if arcBPMcheck(b)==False:
                continue
            if badBPMcheck(b)==True:
                continue
            diffdata=b2data[b]['diffdata']
            for y in range(len(diffdata)):
                if diffdata[y][0]==x:
                    re=diffdata[y][1]
                    im=diffdata[y][2]
                    amp=np.sqrt(re**2+im**2)
                    toavg.append(amp)
        avgRDTshift=np.mean(np.array(toavg))
        avgRDTshifterr=np.std(np.array(toavg))
        csvwout.writerow([x,avgRDTshift,avgRDTshifterr])
    wout.close()


    #############
    ############# LHCB1 RDT deltas
    #############
    ###      ### get the list of crossing angles measured
    xing=[]  
    for b in b1data.keys():
        diffdata=b1data[b]['diffdata']
        for x in range(len(diffdata)):
            xing.append(diffdata[x][0])
        break
    for x in xing:
        fout=f'data_b1_f{rdt}{rdt_plane}rdtdelta_knob_'+str(x)+'.csv'
        wout=open(fout,'w')
        csvwout=csv.writer(wout,delimiter=' ')
        header=['#name','s','delta amp','delta re','delta im']
        csvwout.writerow(header)
        for b in b1data.keys():
            if arcBPMcheck(b)==False:
                continue
            if badBPMcheck(b)==True:
                continue
            s=b1data[b]['s']
            diffdata=b1data[b]['diffdata']
            for y in range(len(diffdata)):
                if diffdata[y][0]==x:
                    re=diffdata[y][1]
                    im=diffdata[y][2]
                    amp=np.sqrt(re**2+im**2)

                    csvwout.writerow([b,s,amp,re,im])
        wout.close()

    #############
    ############# LHCB2 RDT deltas
    #############
    ###      ### get the list of crossing angles measured
    xing=[]  
    for b in b2data.keys():
        diffdata=b2data[b]['diffdata']
        for x in range(len(diffdata)):
            xing.append(diffdata[x][0])
        break
    for x in xing:
        fout=f'data_b2_f{rdt}{rdt_plane}rdtdelta_knob_'+str(x)+'.csv'
        wout=open(fout,'w')
        csvwout=csv.writer(wout,delimiter=' ')
        header=['#name','s','delta amp','delta re','delta im']
        csvwout.writerow(header)
        for b in b2data.keys():
            if arcBPMcheck(b)==False:
                continue
            if badBPMcheck(b)==True:
                continue
            s=b2data[b]['s']
            diffdata=b2data[b]['diffdata']
            for y in range(len(diffdata)):
                if diffdata[y][0]==x:
                    re=diffdata[y][1]
                    im=diffdata[y][2]
                    amp=np.sqrt(re**2+im**2)

                    csvwout.writerow([b,s,amp,re,im])
        wout.close()

    return
###########################################################################################################################################################################
###########################################################################################################################################################################
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

