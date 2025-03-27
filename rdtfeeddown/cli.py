import sys
from .utils import parse_options, initialize_statetracker, get_analysis_knobsetting, getmodelBPMs
from .analysis import getrdt_omc3, fit_BPM, write_RDTshifts
from .plotting import plot_BPM, plot_RDTshifts, plot_RDT

def main():
    print('\n\n')
    print('----------------------------------------------------------------------------------')
    print('A code to get RDT data during a crossing angle scan')
    print('----------------------------------------------------------------------------------')
    print('Running version: ' + str(sys.version))
    
    # Parse options
    model1, model2, ref1, ref2, f_lhcb1, f_lhcb2, outputpath, knob, timeoffset, rdt, rdt_plane, rdtfolder = parse_options()
    
    print('\n\n')
    print('----------------------------------------------------------------------------------')
    print('Output will be written to: ' + outputpath)
    
    # Initialize state tracker
    print('\n\n')
    print('----------------------------------------------------------------------------------')
    print('Initializing state tracker:\n')
    ldb = initialize_statetracker()
    
    # LHCB1 Analysis
    print('\n\n')
    print('----------------------------------------------------------------------------------')
    print('Analysis on OMC3 results files for LHCB1:\n')
    refknob = get_analysis_knobsetting(ldb, knob, ref1, timeoffset)
    print('Reference Measurement ---> ' + ref1 + ' at ' + knob + ' = ' + str(refknob) + '\n')
    for f in f_lhcb1:
        print(f + ' at ' + knob + ' = ' + str(get_analysis_knobsetting(ldb, knob, f, timeoffset)))
    
    b1modelbpmlist, b1bpmdata = getmodelBPMs(model1)
    b1rdtdata = getrdt_omc3(ldb, b1modelbpmlist, b1bpmdata, ref1, f_lhcb1, knob, outputpath, timeoffset, rdt, rdt_plane, rdtfolder)
    b1rdtdata = fit_BPM(b1rdtdata)
    
    for b in b1rdtdata.keys():
        plot_BPM(b, b1rdtdata, rdt, rdt_plane, f"{outputpath}/f{rdt}_{rdt_plane}_{b}.png")
    
    # LHCB2 Analysis
    print('\n\n')
    print('----------------------------------------------------------------------------------')
    print('Analysis on OMC3 results files for LHCB2:\n')
    refknob = get_analysis_knobsetting(ldb, knob, ref2, timeoffset)
    print('Reference Measurement ---> ' + ref2 + ' at ' + knob + ' = ' + str(refknob) + '\n')
    for f in f_lhcb2:
        print(f + ' at ' + knob + ' = ' + str(get_analysis_knobsetting(ldb, knob, f, timeoffset)))
    
    b2modelbpmlist, b2bpmdata = getmodelBPMs(model2)
    b2rdtdata = getrdt_omc3(ldb, b2modelbpmlist, b2bpmdata, ref2, f_lhcb2, knob, outputpath, timeoffset, rdt, rdt_plane, rdtfolder)
    b2rdtdata = fit_BPM(b2rdtdata)
    
    for b in b2rdtdata.keys():
        plot_BPM(b, b2rdtdata, rdt, rdt_plane, f"{outputpath}/f{rdt}_{rdt_plane}_{b}.png")
    
    # Final Plots
    print('\n\n')
    print('----------------------------------------------------------------------------------')
    print('Final Plots:\n')
    plot_RDTshifts(b1rdtdata, b2rdtdata, rdt, rdt_plane, f"{outputpath}/RDT_shifts.png")
    plot_RDT(b1rdtdata, b2rdtdata, rdt, rdt_plane, f"{outputpath}/RDT.png")
    
    # Write CSV Data
    print('\n\n')
    print('----------------------------------------------------------------------------------')
    print('Writing csv data:\n')
    write_RDTshifts(b1rdtdata, b2rdtdata, rdt, rdt_plane)

if __name__ == "__main__":
    main()
