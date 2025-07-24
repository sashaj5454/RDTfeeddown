# Developer Documentation

This document provides information for developers who want to contribute to or extend the RDTfeeddown package.

## Development Setup

### Prerequisites

- Python 3.8+
- Git
- Access to CERN network (for pytimber dependency)
- Development tools: pytest, black, flake8, ruff

### Environment Setup

```bash
# Clone the repository
git clone https://github.com/sashaj5454/RDTfeeddown.git
cd RDTfeeddown

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install in development mode with dev dependencies
pip install -e ".[dev]"

# Install pytimber (CERN users only)
pip install --index-url https://acc-py-repo.cern.ch pytimber
```

### Code Style

The project follows PEP 8 style guidelines with these tools:

```bash
# Format code
black src/ tests/

# Check formatting
black --check src/ tests/

# Lint code
flake8 src/ tests/
ruff check src/ tests/

# Fix automatic issues
ruff check --fix src/ tests/
```

### Pre-commit Hooks

```bash
# Install pre-commit
pip install pre-commit

# Set up hooks
pre-commit install

# Run manually
pre-commit run --all-files
```

## Architecture Overview

### Package Structure

```
src/rdtfeeddown/
├── __init__.py          # Package initialization
├── __main__.py          # Entry point for python -m rdtfeeddown
├── cli.py               # Command-line interface
├── gui.py               # Graphical user interface
├── analysis.py          # Core analysis functions
├── plotting.py          # Visualization functions
├── utils.py             # Utility functions
├── data_handler.py      # Data loading and processing
├── validation_utils.py  # Input validation
├── file_dialog_helpers.py  # GUI file dialogs
├── analysis_runner.py   # Analysis execution
├── style.py             # GUI styling
├── customtitlebar.py    # Custom GUI components
└── resources_rc.py      # Qt resources
```

### Design Principles

1. **Separation of Concerns**: Clear boundaries between analysis, visualization, and UI
2. **Functional Programming**: Prefer pure functions where possible
3. **Error Handling**: Graceful degradation with informative messages
4. **Testability**: Functions designed for easy unit testing
5. **Extensibility**: Plugin-like architecture for new RDT types

### Data Flow

```
Input Files → Validation → Data Loading → Analysis → Fitting → Visualization → Export
     ↓              ↓           ↓           ↓         ↓           ↓           ↓
   File I/O    Validation   Data Handler  Analysis  Analysis   Plotting    File I/O
   Utils       Utils        Module        Module    Module     Module      Utils
```

## Core Modules

### analysis.py

**Purpose**: Core RDT analysis algorithms

**Key Components**:
- `getrdt_omc3()`: Main analysis pipeline
- `filter_outliers()`: Statistical outlier detection
- `fit_BPM()`: Polynomial fitting
- Data structure definitions

**Design Patterns**:
- Pipeline pattern for data processing
- Strategy pattern for different fit types
- Factory pattern for RDT type handling

**Extension Points**:
- Add new RDT types by extending type mappings
- Implement alternative fitting algorithms
- Add custom outlier detection methods

### plotting.py

**Purpose**: Data visualization and plot generation

**Key Components**:
- `plot_BPM()`: Individual BPM analysis plots
- `plot_RDT()`: Ring-wide RDT distribution
- `plot_RDTshifts()`: Beam comparison plots

**Design Patterns**:
- Template method for consistent plot styling
- Observer pattern for real-time plot updates
- Decorator pattern for plot customizations

**Extension Points**:
- Add new plot types by following existing patterns
- Implement custom styling themes
- Add interactive plot features

### gui.py

**Purpose**: Graphical user interface implementation

**Architecture**: 
- Model-View-Controller pattern
- Qt widgets with pyqtgraph integration
- Event-driven architecture

**Key Components**:
- Main window with tabbed interface
- File selection dialogs
- Parameter configuration panels
- Integrated plotting viewers

**Extension Points**:
- Add new tabs for additional functionality  
- Implement custom widgets
- Add plugin system for analysis modules

### utils.py

**Purpose**: Shared utility functions and machine interfaces

**Key Components**:
- CERN logging database interface
- Timestamp parsing and conversion
- File system utilities
- RDT type classification

**Extension Points**:
- Add support for new accelerator complexes
- Implement alternative timestamp formats
- Add new knob types and naming conventions

## Testing Strategy

### Unit Tests

Located in `tests/test_*.py`:

```python
# Example test structure
class TestAnalysis(unittest.TestCase):
    def setUp(self):
        self.test_data = create_test_data()
    
    def test_filter_outliers(self):
        # Test outlier detection
        pass
    
    def test_polynomial_fitting(self):
        # Test fitting algorithms
        pass
```

**Coverage Goals**:
- Analysis functions: >90%
- Utility functions: >85%
- GUI components: >70%

### Integration Tests

```python
def test_full_analysis_workflow():
    """Test complete analysis from files to plots"""
    # Use synthetic test data
    # Verify output consistency
    # Check plot generation
```

### Test Data Generation

```python
def create_synthetic_rdt_data(n_bpms=100, n_points=10, noise_level=0.1):
    """Generate realistic test data"""
    # Create model BPM positions
    # Generate RDT measurements with known patterns
    # Add realistic noise and outliers
    return synthetic_data
```

### Performance Tests

```bash
# Benchmark analysis performance
python -m pytest tests/test_performance.py --benchmark

# Memory profiling
python -m memory_profiler analysis_script.py

# Profile with cProfile
python -m cProfile -o profile.stats analysis_script.py
```

## Adding New Features

### New RDT Types

1. **Update Type Mapping** in `utils.py`:
```python
def rdt_to_order_and_type(rdt: str):
    # Add new RDT classifications
    orders = {
        # ... existing entries ...
        9: "custom_multipole"  # Add new order
    }
```

2. **Add File Handling** in `analysis.py`:
```python
def readrdtdatafile(cfile, rdt, rdt_plane, rdtfolder, ...):
    # Handle new RDT file formats
    # Add custom parsing logic if needed
```

3. **Update GUI** in `gui.py`:
```python
def setup_rdt_dropdown(self):
    # Add new RDT options to dropdown
    rdt_options = ["0030", "1002", "new_rdt"]  # Add here
```

### New Plot Types

1. **Create Plot Function** in `plotting.py`:
```python
def plot_new_type(data, rdt, plane, ax=None, **kwargs):
    """
    Create new visualization type.
    
    Follow existing patterns for:
    - Error handling
    - Styling consistency  
    - Parameter validation
    """
    # Implementation here
```

2. **Add to GUI** in `gui.py`:
```python
def add_plot_tab(self):
    # Create new tab for custom plots
    # Wire up to analysis results
```

### New Analysis Methods

1. **Create Analysis Function**:
```python
def new_analysis_method(data, parameters):
    """
    Implement new analysis algorithm.
    
    Args:
        data: Structured RDT data
        parameters: Analysis configuration
        
    Returns:
        dict: Analysis results following standard format
    """
    # Implementation
```

2. **Add to Pipeline**:
```python
def run_analysis(..., method="standard"):
    if method == "new_method":
        return new_analysis_method(data, params)
    else:
        return standard_analysis(data, params)
```

## GUI Development

### Qt Integration

The GUI uses QtPy for Qt wrapper abstraction:

```python
from qtpy.QtWidgets import QWidget, QVBoxLayout
from qtpy.QtCore import Qt, QTimer
import pyqtgraph as pg

class CustomWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.setup_ui()
        
    def setup_ui(self):
        layout = QVBoxLayout(self)
        # Add widgets
```

### Custom Styling

Styling is managed in `style.py`:

```python
# Define style constants
DARK_BACKGROUND_COLOR = "#2b2b2b"

# Create stylesheets
def create_custom_stylesheet():
    return """
    QWidget {
        background-color: {bg_color};
        color: white;
    }
    """.format(bg_color=DARK_BACKGROUND_COLOR)
```

### Event Handling

```python
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setup_connections()
        
    def setup_connections(self):
        # Connect signals to slots
        self.run_button.clicked.connect(self.on_run_analysis)
        
    def on_run_analysis(self):
        # Handle user actions
        try:
            # Run analysis
            pass
        except Exception as e:
            self.show_error_message(str(e))
```

## Performance Optimization

### Memory Management

```python
# Use generators for large datasets
def process_large_dataset(files):
    for file in files:
        data = load_file(file)
        yield process_data(data)
        del data  # Explicit cleanup

# Implement data streaming
class DataStreamer:
    def __init__(self, chunk_size=1000):
        self.chunk_size = chunk_size
        
    def stream_data(self, source):
        # Process data in chunks
        pass
```

### Caching

```python
from functools import lru_cache

@lru_cache(maxsize=128)
def expensive_computation(params):
    # Cache expensive operations
    pass

# File-based caching
import joblib

def cached_analysis(data_hash, analysis_func, *args):
    cache_file = f"cache/{data_hash}.pkl"
    if os.path.exists(cache_file):
        return joblib.load(cache_file)
    else:
        result = analysis_func(*args)
        joblib.dump(result, cache_file)
        return result
```

### Parallel Processing

```python
from concurrent.futures import ProcessPoolExecutor
import multiprocessing as mp

def parallel_bpm_analysis(bpm_data):
    with ProcessPoolExecutor(max_workers=mp.cpu_count()) as executor:
        futures = {
            executor.submit(analyze_bpm, bpm, data): bpm 
            for bpm, data in bpm_data.items()
        }
        results = {}
        for future in concurrent.futures.as_completed(futures):
            bmp = futures[future]
            try:
                results[bmp] = future.result()
            except Exception as exc:
                print(f'BPM {bpm} generated exception: {exc}')
        return results
```

## Release Process

### Version Management

Version is managed in `src/rdtfeeddown/__init__.py`:

```python
__version__ = "0.1.0"
```

### Release Checklist

1. **Update Version Number**:
   - `src/rdtfeeddown/__init__.py`
   - `pyproject.toml`
   - Release notes

2. **Run Full Test Suite**:
```bash
pytest tests/ --cov=rdtfeeddown --cov-report=html
```

3. **Check Code Quality**:
```bash
black --check src/ tests/
flake8 src/ tests/
ruff check src/ tests/
```

4. **Update Documentation**:
   - README.md
   - API documentation
   - User guide

5. **Create Release**:
```bash
git tag -a v0.1.0 -m "Release version 0.1.0"
git push origin v0.1.0
```

### Continuous Integration

GitHub Actions workflow (`.github/workflows/ci.yml`):

```yaml
name: CI
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: [3.8, 3.9, "3.10", 3.11]
    steps:
    - uses: actions/checkout@v3
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: ${{ matrix.python-version }}
    - name: Install dependencies
      run: |
        pip install -e ".[dev]"
    - name: Run tests
      run: |
        pytest tests/
    - name: Check code style
      run: |
        black --check src/ tests/
        flake8 src/ tests/
```

## Debugging

### Common Issues

**Import Errors**:
```python
# Use try/except for optional dependencies
try:
    import pytimber
    HAS_PYTIMBER = True
except ImportError:
    HAS_PYTIMBER = False
    
def function_requiring_pytimber():
    if not HAS_PYTIMBER:
        raise ImportError("pytimber required for this function")
```

**GUI Debugging**:
```python
# Enable Qt debugging
import os
os.environ['QT_DEBUG_PLUGINS'] = '1'

# Add debug prints
import logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def debug_function():
    logger.debug("Function called with args: %s", args)
```

**Analysis Debugging**:
```python
# Add intermediate result validation
def validate_intermediate_results(data, stage):
    """Validate data at each processing stage"""
    assert isinstance(data, dict), f"Expected dict at {stage}"
    assert len(data) > 0, f"Empty data at {stage}"
    # Add more checks as needed
```

### Profiling

```python
# Function-level profiling
import cProfile
import pstats

def profile_function(func, *args, **kwargs):
    profiler = cProfile.Profile()
    profiler.enable()
    result = func(*args, **kwargs)
    profiler.disable()
    
    stats = pstats.Stats(profiler)
    stats.sort_stats('cumulative')
    stats.print_stats()
    return result

# Line-level profiling with line_profiler
@profile  # Add this decorator
def function_to_profile():
    # Function code here
    pass

# Run with: kernprof -l -v script.py
```

## Contributing Guidelines

### Code Review Process

1. **Fork Repository**: Create personal fork for development
2. **Feature Branch**: Create branch for each feature/fix
3. **Write Tests**: Add tests for new functionality
4. **Documentation**: Update relevant documentation
5. **Pull Request**: Submit PR with clear description
6. **Code Review**: Address reviewer feedback
7. **Merge**: Maintainers merge approved PRs

### Commit Message Format

```
type(scope): short description

Longer description explaining the change and why it was made.

Fixes #123
```

Types: feat, fix, docs, style, refactor, test, chore

### Documentation Standards

- **Docstrings**: Use NumPy style docstrings
- **Type Hints**: Add type annotations for public APIs
- **Comments**: Explain complex algorithms and business logic
- **Examples**: Include usage examples in docstrings

### Testing Requirements

- **Unit Tests**: Required for all new functions
- **Integration Tests**: Required for new workflows
- **Performance Tests**: Required for optimization changes
- **Coverage**: Maintain >80% overall coverage

## Advanced Topics

### Plugin Architecture

```python
# Plugin interface
class AnalysisPlugin:
    def __init__(self):
        self.name = "base_plugin"
        
    def analyze(self, data):
        raise NotImplementedError
        
    def plot(self, results):
        raise NotImplementedError

# Plugin registry
class PluginRegistry:
    def __init__(self):
        self.plugins = {}
        
    def register(self, plugin):
        self.plugins[plugin.name] = plugin
        
    def get_plugin(self, name):
        return self.plugins.get(name)
```

### Custom File Formats

```python
class FileFormatHandler:
    def __init__(self, format_name):
        self.format_name = format_name
        
    def can_handle(self, filepath):
        # Return True if this handler can process the file
        pass
        
    def read_file(self, filepath):
        # Read and parse file content
        pass
        
    def write_file(self, data, filepath):
        # Write data to file
        pass
```

### Machine Integration

```python
class MachineInterface:
    def __init__(self, machine_name):
        self.machine_name = machine_name
        
    def get_knob_setting(self, knob_name, timestamp):
        # Retrieve knob setting from machine database
        pass
        
    def get_bpm_positions(self):
        # Get BPM positions from machine model
        pass
```

This developer documentation provides the foundation for extending and maintaining the RDTfeeddown package. For specific implementation questions, refer to the source code and existing patterns.