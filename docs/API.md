# API Documentation

This document provides detailed information about the RDTfeeddown package APIs and modules.

## Core Modules

### `rdtfeeddown.analysis`

The analysis module contains the core functionality for processing RDT data from OMC3 results.

#### Key Functions

**`getrdt_omc3(ldb, beam, modelbpmlist, bpmdata, ref, flist, knob, rdt, rdt_plane, rdtfolder, sim, propfile, threshold=3, log_func=None)`**

Main analysis function that extracts RDT data from OMC3 analysis results.

- **Purpose**: Process multiple measurement directories to extract RDT evolution
- **Input**: Model data, reference measurement, scan measurements, machine knob info
- **Output**: Structured data dictionary with RDT values vs knob settings
- **Usage**: Primary function for feed-down analysis

**`filter_outliers(data, threshold=3)`**

Removes statistical outliers from RDT measurements using Z-score filtering.

- **Input**: Raw measurement data with amplitude, real, imaginary components
- **Output**: Filtered data with outliers removed
- **Default**: 3-sigma threshold for outlier detection

**`fit_BPM(rdtdata)`**

Performs polynomial fitting of RDT evolution for each BPM.

- **Input**: RDT data dictionary from `getrdt_omc3`
- **Output**: Data with polynomial fit parameters added
- **Method**: Second-order polynomial fitting with error estimation

#### Data Structures

**RDT Data Dictionary Structure**:
```python
{
    'metadata': {
        'beam': 'LHCB1',
        'knob': 'LHCBEAM/IP5-XING-H-MURAD',
        'rdt': '0030',
        'plane': 'x'
    },
    'data': {
        'BPM_NAME': {
            's': position_in_ring,
            'ref': [knob_val, amp, real, imag, error],
            'data': [[knob_val, amp, real, imag, error], ...],
            'diffdata': [[knob_val, delta_real, delta_imag, error], ...],
            'fitdata': [real_fit_params, imag_fit_params]
        }
    }
}
```

### `rdtfeeddown.plotting`

Visualization module for RDT analysis results.

#### Key Functions

**`plot_BPM(BPM, fulldata, rdt, rdt_plane, ax1=None, ax2=None, log_func=None)`**

Generate individual BPM plots showing RDT evolution vs knob setting.

- **Features**: Real/imaginary parts, polynomial fits, error bars
- **Output**: Two subplots (real and imaginary components)
- **Customization**: Automatic color coding by beam

**`plot_RDT(fulldata, rdt, rdt_plane, ax=None, log_func=None)`**

Create ring-wide RDT amplitude plot showing all BPMs.

- **Layout**: S-coordinate vs RDT amplitude
- **Features**: IP markers, beam-specific styling
- **Use case**: Overview of RDT distribution around the ring

**`plot_RDTshifts(b1data, b2data, rdt, rdt_plane, ax=None, log_func=None)`**

Compare RDT shifts between two beams.

- **Input**: Data from both LHCB1 and LHCB2
- **Output**: Side-by-side comparison plot
- **Features**: Differential analysis, relative scaling

#### Styling and Customization

- **Colors**: Automatic beam-based color coding (B1=blue, B2=red)
- **Markers**: IP positions marked on ring plots
- **Error bars**: Included when measurement errors available
- **Fonts**: Consistent mathematical notation for RDT symbols

### `rdtfeeddown.utils`

Utility functions for data processing and machine interface.

#### Key Functions

**`initialize_statetracker()`**

Creates connection to CERN logging database.

- **Returns**: pytimber.LoggingDB object
- **Requirement**: CERN network access
- **Purpose**: Retrieve historical machine knob settings

**`get_analysis_knobsetting(ldb, requested_knob, analyfile, log_func=None)`**

Extract knob settings from OMC3 analysis timestamps.

- **Method**: Parse command.run files, query logging database
- **Validation**: Check consistency across multiple measurements
- **Error handling**: Graceful failure with logging

**`rdt_to_order_and_type(rdt)`**

Convert RDT identifier to human-readable description.

- **Input**: '0030', '1002', etc.
- **Output**: 'normal_quadrupole', 'skew_quadrupole', etc.
- **Use**: File organization, plot labeling

#### Machine Integration

**Knob Names**: Standard CERN accelerator complex knob naming
- Format: `'LHCBEAM/IP5-XING-H-MURAD'` (crossing angle)
- Support: Any logged machine parameter

**Timestamps**: Automatic conversion between timezones
- Source: Kick file naming convention
- Target: Local time for database queries

### `rdtfeeddown.gui`

Graphical user interface for interactive analysis.

#### Main Components

**File Selection**:
- Model file browsers (LHCB1/B2)
- Reference measurement selection
- Multi-file measurement selection
- Output directory selection

**Parameter Configuration**:
- Knob name specification
- RDT type selection (dropdown)
- Plane selection (x/y)
- Analysis options

**Validation**:
- Real-time input validation
- File structure checking
- Beam consistency verification

**Visualization**:
- Integrated plotting tabs
- Interactive plot controls
- Export functionality

#### Usage Patterns

1. **File Setup**: Select model, reference, and measurement files
2. **Parameter Configuration**: Choose RDT type, plane, knob name
3. **Validation**: Check inputs for consistency
4. **Analysis**: Run processing with progress tracking
5. **Visualization**: Review results in integrated plots
6. **Export**: Save plots and analysis results

### `rdtfeeddown.cli`

Command-line interface for batch processing.

#### Command Structure

```bash
rdtfeeddown [OPTIONS]
```

**Required Options**:
- `--model1`, `--model2`: Model files for both beams
- `--ref1`, `--ref2`: Reference measurements
- `--files-b1`, `--files-b2`: Comma-separated file lists
- `--output`: Output directory
- `--knob`: Machine knob name
- `--rdt`: RDT identifier
- `--plane`: Measurement plane

**Optional Parameters**:
- `--timeoffset`: Time offset for database queries
- `--threshold`: Outlier detection threshold
- `--rdtfolder`: RDT subfolder name

#### Batch Processing

The CLI is designed for:
- Automated analysis pipelines
- Large dataset processing
- Reproducible analysis workflows
- Integration with job submission systems

## Error Handling

### Common Issues

**File Not Found**: Missing OMC3 result files or incorrect paths
- **Solution**: Verify file paths and directory structure
- **Prevention**: Use GUI file browsers for path validation

**Beam Mismatch**: Model and data from different beams
- **Detection**: Automatic beam number checking
- **Resolution**: Ensure consistent beam selection

**Database Connection**: pytimber connection failures
- **Cause**: Network issues or missing CERN access
- **Workaround**: Use simulation mode with property files

**Outlier Detection**: Excessive data filtering
- **Adjustment**: Modify threshold parameter
- **Investigation**: Check measurement quality

### Logging and Debugging

**Log Functions**: Optional logging callback in most functions
- **Purpose**: Custom error handling and progress tracking
- **Usage**: `log_func=lambda msg: print(f"LOG: {msg}")`

**Error Messages**: Descriptive error reporting
- **Context**: File paths, parameter values, processing stage
- **Recovery**: Suggestions for resolving issues

## Performance Considerations

### Memory Usage

- **Large Datasets**: Process measurements in chunks if memory limited
- **Plot Generation**: Consider reducing plot resolution for large datasets
- **Data Storage**: Use HDF5 or similar for very large analysis results

### Processing Speed

- **Parallel Processing**: Consider parallel BPM processing for large rings
- **Database Queries**: Batch queries when possible to reduce network overhead
- **File I/O**: Use local storage for intensive processing

## Extension Points

### Custom Analysis

**New RDT Types**: Add entries to order mapping in `utils.py`
**Custom Fitting**: Extend polynomial fitting with other functions
**Additional Plots**: Create new plot types following existing patterns

### Machine Integration

**New Accelerators**: Adapt knob naming and database interfaces
**Different File Formats**: Extend file reading functions
**Custom Timestamps**: Modify timestamp parsing for different naming conventions

## Testing

### Unit Tests

Located in `tests/` directory:
- `test_analysis.py`: Core analysis function testing
- Coverage includes data processing, fitting, outlier detection

### Integration Tests

- Full analysis workflows
- GUI component testing
- File format compatibility

### Test Data

- Synthetic RDT datasets for validation
- Known good analysis results for regression testing
- Edge cases and error conditions