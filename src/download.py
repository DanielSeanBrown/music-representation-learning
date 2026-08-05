def download_midi():
   pass

def download_metadata():
  pass

if __name__ == '__main__':
    download_midi()
    download_metadata()


    from pathlib import Path
    import requests
    from tqdm import tqdm
    import tarfile
    
    from src.config.paths import LMD_MATCHED_DIR, MSD_METADATA_DIR
    
    
    FILES = {
    #"lmd_matched.tar.gz": (
    #    "http://hog.ee.columbia.edu/craffel/lmd/lmd_matched.tar.gz",
    #    LMD_MATCHED_DIR,
    #),
        "lmd_matched_h5.tar.gz": (
            "http://hog.ee.columbia.edu/craffel/lmd/lmd_matched_h5.tar.gz",
            MSD_METADATA_DIR,
        ),
    }
    
    
    def download(url: str, destination: Path):
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
    
    
    for filename, (url, out_dir) in FILES.items(): 
        out_dir.mkdir(parents=True, exist_ok=True)
    
        archive_path = out_dir / filename
    
        if not archive_path.exists():
            download(url, archive_path)
        else:
            print(f"{filename} already exists, skipping download.")
    
        print(f"Extracting {filename}...")
        with tarfile.open(archive_path, "r:gz") as tar:
            tar.extractall(out_dir)
    
    print("Finished.")