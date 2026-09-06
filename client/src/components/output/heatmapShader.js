// Height-based "thermal heatmap" shader. Not physically simulated — just a
// visual encoding of local geometry height blended with the overall average
// inside temperature, so the shelter reads as a heatmap like the reference UI.
export const heatmapVertexShader = /* glsl */ `
  varying vec3 vPos;
  void main() {
    vPos = position;
    gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0);
  }
`;

export const heatmapFragmentShader = /* glsl */ `
  varying vec3 vPos;
  uniform float uMinY;
  uniform float uMaxY;
  uniform float uTempNorm; // 0 = cold (blue-shifted), 1 = warm (red-shifted)
  uniform vec3 uMaterialTint; // subtle tint from the selected wall material

  vec3 colormap(float t) {
    vec3 c0 = vec3(0.14, 0.32, 0.85); // blue
    vec3 c1 = vec3(0.11, 0.66, 0.72); // teal
    vec3 c2 = vec3(0.30, 0.78, 0.35); // green
    vec3 c3 = vec3(0.93, 0.80, 0.20); // yellow
    vec3 c4 = vec3(0.93, 0.55, 0.15); // orange
    vec3 c5 = vec3(0.86, 0.20, 0.18); // red

    if (t < 0.2) return mix(c0, c1, t / 0.2);
    if (t < 0.4) return mix(c1, c2, (t - 0.2) / 0.2);
    if (t < 0.6) return mix(c2, c3, (t - 0.4) / 0.2);
    if (t < 0.8) return mix(c3, c4, (t - 0.6) / 0.2);
    return mix(c4, c5, (t - 0.8) / 0.2);
  }

  void main() {
    float h = clamp((vPos.y - uMinY) / max(uMaxY - uMinY, 0.001), 0.0, 1.0);
    float t = clamp(h * 0.55 + uTempNorm * 0.45, 0.0, 1.0);
    vec3 color = mix(colormap(t), uMaterialTint, 0.12);
    gl_FragColor = vec4(color, 1.0);
  }
`;
