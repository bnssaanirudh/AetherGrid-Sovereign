"use client";

import React, { useState } from 'react';
import DeckGL from '@deck.gl/react';
import { ScatterplotLayer, ArcLayer } from '@deck.gl/layers';
import { Map } from 'react-map-gl/mapbox';
import 'mapbox-gl/dist/mapbox-gl.css';

// Initial viewport settings
const INITIAL_VIEW_STATE = {
  longitude: 0,
  latitude: 20,
  zoom: 1.5,
  pitch: 30,
  bearing: 0
};

// Dummy data for visual presentation
const DUMMY_NODES = [
  { id: '1', position: [-74.006, 40.7128], color: [0, 240, 255], size: 100 },
  { id: '2', position: [-73.98, 40.73], color: [255, 59, 59], size: 150 }, // Failed node
  { id: '3', position: [-74.02, 40.70], color: [0, 240, 255], size: 80 },
  { id: '4', position: [-73.95, 40.75], color: [176, 80, 255], size: 120 }, // High uncertainty
];

const DUMMY_EDGES = [
  { source: [-74.006, 40.7128], target: [-73.98, 40.73], color: [255, 59, 59, 150] }, // Cascade path
  { source: [-74.006, 40.7128], target: [-74.02, 40.70], color: [0, 240, 255, 100] },
];

export default function DigitalTwinMap({ certificate }: { certificate?: any }) {
  const [viewState, setViewState] = useState(INITIAL_VIEW_STATE);

  // Extract background nodes to overlay dynamic data
  const bgNodes = certificate?.graph_visualization?.nodes || [];
  const bgEdges = certificate?.graph_visualization?.edges || [];

  let nodes = DUMMY_NODES;
  let edges = DUMMY_EDGES;
  let blastRadiusData = [];

  if (certificate) {
    // Dynamic overlay based on returned nodes
    nodes = bgNodes.slice(0, 10).map((n: any, i: number) => ({
      id: `trigger_${i}`,
      position: n.position,
      color: [255, 30, 30],
      size: 200
    }));
    
    edges = bgEdges.slice(0, 10).map((e: any) => ({
      source: e.source,
      target: e.target,
      color: [255, 30, 30, 180]
    }));

    const rad = certificate.prediction?.predicted_radius_graph || 15.0;
    // Draw blast radius around the active nodes
    blastRadiusData = nodes.map((n: any) => ({
      position: n.position,
      radius: rad * 200 // scaled for visibility at global zoom
    }));
  }

  const layers = [
    new ArcLayer({
      id: 'background-edges',
      data: certificate?.graph_visualization?.edges || [],
      getSourcePosition: (d: any) => d.source,
      getTargetPosition: (d: any) => d.target,
      getSourceColor: [0, 240, 255, 30], // faint blue laser lines
      getTargetColor: [0, 240, 255, 30],
      getWidth: 1,
    }),
    new ScatterplotLayer({
      id: 'background-nodes',
      data: certificate?.graph_visualization?.nodes || [],
      getPosition: (d: any) => d.position,
      getFillColor: [0, 150, 255, 100], // dim blue dots
      getRadius: 50,
      radiusUnits: 'meters',
      stroked: false,
    }),
    new ArcLayer({
      id: 'cascade-paths',
      data: edges,
      getSourcePosition: (d: any) => d.source,
      getTargetPosition: (d: any) => d.target,
      getSourceColor: (d: any) => d.color,
      getTargetColor: (d: any) => d.color,
      getWidth: 3,
    }),
    new ScatterplotLayer({
      id: 'infrastructure-nodes',
      data: nodes,
      getPosition: (d: any) => d.position,
      getFillColor: (d: any) => d.color,
      getRadius: (d: any) => d.size,
      radiusMinPixels: 4,
      radiusMaxPixels: 20,
      opacity: 0.8,
      stroked: true,
      getLineColor: [255, 255, 255, 100],
      lineWidthMinPixels: 1,
      pickable: true,
    }),
    new ScatterplotLayer({
      id: 'blast-radius',
      data: blastRadiusData,
      getPosition: (d: any) => d.position,
      getFillColor: [255, 59, 59, 30],
      getRadius: (d: any) => d.radius,
      radiusUnits: 'meters',
      stroked: true,
      getLineColor: [255, 59, 59, 200],
      lineWidthMinPixels: 2,
    })
  ];

  return (
    <div style={{ width: '100%', height: '100%', position: 'relative' }}>
      <DeckGL
        layers={layers}
        initialViewState={INITIAL_VIEW_STATE}
        controller={true}
        onViewStateChange={({ viewState }) => setViewState(viewState as any)}
      >
        <Map
          reuseMaps
          mapStyle="mapbox://styles/mapbox/satellite-streets-v12"
          mapboxAccessToken={process.env.NEXT_PUBLIC_MAPBOX_TOKEN || "dummy_token"}
        />
      </DeckGL>
    </div>
  );
}
