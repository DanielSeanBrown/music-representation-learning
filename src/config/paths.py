from pathlib import Path

# Project root
PROJECT_ROOT = Path(__file__).resolve().parents[2]

# Data
DATA_DIR = PROJECT_ROOT / "data"

# Lakh MIDI
LMD_MATCHED_DIR = DATA_DIR / "lmd_matched"

# MSD metadata
MSD_METADATA_DIR = DATA_DIR / "lmd_matched_h5"