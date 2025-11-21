# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a machine learning project template. It uses `uv` for Python package management and includes:
- Core ML utilities in `src/my_ml/`
- Streamlit demo application in `demo/`
- Configuration-driven architecture with YAML configs in `configs/`
- Jupyter notebook templates in `notebooks/`
- Data pipeline structure with raw/intermediate/processed data directories

## Environment Setup

### Initial Development Setup
```bash
# Development environment (includes pre-commit hooks, black, isort)
make init-dev
# OR
bash install.sh --dev

# Production environment
make init
# OR
bash install.sh

# View all available make commands
make help
```

The project uses:
- Python 3.12.9 (pinned version)
- uv for dependency management
- Virtual environment in `.venv/`
- Always activate the virtual environment: `source .venv/bin/activate`

### Environment Variables
Before running the demo application, create environment files from templates:
```bash
cp .env.example .env
cp .env.dev.example .env.dev
```

### Demo Application
```bash
cd demo
streamlit run main.py
```

The demo uses a multi-page Streamlit app with login/logout functionality and navigation to multiple application sections.

**Default login credentials** (defined in [demo/page_utils.py](demo/page_utils.py)):
- Username: `admin`
- Password: `admin`

These are hardcoded for development and should be replaced with environment variables before deployment.

## Code Quality & Formatting

### Pre-commit Hooks
Pre-commit is configured with:
- Ruff (formatting and linting, line-length: 105)
- trailing-whitespace, end-of-file-fixer, mixed-line-ending
- check-added-large-files (max 30MB)
- requirements-txt-fixer
- add-trailing-comma

Pre-commit hooks run automatically on commit when using `--dev` setup.

### Manual Formatting
```bash
make format  # Runs ruff format
```

**Important**: Always maintain line-length of 105 characters for Ruff formatting.

## Architecture

### Directory Structure
```
src/my_ml/            # Main package
  utils/              # Utility modules
    config_loader.py  # YAML config loading
    path.py           # Path constants for project structure
    settings.py       # Random seed and reproducibility utilities
configs/              # YAML configuration files
  data.yaml           # Data paths configuration (commented examples)
  feature.yaml        # Feature engineering configs
  model.yaml          # Model configurations
  train.yaml          # Training pipeline configs
  configs.py          # Config loading for demo (uses AWS Secrets Manager)
demo/                 # Streamlit demo application
  main.py             # Main entry point with navigation
  page_utils.py       # Login/logout utilities
  home/, app1/, app2/ # Application pages
data/                 # Data directory (git-ignored)
  raw/                # Raw data
  intermediate/       # Intermediate processing results
  processed/          # Final processed datasets
notebooks/            # Jupyter notebooks
  template.ipynb      # Notebook template
```

### Configuration System

The project uses a centralized path management system ([src/my_ml/utils/path.py](src/my_ml/utils/path.py)) that defines all project paths relative to the repository root:
- `REPO_ROOT`: Repository root (3 levels up from utils: `Path(__file__).parents[3]`)
- Base paths: `CONFIG_PATH`, `DATA_PATH`, `LOG_PATH`, `NOTEBOOK_PATH`, `SOURCE_PATH`, `PACKAGE_PATH`
- Data subdirectories: `RAW_DATA_PATH`, `INTERMEDIATE_DATA_PATH`, `PROCESSED_DATA_PATH`
- Config file paths: `DATA_CONFIG_PATH`, `FEATURE_CONFIG_PATH`, `MODEL_CONFIG_PATH`

**Important**: All paths are computed relative to REPO_ROOT, ensuring the code works regardless of where it's imported from.

Use `load_config(path)` from `my_ml.utils.config_loader` to load YAML configurations:
```python
from my_ml.utils.config_loader import load_config
from my_ml.utils.path import DATA_CONFIG_PATH

config = load_config(DATA_CONFIG_PATH)
```

### Demo Application Architecture

The demo application ([demo/main.py](demo/main.py)) uses Streamlit's multi-page navigation with:
- Session-based login state management (`st.session_state["login"]`)
- Page routing based on login status (shows login page when not authenticated)
- AWS Secrets Manager integration for configuration ([configs/configs.py](configs/configs.py))
- Uses `.env` and `.env.dev` files for environment-specific settings
- Profile-based configuration: checks `APP_PROFILE` environment variable to determine which .env file to load

**Security Note**: The demo config loader uses `eval()` on AWS Secrets Manager responses ([configs/configs.py:39](configs/configs.py#L39)), which should be reviewed for security considerations. Consider using `json.loads()` instead.

### Notebook Template Structure

The Jupyter notebook template ([notebooks/template.ipynb](notebooks/template.ipynb)) includes:
- Author name and date fields (initial issue and last update)
- Revision history section
- Automatic `.env` loading with `load_dotenv()`

Use this template as the starting point for all new notebooks.

## Dependencies

This project includes extensive ML/AI dependencies:
- ML frameworks: torch, lightning, scikit-learn, xgboost, statsmodels
- LLM/GenAI: langchain, langgraph, litellm, langchain-aws, traceloop-sdk
- Data processing: pandas, polars, numpy, pyarrow
- Cloud services: boto3, azure-cognitiveservices-speech, google-cloud-aiplatform
- APIs: fastapi, streamlit
- Database: pymongo, motor, sqlalchemy, pg8000, redis, opensearch-py, pyvespa
- Observability: opentelemetry instrumentation, prometheus-client
- Optimization: optuna
- Visualization: matplotlib, seaborn, shap, streamlit-aggrid
- Audio/Video: amazon-transcribe, azure-cognitiveservices-speech

When adding new dependencies:
```bash
uv add <package>  # Adds to pyproject.toml and syncs
```

## Development Workflow

1. Activate the virtual environment: `source .venv/bin/activate`
2. Pre-commit hooks run automatically on commit (if using `--dev` setup)
3. Configuration changes go in YAML files under `configs/`
4. New utilities should be added to `src/my_ml/utils/`
5. Data files are git-ignored; only code and configs are versioned
6. Use the notebook template for new Jupyter notebooks
7. Import utilities using `from my_ml.utils import ...` after environment activation

### Reproducibility

Use `set_random_seed()` from [src/my_ml/utils/settings.py](src/my_ml/utils/settings.py) to ensure reproducible results:
```python
from my_ml.utils.settings import set_random_seed

set_random_seed(random_seed=42, use_torch=True)  # Sets seeds for random, numpy, and optionally torch
```
