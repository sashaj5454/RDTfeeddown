import matplotlib.pyplot as plt
import numpy as np

# ...existing code for plot_BPM, plot_RDTshifts, plot_RDT...
def plot_BPM(BPM,data,rdt,rdt_plane,filename):

    fig, (ax1, ax2) = plt.subplots(2,  1, sharey=False)
    diffdata=data[BPM]['diffdata']
    fitdata=data[BPM]['fitdata']
    xing=[]
    re=[]
    im=[]
    re_err=[]
    im_err=[]
    for x in range(len(diffdata)):
        xing.append(diffdata[x][0])
        re.append(diffdata[x][1])
        im.append(diffdata[x][2])

    xing=np.array(xing)
    re=np.array(re)
    im=np.array(im)
    
    xing_min=np.min(xing)
    xing_max=np.max(xing)
    xing_ran=xing_max-xing_min
    print(xing_min,xing_max,xing_ran)
    xfit=np.arange(xing_min,xing_max,xing_ran/100.0)
    refit=polyfunction(xfit,fitdata[0][0],fitdata[0][1],fitdata[0][2])
    imfit=polyfunction(xfit,fitdata[3][0],fitdata[3][1],fitdata[3][2])
    
    ax1.set_ylabel(BPM+f' Re$f_{{{rdt_plane},{rdt}}}$')
    ax1.set_xlabel('Knob trim')
    ax1.plot(xfit,refit)
    ax1.plot(xing,re,'ro')

    ax2.set_ylabel(BPM+f' Im$f_{{{rdt_plane},{rdt}}}$')
    ax2.set_xlabel('Knob trim')
    ax2.plot(xfit,imfit)
    ax2.plot(xing,im,'ro')

    plt.tight_layout()
    plt.savefig(filename, bbox_inches='tight')
    return

def plot_avg_rdt_shift(ax, data, rdt, rdt_plane, label_prefix):
    """
    Plot the average RDT shift and standard deviation for given data on the provided axis.
    """
    xing, ampdat, stddat = calculate_avg_rdt_shift(data)
    ax.set_ylabel(f'{label_prefix} sqrt($\\Delta$Re$f_{{{rdt_plane},{rdt}}}^2$+$\\Delta$Im$f_{{{rdt_plane},{rdt}}}^2$)')
    ax.set_xlabel(f'{label_prefix} Knob trim')
    ax.plot(xing, ampdat)
    ax.errorbar(xing, ampdat, yerr=stddat, fmt='ro')

def plot_RDTshifts(b1data, b2data, rdt, rdt_plane, filename):
    fig, ((ax1, ax2), (ax3, ax4), (ax5, ax6)) = plt.subplots(3, 2, sharey=False, figsize=(12, 10))

    # LHCB1 gradients
    sdat = []
    dredkdat = []
    dimdkdat = []
    dredkerr = []
    dimdkerr = []
    for b in b1data.keys():
        if not arcBPMcheck(b) or badBPMcheck(b):
            continue
        s = b1data[b]['s']
        dredk = b1data[b]['fitdata'][0][1]
        dimdk = b1data[b]['fitdata'][3][1]
        dreerr = b1data[b]['fitdata'][2][1]
        dimerr = b1data[b]['fitdata'][5][1]
        sdat.append(s)
        dredkdat.append(dredk)
        dimdkdat.append(dimdk)
        dredkerr.append(dreerr)
        dimdkerr.append(dimerr)

    sdat = np.array(sdat)
    dredkdat = np.array(dredkdat)
    dimdkdat = np.array(dimdkdat)
    dredkerr = np.array(dredkerr)
    dimdkerr = np.array(dimdkerr)

    ax3.set_ylabel(f'LHCB1 dRe$f_{{{rdt_plane},{rdt}}}$/dknob')
    ax3.set_xlabel('LHCB1 Knob trim')
    ax3.plot(sdat, dredkdat)
    ax3.errorbar(sdat, dredkdat, yerr=dredkerr, fmt='ro')

    ax5.set_ylabel(f'LHCB1 dIm$f_{{{rdt_plane},{rdt}}}$/dknob')
    ax5.set_xlabel('LHCB1 Knob trim')
    ax5.plot(sdat, dimdkdat)
    ax5.errorbar(sdat, dimdkdat, yerr=dimdkerr, fmt='ro')

    # LHCB2 gradients
    sdat = []
    dredkdat = []
    dimdkdat = []
    dredkerr = []
    dimdkerr = []
    for b in b2data.keys():
        if not arcBPMcheck(b) or badBPMcheck(b):
            continue
        s = b2data[b]['s']
        dredk = b2data[b]['fitdata'][0][1]
        dimdk = b2data[b]['fitdata'][3][1]
        dreerr = b2data[b]['fitdata'][2][1]
        dimerr = b2data[b]['fitdata'][5][1]
        sdat.append(s)
        dredkdat.append(dredk)
        dimdkdat.append(dimdk)
        dredkerr.append(dreerr)
        dimdkerr.append(dimerr)

    sdat = np.array(sdat)
    dredkdat = np.array(dredkdat)
    dimdkdat = np.array(dimdkdat)
    dredkerr = np.array(dredkerr)
    dimdkerr = np.array(dimdkerr)

    ax4.set_ylabel(f'LHCB2 dRe$f_{{{rdt_plane},{rdt}}}$/dknob')
    ax4.set_xlabel('LHCB2 Knob trim')
    ax4.plot(sdat, dredkdat)
    ax4.errorbar(sdat, dredkdat, yerr=dredkerr, fmt='ro')

    ax6.set_ylabel(f'LHCB2 dIm$f_{{{rdt_plane},{rdt}}}$/dknob')
    ax6.set_xlabel('LHCB2 Knob trim')
    ax6.plot(sdat, dimdkdat)
    ax6.errorbar(sdat, dimdkdat, yerr=dimdkerr, fmt='ro')

    # LHCB1 avg re**2+im**2
    plot_avg_rdt_shift(ax1, b1data, rdt, rdt_plane, "LHCB1")

    # LHCB2 avg re**2+im**2
    plot_avg_rdt_shift(ax2, b2data, rdt, rdt_plane, "LHCB2")

    # Adjust layout and spacing
    plt.tight_layout()
    plt.subplots_adjust(hspace=0.4, wspace=0.3)  # Adjust spacing between subplots
    plt.savefig(filename, bbox_inches='tight')
    return
###########################################################################################################################################################################
###########################################################################################################################################################################
def plot_RDT(b1data,b2data,rdt,rdt_plane, filename):
    fig, ((ax1,ax2),(ax3,ax4),(ax5,ax6)) = plt.subplots(3,  2, sharey=False)

    #############
    ############# LHCB1
    #############
    ax1.set_ylabel(f'LHCB1 $|f_{{{rdt_plane},{rdt}}}|$)')
    ax1.set_xlabel('LHCB1 Knob trim')

    ax3.set_ylabel(f'LHCB1 $\Delta Re(f_{{{rdt_plane},{rdt}}})$)')
    ax3.set_xlabel('LHCB1 Knob trim')

    ax5.set_ylabel(f'LHCB1 $\Delta Im(f_{{{rdt_plane},{rdt}}})$)')
    ax5.set_xlabel('LHCB1 Knob trim')

    ###      ### get the list of crossing angles measured
    xing=[]  
    for b in b1data.keys():
        diffdata=b1data[b]['diffdata']
        for x in range(len(diffdata)):
            xing.append(diffdata[x][0])
        break
    for x in xing:
        sdat=[]
        ampdat=[]
        amperrdat=[]
        redat=[]
        imdat=[]
        reerrdat=[]
        imerrdat=[]
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
                    sdat.append(s)
                    ampdat.append(amp)
                    redat.append(re)
                    imdat.append(im)

        sdat=np.array(sdat)
        ampdat=np.array(ampdat)
        amperrdat=np.array(amperrdat)
        redat=np.array(redat)
        imdat=np.array(imdat)
        reerrdat=np.array(reerrdat)
        imerrdat=np.array(imerrdat)
        
        ax1.plot(sdat,ampdat)
        ax1.plot(sdat,ampdat)

        ax3.plot(sdat,redat)
        ax3.plot(sdat,redat)

        ax5.plot(sdat,imdat)
        ax5.plot(sdat,imdat)


    #############
    ############# LHCB2
    #############
    ax2.set_ylabel(f'LHCB2 $|f_{{{rdt_plane},{rdt}}}|$)')
    ax2.set_xlabel('LHCB2 Knob trim')

    ax4.set_ylabel(f'LHCB2 $\Delta Re(f_{{{rdt_plane},{rdt}}})$)')
    ax4.set_xlabel('LHCB1 Knob trim')

    ax6.set_ylabel(f'LHCB2 $\Delta Im(f_{{{rdt_plane},{rdt}}})$)')
    ax6.set_xlabel('LHCB2 Knob trim')

    ###      ### get the list of crossing angles measured
    xing=[]  
    for b in b2data.keys():
        diffdata=b2data[b]['diffdata']
        for x in range(len(diffdata)):
            xing.append(diffdata[x][0])
        break
    for x in xing:
        sdat=[]
        ampdat=[]
        amperrdat=[]
        redat=[]
        imdat=[]
        reerrdat=[]
        imerrdat=[]
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
                    sdat.append(s)
                    ampdat.append(amp)
                    redat.append(re)
                    imdat.append(im)

        sdat=np.array(sdat)
        ampdat=np.array(ampdat)
        amperrdat=np.array(amperrdat)
        redat=np.array(redat)
        imdat=np.array(imdat)
        
        ax2.plot(sdat,ampdat)
        ax2.plot(sdat,ampdat)

        ax4.plot(sdat,redat)
        ax4.plot(sdat,redat)

        ax6.plot(sdat,imdat)
        ax6.plot(sdat,imdat)
    

        
    plt.tight_layout()
    plt.savefig(filename, bbox_inches='tight')
    return   
