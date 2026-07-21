"use client";

import React, { useState } from 'react';
import DeckGL from '@deck.gl/react';
import { ScatterplotLayer, ArcLayer } from '@deck.gl/layers';
import { Map } from 'react-map-gl/maplibre';
import 'maplibre-gl/dist/maplibre-gl.css';

// Initial viewport settings
const INITIAL_VIEW_STATE = {
  longitude: -74.006,
  latitude: 40.7128,
  zoom: 11,
  pitch: 45,
  bearing: 0
};

// Dark matter style from Carto as a free MapLibre base map
const MAP_STYLE = 'https://basemaps.cartocdn.com/gl/dark-matter-gl-style/style.json';

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

export default function DigitalTwinMap() {
  const [viewState, setViewState] = useState(INITIAL_VIEW_STATE);

  const layers = [
    new ArcLayer({
      id: 'cascade-paths',
      data: DUMMY_EDGES,
      getSourcePosition: d => d.source,
      getTargetPosition: d => d.target,
      getSourceColor: d => d.color,
      getTargetColor: d => d.color,
      getWidth: 3,
    }),
    new ScatterplotLayer({
      id: 'infrastructure-nodes',
      data: DUMMY_NODES,
      getPosition: d => d.position,
      getFillColor: d => d.color,
      getRadius: d => d.size,
      radiusMinPixels: 4,
      radiusMaxPixels: 20,
      opacity: 0.8,
      stroked: true,
      getLineColor: [255, 255, 255, 100],
      lineWidthMinPixels: 1,
      pickable: true,
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
          mapStyle={MAP_STYLE}
        />
      </DeckGL>
    </div>
  );
}
