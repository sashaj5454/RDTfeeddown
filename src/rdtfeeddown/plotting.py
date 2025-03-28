import matplotlib.pyplot as plt
import numpy as np
from .analysis import polyfunction, calculate_avg_rdt_shift, arcBPMcheck, badBPMcheck

def plot_BPM(BPM, data, rdt, rdt_plane, filename):

    fig, (ax1, ax2) = plt.subplots(2,  1, sharey=False)
    diffdata = data[BPM]['diffdata']
    fitdata = data[BPM]['fitdata']
    xing = []
    re = []
    im = []
    for x in range(len(diffdata)):
        xing.append(diffdata[x][0])
        re.append(diffdata[x][1])
        im.append(diffdata[x][2])

    xing = np.array(xing)
    re = np.array(re)
    im = np.array(im)
    
    xing_min = np.min(xing)
    xing_max = np.max(xing)
    xing_ran = xing_max - xing_min
    print(xing_min, xing_max, xing_ran)
    xfit = np.arange(xing_min, xing_max, xing_ran / 100.0)
    refit = polyfunction(xfit, fitdata[0][0], fitdata[0][1], fitdata[0][2])
    imfit = polyfunction(xfit, fitdata[3][0], fitdata[3][1], fitdata[3][2])
    
    ax1.set_ylabel(BPM + f' Re$f_{{{rdt_plane},{rdt}}}$')
    ax1.set_xlabel('Knob trim')
    ax1.plot(xfit, refit)
    ax1.plot(xing, re, 'ro')

    ax2.set_ylabel(BPM + f' Im$f_{{{rdt_plane},{rdt}}}$')
    ax2.set_xlabel('Knob trim')
    ax2.plot(xfit, imfit)
    ax2.plot(xing, im, 'ro')

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

def plot_RDTshifts(beam_data, rdt, rdt_plane, filename):
    fig, axes = plt.subplots(3, 2, sharey=False, figsize=(12, 10))
    ax1, ax2, ax3, ax4, ax5, ax6 = axes.flatten()

    for i, (beam_label, data) in enumerate(beam_data.items()):
        sdat, dredkdat, dimdkdat, dredkerr, dimdkerr = [], [], [], [], []
        for b in data.keys():
            if not arcBPMcheck(b) or badBPMcheck(b):
                continue
            s = data[b]['s']
            dredk = data[b]['fitdata'][0][1]
            dimdk = data[b]['fitdata'][3][1]
            dreerr = data[b]['fitdata'][2][1]
            dimerr = data[b]['fitdata'][5][1]
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

        ax3.set_ylabel(f'{beam_label} dRe$f_{{{rdt_plane},{rdt}}}$/dknob')
        ax3.set_xlabel(f'{beam_label} Knob trim')
        ax3.plot(sdat, dredkdat)
        ax3.errorbar(sdat, dredkdat, yerr=dredkerr, fmt='ro')

        ax5.set_ylabel(f'{beam_label} dIm$f_{{{rdt_plane},{rdt}}}$/dknob')
        ax5.set_xlabel(f'{beam_label} Knob trim')
        ax5.plot(sdat, dimdkdat)
        ax5.errorbar(sdat, dimdkdat, yerr=dimdkerr, fmt='ro')

        plot_avg_rdt_shift(ax1 if i == 0 else ax2, data, rdt, rdt_plane, beam_label)

    plt.tight_layout()
    plt.subplots_adjust(hspace=0.4, wspace=0.3)
    plt.savefig(filename, bbox_inches='tight')
    return

def plot_RDT(beam_data, rdt, rdt_plane, filename):
    fig, axes = plt.subplots(3, 2, sharey=False)
    ax1, ax2, ax3, ax4, ax5, ax6 = axes.flatten()

    for i, (beam_label, data) in enumerate(beam_data.items()):
        ax1.set_ylabel(f'{beam_label} $|f_{{{rdt_plane},{rdt}}}|$')
        ax1.set_xlabel(f'{beam_label} Knob trim')

        ax3.set_ylabel(f'{beam_label} $\Delta Re(f_{{{rdt_plane},{rdt}}})$')
        ax3.set_xlabel(f'{beam_label} Knob trim')

        ax5.set_ylabel(f'{beam_label} $\Delta Im(f_{{{rdt_plane},{rdt}}})$')
        ax5.set_xlabel(f'{beam_label} Knob trim')

        xing = []
        for b in data.keys():
            diffdata = data[b]['diffdata']
            for x in range(len(diffdata)):
                xing.append(diffdata[x][0])
            break

        for x in xing:
            sdat, ampdat, redat, imdat = [], [], [], []
            for b in data.keys():
                if not arcBPMcheck(b) or badBPMcheck(b):
                    continue
                s = data[b]['s']
                diffdata = data[b]['diffdata']
                for y in range(len(diffdata)):
                    if diffdata[y][0] == x:
                        re = diffdata[y][1]
                        im = diffdata[y][2]
                        amp = np.sqrt(re**2 + im**2)
                        sdat.append(s)
                        ampdat.append(amp)
                        redat.append(re)
                        imdat.append(im)

            sdat = np.array(sdat)
            ampdat = np.array(ampdat)
            redat = np.array(redat)
            imdat = np.array(imdat)

            ax1.plot(sdat, ampdat)
            ax3.plot(sdat, redat)
            ax5.plot(sdat, imdat)

    plt.tight_layout()
    plt.savefig(filename, bbox_inches='tight')
    return
