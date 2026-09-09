import { Suspense, useMemo, useRef } from 'react';
import { Canvas, useFrame } from '@react-three/fiber';
import { OrbitControls, Html, ContactShadows } from '@react-three/drei';
import * as THREE from 'three';
import { heatmapVertexShader, heatmapFragmentShader, HEATMAP_MAX_PROFILE } from './heatmapShader';
import { useSimulation } from '../../context/SimulationContext';

const SIZE_SCALE = { small: 0.78, medium: 1, large: 1.32 };

function useShelterGeometry(shape, size) {
  return useMemo(() => {
    const scale = SIZE_SCALE[size] || 1;
    let geometry;

    if (shape === 'dome') {
      geometry = new THREE.SphereGeometry(1.15 * scale, 40, 24, 0, Math.PI * 2, 0, Math.PI * 0.52);
      geometry.translate(0, 0, 0);
    } else if (shape === 'custom') {
      geometry = new THREE.IcosahedronGeometry(1.15 * scale, 2);
      // flatten the base so it sits on the ground plausibly
      const pos = geometry.attributes.position;
      for (let i = 0; i < pos.count; i++) {
        if (pos.getY(i) < -0.15 * scale) pos.setY(i, -0.15 * scale);
      }
      geometry.computeVertexNormals();
    } else {
      const w = 1.9 * scale;
      const h = 1.3 * scale;
      const d = 1.5 * scale;
      const box = new THREE.BoxGeometry(w, h, d);
      box.translate(0, h / 2, 0);
      const roof = new THREE.ConeGeometry(Math.max(w, d) * 0.78, 0.7 * scale, 4);
      roof.rotateY(Math.PI / 4);
      roof.translate(0, h + 0.35 * scale, 0);
      geometry = mergeGeometries([box, roof]);
    }

    geometry.computeBoundingBox();
    return geometry;
  }, [shape, size]);
}

// Minimal manual merge (avoids pulling in BufferGeometryUtils for two shapes).
function mergeGeometries(geoms) {
  const merged = new THREE.BufferGeometry();
  const positions = [];
  const normals = [];
  geoms.forEach((g) => {
    // BoxGeometry/ConeGeometry are indexed — flatten to non-indexed first,
    // otherwise reading .position.array sequentially produces garbage triangles.
    const flat = g.index ? g.toNonIndexed() : g;
    flat.computeVertexNormals();
    const pos = flat.attributes.position.array;
    const norm = flat.attributes.normal.array;
    for (let i = 0; i < pos.length; i++) positions.push(pos[i]);
    for (let i = 0; i < norm.length; i++) normals.push(norm[i]);
  });
  merged.setAttribute('position', new THREE.Float32BufferAttribute(positions, 3));
  merged.setAttribute('normal', new THREE.Float32BufferAttribute(normals, 3));
  return merged;
}

function ShelterMesh() {
  const { shape, size, result, wallLayers, materials } = useSimulation();
  const geometry = useShelterGeometry(shape, size);
  const materialRef = useRef();

  const avgTemp = useMemo(() => {
    if (!result?.insideTemp?.values?.length) return 0;
    const vals = result.insideTemp.values;
    return vals.reduce((a, b) => a + b, 0) / vals.length;
  }, [result]);

  const tempNorm = THREE.MathUtils.clamp((avgTemp + 20) / 50, 0, 1);

  // Real (or synthetic-fallback) floor-to-roof temperature stratification —
  // see result.verticalProfile, sourced from ANSYS's actual per-height
  // nodal field when live, or a physics-informed synthetic profile in mock
  // mode. Normalized onto the same 0-1 color scale as uTempNorm.
  const profile = useMemo(() => {
    const points = result?.verticalProfile;
    if (!Array.isArray(points) || points.length < 2) return null;
    const sorted = [...points].sort((a, b) => a.heightFrac - b.heightFrac);
    const heights = sorted.map((p) => THREE.MathUtils.clamp(p.heightFrac, 0, 1));
    const temps = sorted.map((p) => THREE.MathUtils.clamp((p.tempC + 20) / 50, 0, 1));
    return { heights, temps, count: Math.min(heights.length, HEATMAP_MAX_PROFILE) };
  }, [result]);

  const firstMaterial = materials.find((m) => m.id === wallLayers[0]?.materialId);
  const tintColor = useMemo(() => new THREE.Color(firstMaterial?.color || '#4f8bf2'), [firstMaterial]);

  const uniforms = useMemo(() => {
    const heights = new Array(HEATMAP_MAX_PROFILE).fill(0);
    const temps = new Array(HEATMAP_MAX_PROFILE).fill(0);
    return {
      uMinY: { value: geometry.boundingBox.min.y },
      uMaxY: { value: geometry.boundingBox.max.y },
      uTempNorm: { value: tempNorm },
      uMaterialTint: { value: tintColor },
      uProfileHeights: { value: heights },
      uProfileTemps: { value: temps },
      uProfileCount: { value: 0 },
      uUseProfile: { value: 0 },
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [geometry]);

  useFrame(() => {
    if (!materialRef.current) return;
    const u = materialRef.current.uniforms;
    u.uTempNorm.value = THREE.MathUtils.lerp(u.uTempNorm.value, tempNorm, 0.06);
    u.uMaterialTint.value.lerp(tintColor, 0.08);

    const targetUseProfile = profile ? 1 : 0;
    u.uUseProfile.value = THREE.MathUtils.lerp(u.uUseProfile.value, targetUseProfile, 0.08);
    if (profile) {
      u.uProfileCount.value = profile.count;
      for (let i = 0; i < profile.count; i++) {
        u.uProfileHeights.value[i] = profile.heights[i];
        u.uProfileTemps.value[i] = THREE.MathUtils.lerp(u.uProfileTemps.value[i] || profile.temps[i], profile.temps[i], 0.1);
      }
    }
  });

  return (
    <group>
      <mesh geometry={geometry} castShadow receiveShadow>
        <shaderMaterial
          ref={materialRef}
          uniforms={uniforms}
          vertexShader={heatmapVertexShader}
          fragmentShader={heatmapFragmentShader}
        />
      </mesh>

      {/* base accent ring — reflects the primary selected wall material */}
      <mesh position={[0, 0.02, 0]} rotation={[-Math.PI / 2, 0, 0]}>
        <ringGeometry args={[1.15 * (SIZE_SCALE[size] || 1), 1.32 * (SIZE_SCALE[size] || 1), 48]} />
        <meshStandardMaterial color={firstMaterial?.color || '#4f8bf2'} opacity={0.85} transparent />
      </mesh>

      <Html position={[0, geometry.boundingBox.max.y + 0.35, 0]} center distanceFactor={8}>
        <div className="px-2 py-1 rounded bg-black/60 border border-white/10 text-white text-xs font-semibold whitespace-nowrap backdrop-blur-sm">
          {avgTemp >= 0 ? '+' : ''}
          {avgTemp.toFixed(1)}°C Avg
        </div>
      </Html>
    </group>
  );
}

export default function ShelterViewport() {
  return (
    <div className="w-full h-full">
      <Canvas shadows camera={{ position: [3.2, 2.4, 3.6], fov: 42 }}>
        <color attach="background" args={['#0a0e1a']} />
        <ambientLight intensity={0.55} />
        <directionalLight
          position={[4, 6, 3]}
          intensity={1.1}
          castShadow
          shadow-mapSize={[1024, 1024]}
        />
        <directionalLight position={[-4, 2, -3]} intensity={0.25} />

        <Suspense fallback={null}>
          <ShelterMesh />
          <ContactShadows position={[0, 0, 0]} opacity={0.5} scale={10} blur={2} far={2} />
        </Suspense>

        <gridHelper args={[14, 28, '#26304f', '#161d33']} />
        <OrbitControls
          enablePan={false}
          minDistance={2.5}
          maxDistance={9}
          maxPolarAngle={Math.PI / 2.05}
        />
      </Canvas>
    </div>
  );
}
