# Changelog

All notable changes to the RDTfeeddown project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Comprehensive README with project description, installation guide, and usage examples
- Detailed API documentation in `docs/API.md` covering all core modules
- User guide in `docs/UserGuide.md` with step-by-step tutorials for CLI and GUI
- Developer documentation in `docs/DeveloperGuide.md` for contributors
- Enhanced docstrings for key analysis functions with NumPy-style documentation
- Example scripts demonstrating basic and batch processing workflows
- `.gitignore` file to exclude build artifacts and temporary files

### Enhanced
- Function documentation for `getrdt_omc3`, `filter_outliers`, `plot_BPM`, and utility functions
- Type hints and parameter descriptions for better API clarity
- Error handling examples and troubleshooting guides

### Documentation Structure
```
docs/
├── API.md              # Detailed API reference
├── UserGuide.md        # End-user documentation
└── DeveloperGuide.md   # Developer contribution guide

examples/
├── README.md           # Examples overview
├── basic_analysis.py   # Single RDT analysis workflow
└── batch_processing.py # Multi-RDT batch processing
```

## [0.1.0] - Initial Release

### Added
- Core RDT analysis functionality
- Command-line interface
- Graphical user interface
- Plotting and visualization modules
- OMC3 integration
- CERN logging database interface
- Basic test suite