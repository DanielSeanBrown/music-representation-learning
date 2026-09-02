# Song Similarity Mapping

This repository serves to hold the code and documentation for my MSc Data Science Project.

The project aimed to produce a music similarity exploration tool which can map and quantify how similar songs are. This was done by extracting musical features for each individual track over the Lakh MIDI dataset, producing vector embeddings and building a FAISS index. FastAPI and React were then used to build a frontend tool the user can interact with. For in depth documentation, please refer to the project report. 

On repository structure, light project outlines and guidance for running and recreating the tool, please see the sections below.

---

## Tool Features
The tool has 3 main features and these are as follows:

### Similarity Neighbourhood
The user can query the similarity neighbourhood of any song in the dataset. This will retrieve the K most similar songs, where K is adjustable. The neighbourhood is presented as a list of similar songs with a similarity score from 0 to 1 as well as a graph with labelled nodes and edges. The graph also contains the secondary similarity neighbourhood. That is, the K most similar songs to each neighbour.

### Shortest Path Calculation
The user can select any two songs to be the start and end destination of a path and the tool will find the shortest path between them, where the length of the path is minimised for dissimilarity.

### Custom Similarity Weighting
The user can manually adjust the weightings of different musical feature groups, giving a custom agenda for measuring similarity. 

---

# Dataset

The project uses MIDI data from the **Lakh MIDI Dataset**, which uses metadata from the **Million Song Dataset (MSD)**. In accordance with the wishes of the dataset's author, I reference them here: 

"Colin Raffel. "Learning-Based Methods for Comparing Sequences, with Applications to Audio-to-MIDI Alignment and Matching". PhD Thesis, 2016."

Subsequently, on referencing the million song dataset:

"Thierry Bertin-Mahieux, Daniel P. W. Ellis, Brian Whitman, and Paul Lamere. "The Million Song Dataset". In Proceedings of the 12th International Society for Music Information Retrieval Conference, pages 591–596, 2011."

These references are also included in the report.


---

# Short Methodology

For a full methodology, please refer to the project report.

## MIDI Feature Extraction

Beyond dataset downloading and initial cleaning, first features describing musical information are extracted for each track. These features are grouped categorically into the following:

1) Basic Descriptive
2) Chroma
3) Entropy
4) Melody
5) Rhythm
6) Structure

For a full description of features please see the feature dictionary. 

## Embedding Construction and Index Creation
Features are embedded as vectors, scaled and normalised to use cosine similarity as a similarity metric. These are then used to create a FAISS index for retrieving similarity neighbourhoods.

## Weight Optimisation
One of the challenges in this project came from the lack of ground truth. It can be difficult to quantify what similarity means and certainly there is no pre-existing metric to evaluate against. As such, I hand annotated roughly 360 tracks to create "truth triplets" indicating an inequality relationship that should hold. Roughly 40,000 weight simulations were performed to find the most ideal group weightings where accuracy is maximised. I highly recommend taking a look at the respective notebook for further detail. The best performing weight configuration was used to weight feature groups when constructing the index.


## Exploring the Index
The majority of the work for navigating the similarity index is performed by the MusicExplorer class in the respective script. This makes the actions listed under tool features possible.

## Backend

The backend is implemented using **FastAPI**. It provides the API endpoints for communication between the MusicExplorer class and the tool frontend. 

## Frontend

The frontend is implemented using **React**. It provides an ergonomic user experience and enables smooth engagement with the index. It communicates with the FastAPI using HTTP requests. 

---

# Project Structure

A simplified overview of the repository is shown below. Note that the frontend section does contain more files, these however are not listed as they come from default installation.

```text
music-representation-learning/
│
├── data/
│   ├── midi_files/
│   ├── midi_metadata/
│   └── processed/
│       ├──weight_evaluation_limit_31034.parquet
│       ├──best_weighting_limit_31034.parquet
│       └──evaluation_table.parquet
│
├── documents/
│   ├── report.docx
│   └── feature_dictionary.md
│
├── frontend/
│    └──src/
│       ├── App.css
│       ├── App.jsx
│       ├── Graph.jsx
│       ├── index.css
│       ├── main.jsx
│       └── ShortestPathGraph.jsx
│
├── notebooks/
│    └──weighting_evaluation.ipynb
│
├── src/
│   ├── api/
│   │   ├── models.py
│   │   └── app.py
│   │
│   ├── config/
│   │   └── paths.py
│   │
│   ├── evaluation/
│   │   ├── produce_evaluation_table.py
│   │   └── perform_evaluation.py
│   │
│   ├── features/
│   │   ├── basic.py
│   │   ├── chroma.py
│   │   ├── entropy.py
│   │   ├── ngrams.py
│   │   ├── rhythms.py
│   │   └── structure.py
│   │
│   ├── retrieval/
│   │   ├── laod.py
│   │   └── music_explorer.py
│   │
│   ├── cleaning.py
│   ├── download.py
│   ├── embeddings.py
│   ├── feature_extraction.py
│   └── produce_file_index.py
│    
│
├── feature_dictionary.md
├── requirements.txt
├── README.md
└── run.py
```

# Installation

For running the tool, please follow the instructions below:

## 1. Clone the repository

```bash
git clone https://github.com/DanielSeanBrown/music-representation-learning
cd music-representation-learning
```

## 2. Install the Python dependencies

Install the required Python packages:

```bash
pip install -r requirements.txt
```

## 3. Install Node.js

The frontend requires Node.js and npm. Download and install the latest LTS version of Node.js from the official website:

https://nodejs.org/en/download

During installation, use the default installation options.

To check if installation was successful, in a new terminal the commands:

```bash
node --version
npm --version
```
Should each return a version number.

## 4. Install frontend dependencies

Navigate to the frontend directory:

```bash
cd frontend
```

Then install the Node dependencies:

```bash
npm install
```

---

# Running the Tool

Once all relevant packages have been installed, data fetching and processing will have to be performed. Note that this can take a long time! Afterwards, to run the tool in its current form, the back and frontend need to be run separately. As such, it will require two command prompts.

## 1. Fetch and Process Datasets

Run the main script to download and process MIDI data into a similarity index.
PLEASE NOTE: This is a long process. For reference, it took the university's library desktop about 7 hours to execute this script.

```bash
run.py
```

## 2. Launch FastAPI backend

From the root of the repository run:

```bash
uvicorn src.api.app:app --reload
```

The API will be available at:

```text
http://127.0.0.1:8000
```
But this isn't particurlarly useful in a user orientated sense. Visiting the URL is more for diagnostics and debugging.


## 3. Launch the React frontend

In a second terminal navigate to the frontend folder of the repository.

```bash
cd frontend
```

Run the following code:

```bash
npm run dev
```

The tool can now be accessed at:

**http://localhost:5173/**

---


# License

The project is intended primarily for research, as such it is free to use by anyone as long as they cite it.
