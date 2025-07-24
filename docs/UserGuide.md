# User Guide

This guide provides step-by-step instructions for using RDTfeeddown to analyze resonance driving terms (RDT) feed-down effects in particle accelerators.

## What is RDT Feed-down Analysis?

Resonance Driving Terms (RDTs) are mathematical quantities that describe how magnetic field errors affect particle motion in accelerators. Feed-down analysis studies how these RDTs change when machine parameters (like crossing angles) are varied, which is crucial for:

- Understanding beam-beam effects at interaction points
- Optimizing machine performance during physics data taking
- Identifying sources of nonlinear perturbations
- Correcting optical distortions

## Quick Start

### Prerequisites

1. **CERN Access**: You need access to CERN's network and logging database
2. **OMC3 Results**: Pre-processed optics measurement data
3. **Model Files**: Accelerator model files for both beams

### Basic Workflow

1. **Prepare Data**: Organize OMC3 analysis results and model files
2. **Choose Interface**: Use GUI for interactive analysis or CLI for batch processing
3. **Configure Analysis**: Select RDT type, measurement plane, and knob
4. **Run Analysis**: Process data with outlier filtering and fitting
5. **Review Results**: Examine plots and export data

## Data Preparation

### Required Files

**Model Files**: Contain BPM positions and optical functions
- Format: TFS files from MAD-X or similar
- Required: One file each for LHCB1 and LHCB2
- Location: Usually in `/afs/cern.ch/eng/lhc/optics/...`

**Reference Measurements**: Baseline RDT measurements
- Format: OMC3 analysis result directories
- Contents: `rdt/` subdirectory with TFS files
- Purpose: Define zero-point for differential analysis

**Scan Measurements**: RDT measurements at different knob settings
- Format: Multiple OMC3 analysis result directories
- Requirements: Each directory must contain `command.run` and `rdt/` files
- Organization: One directory per knob setting

### File Structure Example

```
/path/to/analysis/
├── models/
│   ├── lhcb1_model.tfs
│   └── lhcb2_model.tfs
├── reference/
│   ├── lhcb1_ref/
│   │   ├── command.run
│   │   └── rdt/normal_quadrupole/f0030_x.tfs
│   └── lhcb2_ref/
│       ├── command.run
│       └── rdt/normal_quadrupole/f0030_x.tfs
└── measurements/
    ├── lhcb1_scan_001/
    ├── lhcb1_scan_002/
    ├── lhcb2_scan_001/
    └── lhcb2_scan_002/
```

## Using the Graphical Interface

### Launching the GUI

```bash
# Start the application
python -m rdtfeeddown

# Or if installed globally
rdtfeeddown-gui
```

### Step 1: File Selection

1. **Model Files**:
   - Click "Browse" next to "LHCB1 Model" and "LHCB2 Model"
   - Select the appropriate TFS model files

2. **Reference Measurements**:
   - Select reference directories for both beams
   - These define your baseline RDT values

3. **Scan Measurements**:
   - Use the multi-select browser to choose scan directories
   - Select multiple directories for each beam

4. **Output Directory**:
   - Choose where results and plots will be saved

### Step 2: Analysis Configuration

1. **Knob Selection**:
   - Enter the machine knob name (e.g., `LHCBEAM/IP5-XING-H-MURAD`)
   - This must match the logged parameter name exactly

2. **RDT Parameters**:
   - **RDT Type**: Select from dropdown (f0030, f1002, etc.)
   - **Plane**: Choose 'x' or 'y' measurement plane
   - **Threshold**: Outlier detection sensitivity (default: 3σ)

### Step 3: Validation

1. **Check Files**: Click "Validate" to verify:
   - File structure consistency
   - Beam number matching
   - Required subdirectories present

2. **Review Warnings**: Address any validation issues before proceeding

### Step 4: Run Analysis

1. **Start Processing**: Click "Run Analysis"
2. **Monitor Progress**: Watch the progress bar and log messages
3. **Review Results**: Examine generated plots in the integrated viewer

### Step 5: Export Results

1. **Plots**: Use "Export" buttons to save individual plots
2. **Data**: Save processed data in various formats
3. **Reports**: Generate summary reports with key findings

## Using the Command Line

### Basic Syntax

```bash
rdtfeeddown \
    --model1 /path/to/lhcb1_model.tfs \
    --model2 /path/to/lhcb2_model.tfs \
    --ref1 /path/to/lhcb1_reference/ \
    --ref2 /path/to/lhcb2_reference/ \
    --files-b1 /path/to/b1_scan1/,/path/to/b1_scan2/ \
    --files-b2 /path/to/b2_scan1/,/path/to/b2_scan2/ \
    --output /path/to/output/ \
    --knob "LHCBEAM/IP5-XING-H-MURAD" \
    --rdt "0030" \
    --plane "x"
```

### Advanced Options

```bash
# With additional parameters
rdtfeeddown \
    [basic options...] \
    --timeoffset 0 \
    --threshold 2.5 \
    --rdtfolder "normal_quadrupole"
```

### Batch Processing Example

```bash
#!/bin/bash
# Process multiple RDT types
for rdt in "0030" "1002" "0012"; do
    for plane in "x" "y"; do
        rdtfeeddown \
            --model1 models/lhcb1.tfs \
            --model2 models/lhcb2.tfs \
            --ref1 reference/b1/ \
            --ref2 reference/b2/ \
            --files-b1 $(ls -d scans/b1_*/ | tr '\n' ',') \
            --files-b2 $(ls -d scans/b2_*/ | tr '\n' ',') \
            --output results/f${rdt}_${plane}/ \
            --knob "LHCBEAM/IP5-XING-H-MURAD" \
            --rdt "$rdt" \
            --plane "$plane"
    done
done
```

## Understanding the Results

### Plot Types

**BPM-by-BPM Plots** (`f{rdt}_{plane}_{bpm}.png`):
- Show RDT evolution vs knob setting for individual BPMs
- Include polynomial fits and error bars
- Separate subplots for real and imaginary parts

**Ring Plots** (`f{rdt}_{plane}_ring.png`):
- Display RDT amplitude around the entire ring
- Show IP positions and beam-specific patterns
- Useful for identifying localized effects

**Shift Comparison** (`f{rdt}_{plane}_shifts.png`):
- Compare RDT changes between beams
- Highlight differential effects
- Important for beam-beam interaction studies

### Interpreting Data

**Polynomial Fits**:
- **Linear**: Indicates proportional feed-down effect
- **Quadratic**: Shows nonlinear response to knob changes
- **Poor Fit**: May indicate measurement issues or complex dynamics

**Error Bars**:
- **Small**: High-precision measurements
- **Large**: Potentially noisy data or unstable conditions
- **Asymmetric**: May indicate systematic effects

**Beam Differences**:
- **Similar Patterns**: Expected for symmetric machine
- **Large Differences**: May indicate asymmetric errors or beam-beam effects
- **Opposite Signs**: Could indicate coupling or feed-down mechanisms

## Troubleshooting

### Common Issues

**"No module named pytimber"**
```bash
# Solution: Install from CERN repository
pip install --index-url https://acc-py-repo.cern.ch pytimber
```

**"Reference knob not found"**
- Check knob name spelling and format
- Verify command.run files contain correct timestamps
- Ensure database connection is working

**"Beam number mismatch"**
- Verify model files match measurement beam
- Check that B1 and B2 files aren't mixed up
- Review file selection in GUI

**"No BPM data found"**
- Confirm RDT files exist in `rdt/` subdirectories
- Check RDT type and plane selection
- Verify file permissions and paths

### Data Quality Issues

**Excessive Outliers**:
- Reduce threshold parameter (e.g., from 3 to 2)
- Check measurement conditions during scan
- Review individual BPM plots for patterns

**Poor Fits**:
- Examine knob setting range and spacing
- Look for measurement gaps or inconsistencies
- Consider different polynomial orders

**Missing Data Points**:
- Check for incomplete scans
- Verify all measurement directories are included
- Review log messages for processing errors

## Advanced Usage

### Custom RDT Types

To analyze custom RDT types:

1. **Add RDT Definition**: Modify `utils.py` order mapping
2. **Create Files**: Ensure OMC3 generates appropriate RDT files  
3. **Update Folders**: Use correct `--rdtfolder` parameter

### Simulation Mode

For simulated data analysis:

```bash
rdtfeeddown \
    [standard options...] \
    --simulation \
    --propfile mapping.csv
```

The mapping file should contain:
```csv
MATCH,KNOB
measurement_pattern_1,0.5
measurement_pattern_2,1.0
```

### Programming Interface

For custom analysis workflows:

```python
import rdtfeeddown as rdt

# Load and process data
ldb = rdt.utils.initialize_statetracker()
model_bpms, bpm_data = rdt.utils.getmodelBPMs('model.tfs')

# Run analysis
results = rdt.analysis.getrdt_omc3(
    ldb, 'LHCB1', model_bpms, bmp_data,
    'reference/', ['scan1/', 'scan2/'],
    'LHCBEAM/IP5-XING-H-MURAD',
    '0030', 'x', 'normal_quadrupole',
    False, None
)

# Generate plots
fitted_results = rdt.analysis.fit_BPM(results)
for bpm in fitted_results['data'].keys():
    rdt.plotting.plot_BPM(bmp, fitted_results, '0030', 'x')
```

## Best Practices

### Measurement Planning

1. **Knob Range**: Choose range that covers expected physics requirements
2. **Step Size**: Balance between resolution and measurement time
3. **Reference**: Take reference at nominal conditions
4. **Repetition**: Consider multiple measurements for error estimation

### Data Quality

1. **Validation**: Always validate files before analysis
2. **Outliers**: Review outlier detection results carefully
3. **Consistency**: Check beam-to-beam consistency
4. **Documentation**: Record measurement conditions and settings

### Analysis Workflow

1. **Incremental**: Process data incrementally during measurements
2. **Backup**: Keep copies of raw data and analysis results
3. **Version Control**: Track analysis parameters and code versions
4. **Review**: Have results reviewed by domain experts

## Getting Help

### Documentation
- **API Reference**: See `docs/API.md` for detailed function documentation
- **Examples**: Check `examples/` directory for sample workflows
- **Source Code**: Read docstrings in source files for implementation details

### Support Channels
- **GitHub Issues**: Report bugs and request features
- **CERN Forums**: Discuss physics and measurement questions
- **Email**: Contact package maintainers for specific issues

### Contributing
- **Bug Reports**: Include minimal reproducible examples
- **Feature Requests**: Describe use cases and expected behavior  
- **Code Contributions**: Follow existing code style and add tests