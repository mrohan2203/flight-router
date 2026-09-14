import React, { useRef, useMemo } from 'react';
import { useFrame } from '@react-three/fiber';
import * as THREE from 'three';

export default function Aircraft({ data, isConflicted, onClick }) {
  const meshRef = useRef();

  const targetPosition = useMemo(
    () => new THREE.Vector3(data.x, data.z / 1000, -data.y),
    [data.x, data.y, data.z]
  );

  useFrame((state, delta) => {
    if (meshRef.current) {
      meshRef.current.position.lerp(targetPosition, delta * 0.5); 
    }
  });

  return (
    <group ref={meshRef} position={[data.x, data.z / 1000, -data.y]} onClick={(e) => { e.stopPropagation(); onClick(); }}>
      <mesh rotation={[-Math.PI / 2, 0, 0]}>
        <coneGeometry args={[0.4, 1.2, 4]} />
        <meshStandardMaterial 
          color={isConflicted ? "#ff4444" : "#00ffcc"} 
          emissive={isConflicted ? "#ff0000" : "#00ffcc"}
          emissiveIntensity={0.8}
        />
      </mesh>
      
      <mesh>
        <sphereGeometry args={[isConflicted ? 2.5 : 1.5, 16, 16]} />
        <meshBasicMaterial 
          color={isConflicted ? "#ff4444" : "#00ffcc"} 
          wireframe 
          transparent 
          opacity={0.3} 
        />
      </mesh>
    </group>
  );
}