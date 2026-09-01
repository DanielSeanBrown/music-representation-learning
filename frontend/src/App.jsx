import {
  useCallback,
  useState,
} from "react";

import Graph from "./Graph";
import ShortestPathGraph from "./ShortestPathGraph";
import "./App.css";


const API_URL = "http://127.0.0.1:8000";


const DEFAULT_WEIGHTS = {
  stats: 1.0,
  chroma: 1.0,
  entropy: 1.0,
  rhythm: 1.0,
  structure: 1.0,
  melody: 1.0,
  low: 1.0,
  mid: 1.0,
  high: 1.0,
};


const WEIGHT_LABELS = {
  stats: "Stats",
  chroma: "Chroma",
  entropy: "Entropy",
  rhythm: "Rhythm",
  structure: "Structure",
  melody: "Melody",
  low: "Low register",
  mid: "Mid register",
  high: "High register",
};


function App() {
// Serach functionality
  const [query, setQuery] = useState("");
  const [searchMode, setSearchMode] = useState("title");
  const [results, setResults] = useState([]);
  const [loading, setLoading] = useState(false);

// Current song
  const [selectedSong, setSelectedSong] = useState(null);

// Neighbours
  const [neighbours, setNeighbours] = useState([]);
  const [neighbourCount, setNeighbourCount] = useState(5);
  const [loadingNeighbours, setLoadingNeighbours] = useState(false);

// Graph display
  const [graphData, setGraphData] = useState(null);
  const [loadingGraph, setLoadingGraph] = useState(false);

// Error message
  const [error, setError] = useState("");

// Navigation history
  const [history, setHistory] = useState([]);
  const [historyIndex, setHistoryIndex] = useState(-1);

// Shortest Path search
  const [pathStart, setPathStart] = useState(null);
  const [pathEnd, setPathEnd] = useState(null);
  const [pathK, setPathK] = useState(3);
  const [shortestPath, setShortestPath] = useState(null);
  const [shortestPathGraphData, setShortestPathGraphData] = useState(null);
  const [loadingPath, setLoadingPath] = useState(false);
  const [guideOpen, setGuideOpen] =  useState(false);

// Custom Weights
  const [weights, setWeights] = useState(DEFAULT_WEIGHTS);
  const [similarityMode, setSimilarityMode] = useState("default");
  const [loadingWeights, setLoadingWeights] = useState(false);
  const [weightsOpen, setWeightsOpen] = useState(false);



  async function searchSongs() {
    {/* Search for songs based on the current query and search mode */}

    if (!query.trim()) {
      return;
    }

    setLoading(true);
    setError("");
    setResults([]);
    setSelectedSong(null);
    setNeighbours([]);
    setGraphData(null);

    try {
      /*Determine if search is by artist or by query amd then select the correct one */
      const parameter = searchMode === "artist" ? "artist": "query";

      /*Produce the search request */
      const response = await fetch(`${API_URL}/search?${parameter}=${encodeURIComponent(query)}`);

      /*Check if the response is ok, if not throw an error */
      if (!response.ok) {throw new Error("Search request failed");}

      /* Parse the response data as JSON */
      const data = await response.json();
      setResults(data);
    } 
    
    catch (error) {
      console.error(error); setError( "Error searching for songs. Please check your API server and try again.");
    } 
    
    finally {
      /* Reset state to inform API */
      setLoading(false);
    }
  }



  // This function retrieves a song by its ID and verifies that the returned song matches the requested ID.
  async function getSong(songId) {

    // Ensure correct data type
    const id = Number(songId);
    
    const response = await fetch(`${API_URL}/songs/${id}`);
    if (!response.ok) {throw new Error("Could not retrieve song.");}
    const song = await response.json();

    return song;
  }



  const loadNeighbours =
    useCallback( /* Retain function unless number of neighbours selected changes */
      async (songId) => {

        /*Reset error and indicate loading state*/
        setLoadingNeighbours(true);
        setError("");

        try {

          const id = Number(songId);
          const response = await fetch(`${API_URL}/songs/${id}/neighbours?k=${neighbourCount}`);

          if (!response.ok) {throw new Error("Could not retrieve neighbours");}

          const data = await response.json();
          /*Update neighbours state with retrieved data*/
          setNeighbours(data);

        } 

        catch (error) {

          console.error(error);
          setError("An error occurred, could not retrieve similar songs");
        } 

        finally {
          /* Reset loading state at end of function */
          setLoadingNeighbours(false);
        }

      },
      [neighbourCount]
    );



/* Load the graph displaying the two-hop neighbourhood of a song */
  const loadGraph =
    useCallback( /* Retain function unless number of neighbours selected changes */
      async (songId) => {

        /*Reset error and indicate loading state*/
        setLoadingGraph(true);
        setError("");

        try {
          const requestedId = Number(songId);

          /* Request the two-hop graph for the requested song from the API */
          const response = await fetch(`${API_URL}/songs/${requestedId}/graph/two-hop?k=${neighbourCount}`);

          if (!response.ok) {throw new Error("Could not retrieve graph.");}

          const data = await response.json();

          /* Read nodes and edges. If they are not arrays, default to empty arrays */
          const sourceNodes = Array.isArray(data.nodes) ? data.nodes : [];
          const sourceEdges = Array.isArray(data.edges) ? data.edges : [];


          /* Set the centre node to be the requested song while separating it from other nodes */
          const centreNode = sourceNodes.find((node) => Number(node.id) === requestedId);
          const otherNodes = sourceNodes.filter((node) => Number(node.id) !== requestedId);



          /*Normalise nodes for ease of display on frontend below*/

          const normalizedCentre = {
            ...centreNode, /*Copy all properties from the original centre node*/
            id: requestedId,
            type: "query",
          };


          /*Ensure centre node is first in the list of nodes */
          const normalizedNodes = [
            normalizedCentre,
            ...otherNodes, /* Append the remaining nodes after the centre node */
          ];


          /*Normalise edges for ease of display on frontend below*/

          /*Filter out edges that do not have valid integer source and target IDs */
          const normalizedEdges =
            sourceEdges.filter((edge) => {
                const source = Number(edge.source);
                const target = Number(edge.target);
                return (Number.isInteger(source) && Number.isInteger(target));
              }
            );


          /*Build teh graph object with the validated edges and nodes */
          const normalizedGraph = {
            ...data,
            nodes: normalizedNodes,
            edges: normalizedEdges,
          };


          // Console log for diagnostic
          console.log(
            "GRAPH LOADED",
            {requestedId,
              centreId:Number(normalizedCentre.id),
              centreTitle: normalizedCentre.title,
              centreArtist: normalizedCentre.artist_name,
              nodeCount: normalizedNodes.length,
              edgeCount: normalizedEdges.length,
              nodes: normalizedNodes,
            }
          );


          /*Update the graph state */
          setGraphData(normalizedGraph);

        } 
        catch (error) {
          /*Log error and reset graph state */
          console.error("GRAPH ERROR:", error);
          setGraphData(null);
          setError(error.message || "Could not retrieve the music graph.");
        } 

        finally {
          /*Reset loading state */
          setLoadingGraph(false);
        }

      },
      [neighbourCount]
    );



/*Song exploration function*/
//This function takes a song object, updates history for it and retries its graph and neighbours//
  async function exploreSong(
    song,
    addToHistory = true
  ) {

    const songId =Number(song?.id);


    /* Ensure selecetd song has valid integer ID */
    if (!Number.isInteger(songId)) {
      setError("Invalid song selected");
      return;
    }

    const normalizedSong = {
      ...song,
      id: songId,
    };


    setSelectedSong(normalizedSong);

    /* Collapse search results once a songh is selecetd */
    setResults([]);
    setNeighbours([]);
    setGraphData(null);
    setError("");


    /* Update the history with the newly selected song (if addToHistory is true) */
    if (addToHistory) {

      setHistory((previous) => {

        /*Keep history only up to the current history index */
        const truncated = previous.slice(0, historyIndex + 1);
        const last =truncated[truncated.length - 1];

        /* Avoid adding the same song consecutively */
        if (last &&Number(last.id) ===songId) {return truncated;}

        /* Add the new song to the history)*/
        return [
          ...truncated,
          normalizedSong,
        ];

      });

      /* Move index for the newly added song */
      setHistoryIndex(
        (previous) =>
          previous + 1
      );
    }


    /*Load the graph and neighbours for the selected song */
    await loadNeighbours(songId);
    await loadGraph(songId);
  }


/* Explore song by its graph node ID */
/*This function takes a graph node ID and then retries its neighbourhood.
It is called when the user clicks on a node in the graph */
  async function exploreSongById(
    songId
  ) {

    const id = Number(songId);


    try {

      /* Retrieve clicked songs data by ID */
      const song = await getSong(id);

      /*Diagnostic for console */
      console.log("GRAPH NODE CLICK",
        {
          graphId: id,
          loadedSongId: Number(song.id),
          title: song.title,
          artist: song.artist_name,
        }
      );

      /*Retrieve the clicked songs neighbourhood, graph and update track history*/
      await exploreSong(song, true);

    } 
    catch (error) {
      console.error("Could not explore graph node:",error);
      setError(error.message ||"Could not retrieve selected song.");
    }
  }


/* Function to change the number of neighbours retrieved for the selected song */
  async function changeNeighbourCount(
    value
  ) {

    const count =Number(value);

    /* If the provided number is negative or not finite, return none */
    if (!Number.isFinite(count) ||count < 1) {return;}

    /* Update the number of neighbours to retrieve with the new count */
    setNeighbourCount(count);

    /* If a song is currently selected, reload its neighbours and graph with the new count */
    if (selectedSong) {
      await loadNeighbours(selectedSong.id);
      await loadGraph(selectedSong.id);
    }
  }


/* Function to for navigating one step back in the track history */
  async function goBack() {

    /* If there is no previous song in the history, return none*/
    if (historyIndex <= 0) {return;}

    /* Calculate and update the new index */
    const newIndex = historyIndex - 1;
    const song = history[newIndex];

    if (!song) {return;}

    setHistoryIndex(newIndex);

    /* Explore the song navigated back to but without adding it again to the track history */
    await exploreSong(song, false);
  }


/* Function to for navigating one step forward in the track history */
  async function goForward() {

    /* If there is no next song in the history, return none */
    if (historyIndex >=history.length - 1) {return;}

    /* Calculate and update the new index */
    const newIndex = historyIndex + 1;
    const song = history[newIndex];
    if (!song) {return;}

    setHistoryIndex(newIndex);

    /* Explore the song navigated forward to but without adding it again to the track history */
    await exploreSong(song,false);
  }

/*This function allows jumping to a specific song in the track history */
/*Unlike the previous goBack and goForward functions,
this does not change history since it responds to the user clicking on a specific song in history*/
  async function goToHistory(
    index
  ) {
    const song = history[index];
    if (!song) {return;}
    setHistoryIndex(index);
    await exploreSong(song, false);
  }


/*Function for resetting the track history */
/*It clears the list of tracks visited and resets the history index */
  function clearHistory() {
    setHistory([]);
    setHistoryIndex(-1);
  }



/* The two functions below allow the user to select the starting and ending songs for finding the shortest path */
/* Choosing a new start or end song will reset the current shortest path and any associated graph data */

  function choosePathStart(
    song
  ) {
    setPathStart(song);
    setShortestPath(null);
    setShortestPathGraphData(null);
    setError("");
  }

  function choosePathEnd(
    song
  ) {
    setPathEnd(song);
    setShortestPath(null);
    setShortestPathGraphData(null);
    setError("");
  }


/*Function for finding the shortest path between the selected starting and ending songs */

  async function findShortestPath() {

    /*If there isnt both a starting and ending song selected, show an error and return none */
    if (!pathStart || !pathEnd) {
      setError("Please select both a starting song and an ending song.");
      return;
    }

    /*If the starting and ending songs are the same, show an error and return none */
    if (Number(pathStart.id) === Number(pathEnd.id)) {
      setError("The starting and ending songs must be different.");
      return;
    }

    /*Ensure all relevant states are reset in preparation for finding a new shortest path */
    setLoadingPath(true);
    setError("");
    setShortestPath(null);
    setShortestPathGraphData(null);


    try {

      /* Send API request to find the shortest path between the starting and ending songs */
      const response = await fetch(`${API_URL}/songs/${pathStart.id}/path/${pathEnd.id}?k=${pathK}`);

      /* Show an error if there was an issue with the API response */
      if (!response.ok) {throw new Error("Could not calculate shortest path.");}


      const data = await response.json();
      
      /* Log the shortest path data for diagnostics */
      console.log("SHORTEST PATH:",data);

      /* Set the shortest path state with the retrieved data */
      setShortestPath(data);

      /* If the retrieved data contains both nodes and edges, set the graph data accordingly */
      if (data.nodes && data.nodes.length > 0 && data.edges && data.edges.length > 0) {setShortestPathGraphData(data);} 
      
      /*Otherwise, clear the shortest path graph data */
      else {setShortestPathGraphData(null);}

      /* If the path retrieved contains no nodes,
       this is likely because no valid path could be found with the given value of k (the number of neighbours to try at each step)*/
      if (!data.nodes || data.nodes.length === 0) {setError(`No path could be found with k=${pathK}. Please try increasing the value of k.`);}
    } 

    /* Catch any errors that occur during the API request */
    catch (error) {
      console.error(error);
      setError(error.message ||"Could not calculate shortest path."
      );

    } 
    /* Reset the loading state regardless of success or failure */
    finally {
      setLoadingPath(false);
    }
  }


/*Function to clear the shortest path */
  function clearShortestPath() {
    setPathStart(null);
    setPathEnd(null);
    setShortestPath(null);
    setShortestPathGraphData(null);
  }


/*Function to change the weight feature groups*/
  function changeWeight(
    name,
    value
  ) {

    const numericValue = Number(value);

    /* If the provided weight is not finite, return none */
    if (!Number.isFinite(numericValue)) {return;}

    /* Update the weights state with the new numeric value */
    setWeights(
      (previous) => ({
        ...previous,
        [name]: numericValue,
      })
    );

  }


/*This function applies the custom weights set by the user*/
  async function applyCustomWeights() {

    setLoadingWeights(true);
    setError("");

    try {

      /* Send a POST request to the API to build a new index with the custom weights*/
      const response =await fetch(`${API_URL}/similarity/custom`,
          {
            method: "POST",
            headers: {"Content-Type": "application/json",},
            body:JSON.stringify(weights),
          }
        );


      const data = await response.json();

      /* Throw an error if the response shows any issues*/
      if (!response.ok) {throw new Error(data.detail || "Could not build custom similarity.");}

      /*Update the similarity mode to custom from default (or any previously applied custom weights)*/
      setSimilarityMode("custom");

      /* Log the custom similarity data for diagnostics*/
      console.log("CUSTOM SIMILARITY:",data);


      /*If there is a selcetd song currently being explored, 
      reload its neighbours and graph with the new custom index*/
      if (selectedSong) {
        await loadNeighbours(selectedSong.id);
        await loadGraph(selectedSong.id);
      }


      /* Clear the existing shortest path as it may no longer be valid */
      setShortestPath(null);
      setShortestPathGraphData(null);


    } 
    catch (error) {
      console.error(error);
      setError(error.message ||"Could not apply custom weights.");
    } 
    
    /*Reset the loading state after attempting to apply custom weights*/
    finally {
      setLoadingWeights(false);
    }
  }


/*Function for returning to the default index*/
  async function useDefaultSimilarity() {

    setLoadingWeights(true);
    setError("");

    try {

      /*API request for restoring the default similarity index */
      const response = await fetch(`${API_URL}/similarity/default`,{method: "POST",});

      const data = await response.json();

      /* Throw an error if the response shows any issues*/
      if (!response.ok) {throw new Error(data.detail ||"Could not restore default similarity.");}


      /* Update the similarity mode and reset the weights to default */
      setSimilarityMode("default");
      setWeights(DEFAULT_WEIGHTS);

      /* If there is a selected song currently being explored, 
      reload its neighbours and graph with the default index */
      if (selectedSong) {
        await loadNeighbours(selectedSong.id);
        await loadGraph(selectedSong.id);
      }


      /* Existing path is no longer valid and as such it should be cleared */
      setShortestPath(null);
      setShortestPathGraphData(null);
    } 

    /* Handle any errors that occur during the process */
    catch (error) {
      console.error(error);
      setError(error.message ||"Could not restore default similarity.");

    } 

    /*Reset loading state after switch back to default similarity*/
    finally {setLoadingWeights(false);}
  }



// HTML structure for frontend application
  return (
    <div className="app">

{/* Header Display*/}

      <header className="app-header">
        <div>
          <div className="app-title-row">
            <h1>
              Track Similarity Explorer
            </h1>
          </div>
          <p>
            Discover connections between songs.
          </p>
        </div>

{/*Header Actions*/}

        <div className="header-actions">

          {/* Button for switching between default and custom similarity weights */}
          <button
            className="similarity-toggle"
            onClick={() =>setWeightsOpen((previous) => !previous)}
          >
            Similarity:{" "}
            <strong>
              {similarityMode === "custom"
                ? "Custom"
                : "Default"}
            </strong>
          </button>

          {/* Button for opening the tool guide*/}
          <button
            className="guide-button"
            onClick={() => setGuideOpen(true)}
          >
            Guide
          </button>
        </div>
      </header>


{/* Similarity Setting Display*/}

      {weightsOpen && (
        <section className="settings-panel">
          <div className="settings-header">
            <div>
              <h2>
                Similarity weighting
              </h2>
              <p>
                Adjust how strongly each musical feature
                contributes to similarity.
              </p>
            </div>

{/*Similarity Settings Actions */}


  {/*Button for closing the similarity settings panel*/}
            <button
              className="close-settings"
              onClick={() =>setWeightsOpen(false)}
            >
              ×
            </button>
          </div>


  {/* Weight adjustment sliders */}
          <div className="weight-grid">
            {Object.entries(weights).map(([name, value]) => (
                <div
                  className="weight-row"
                  key={name}
                >
                  <label
                    htmlFor={`weight-${name}`}
                  >
                    <span>
                      {WEIGHT_LABELS[name]}
                    </span>
                    <strong>
                      {Number(value).toFixed(2)}
                    </strong>
                  </label>
                  <input
                    id={`weight-${name}`}
                    type="range"
                    min="0"
                    max="5"
                    step="0.05"
                    value={value}
                    onChange={(event) =>changeWeight(name,event.target.value)
                    }
                  />
                </div>
              )
            )}
          </div>


  {/*Button to apply custom weights */}
          <div className="settings-actions">
            <button
              className="primary-button"
              onClick={applyCustomWeights}
              disabled={loadingWeights}
            >
              {loadingWeights
                ? "Building index..."
                : "Apply custom weights"}
            </button>


  {/* Button to return to default similarity weights */}
            <button
              className="secondary-button"
              onClick={useDefaultSimilarity}
              disabled={loadingWeights ||similarityMode === "default"}
            >
              Return to default
            </button>
          </div>
        </section>
      )}



{/* Search Display */}


      <section className="search-section">
        <div className="section-label">
          FIND MUSIC
        </div>
        <div className="search-mode">
          <span>
            Search by
          </span>

{/* Search Actions*/}


  {/*Search by title selector button*/}
          <div className="search-mode-buttons">
            <button
              className={
                searchMode === "title"
                  ? "search-mode-button active"
                  : "search-mode-button"
              }
              onClick={() => {
                setSearchMode("title");
                setResults([]);
                setError("");
              }}
            >
              Song title
            </button>


  {/*Search by artist selector button*/}
            <button
              className={
                searchMode === "artist"
                  ? "search-mode-button active"
                  : "search-mode-button"
              }
              onClick={() => {
                setSearchMode("artist");
                setResults([]);
                setError("");
              }}
            >
              Artist
            </button>
          </div>
        </div>


  {/* Search box for entering the query */}
        <div className="search-container">
          <input
            type="text"
        /* Placeholder text in search box. Changes depending on search mode */
            placeholder={
              searchMode === "artist"
                ? "Search for an artist..."
                : "Search for a song..."
            }
            value={query}
            onChange={(event) =>
              setQuery(
                event.target.value
              )
            }

        /* Search query if user presses Enter */
            onKeyDown={(event) => {
              if (event.key === "Enter") {
                searchSongs();
              }
            }}
          />


  {/* Button for executing search */}
          <button
            className="primary-button"
            onClick={searchSongs}
            disabled={loading}
          >
            {loading
              ? "Searching..." /*Change to indicate action in progress */
              : "Search"}
          </button>
        </div>
      </section>
    
    {/*Display error message if appropriate from search*/}
      {error && (
        <div className="error-message">
          {error}
        </div>
      )}


    {/*Display loading message while search is in progress*/}
      {loading && (
        <div className="loading-message">
          Searching...
        </div>
      )}


{/*Display search results */}

      {!loading && results.length > 0 && (

        <section className="results-section">
          <div className="section-heading">
            <div>
              <div className="section-label">
                RESULTS
              </div>
              <h2>
                {searchMode === "artist"
                  ? "Artist search results"
                  : "Track search results"}
              </h2>
            </div>
            {/* Display the number of search results */}
            <span className="result-count">
              {results.length}
            </span>
          </div>
          <div className="song-list">
            {results.map((song) => (
              <div
                className="song-card"
                key={song.id}
              >
                <div className="song-info">
                  <h3>
                    {song.title}
                  </h3>
                  <p>
                    {song.artist_name}
                  </p>
                </div>


{/*Actions for tracks returned by search query */}


    {/*Button for getting the nearest k neighbours and producing 2-hop graph */}
                <div className="song-actions">
                  <button
                    onClick={() =>
                      exploreSong(song)
                    }
                  >
                    Explore
                  </button>


  {/*Button for selecting track as starting point in a shortest path search */}
                  <button
                    onClick={() =>
                      choosePathStart(song)
                    }
                  >
                    Path from here
                  </button>


  {/*Button for selecting track as ending point in a shortest path search */}
                  <button
                    onClick={() =>
                      choosePathEnd(song)
                    }
                  >
                    Path to here
                  </button>
                </div>
              </div>
            ))}
          </div>
        </section>
      )}



{/* Display the shortest path section*/}
      {(pathStart ||
        pathEnd ||
        shortestPath) && (

  /*Main section display */
        <section className="path-section">
          <div className="section-heading">
            <div>
              <div className="section-label">
                CONNECTION
              </div>
              <h2>
                Shortest path
              </h2>
            </div>
          </div>


  {/*Starting song display */}
          <div className="path-selection">
            <div className="path-song">
              <span className="path-label">
                START
              </span>
              {pathStart ? (
                <>
                  <h3>
                    {pathStart.title}
                  </h3>
                  <p>
                    {pathStart.artist_name}
                  </p>
                </>
              ) : (
                <div className="path-empty">
                  Select a starting song
                </div>
              )}


  {/*Connecting arrow between tracks */}
            </div>
            <div className="path-arrow">
              →
            </div>
            <div className="path-song">
  

  {/*End song display */}
              <span className="path-label">
                END
              </span>
              {pathEnd ? (
                <>
                  <h3>
                    {pathEnd.title}
                  </h3>
                  <p>
                    {pathEnd.artist_name}
                  </p>
                </>
              ) : (
                <div className="path-empty">
                  Select an ending song
                </div>
              )}
            </div>
          </div>


  {/*Display and clicker for number of neighbours considered per step*/}        
          <div className="path-options">
            <label>
              Neighbours observed per step
              <input
                type="number"
                min="1"
                max="50"
                value={pathK}
                onChange={(event) => {
                  const value =
                    Number(
                      event.target.value
                    );
                  if (
                    Number.isFinite(value) &&
                    value >= 1
                  ) {
                    setPathK(value);
                  }
                }}
              />
            </label>
          </div>


{/*Actions for shortest path section*/}


  {/*Button for executing the search */}
          <div className="path-actions">
            <button
              className="primary-button"
              onClick={findShortestPath}
              disabled={
                !pathStart ||
                !pathEnd ||
                loadingPath
              }
            >
              {loadingPath
                ? "Finding path..."
                : "Find shortest path"}
            </button>


  {/*Button for clearing the search results */}
            <button
              className="secondary-button"
              onClick={clearShortestPath}
            >
              Clear
            </button>
          </div>


{/*Display for the returned shortest path */}


  {/*Shortest path header display */}
          {shortestPath && (
            <div className="path-result">
              {shortestPath.nodes &&
               shortestPath.nodes.length > 0 ? (
                <>
                  <div className="path-result-header">
                    <div>
                      <span className="section-label">
                        ROUTE
                      </span>
                      <h3>
                        Musical connection
                      </h3>
                    </div>
    
    
  {/*Shortest path cost display */}
                    {shortestPath.total_cost !== null &&
                     shortestPath.total_cost !== undefined && (
                      <div className="path-cost">
                        <span>
                          COST
                        </span>
                        <strong>
                          {Number(
                            shortestPath.total_cost
                          ).toFixed(3)}
                        </strong>
                      </div>
                    )}
                  </div>


  {/*Shortest path route taken display */}
                  <div className="path-list">

                    {/* Go through the nodes in the shortest path and display each song along with the edge weight to the next song */}
                    {shortestPath.nodes.map(
                      (song, index) => {
                        const nextSong = shortestPath.nodes[index + 1];
                        let edgeWeight = null;
                        if (nextSong) {

                          /* Find the edge connecting the current song to the next song and check if it exists */
                          const edge =
                            (shortestPath.edges || [])
                              .find((candidate) => {

                                /* Extract the source and target IDs from the candidate edge */
                                const source =Number(candidate.source);
                                const target =Number(candidate.target);

                                const currentId =Number(song.id);
                                const nextId =Number(nextSong.id);
                                  
                                /*return truth value indicating if this edge connects the current song to the next song */  
                                return (
                                  (source === currentId && target === nextId) || (source === nextId &&target === currentId)
                                );

                              });
                          
                          /*If found, extract the edge weight */
                          if (edge) {
                            edgeWeight =Number(edge.similarity);
                          }

                        }
                      
                        /* Return the JSX for the step in the found route */
                        return (

      /*Display the current step in the shortest path */
                          <div
                            className="path-step"
                            key={`${song.id}-${index}`}
                          >
                            <div className="path-number">
                              {index + 1}
                            </div>
                            <div className="path-step-content">
                              <strong>
                                {song.title}
                              </strong>
                              <span>
                                {song.artist_name}
                              </span>
                            </div>


      {/* Display the edge weight if it exists */}
                            {edgeWeight !== null && (
                              <div className="path-step-weight">
                                <strong>
                                  {edgeWeight.toFixed(3)}
                                </strong>
                              </div>
                            )}
                          </div>
                        );
                      }
                    )}
                  </div>
                </>
              ) : (


      /* Display a message when no path could be found */
                <div className="no-path">
                  No path could be found with the
                  current settings.
                </div>
              )}
            </div>
          )}


  {/* Display for the shortest rouet as a graph,
  with action of selecting tracks for exploration on node click.*/}
          {shortestPathGraphData && (
            <div className="path-graph">
              <div className="section-label">
                ROUTE GRAPH
              </div>
              <p>
                The highlighted route shows the shortest
                connection between the selected songs.
              </p>
              <ShortestPathGraph
                graphData={shortestPathGraphData}
                onNodeClick={exploreSongById}
              />
            </div>
          )}
        </section>
      )}



{/*Track Neighbourhood Display*/}

  {/* Display metadata for track being queried*/}
      {selectedSong && (
        <section className="exploration-section">
          <div className="exploration-header">
            <div>
              <div className="section-label">
                NOW EXPLORING
              </div>
              <h2>
                {selectedSong.title}
              </h2>
              <p>
                {selectedSong.artist_name}
              </p>
            </div>


  {/*Track exploration history display and actions*/}

        {/*Button for going backwards*/}
            <div className="history-controls">
              <button
                disabled={historyIndex <= 0} // Disable the button if at the start of history
                onClick={goBack}
              >
                Back
              </button>


        {/*Button for going forwards*/}
              <button
                disabled={historyIndex >= history.length - 1} // Disable the button if at the end of history
                onClick={goForward}
              >
                Forward
              </button>
            </div>
          </div>


        {/*History display */}
          {history.length > 0 && (
            <div className="history">
              <div className="history-header">
                <span>
                  Navigation history
                </span>

        {/*Button for clearing history */}
                <button
                  onClick={clearHistory}
                >
                  Clear
                </button>
              </div>

        {/*History path display */}
              <div className="history-path">
                {history.map(
                  (song, index) => (

        /*tracks in the history function as buttons for selection for exploration */
                    <button
                      key={`${song.id}-${index}`}
                      className={
                        index === historyIndex
                          ? "history-item active"
                          : "history-item"
                      }
                      onClick={() =>
                        goToHistory(index)
                      }
                    >
                      {song.title}
                    </button>
                  )
                )}
              </div>
            </div>
          )}

  {/*Display header info for the tracks similarity neighbourhood*/}
          <div className="neighbours-section">
            <div className="section-heading">
              <div>
                <div className="section-label">
                  SIMILAR MUSIC
                </div>
                <h2>
                  Neighbours
                </h2>
              </div>

  {/*Selector for changing the number of neighbours to display. 
  This affects both the text and graph displays*/}

              <label className="inline-control">
                <span>
                  Count
                </span>
                <input
                  type="number"
                  min="1"
                  max="50"
                  value={neighbourCount}
                  onChange={(event) =>
                    changeNeighbourCount(
                      event.target.value
                    )
                  }
                />
              </label>
            </div>


  {/*Display message whilst querrying neighbourhood of tracks*/}
            {loadingNeighbours && (
              <div className="loading-message">
                Finding similar songs...
              </div>
            )}

  {/*Display track neighbourhood once loaded as a text list*/}  
            {!loadingNeighbours &&
             neighbours.length > 0 && (

              <div className="neighbour-list">
                {neighbours.map((song) => (
                  <div
                    className="neighbour-card"
                    key={song.id}
                  >
                    <div className="song-info">
                      <h3>
                        {song.title}
                      </h3>
                      <p>
                        {song.artist_name}
                      </p>
                    </div>

    {/*Display actions for each neighbour, including similarity score and path options*/}
                    <div className="neighbour-actions">

        {/*Similarity score*/}
                      {song.score !== undefined && (
                        <span className="score">
                          {Number(
                            song.score
                          ).toFixed(3)}
                        </span>
                      )}


        {/*Button to query the neighbourhood of the respective track*/}
                      <button
                        onClick={() =>
                          exploreSong(song)
                        }
                      >
                        Explore
                      </button>

        {/*Button to select the track as the starting pint in a shortest path search*/}
                      <button
                        onClick={() =>
                          choosePathStart(song)
                        }
                      >
                        Path from here
                      </button>

        {/*Button to select the track as the end point in a shortest path search*/}
                      <button
                        onClick={() =>
                          choosePathEnd(song)
                        }
                      >
                        Path to here
                      </button>

                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>


  {/*Display for the graph visualiser of the queried track */}

    {/*Display explanatory text */}
          <div className="graph-section">
            <div className="section-heading">
              <div>
                <div className="section-label">
                  NETWORK
                </div>
                <h2>
                  Music neighbourhood
                </h2>
                <p>
                  Explore two levels of musical similarity.
                  Click any node to make it the centre.
                </p>
              </div>
            </div>


    {/*Display text whilst loading graph*/}
            {loadingGraph && (
              <div className="loading-message">
                Building music graph...
              </div>
            )}

    {/*Display the graph with on click functionality to explroe tracks by clicking their node*/}
            {graphData &&
             !loadingGraph && (
              <div className="graph-card">
                <Graph
                  graphData={graphData}
                  onNodeClick={
                    exploreSongById
                  }
                />
              </div>
            )}


          </div>
        </section>
      )}


{/*Tool guide for the user is contained below*/}

{guideOpen && (

  <div
    className="guide-overlay"
    onClick={() => setGuideOpen(false)}
  >
    <section
      className="guide-modal"
      onClick={(event) =>
        event.stopPropagation()
      }
    >


  {/*Guide title and subtitle*/}
      <div className="guide-header">
        <div>
          <div className="section-label">
            GUIDE
          </div>
          <h2>
            How to use Track Similarity Explorer
          </h2>
        </div>


  {/*Button for closing guide*/}
        <button
          className="guide-close"
          onClick={() => setGuideOpen(false)}
          aria-label="Close guide"
        >
          x
        </button>
      </div>


  {/*Display the main body of text in teh guide*/}
      <div className="guide-content">


        <section className="guide-section">
          <h3>
            What is this tool?
          </h3>
          <p>
            This tool is for exploring similarity between tracks based on their musical characteristics. 
          </p>
        </section>


        <section className="guide-section">
          <h3>
            Finding Tracks
          </h3>
          <p>
            The search box at the start of the page can be used to search for tracks in the dataset.
          </p>
          <ul>
            <li>
              Choose <strong>Song title</strong> to search
              for a particular track by title.
            </li>
            <li>
              Choose <strong>Artist</strong> to search
              for a particular track by artist.
            </li>
            <li>
              Select <strong>Explore</strong> on a result
              to begin exploring that song.
            </li>
          </ul>
          <p>
            If the track you are searching for was not in the list of found results, unfortunately that means
            your requested song is not in the tool's database.
          </p>
        </section>


        <section className="guide-section">
          <h3>
            Exploring a song
          </h3>
          <p>
            Once you a select a song for exploration, the <strong>Neighbours</strong> section lists songs that are found to be similar.
            This is by default the 5 most similar, but more or less can be shown using You can change the using the <strong>Count control</strong> on the right hand side.
          </p>
          <p>
            On each similar songs row, there are three buttons enabling further exploration and a score outlining similarity scored between 0 and 1. 
            The explore button selects that song for querying its most similar songs, allowing you to "hop" across songs to observe each one's local neighbourhood of 
            similar songs. The other two buttons allow you to mark a song as a start or end point in a path. This is explained in more depth at a later section. 
          </p>
          <p>
            When a song is selected for exploration, below the list of similar songs there will also be a graph showing the song's local neighbourhood. This is explained next.
          </p>
        </section>


        <section className="guide-section">
          <h3>
            Understanding the graph
          </h3>
          <p>
            The graph provides a visual representation of the songs neighbourhood of most similar tracks.
            Nodes represent songs, with the central node being the currently explored song and surrounding nodes representing similar tracks.
            The edges connecting nodes are labelled with those tracks similarity scores as well as indicating that the tracks are neighbours.
            The graph by default extends to show not only the queried song's immediate neighbours but also the second ring of similar tracks, that is, the neighbours of the neighbours.
          </p>
          <p>
            See the key below for an explanation of the different types of nodes in the graph.
          </p>
          <div className="guide-graph-key">
            <div>
              <span className="guide-key-dot centre" />
              <strong>Centre</strong>
              <p>
                The song currently being explored.
              </p>
            </div>
            <div>
              <span className="guide-key-dot first" />
              <strong>1-hop</strong>
              <p>
                Songs directly connected to the centre.
              </p>
            </div>
            <div>
              <span className="guide-key-dot second" />
              <strong>2-hop</strong>
              <p>
                Songs connected through the first ring.
              </p>
            </div>
          </div>
          <p>
            Nodes in the graph can be selected to move them around for better visibility. 
            Also, clicking any node in the graph will make that song the new centre of the exploration,
            updating both the graph and list of neighbours for that song.
          </p>
        </section>


        <section className="guide-section">
          <h3>
            Similarity scores
          </h3>
          <p>
            It was mentioned earlier that similarity scores range from 0 to 1, with 0 indicating no similarity and 1 indicating identical songs.
            The score is calculated as the cosine similarity between the feature vectors of the two songs. Vectors here represent the various musical features extracted from the songs.
            Each grouping of vectors, by the category of musical features they represent, has an associated weight that influences how much it contributes to this similarity metric.
            Through experimentation and tuning, these weights have been selected as giving the best balance for accurately reflecting the feeling that two songs are similar to each other.
          </p>
          <p>
            These weights, however, may be adjusted manually if you would prefer to weight all features equally or indeed use your own custom angle for comparison.
          </p>
        </section>


        <section className="guide-section">
          <h3>
            Similarity weighting
          </h3>
          <p>
            The Similarity control lets you change which
            musical characteristics have the greatest
            influence on the results.
          </p>
          <p>
            The available feature groups are:
          </p>
          <ul>
            <li><strong>Stats</strong> - Represents basic statistical features of the song such as mean, variance, and standard deviation of pitches</li>
            <li><strong>Chroma</strong> - Represents the distribution of pitch classes over time</li>
            <li><strong>Entropy</strong> - Represents the unpredictability or complexity of the musical content</li>
            <li><strong>Rhythm</strong> - Represents temporal patterns and beat structures</li>
            <li><strong>Structure</strong> - Represents the overall arrangement and sections of the song</li>
            <li><strong>Melody</strong> - Represents the sequence of pitches forming the main tune</li>
            <li><strong>Low register</strong> - Represents the sequence of features in the lower frequency range</li>
            <li><strong>Mid register</strong> - Represents the sequence of features in the mid frequency range</li>
            <li><strong>High register</strong> - Represents the sequence of features in the higher frequency range</li>
          </ul>
          <p>
            So, adjusting these weights allows you to control which musical features have the most impact on the similarity calculations. 
            If you would prefer, for example, to explore song similarity only by bass lines and drum rhythms, 
            you can increase the weights for <strong>Low register</strong> and <strong>Rhythm</strong> while decreasing the others.
          </p>
          <p>
            You can always return to the default weighting
            using <strong>Return to default</strong>.
          </p>
        </section>


        <section className="guide-section">
          <h3>
            Finding a shortest path
          </h3>
          <p>
            As mentioned earlier, within the list of similar songs,
            there are buttons for marking songs as the start or end point for a shortest path search.
            Doing so and selecting <strong>Find shortest path</strong>, will launch a search to find
            the shortest path where the route's length is the sum of (1 - similarity) for each track visited along the path.
            The reason for not simply using similarity directly is because a higher similarity should correspond to a 
            shorter path and this method aims to minimise path length.
          </p>
          <p>
            This feature of the tool can be an interesting way of looking at how one might go from dissimilar songs to similar ones, tracing a path through the network of song similarities.
          </p>
          <p>
            For performing the search, Dijkstra's algorithm is used. If you are interested in how this algorithm works,
            I recommend looking up resources on Dijkstra's algorithm for a detailed explanation. The reason the method is important
            to highlight briefly however, is the control for how many neighbours are considered at each step in the search. 
            As the dataset contains thousands of songs, it is not efficient to observe every possible connection at each step. 
            Instead, only a selected number of closest tracks are considered for each step. 
            Keeping this number low will speed up the search, but may miss some potential paths or in fact fail to find the shortest path.
            Conversely, increasing this number will make the search more thorough but slower. I would warn that a high number may significantly impact performance.
          </p>
          <p>
            For launching this search, please see the clear step by step instructions below:
          </p>
          <ol>
            <li>
              Select <strong>Path from here</strong> on the
              first song.
            </li>
            <li>
              Select <strong>Path to here</strong> on the
              second song.
            </li>
            <li>
              Choose how many neighbours can be considered
              at each step. (This is by default 3)
            </li>
            <li>
              Select <strong>Find shortest path</strong>.
            </li>
          </ol>
          <p>
            The route found is displayed with each song along the path shown in order 
            with accompanying similarity score for each connection. 
            This information is also displayed as a graph and as before by clicking the nodes you can bring up that song for exploration.
          </p>


        </section>
        <section className="guide-section">
          <h3>
            Navigation history
          </h3>
          <p>
            Finally, every track you explore is recorded in the navigation history. 
            This way, you can easily revisit previous songs and retrace your exploration steps.
          </p>
          <p>
            Use <strong>Back</strong> and
            <strong> Forward</strong> to move through your
            previous explorations, or select a song directly
            from the history trail.
          </p>
          <p>
            If you find the navigation history becoming too long or cluttered, you can use <strong>Clear</strong> to start fresh.
          </p>
        </section>

        <section>
          Thank you for reading this guide. I hope you enjoy exploring music with my tool!
        </section>

      </div>
    </section>
  </div>

)}
    </div>
  );
}

export default App;