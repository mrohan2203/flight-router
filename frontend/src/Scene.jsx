import React from 'react';
import Aircraft from './Aircraft';

export default function Scene({ telemetry, conflicts, onSelectAircraft }) {
  return (
    <>
      {[10, 20, 30].map((radius, idx) => (
        <mesh key={idx} rotation={[-Math.PI / 2, 0, 0]} position={[0, 0.02, 0]}>
          <ringGeometry args={[radius, radius + 0.1, 64]} />
          <meshBasicMaterial color="#00ffcc" transparent opacity={0.15} />
        </mesh>
      ))}

      <mesh rotation={[-Math.PI / 2, 0, 0]} position={[0, 0.01, 0]}>
        <planeGeometry args={[100, 0.1]} />
        <meshBasicMaterial color="#00ffcc" transparent opacity={0.1} />
      </mesh>
      <mesh rotation={[-Math.PI / 2, 0, Math.PI / 2]} position={[0, 0.01, 0]}>
        <planeGeometry args={[100, 0.1]} />
        <meshBasicMaterial color="#00ffcc" transparent opacity={0.1} />
      </mesh>

      {telemetry.map(ac => (
        <Aircraft
          key={ac.id}
          data={ac}
          isConflicted={conflicts.some(c => c.includes(ac.id))}
          onClick={() => onSelectAircraft(ac)}
        />
      ))}
    </>
  );
}