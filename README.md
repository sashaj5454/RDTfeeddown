# RDTfeeddown

RDTfeeddown is a comprehensive Python package for analyzing Resonance Driving Terms (RDT) feed-down effects in particle accelerators. It provides both command-line and graphical user interfaces for processing OMC3 analysis results and studying RDT behavior during crossing angle scans.

## Features

- **RDT Analysis**: Extract and analyze RDT data from OMC3 result files
- **Feed-down Studies**: Investigate RDT feed-down effects during crossing angle variations
- **Data Visualization**: Generate comprehensive plots for BPM-by-BPM RDT analysis
- **Multiple Interfaces**: Both CLI and GUI applications available
- **Data Processing**: Outlier filtering, polynomial fitting, and statistical analysis
- **Multi-beam Support**: Handles both LHCB1 and LHCB2 data simultaneously

## Installation

### Prerequisites

This package requires access to CERN's `pytimber` package for logging database access. You'll need to install it from the CERN package repository:

```bash
# Install pytimber from CERN repository (CERN users only)
pip install --index-url https://acc-py-repo.cern.ch pytimber
```

For more information about `pytimber`, see: https://wikis.cern.ch/pages/viewpage.action?pageId=145493385

### Standard Installation

```bash
# Clone the repository
git clone https://github.com/sashaj5454/RDTfeeddown.git
cd RDTfeeddown

# Install the package
pip install -e .

# Or install with development dependencies
pip install -e ".[dev]"
```

### Dependencies

- `numpy` - Numerical computations
- `matplotlib` - Plotting and visualization
- `scipy` - Scientific computing and fitting
- `pytimber` - CERN logging database access (CERN-specific)
- `tfs` - TFS file format handling
- `pyqtgraph` - Interactive plotting (for GUI)
- `qtpy` - Qt wrapper for GUI components

## Usage

### Command Line Interface

The package provides a CLI tool for batch processing:

```bash
# Run RDT analysis
rdtfeeddown --help

# Example usage (replace with actual paths and parameters)
rdtfeeddown \
    --model1 /path/to/lhcb1/model \
    --model2 /path/to/lhcb2/model \
    --ref1 /path/to/lhcb1/reference \
    --ref2 /path/to/lhcb2/reference \
    --files-b1 /path/to/b1/file1,/path/to/b1/file2 \
    --files-b2 /path/to/b2/file1,/path/to/b2/file2 \
    --output /path/to/output \
    --knob "LHCBEAM/IP5-XING-H-MURAD" \
    --rdt "0030" \
    --plane "x"
```

### Graphical User Interface

Launch the GUI application:

```bash
python -m rdtfeeddown
```

The GUI provides:
- File selection dialogs for models, references, and data files
- Interactive parameter configuration
- Real-time validation of inputs
- Integrated plotting and visualization
- Progress tracking and error reporting

### Python API

You can also use the package programmatically:

```python
import rdtfeeddown as rdt

# Initialize logging database connection
ldb = rdt.utils.initialize_statetracker()

# Load model data
model_bpms, bpm_data = rdt.utils.getmodelBPMs('/path/to/model')

# Analyze RDT data
rdt_data = rdt.analysis.getrdt_omc3(
    ldb=ldb,
    modelbpmlist=model_bpms,
    bpmdata=bpm_data,
    ref='/path/to/reference',
    flist=['/path/to/file1', '/path/to/file2'],
    knob='LHCBEAM/IP5-XING-H-MURAD',
    outputpath='/path/to/output',
    timeoffset=0,
    rdt='0030',
    rdt_plane='x',
    rdtfolder='normal_quadrupole'
)

# Fit the data
fitted_data = rdt.analysis.fit_BPM(rdt_data)

# Generate plots
for bpm in fitted_data.keys():
    rdt.plotting.plot_BPM(
        bpm, fitted_data, '0030', 'x', 
        f'/path/to/output/f0030_x_{bpm}.png'
    )
```

## RDT Types and Analysis

The package supports various RDT orders:
- **Normal/Skew**: Determined by (l+m) parity
- **Orders**: Dipole, Quadrupole, Sextupole, Octupole, etc.
- **Common RDTs**: f0030 (normal quadrupole), f1002 (skew quadrupole), etc.

### Analysis Features

- **Outlier Detection**: Z-score based filtering of anomalous measurements
- **Polynomial Fitting**: Fit RDT evolution vs. knob settings
- **Statistical Analysis**: Error bars and confidence intervals  
- **Multi-beam Comparison**: Simultaneous LHCB1/LHCB2 analysis

## File Structure

The package expects OMC3 analysis result directories with:
- `command.run` - Contains analysis commands and file lists
- RDT files in subdirectories (e.g., `normal_quadrupole/`)
- TFS format files with BPM-specific RDT measurements

## Development

### Running Tests

```bash
# Install test dependencies
pip install pytest

# Run test suite
pytest tests/ -v
```

### Code Style

The project uses:
- `black` for code formatting
- `flake8` for linting  
- `ruff` for additional checks

```bash
# Format code
black src/ tests/

# Run linting
flake8 src/ tests/
ruff check src/ tests/
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes with appropriate tests
4. Ensure code passes linting and tests
5. Submit a pull request

## License

This project is licensed under the terms specified in the LICENSE file.

## Support

For questions about RDT analysis or particle accelerator physics concepts, consult the relevant CERN documentation or contact the package maintainers.

For technical issues with the software, please open an issue on the GitHub repository.
