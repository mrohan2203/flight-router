// 1 Three.js unit = 1 Nautical Mile (Lateral)
export const scaleLateral = (nm) => nm;

// 1 Three.js unit = 1000 feet (Vertical)
// This slightly exaggerates vertical scale for visual clarity on screen
export const scaleVertical = (feet) => feet / 1000; 
