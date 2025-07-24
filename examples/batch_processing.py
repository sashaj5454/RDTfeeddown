#!/usr/bin/env python3
"""
Batch Processing Example

This example demonstrates how to process multiple RDT types and planes
in a batch workflow, suitable for automated analysis pipelines.
"""

import os
import sys
import itertools
from datetime import datetime
import rdtfeeddown as rdt

def setup_logging():
    """Setup basic logging for batch processing."""
    import logging
    
    # Create logs directory
    os.makedirs('logs', exist_ok=True)
    
    # Configure logging
    log_filename = f"logs/batch_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_filename),
            logging.StreamHandler(sys.stdout)
        ]
    )
    return logging.getLogger(__name__)

def batch_analysis(config):
    """
    Run batch analysis for multiple RDT types and planes.
    
    Parameters
    ----------
    config : dict
        Configuration dictionary with analysis parameters
        
    Returns
    -------
    dict
        Results summary with success/failure counts
    """
    logger = setup_logging()
    
    # Define RDT types and planes to analyze
    rdt_types = config.get('rdt_types', ['0030', '1002', '0012'])
    planes = config.get('planes', ['x', 'y'])
    
    # Initialize results tracking
    results = {
        'total': 0,
        'successful': 0,
        'failed': 0,
        'details': []
    }
    
    # Initialize database connection once
    logger.info("Initializing database connection...")
    try:
        ldb = rdt.utils.initialize_statetracker()
        logger.info("Database connection established")
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        return results
    
    # Load model data once
    logger.info("Loading model data...")
    try:
        b1_model_bpms, b1_bpm_data = rdt.utils.getmodelBPMs(config['model_b1'])
        b2_model_bpms, b2_bpm_data = rdt.utils.getmodelBPMs(config['model_b2'])
        logger.info(f"Models loaded: B1={len(b1_model_bpms)} BPMs, B2={len(b2_model_bpms)} BPMs")
    except Exception as e:
        logger.error(f"Failed to load models: {e}")
        return results
    
    # Process each RDT type and plane combination
    for rdt_type, plane in itertools.product(rdt_types, planes):
        results['total'] += 1
        analysis_id = f"f{rdt_type}_{plane}"
        
        logger.info(f"Starting analysis: {analysis_id}")
        
        try:
            # Create output directory for this analysis
            output_dir = os.path.join(config['base_output_dir'], analysis_id)
            os.makedirs(output_dir, exist_ok=True)
            
            # Determine RDT folder name
            rdtfolder = rdt.utils.rdt_to_order_and_type(rdt_type)
            
            # Analyze LHCB1
            logger.info(f"  Analyzing LHCB1 data for {analysis_id}...")
            b1_data = rdt.analysis.getrdt_omc3(
                ldb=ldb,
                beam='LHCB1',
                modelbpmlist=b1_model_bpms,
                bpmdata=b1_bpm_data,
                ref=config['ref_b1'],
                flist=config['files_b1'],
                knob=config['knob'],
                rdt=rdt_type,
                rdt_plane=plane,
                rdtfolder=rdtfolder,
                sim=config.get('simulation', False),
                propfile=config.get('propfile', None),
                threshold=config.get('threshold', 3.0),
                log_func=logger.info
            )
            
            # Analyze LHCB2
            logger.info(f"  Analyzing LHCB2 data for {analysis_id}...")
            b2_data = rdt.analysis.getrdt_omc3(
                ldb=ldb,
                beam='LHCB2',
                modelbpmlist=b2_model_bpms,
                bpmdata=b2_bpm_data,
                ref=config['ref_b2'],
                flist=config['files_b2'],
                knob=config['knob'],
                rdt=rdt_type,
                rdt_plane=plane,
                rdtfolder=rdtfolder,
                sim=config.get('simulation', False),
                propfile=config.get('propfile', None),
                threshold=config.get('threshold', 3.0),
                log_func=logger.info
            )
            
            # Perform fitting
            logger.info(f"  Fitting data for {analysis_id}...")
            b1_fitted = rdt.analysis.fit_BPM(b1_data)
            b2_fitted = rdt.analysis.fit_BPM(b2_data)
            
            # Generate plots
            logger.info(f"  Generating plots for {analysis_id}...")
            plot_count = generate_all_plots(
                b1_fitted, b2_fitted, rdt_type, plane, output_dir, logger
            )
            
            # Calculate summary statistics
            b1_avg_shift = rdt.analysis.calculate_avg_rdt_shift(b1_fitted)
            b2_avg_shift = rdt.analysis.calculate_avg_rdt_shift(b2_fitted)
            
            # Record success
            results['successful'] += 1
            results['details'].append({
                'analysis_id': analysis_id,
                'status': 'success',
                'b1_bpms': len(b1_fitted['data']),
                'b2_bpms': len(b2_fitted['data']),
                'plots_generated': plot_count,
                'b1_avg_shift': b1_avg_shift,
                'b2_avg_shift': b2_avg_shift,
                'output_dir': output_dir
            })
            
            logger.info(f"  ✓ {analysis_id} completed successfully")
            logger.info(f"    B1 BPMs: {len(b1_fitted['data'])}, B2 BPMs: {len(b2_fitted['data'])}")
            logger.info(f"    Plots: {plot_count}, Output: {output_dir}")
            
        except Exception as e:
            # Record failure
            results['failed'] += 1
            results['details'].append({
                'analysis_id': analysis_id,
                'status': 'failed',
                'error': str(e)
            })
            
            logger.error(f"  ✗ {analysis_id} failed: {e}")
            
    return results

def generate_all_plots(b1_data, b2_data, rdt_type, plane, output_dir, logger):
    """Generate all plots for an analysis."""
    plot_count = 0
    
    try:
        # Individual BPM plots for B1
        for bpm in b1_data['data'].keys():
            try:
                rdt.plotting.plot_BPM(bpm, b1_data, rdt_type, plane)
                plot_count += 1
            except Exception as e:
                logger.warning(f"Failed to plot B1 BPM {bpm}: {e}")
        
        # Individual BPM plots for B2
        for bpm in b2_data['data'].keys():
            try:
                rdt.plotting.plot_BPM(bpm, b2_data, rdt_type, plane)
                plot_count += 1
            except Exception as e:
                logger.warning(f"Failed to plot B2 BPM {bpm}: {e}")
        
        # Ring plots
        try:
            rdt.plotting.plot_RDT(b1_data, rdt_type, plane)
            plot_count += 1
        except Exception as e:
            logger.warning(f"Failed to generate B1 ring plot: {e}")
            
        try:
            rdt.plotting.plot_RDT(b2_data, rdt_type, plane)
            plot_count += 1
        except Exception as e:
            logger.warning(f"Failed to generate B2 ring plot: {e}")
        
        # Comparison plot
        try:
            rdt.plotting.plot_RDTshifts(b1_data, b2_data, rdt_type, plane)
            plot_count += 1
        except Exception as e:
            logger.warning(f"Failed to generate comparison plot: {e}")
            
    except Exception as e:
        logger.error(f"Error during plot generation: {e}")
    
    return plot_count

def generate_summary_report(results, output_file):
    """Generate a summary report of batch processing results."""
    
    with open(output_file, 'w') as f:
        f.write("RDTfeeddown Batch Analysis Summary Report\n")
        f.write("=" * 50 + "\n\n")
        f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        
        # Overall statistics
        f.write("Overall Statistics:\n")
        f.write(f"  Total analyses: {results['total']}\n")
        f.write(f"  Successful: {results['successful']}\n")
        f.write(f"  Failed: {results['failed']}\n")
        f.write(f"  Success rate: {results['successful']/results['total']*100:.1f}%\n\n")
        
        # Successful analyses
        if results['successful'] > 0:
            f.write("Successful Analyses:\n")
            f.write("-" * 20 + "\n")
            for detail in results['details']:
                if detail['status'] == 'success':
                    f.write(f"  {detail['analysis_id']}:\n")
                    f.write(f"    B1 BPMs: {detail['b1_bpms']}, B2 BPMs: {detail['b2_bpms']}\n")
                    f.write(f"    Plots: {detail['plots_generated']}\n")
                    f.write(f"    B1 avg shift: {detail['b1_avg_shift']:.6f}\n")
                    f.write(f"    B2 avg shift: {detail['b2_avg_shift']:.6f}\n")
                    f.write(f"    Output: {detail['output_dir']}\n\n")
        
        # Failed analyses
        if results['failed'] > 0:
            f.write("Failed Analyses:\n")
            f.write("-" * 16 + "\n")
            for detail in results['details']:
                if detail['status'] == 'failed':
                    f.write(f"  {detail['analysis_id']}: {detail['error']}\n")

def main():
    """Main batch processing function."""
    
    # Configuration
    config = {
        # File paths
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
        
        # Analysis parameters
        'knob': 'LHCBEAM/IP5-XING-H-MURAD',
        'rdt_types': ['0030', '1002', '0012', '0021'],  # Multiple RDT types
        'planes': ['x', 'y'],  # Both planes
        'threshold': 3.0,
        'simulation': False,
        
        # Output
        'base_output_dir': '/path/to/batch_output/',
    }
    
    print("RDTfeeddown Batch Processing")
    print("=" * 30)
    print(f"RDT types: {config['rdt_types']}")
    print(f"Planes: {config['planes']}")
    print(f"Total analyses: {len(config['rdt_types']) * len(config['planes'])}")
    print(f"Output directory: {config['base_output_dir']}")
    print()
    
    # Create base output directory
    os.makedirs(config['base_output_dir'], exist_ok=True)
    
    # Run batch analysis
    results = batch_analysis(config)
    
    # Generate summary report
    summary_file = os.path.join(config['base_output_dir'], 'summary_report.txt')
    generate_summary_report(results, summary_file)
    
    # Print final summary
    print("\nBatch Processing Complete!")
    print(f"Total: {results['total']}, Successful: {results['successful']}, Failed: {results['failed']}")
    print(f"Success rate: {results['successful']/results['total']*100:.1f}%")
    print(f"Summary report: {summary_file}")
    
    return 0 if results['failed'] == 0 else 1

if __name__ == "__main__":
    sys.exit(main())