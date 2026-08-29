import {
  useEffect,
  useRef,
} from "react";

import cytoscape from "cytoscape";

/*ShortestPathGraph function renders a Cytoscape graph for visualizing the shortest path between nodes.
 
Args:
 graphData: The data representing the graph structure.
  onNodeClick: Callback function invoked when a node is clicked.
 */

function ShortestPathGraph({
  graphData,
  onNodeClick,
}) {

  /*Reference to the container element for the Cytoscape graph, the actual cytoscape instance, and the onNodeClick callback*/
  const containerRef = useRef(null);
  const cyRef = useRef(null);
  const onNodeClickRef = useRef(onNodeClick);

  /* Update the function reference for the onNodeClick callback whenever it changes */
  useEffect(() => {onNodeClickRef.current = onNodeClick;}, [onNodeClick]);

  /* Create the Cytoscape instance when the component mounts, but not if the container element is not available */
  useEffect(() => {if (!containerRef.current) {return;}


    const cy =
      cytoscape({
        container: containerRef.current,
        elements: [],

        /* Cytoscape graph styling for nodes and edges */

        /*Generic Node Styling*/
        style: [
          {
            selector: "node",
            style: {
              label: "data(label)",
              "text-wrap": "wrap",
              "text-max-width": "100px",
              "text-valign": "center",
              "text-halign": "center",
              "background-color": "#252b35",
              width: "46px",
              height: "46px",
              "font-size": "8px",
              "font-family": "monospace",
              color: "#c8d1dc",
              "border-width": "1px",
              "border-color": "#4a5563",
              "overlay-opacity": 0,
            },
          },

          /* Path nodes */
          {
            selector: 'node[path="true"]',
            style: {
              "background-color": "#243845",
              color: "#d8f3fa",
              width: "58px",
              height: "58px",
              "font-size": "8px",
              "border-width": "2px",
              "border-color": "#247f9d",
            },
          },


          /* Start Node */
          {
            selector: 'node[pathStart="true"]',
            style: {
              "background-color": "#102b36",
              color: "#e7f7fb",
              width: "76px",
              height: "76px",
              "font-size": "10px",
              "border-width": "2px",
              "border-color": "#00a8d8",

            },

          },

          /* End Node */
          {
            selector: 'node[pathEnd="true"]',
            style: {
              "background-color": "#163b4d",
              color: "#dff7ff",
              width: "76px",
              height: "76px",
              "font-size": "10px",
              "border-width": "2px",
              "border-color": "#4dd9ff",
            },
          },


          /* Edges */

          {
            selector: "edge",
            style: {
              width: "mapData(weight, 0.5, 1, 1, 4)",
              "line-color": "#36414e",
              "curve-style": "bezier",
              "target-arrow-shape": "none",
              label: "data(label)",
              "font-size": "8px",
              "font-family": "monospace",
              color: "#687586",
              "text-background-color": "#11161d",
              "text-background-opacity": 1,
              "text-background-padding": "3px",
              "text-border-width": 0,
              "overlay-opacity": 0,
            },
          },

          /* Path edges */
          {
            selector: 'edge[path="true"]',
            style: {
              width: "mapData(weight, 0.5, 1, 2, 5)",
              "line-color": "#247f9d",
              "curve-style": "bezier",
              "target-arrow-shape": "none",
              label: "data(label)",
              "font-size": "8px",
              "font-family": "monospace",
              color: "#8fa6b8",
              "text-background-color": "#11161d",
              "text-background-opacity": 1,
              "text-background-padding": "3px",
              opacity: 1,
            },
          },


          /* Selected node */
          {
            selector: "node:selected",
            style: {
              "border-width": "3px",
              "border-color": "#66d9f5",
            },
          },


          /* Active node */
          {
            selector: "node:active",
            style: {
              "border-width": "3px",
              "border-color": "#66d9f5",
            },
          },

          /* Active edge */
          {
            selector: "edge:active",
            style: {
              "line-color":
                "#66d9f5",
              opacity: 1,
            },
          },
        ],

        /* Inform of manual layout (even though it sais "preset") */
        layout: {name: "preset",},
        minZoom: 0.25,
        maxZoom: 2.5,
      });


    cyRef.current = cy;


    /*Handle node click event, passing the node ID to the callback */
    const handleNodeClick =
      (event) => {
        const node = event.target;
        const id = Number(node.data("id"));
        onNodeClickRef.current?.(id);
      };


    cy.on("tap", "node", handleNodeClick);


    /* Cleanup function for when the component is unmounted */
    return () => {
      cy.removeListener("tap", "node", handleNodeClick);
      cy.destroy();
      cyRef.current = null;
    };

  }, []);

  /*Update function for whenever the graph data changes */
  useEffect(() => {

    const cy = cyRef.current;
    
    /*If there is no Cytoscape instance or no graph data, return none*/
    if (!cy || !graphData) {return;}

    /*Format nodes for Cytoscape */
    const nodes =
      (graphData.nodes || []).map(
        (node) => {

          /* If the node already has data, use it and don't rebuild it */
          if (node.data) {
            const data ={...node.data,};
            if (data.path === undefined) {data.path ="true";}
            if (data.pathStart === undefined) {data.pathStart =data.type === "path-start" ? "true" : "false";}
            if (data.pathEnd === undefined) {data.pathEnd = data.type === "path-end" ? "true" : "false";}
            return {data};
          }

          /*Otherwise build the node data from scratch */
          const id = String(node.id);
          const type = node.type || "path";

          return {
            data: {
              id,
              label: `${node.title || "Unknown"} \n ${node.artist_name || "Unknown artist"}`,
              title: node.title,
              artist: node.artist_name,
              path: "true",
              pathStart: type === "start" ? "true" : "false",
              pathEnd: type === "end" ? "true" : "false",

            },
          };
        }
      );


    /*Format edges for Cytoscape */
    const edges =
      (graphData.edges || []).map(
        (edge, index) => {
          /*If the edge already has data, use it and don't rebuild it */
          if (edge.data) {
            const data ={...edge.data,};
            data.source =String(data.source);
            data.target =String(data.target);
            data.path = "true";
            const weight = Number(data.similarity);
            data.weight = weight;
            data.label = weight.toFixed(3);
            return {data};
          }

          /*Otherwise build the edge data from scratch */
          const source = String(edge.source);
          const target = String(edge.target);
          const similarity = Number(edge.similarity);
          const cost = Number(edge.cost);
          const weight = similarity;

          return {
            data: {
              id:`shortest-edge-${index}`,
              source,
              target,
              similarity,
              cost,
              weight,
              label: Number.isFinite(weight) ? weight.toFixed(3) : "",
              path: "true",
            },
          };
        }
      );


    /*Replace existing elements in the Cytoscape instance with the new nodes and edges */
    cy.elements().remove();
    cy.add([...nodes, ...edges]);

    /* If there are no nodes to display, return none */
    if (!nodes.length) {return;}

    
    /*Code below positions the nodes in a gentle alternating swerve pattern */

    const nodeElements = cy.nodes().toArray(); // Convert Cytoscape nodes to a JavaScript arrayon

    /*Calculate and set up the framing for the graph*/
    const width = containerRef.current?.clientWidth || 1000;
    const height = containerRef.current?.clientHeight || 600;
    const horizontalPadding = 100;
    const usableWidth = Math.max(300, width - horizontalPadding * 2);

    /*Calculate and set up node postions for the alternating swerve layout */
    const nodeCount = nodeElements.length;
    const spacing = nodeCount > 1 ? usableWidth / (nodeCount - 1): 0; // horizontal spacing between nodes
    const centreY = height / 2;
    const swerve = Math.min(75, height * 0.13); // vertical swerve between nodes

    /*Place each node*/
    nodeElements.forEach(
      (node, index) => {

        let y = centreY;

        if (nodeCount >= 3) {// Don't swerve if there are only two nodes
          if (index % 2 === 1) {y = centreY - swerve;} // Odd-indexed nodes swerve upwards
          else {y = centreY + swerve;} // Even-indexed nodes swerve downwards
        }


        /*Start and end nodes are placed closer to the centre */
        if (index === 0 || index === nodeCount - 1) {y = centreY;}
        const x = nodeCount === 1 ? width / 2 : horizontalPadding + index * spacing;


        node.position({x,y});

      }
    );



    /*Adjust the viewport with some light padding and zoom out */
    cy.resize();
    cy.fit(cy.elements(),80);
    cy.zoom(cy.zoom() * 0.9);

  }, [graphData]); /* Re-render the graph whenever the graphData changes */

  /*HTML for the actual graph render */
  return (
    <div
      ref={containerRef}
      className="graph-container shortest-path-graph"
      style={{
        width: "100%",
        height: "600px",
      }}
    />
  );
}


export default ShortestPathGraph;