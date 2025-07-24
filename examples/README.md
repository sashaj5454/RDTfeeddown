# Examples

This directory contains example scripts demonstrating various usage patterns for the RDTfeeddown package.

## Available Examples

### `basic_analysis.py`
**Purpose**: Demonstrates the fundamental workflow for RDT analysis
**Features**:
- Single RDT type and plane analysis
- Complete workflow from data loading to plot generation
- Error handling and progress reporting
- Summary statistics calculation

**Usage**:
```bash
python basic_analysis.py
```

**Prerequisites**:
- Update file paths in the configuration section
- Ensure CERN network access for pytimber
- Have OMC3 analysis results available

### `batch_processing.py`
**Purpose**: Shows how to process multiple RDT types and planes in batch
**Features**:
- Multiple RDT types and planes in single run
- Automated logging and error handling
- Summary report generation
- Progress tracking across analyses

**Usage**:
```bash
python batch_processing.py
```

**Output**:
- Individual directories for each RDT/plane combination
- Comprehensive logging
- Summary report with statistics

## Configuration

Both examples require updating the configuration dictionaries with your specific file paths:

### Required Paths
```python
config = {
    'model_b1': '/path/to/lhcb1_model.tfs',        # LHCB1 model file
    'model_b2': '/path/to/lhcb2_model.tfs',        # LHCB2 model file
    'ref_b1': '/path/to/lhcb1_reference/',         # LHCB1 reference measurement
    'ref_b2': '/path/to/lhcb2_reference/',         # LHCB2 reference measurement
    'files_b1': [                                  # LHCB1 scan measurements
        '/path/to/lhcb1_scan_001/',
        '/path/to/lhcb1_scan_002/',
        # ... more files
    ],
    'files_b2': [                                  # LHCB2 scan measurements
        '/path/to/lhcb2_scan_001/',
        '/path/to/lhcb2_scan_002/',
        # ... more files
    ],
    'output_dir': '/path/to/output/',              # Output directory
    'knob': 'LHCBEAM/IP5-XING-H-MURAD',          # Machine knob name
}
```

### File Structure Requirements

Your data should be organized as follows:

```
measurement_directory/
├── command.run                    # OMC3 command file with timestamps
└── rdt/                          # RDT analysis results
    ├── normal_quadrupole/        # For f0030, f1200, etc.
    │   ├── f0030_x.tfs
    │   ├── f0030_y.tfs
    │   └── ...
    ├── skew_quadrupole/          # For f1002, f0021, etc.
    │   ├── f1002_x.tfs
    │   ├── f1002_y.tfs
    │   └── ...
    └── ...
```

## Common Patterns

### Error Handling
Both examples demonstrate proper error handling:

```python
try:
    # Analysis code
    result = rdt.analysis.getrdt_omc3(...)
except Exception as e:
    logger.error(f"Analysis failed: {e}")
    # Handle gracefully
```

### Logging Integration
Use logging functions for better error tracking:

```python
def log_message(msg):
    logger.info(msg)

# Pass to analysis functions
result = rdt.analysis.getrdt_omc3(..., log_func=log_message)
```

### Progress Tracking
Monitor analysis progress:

```python
total_analyses = len(rdt_types) * len(planes)
completed = 0

for rdt_type, plane in itertools.product(rdt_types, planes):
    # Run analysis
    completed += 1
    print(f"Progress: {completed}/{total_analyses}")
```

## Creating Custom Examples

### Template Structure
```python
#!/usr/bin/env python3
"""
Custom Analysis Example

Description of what this example demonstrates.
"""

import rdtfeeddown as rdt

def main():
    # Configuration
    config = {...}
    
    # Initialize
    ldb = rdt.utils.initialize_statetracker()
    
    # Load models
    model_data = rdt.utils.getmodelBPMs(config['model'])
    
    # Run analysis
    results = rdt.analysis.getrdt_omc3(...)
    
    # Process results
    fitted_results = rdt.analysis.fit_BPM(results)
    
    # Generate outputs
    rdt.plotting.plot_BPM(...)
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
```

### Best Practices

1. **Configuration**: Keep all file paths and parameters in a config dictionary
2. **Error Handling**: Wrap analysis steps in try/except blocks
3. **Logging**: Use logging for progress and error reporting
4. **Output Organization**: Create organized output directories
5. **Documentation**: Include clear docstrings and comments

### Integration with Job Systems

For HTC/batch job integration:

```python
import argparse

def parse_arguments():
    parser = argparse.ArgumentParser(description='RDT Analysis Job')
    parser.add_argument('--config', required=True, help='Configuration file')
    parser.add_argument('--rdt', required=True, help='RDT type')
    parser.add_argument('--plane', required=True, help='Measurement plane')
    return parser.parse_args()

def main():
    args = parse_arguments()
    
    # Load configuration from file
    import json
    with open(args.config) as f:
        config = json.load(f)
    
    # Run analysis for specific RDT/plane
    run_single_analysis(config, args.rdt, args.plane)
```

Submit jobs with:
```bash
# Job submission script
for rdt in "0030" "1002" "0012"; do
    for plane in "x" "y"; do
        sbatch --export=RDT=$rdt,PLANE=$plane analysis_job.sh
    done
done
```

## Testing Examples

To test examples with synthetic data:

```python
# Create test data
def create_test_environment():
    import tempfile
    import os
    
    test_dir = tempfile.mkdtemp()
    
    # Create mock file structure
    os.makedirs(f"{test_dir}/models")
    os.makedirs(f"{test_dir}/reference/rdt/normal_quadrupole")
    os.makedirs(f"{test_dir}/scan1/rdt/normal_quadrupole")
    
    # Create mock files (empty for testing structure)
    open(f"{test_dir}/models/lhcb1.tfs", 'w').close()
    open(f"{test_dir}/reference/command.run", 'w').close()
    open(f"{test_dir}/reference/rdt/normal_quadrupole/f0030_x.tfs", 'w').close()
    
    return test_dir

# Update config to use test environment
test_env = create_test_environment()
config['model_b1'] = f"{test_env}/models/lhcb1.tfs"
# ... update other paths
```

## Performance Considerations

For large datasets:

```python
# Process in chunks to manage memory
def process_in_chunks(data, chunk_size=100):
    for i in range(0, len(data), chunk_size):
        chunk = data[i:i+chunk_size]
        yield process_chunk(chunk)

# Parallel processing for independent analyses
from concurrent.futures import ProcessPoolExecutor

def parallel_analysis(configs):
    with ProcessPoolExecutor() as executor:
        futures = [executor.submit(run_analysis, cfg) for cfg in configs]
        results = [f.result() for f in futures]
    return results
```

These examples provide a solid foundation for using RDTfeeddown in various scenarios, from interactive analysis to automated processing pipelines.