#!/usr/bin/env python3
"""
Basic RDT Analysis Example

This example demonstrates the basic workflow for analyzing RDT feed-down
effects using the RDTfeeddown package.
"""

import os
import sys
import rdtfeeddown as rdt

def main():
    """Run basic RDT analysis example."""
    
    print("RDTfeeddown Basic Analysis Example")
    print("=" * 40)
    
    # Configuration
    config = {
        'model_b1': '/path/to/lhcb1_model.tfs',
        'model_b2': '/path/to/lhcb2_model.tfs',
        'ref_b1': '/path/to/lhcb1_reference/',
        'ref_b2': '/path/to/lhcb2_reference/',
        'files_b1': [
            '/path/to/lhcb1_scan_001/',
            '/path/to/lhcb1_scan_002/',
            '/path/to/lhcb1_scan_003/',
        ],
        'files_b2': [
            '/path/to/lhcb2_scan_001/',
            '/path/to/lhcb2_scan_002/',
            '/path/to/lhcb2_scan_003/',
        ],
        'output_dir': '/path/to/output/',
        'knob': 'LHCBEAM/IP5-XING-H-MURAD',
        'rdt': '0030',
        'plane': 'x',
        'threshold': 3.0
    }
    
    try:
        # Step 1: Initialize logging database connection
        print("\n1. Initializing database connection...")
        ldb = rdt.utils.initialize_statetracker()
        print("   ✓ Database connection established")
        
        # Step 2: Load model data for both beams
        print("\n2. Loading model data...")
        
        # LHCB1 model
        b1_model_bpms, b1_bpm_data = rdt.utils.getmodelBPMs(config['model_b1'])
        print(f"   ✓ LHCB1 model: {len(b1_model_bpms)} BPMs loaded")
        
        # LHCB2 model  
        b2_model_bpms, b2_bpm_data = rdt.utils.getmodelBPMs(config['model_b2'])
        print(f"   ✓ LHCB2 model: {len(b2_model_bpms)} BPMs loaded")
        
        # Step 3: Analyze LHCB1 data
        print("\n3. Analyzing LHCB1 data...")
        b1_rdt_data = rdt.analysis.getrdt_omc3(
            ldb=ldb,
            beam='LHCB1',
            modelbpmlist=b1_model_bpms,
            bpmdata=b1_bmp_data,
            ref=config['ref_b1'],
            flist=config['files_b1'],
            knob=config['knob'],
            rdt=config['rdt'],
            rdt_plane=config['plane'],
            rdtfolder=rdt.utils.rdt_to_order_and_type(config['rdt']),
            sim=False,
            propfile=None,
            threshold=config['threshold']
        )
        print(f"   ✓ Analysis complete: {len(b1_rdt_data['data'])} BPMs processed")
        
        # Step 4: Analyze LHCB2 data
        print("\n4. Analyzing LHCB2 data...")
        b2_rdt_data = rdt.analysis.getrdt_omc3(
            ldb=ldb,
            beam='LHCB2', 
            modelbpmlist=b2_model_bpms,
            bpmdata=b2_bpm_data,
            ref=config['ref_b2'],
            flist=config['files_b2'],
            knob=config['knob'],
            rdt=config['rdt'],
            rdt_plane=config['plane'],
            rdtfolder=rdt.utils.rdt_to_order_and_type(config['rdt']),
            sim=False,
            propfile=None,
            threshold=config['threshold']
        )
        print(f"   ✓ Analysis complete: {len(b2_rdt_data['data'])} BPMs processed")
        
        # Step 5: Perform polynomial fitting
        print("\n5. Performing polynomial fits...")
        b1_fitted = rdt.analysis.fit_BPM(b1_rdt_data)
        b2_fitted = rdt.analysis.fit_BPM(b2_rdt_data)
        print("   ✓ Polynomial fitting complete for both beams")
        
        # Step 6: Generate plots
        print("\n6. Generating plots...")
        os.makedirs(config['output_dir'], exist_ok=True)
        
        # Individual BPM plots for B1
        plot_count = 0
        for bpm in b1_fitted['data'].keys():
            output_file = os.path.join(
                config['output_dir'], 
                f"f{config['rdt']}_{config['plane']}_{bmp}_B1.png"
            )
            rdt.plotting.plot_BPM(bpm, b1_fitted, config['rdt'], config['plane'])
            plot_count += 1
            
        # Individual BPM plots for B2
        for bpm in b2_fitted['data'].keys():
            output_file = os.path.join(
                config['output_dir'],
                f"f{config['rdt']}_{config['plane']}_{bpm}_B2.png"
            )
            rdt.plotting.plot_BPM(bpm, b2_fitted, config['rdt'], config['plane'])
            plot_count += 1
            
        print(f"   ✓ {plot_count} individual BPM plots generated")
        
        # Ring-wide plots
        ring_plot_b1 = os.path.join(
            config['output_dir'],
            f"f{config['rdt']}_{config['plane']}_ring_B1.png"
        )
        rdt.plotting.plot_RDT(b1_fitted, config['rdt'], config['plane'])
        
        ring_plot_b2 = os.path.join(
            config['output_dir'],
            f"f{config['rdt']}_{config['plane']}_ring_B2.png"
        )
        rdt.plotting.plot_RDT(b2_fitted, config['rdt'], config['plane'])
        
        print("   ✓ Ring-wide plots generated")
        
        # Beam comparison plot
        comparison_plot = os.path.join(
            config['output_dir'],
            f"f{config['rdt']}_{config['plane']}_comparison.png"
        )
        rdt.plotting.plot_RDTshifts(
            b1_fitted, b2_fitted, config['rdt'], config['plane']
        )
        print("   ✓ Beam comparison plot generated")
        
        # Step 7: Summary statistics
        print("\n7. Analysis Summary:")
        print(f"   RDT Type: f{config['rdt']} ({rdt.utils.rdt_to_order_and_type(config['rdt'])})")
        print(f"   Measurement Plane: {config['plane']}")
        print(f"   Knob: {config['knob']}")
        print(f"   LHCB1 BPMs: {len(b1_fitted['data'])}")
        print(f"   LHCB2 BPMs: {len(b2_fitted['data'])}")
        print(f"   Output Directory: {config['output_dir']}")
        
        # Calculate average RDT shifts
        b1_avg_shift = rdt.analysis.calculate_avg_rdt_shift(b1_fitted)
        b2_avg_shift = rdt.analysis.calculate_avg_rdt_shift(b2_fitted)
        
        print(f"\n   Average RDT Shifts:")
        print(f"   LHCB1: {b1_avg_shift:.4f}")
        print(f"   LHCB2: {b2_avg_shift:.4f}")
        print(f"   Difference: {abs(b1_avg_shift - b2_avg_shift):.4f}")
        
        print("\n✓ Analysis completed successfully!")
        
    except Exception as e:
        print(f"\n✗ Error during analysis: {e}")
        import traceback
        traceback.print_exc()
        return 1
        
    return 0

if __name__ == "__main__":
    sys.exit(main())