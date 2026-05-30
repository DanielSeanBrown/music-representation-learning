import h5py
import numpy as np
import pandas as pd
from pathlib import Path


files = list(Path("data").rglob("*.h5"))

rows = []

findings = set()
for f in files:
    with h5py.File(f, "r") as h5:
        if tuple(list(h5.keys())) not in findings:
            findings.add(tuple(list(h5.keys())))
            print(list(h5.keys()))

        if tuple(list(h5["metadata"].keys())) not in findings:
            findings.add(tuple(list(h5["metadata"].keys())))
            print(list(h5["metadata"].keys()))


with h5py.File(r"C:\Users\danie\Documents\GitHub\music-representation-learning\data\raw\lmd_matched_h5\lmd_matched_h5\G\Z\Q\TRGZQQL12903CF7EBE.h5", "r") as h5:
    songs = h5["metadata"]["songs"]
    print(type(songs),'\n')
    print(songs.shape,'\n')
    print(songs.dtype,'\n')

    print(songs[:],'\n')


#for f in files:
#    with h5py.File(f, "r") as h5:
#        rows.append({
#            "file": str(f),
#            "song_id": h5["metadata"]["song_id"][()],
#        })
#
#
#df = pd.DataFrame(rows)
#print(df.head())
#df.to_csv("data/match_meta_data.csv", index=False)