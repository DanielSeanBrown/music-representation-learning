from pathlib import Path

# Project root
PROJECT_ROOT = Path(__file__).resolve().parents[2]

# Data
DATA_DIR = PROJECT_ROOT / "data"

# Lakh MIDI
LMD_MATCHED_DIR = DATA_DIR / "midi_files"

# MSD metadata
MSD_METADATA_DIR = DATA_DIR / "midi_metadata"

# Processed Data
PROCESSED_DATA_DIR = DATA_DIR / "processed"

# Notebook datasets
NOTEBOOK_DATASETS_DIR = PROJECT_ROOT / "notebooks" / "notebook_datasets"