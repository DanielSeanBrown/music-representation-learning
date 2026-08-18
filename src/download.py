from pathlib import Path
import requests
from tqdm import tqdm
import tarfile
from loguru import logger
from src.config.paths import LMD_MATCHED_DIR, MSD_METADATA_DIR

def extract_flat(archive_path: Path, out_dir: Path):
    """Extract a tar.gz archive to the specified output directory, flattening the directory structure."""
    with tarfile.open(archive_path, "r:gz") as tar:
        for member in tar.getmembers():
            parts = Path(member.name).parts

            # Skip the top-level directory
            if len(parts) <= 1:
                continue

            member.name = str(Path(*parts[1:]))
            tar.extract(member, out_dir)


def perform_download(url: str, destination: Path):
    """Download a file from a URL to the specified destination"""
    response = requests.get(url, stream=True)
    response.raise_for_status()
    total = int(response.headers.get("content-length", 0))
    with open(destination, "wb") as f, tqdm(
        total=total,
        unit="B",
        unit_scale=True,
        desc=destination.name,
    ) as pbar:
        for chunk in response.iter_content(chunk_size=1024 * 1024):
            if chunk:
                f.write(chunk)
                pbar.update(len(chunk))

def download_files():
    """Download and extract the LMD matched and LMD matched h5 datasets."""

    FILES = {
        "lmd_matched.tar.gz": (
            "http://hog.ee.columbia.edu/craffel/lmd/lmd_matched.tar.gz",
            LMD_MATCHED_DIR,
        ),
        "lmd_matched_h5.tar.gz": (
            "http://hog.ee.columbia.edu/craffel/lmd/lmd_matched_h5.tar.gz",
            MSD_METADATA_DIR,
        ),
    }

    for filename, (url, out_dir) in FILES.items(): 
        out_dir.mkdir(parents=True, exist_ok=True)

        archive_path = out_dir / filename

        if not archive_path.exists():
            logger.info(f"Downloading {filename}...")
            perform_download(url, archive_path)
        else:
            logger.info(f"{filename} already exists, skipping download.")

        logger.info(f"Extracting {filename}...")
        extract_flat(archive_path, out_dir)

    logger.info("Download and extraction completed.")


if __name__ == '__main__':
    download_files()
