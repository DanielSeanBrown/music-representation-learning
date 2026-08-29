import { useEffect, useRef } from "react";
import cytoscape from "cytoscape";



/* Graph function for rendering a Cytoscape graph 
Two args are taken,
  1. graphData: The data representing the graph (nodes and edges)
  2. onNodeClick: Callback function to handle node click events
*/

function Graph({
  graphData,
  onNodeClick,
}) {
  const containerRef = useRef(null);
  const cyRef = useRef(null);
  const onNodeClickRef = useRef(onNodeClick);


  /*Keep the most recent onNodeClick callback in a ref, so the event listener doesnt have to be rebound at every update */
  useEffect(() => {onNodeClickRef.current = onNodeClick;}, [onNodeClick]);

  /* Create Cytoscape instance */
  useEffect(() => {
    
    /* Get the container element for Cytoscape */
    const container = containerRef.current;

    /* If the container element is not available, return none*/
    if (!container) {return;}

    /* Initialize Cytoscape instance */
    const cy = cytoscape({
      container,
      elements: [],
      style: [


        /*Styling for default node */
        {
          selector: "node",
          style: {
            label: "data(label)",
            "text-wrap": "wrap",
            "text-max-width": "100px",
            "text-valign": "center",
            "text-halign": "center",
            "background-color": "#252b35",
            width: "42px",
            height: "42px",
            "font-size": "8px",
            "font-family": "monospace",
            "font-weight": "normal",
            color: "#c8d1dc",
            "border-width": "1px",
            "border-color": "#4a5563",
            "overlay-opacity": 0,
          },
        },


        /*Styling for query node */
        {
          selector: 'node[type="query"]',
          style: {
            "background-color": "#102b36",
            color: "#e7f7fb",
            width: "76px",
            height: "76px",
            "font-size": "10px",
            "font-weight": "bold",
            "border-width": "2px",
            "border-color": "#00a8d8",
          },
        },


        /*Styling for first hop node */
        {
          selector: 'node[type="hop_1"]',
          style: {
            "background-color": "#193845",
            color: "#d8f3fa",
            width: "54px",
            height: "54px",
            "font-size": "8px",
            "font-weight": "normal",
            "border-width": "1px",
            "border-color": "#2185a3",
          },
        },


        /*Styling for second hop node */
        {
          selector: 'node[type="hop_2"]',
          style: {
            "background-color": "#202731",
            color: "#8995a5",
            width: "36px",
            height: "36px",
            "font-size": "7px",
            "font-weight": "normal",
            "border-width": "1px",
            "border-color": "#3d4653",
          },
        },


        /*Styling for default edges */
        {
          selector: "edge",
          style: {
            width: "mapData(weight, 0.5, 1, 1, 4)",
            "line-color": "#36414e",
            "curve-style": "bezier",
            "target-arrow-shape": "none",
            label: "data(label)",
            "font-size": "7px",
            "font-family": "monospace",
            "font-weight": "normal",
            color: "#687586",
            "text-background-color": "#11161d",
            "text-background-opacity": 1,
            "text-background-padding": "2px",
            "overlay-opacity": 0,
          },
        },


        /*Styling for first-hop edges */
        {
          selector: 'edge[hop="1"]',
          style: {
            "line-color": "#247f9d",
            width: "mapData(weight, 0.5, 1, 2, 5)",
            "line-style": "solid",
            "z-index": 2,
          },
        },


        /*Styling for second-hop edges */
        {
          selector: 'edge[hop="2"]',
          style: {
            "line-color": "#303b48",
            width: "mapData(weight, 0.5, 1, 1, 2)",
            "line-style": "dashed",
            "z-index": 1,
          },
        },


        /*Styling for selected node */
        {
          selector: "node:selected",
          style: {
            "border-width": "2px",
            "border-color": "#00a8d8",
          },
        },


        /*Styling for active node */
        {
          selector: "node:active",
          style: {
            "overlay-opacity": 0.08,
            "overlay-color": "#00a8d8",
          },
        },
      ],

      layout: {
        name: "preset",
      },
    });

    /*Store graph instance */
    cyRef.current = cy;

    /*Initialize hover over tooltip */
    let activeTooltip = null;

    /*Function for deleting tooltip */
    function removeTooltip() {
      if (activeTooltip) {
        activeTooltip.remove();
        activeTooltip = null;
      }
    }


    /*Function for positioning tooltip */
    function positionTooltip(event, tooltip) {
      const originalEvent = event?.originalEvent;

      /*If the event from the mouse hover didnt happen, return none */
      if (!originalEvent) {return;}

      /*Position the tooltip slightly offset from the mouse cursor */
      tooltip.style.left = `${originalEvent.clientX + 12}px`;
      tooltip.style.top = `${originalEvent.clientY + 12}px`;
    }

    /* Function for showing tooltip */
    function showTooltip(html, event) {

      /* Remove any existing tooltip before showing a new one */
      removeTooltip();

      /* Build the tooltip element using the provided HTML and style it appropriately using the supplementary CSS class */
      const tooltip = document.createElement("div");
      tooltip.className = "graph-tooltip";
      tooltip.innerHTML = html;
      document.body.appendChild(tooltip);
      activeTooltip = tooltip;

      /* Position the tooltip relative to the mouse event */
      positionTooltip(event, tooltip);
    }


    /* Function for moving an active tooltip if the mouse moves */
    function moveTooltip(event) {
      if (!activeTooltip) {return;}
      positionTooltip(event, activeTooltip);
    }


    /* Function for handling a node click */
    function handleNodeClick(event) {

      /* Extract the node and its ID from the event */
      const node = event.target;
      const rawId = node.data("id");
      const id = Number(rawId);

      /* Log the node click for debugging purposes */
      console.log(
        "GRAPH NODE CLICK:",
        {
          id,
          rawId,
          title: node.data("title"),
          artist: node.data("artist"),
          type: node.data("type"),
          data: node.data(),
        }
      );


      removeTooltip();

      /* Call the explore song function with the clicked node's ID*/
      const callback = onNodeClickRef.current;
      callback(id);
      
    }

    /*Function for handling a node mouse over */
    function handleNodeMouseOver(event) {

      /* Extract relevant data from the node, these will be used to populate the tooltip */
      const node = event.target;
      const title = node.data("title");
      const artist = node.data("artist");
      const type = node.data("type");
      const neighbours = node.data("neighbours");

      let hopText = "Centre song";
      if (type === "hop_1") {hopText ="1-hop neighbour";}
      if (type === "hop_2") {hopText ="2-hop neighbour";}

      let neighbourText = "";

      /* If the node has neighbours, prepare the neighbour text for the tooltip */
      if (Array.isArray(neighbours) && neighbours.length > 0) {
        neighbourText = `
          <br />
          <small>
            Connected neighbours: ${neighbours.length}
          </small>
        `;
      }

      /* Show the tooltip with the prepared content */
      showTooltip(
        `
          <strong>
            ${escapeHtml(title)}
          </strong>
          <br />
          ${escapeHtml(artist)}
          <br />
          <small>
            ${hopText}
          </small>
          ${neighbourText}
        `,
        event
      );
    }


    /* Functions for handling a node mouse move */
    function handleNodeMouseMove(event) {moveTooltip(event);}
    function handleNodeMouseOut() {removeTooltip();}


    /* Functions for displaying edge tooltips */
    function handleEdgeMouseOver(event) {
      const edge = event.target;
      const weight = Number(edge.data("weight"));
      const hop = edge.data("hop");
      const sourceTitle = edge.data("sourceTitle");
      const sourceArtist = edge.data("sourceArtist");
      const targetTitle = edge.data("targetTitle");
      const targetArtist = edge.data("targetArtist");

      /*If they exist, prepare the source and target text for the tooltip */
      const sourceText = sourceTitle ? `${sourceTitle} — ${sourceArtist}` : "";
      const targetText = targetTitle ? `${targetTitle} — ${targetArtist}`: "";
      const connectionText =
        sourceText && targetText
          ? `
              <br />
              <small>
                ${escapeHtml(sourceText)}
                <br />
                ↕
                <br />
                ${escapeHtml(targetText)}
              </small>
            `
          : "";

      /* Show the tooltip for the edge */
      showTooltip(
        `
          <strong>
            Similarity
          </strong>
          <br />
          ${
            Number.isFinite(weight)
              ? weight.toFixed(3)
              : "—"
          }
          <br />
          <small>
            ${
              hop === "1"
                ? "1-hop connection"
                : "2-hop connection"
            }
          </small>
          ${connectionText}
        `,
        event
      );
    }

    /* Functions for handling tooltip for edges when the mouse moves away */
    function handleEdgeMouseMove(event) {moveTooltip(event);}
    function handleEdgeMouseOut() {removeTooltip();}


 
  /*Connect the Cytospace events to their respective functions*/
    cy.on("tap", "node", handleNodeClick);
    cy.on("mouseover", "node", handleNodeMouseOver);
    cy.on("mousemove", "node", handleNodeMouseMove);
    cy.on("mouseout", "node", handleNodeMouseOut);
    cy.on("mouseover", "edge", handleEdgeMouseOver);
    cy.on("mousemove", "edge",  handleEdgeMouseMove);
    cy.on("mouseout", "edge", handleEdgeMouseOut);

    /*Remove tooltip if the mouse leaves the container */
    function handleContainerMouseLeave() {removeTooltip();}
    container.addEventListener("mouseleave", handleContainerMouseLeave);


    /*Once the component is unmounted, clean up event listeners and destroy the Cytoscape instance */
    return () => {
      removeTooltip();
      container.removeEventListener("mouseleave", handleContainerMouseLeave);
      cy.removeListener("tap", "node", handleNodeClick);
      cy.removeListener("mouseover", "node", handleNodeMouseOver);
      cy.removeListener("mousemove", "node", handleNodeMouseMove);
      cy.removeListener("mouseout", "node", handleNodeMouseOut);
      cy.removeListener("mouseover", "edge", handleEdgeMouseOver);
      cy.removeListener("mousemove", "edge", handleEdgeMouseMove);
      cy.removeListener("mouseout", "edge", handleEdgeMouseOut);
      cy.destroy();
      cyRef.current = null;
    };
  }, []);



/*Function to update the graph when the data changes*/
  useEffect(() => {

    /*The existing cytoscape graph*/
    const cy = cyRef.current;

    /*If the graph data or graph object are missing then return none */
    if (!cy || !graphData) {return;}

    /*Retrieve current nodes and edges with added safety checks */
    const graphNodes = Array.isArray(graphData.nodes) ? graphData.nodes : [];
    const graphEdges = Array.isArray(graphData.edges) ? graphData.edges : [];



    /*Build Cytoscape nodes from the graph data */
    const nodes = graphNodes.map(
      (node) => ({
          data: {
            id: String(node.id),
            label:`${node.title || "Unknown"} \n ${node.artist_name || "Unknown artist"}`,
            title: node.title || "Unknown",
            artist: node.artist_name || "Unknown artist",
            type: node.type || "hop_2",
            neighbours: Array.isArray(node.neighbours) ? node.neighbours : [],
          },
        })
      );

    /*Build Cytoscape edges from the graph data */
    const edges = graphEdges.map(
        (edge, index) => {

          /*Retrieve the source and target nodes for this edge */
          const sourceNode =
            graphNodes.find((node) => String(node.id) === String(edge.source));
          const targetNode =
            graphNodes.find((node) => String(node.id) === String(edge.target));
          
          /*Assume second hop by default, then check if either node is a query node and set hop to one*/
          let hop = "2";
          if (sourceNode?.type === "query" || targetNode?.type === "query") {hop = "1";}

          const weight = Number(edge.weight);

          /*Return the constructed data as a Cytoscape object */
          return {
            data: {
              id:`edge-${String(edge.source)}-${String(edge.target)}-${index}`,
              source: String(edge.source),
              target: String(edge.target),
              weight,
              label: Number.isFinite(weight) ? weight.toFixed(3): "",
              hop,
              sourceTitle: sourceNode?.title || "",
              sourceArtist: sourceNode?.artist_name || "",
              targetTitle: targetNode?.title || "",
              targetArtist: targetNode?.artist_name || "",
            },
          };
        }
      );


    /* Remove existing graph elements and replace them with the new ones*/
    cy.elements().remove();
    cy.add([...nodes, ...edges,]);

    /*If there are no nodes to display, return none */
    if (!nodes.length) {return;}



    /*The section below focuses on the layout of teh graph.
    More specifically, it arranges the query node at the center,
    the first hop nodes in an inner ring,
    and the second hop nodes in an outer ring.
    By doing so, it should produce a graph with relatively little clutter from overlap.*/

    /* Get references to the query node, first hop nodes, and second hop nodes */
    const queryNode = cy.nodes('node[type="query"]');
    const hop1 = cy.nodes('node[type="hop_1"]');
    const hop2 = cy.nodes('node[type="hop_2"]');

    /* Get container dimensions if they exist, otherwise use default values */
    const width = containerRef.current?.clientWidth || 1000;
    const height = containerRef.current?.clientHeight || 700;

    /* Get container centre coordinates*/
    const centreX = width / 2;
    const centreY = height / 2;

    /* Get the radii for the one and two hop node rings */
    const innerRadius =Math.min(width, height) * 0.30;
    const outerRadius =Math.min(width, height) * 0.46;

    /*Stick query node at the centre of the graph */
    queryNode.positions({x: centreX, y: centreY});

    /*Position the first hop nodes in a ring around the query node */
    positionRing(
      hop1,
      centreX,
      centreY,
      innerRadius
    );

    /*Position the second hop nodes in a ring around the query node */
    positionRing(
      hop2,
      centreX,
      centreY,
      outerRadius
    );


    /*Adjust the viewport to fit all elements within the container.
    This comes with some padding and a slight zoom out. */
    cy.fit(cy.elements(), 80);
    cy.zoom(cy.zoom() * 0.90);

  }, [graphData]); /*Recall these effects whenever the graph data changes */

/* Render the graph */
  return (
    <div
      ref={containerRef}
      className="graph-container"
    />
  );
}


/*This is the function used above for producing a ring layout for the nodes of a given hop */
function positionRing(
  collection,
  centreX,
  centreY,
  radius
) {
  
  /*Convert cytoscape collection object to an array*/
  const nodes = collection.toArray();

  /*Return none if no nodes in ring */
  if (!nodes.length) {return;}

  /*Calculate the angle covered between each node in the ring */
  const angleStep = (Math.PI * 2) / nodes.length;

  /*Position each node in the ring */
  nodes.forEach(
    (node, index) => {

      /*Go around the circumference of the ring using the calculated angle */
      const angle = index * angleStep - Math.PI / 2;

      /*Calculate the position of the node on the ring */
      node.position({
        x: centreX + Math.cos(angle) * radius,
        y: centreY + Math.sin(angle) * radius,
      });
    }
  );
}


/*This function escapes HTML special characters in a given string.
This is important for the tooltip rendering in the graph where values may contain HTML special characters */
function escapeHtml(value) {
  return String(value ?? "") // Use empty string if value is null or undefined
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

/*Make the graph available to other files*/
export default Graph;