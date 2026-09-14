import React, { useState, useEffect } from 'react';
import { Canvas } from '@react-three/fiber';
import { OrbitControls } from '@react-three/drei';
import Scene from './Scene';

export default function App() {
  const [telemetry, setTelemetry] = useState([]);
  const [conflicts, setConflicts] = useState([]);
  const [selectedAircraft, setSelectedAircraft] = useState(null);
  const [activeAirport, setActiveAirport] = useState("LHR");
  const [spokenCache, setSpokenCache] = useState(new Set());

  useEffect(() => {
    const wsUrl = import.meta.env.VITE_WS_URL 
      ? `${import.meta.env.VITE_WS_URL}/${activeAirport}`
      : `ws://localhost:8000/ws/telemetry/${activeAirport}`;
      
    const ws = new WebSocket(wsUrl);

    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        if (data.telemetry) setTelemetry(data.telemetry);
        if (data.conflicts) setConflicts(data.conflicts);
        
        if (data.broadcasts && data.broadcasts.length > 0) {
          data.broadcasts.forEach((phrase) => {
            setSpokenCache((prevCache) => {
              if (!prevCache.has(phrase)) {
                const utterance = new SpeechSynthesisUtterance(phrase);
                utterance.pitch = 0.9;
                utterance.rate = 1.2;
                window.speechSynthesis.speak(utterance);
                
                return new Set(prevCache).add(phrase);
              }
              return prevCache;
            });
          });
        }
      } catch (err) {
        console.error('Error parsing telemetry JSON:', err);
      }
    };

    ws.onerror = (err) => console.error('WebSocket encountered an error:', err);
    ws.onclose = () => console.log('WebSocket disconnected');

    return () => ws.close();
  }, [activeAirport]);

  useEffect(() => {
    if (selectedAircraft) {
      const refreshed = telemetry.find((ac) => ac.id === selectedAircraft.id);
      if (refreshed) {
        setSelectedAircraft(refreshed);
      }
    }
  }, [telemetry, selectedAircraft]);

  return (
    <div style={{ width: '100vw', height: '100vh', background: '#050a0a', position: 'relative', overflow: 'hidden', fontFamily: 'monospace' }}>
      <Canvas camera={{ position: [0, 75, 75], fov: 50 }}>
        <ambientLight intensity={0.8} />
        <pointLight position={[10, 20, 10]} intensity={1.2} />
        <OrbitControls maxPolarAngle={Math.PI / 2.1} minDistance={10} maxDistance={250} />
        <Scene
          telemetry={telemetry}
          conflicts={conflicts}
          onSelectAircraft={setSelectedAircraft}
        />
      </Canvas>

      <div
        style={{
          position: 'absolute', top: 20, left: 20, width: 340,
          background: 'rgba(5, 15, 15, 0.88)', border: '1px solid #1a4d40',
          borderRadius: 8, padding: 18, color: '#e0e0e0',
          boxShadow: '0 8px 32px rgba(0, 0, 0, 0.6)', backdropFilter: 'blur(6px)',
          zIndex: 10, maxHeight: '90vh', display: 'flex', flexDirection: 'column'
        }}
      >
        <div style={{ overflowY: 'auto', paddingRight: 8 }}>
          <div style={{ fontSize: 16, fontWeight: 'bold', color: '#ffffff', marginBottom: 12 }}>
            ATC Agent Log
          </div>

          <select
            value={activeAirport}
            onChange={(e) => setActiveAirport(e.target.value)}
            style={{
              width: '100%', background: 'rgba(0, 0, 0, 0.5)', color: '#00ffcc',
              border: '1px solid #1a4d40', padding: '6px', marginBottom: '12px',
              fontFamily: 'monospace', borderRadius: '4px', cursor: 'pointer'
            }}
          >
            <option value="LHR">LHR - London Heathrow</option>
            <option value="JFK">JFK - New York</option>
            <option value="SIN">SIN - Singapore Changi</option>
            <option value="MAA">MAA - Chennai International</option>
            <option value="DXB">DXB - Dubai</option>
          </select>

          <div style={{ marginBottom: 14 }}>
            <div style={{ color: '#00ffcc', fontWeight: 'bold', fontSize: 13, marginBottom: 6 }}>
              Active Stack ({telemetry.length}):
            </div>
            <div style={{ fontSize: 12, lineHeight: 1.6 }}>
              {telemetry.length === 0 ? (
                <span style={{ color: '#666' }}>Scanning airspace...</span>
              ) : (
                telemetry.map((ac) => (
                  <div key={ac.id} style={{ display: 'flex', justifyContent: 'space-between' }}>
                    <span style={{ color: '#00ffcc', fontWeight: 'bold' }}>{ac.id}</span>
                    <span style={{ color: '#888' }}>| {ac.z}ft | {ac.wake_category}</span>
                  </div>
                ))
              )}
            </div>
          </div>

          <div style={{ height: 1, background: '#1a4d40', margin: '12px 0' }} />

          <div style={{ marginBottom: 14 }}>
            <div style={{ color: '#ffffff', fontWeight: 'bold', fontSize: 13, marginBottom: 6 }}>
              Active Conflicts / System Alerts:
            </div>
            <div style={{ fontSize: 12, lineHeight: 1.5 }}>
              {conflicts.length === 0 ? (
                <span style={{ color: '#888' }}>No active conflicts. Airspace clear.</span>
              ) : (
                conflicts.map((conflict, idx) => (
                  <div key={idx} style={{ color: '#ff4444', marginBottom: 6 }}>
                    • {conflict}
                  </div>
                ))
              )}
            </div>
          </div>

          {selectedAircraft && (
            <>
              <div style={{ height: 1, background: '#1a4d40', margin: '12px 0' }} />
              <div>
                <div style={{ color: '#ffffff', fontWeight: 'bold', fontSize: 13, marginBottom: 8 }}>
                  Target Inspector:
                </div>
                <div style={{ fontSize: 12, lineHeight: 1.8 }}>
                  <div><span style={{ color: '#888' }}>Callsign:</span> <span style={{ color: '#00ffcc', fontWeight: 'bold' }}>{selectedAircraft.id}</span></div>
                  <div><span style={{ color: '#888' }}>Operator:</span> <span style={{ color: '#00ffcc' }}>{selectedAircraft.operator}</span></div>
                  <div><span style={{ color: '#888' }}>Altitude:</span> <span style={{ color: '#00ffcc' }}>{selectedAircraft.z} ft</span></div>
                  <div><span style={{ color: '#888' }}>Category:</span> <span style={{ color: '#00ffcc' }}>{selectedAircraft.wake_category}</span></div>
                </div>
                <button
                  onClick={() => setSelectedAircraft(null)}
                  style={{
                    marginTop: 10, padding: '5px 12px', background: 'transparent',
                    border: '1px solid #00ffcc', color: '#00ffcc', borderRadius: 4,
                    fontSize: 11, fontFamily: 'monospace', cursor: 'pointer', transition: 'all 0.2s'
                  }}
                >
                  Clear Selection
                </button>
              </div>
            </>
          )}
        </div>

        <div style={{ height: 1, background: '#1a4d40', margin: '16px 0' }} />
        <button 
          onClick={() => window.open('http://localhost:8000/download-report', '_blank')}
          style={{
            width: '100%', padding: '8px 0', background: 'rgba(0, 255, 204, 0.1)',
            border: '1px solid #00ffcc', color: '#00ffcc', borderRadius: 4,
            fontSize: 13, fontWeight: 'bold', fontFamily: 'monospace',
            cursor: 'pointer', transition: 'all 0.2s', flexShrink: 0
          }}
        >
          [ Generate Shift Report ]
        </button>
      </div>
    </div>
  );
}