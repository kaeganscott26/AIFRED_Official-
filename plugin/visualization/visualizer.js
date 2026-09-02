import * as THREE from './three.module.min.js';

const sceneCanvas = document.querySelector('#three-scene');
const spectrumCanvas = document.querySelector('#spectrum');
const stateLabel = document.querySelector('#state-label');
const renderer = new THREE.WebGLRenderer({ canvas: sceneCanvas, alpha: true, antialias: true });
renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 2));
renderer.setClearColor(0x000000, 0);

const scene = new THREE.Scene();
const camera = new THREE.PerspectiveCamera(40, 1, .1, 100);
camera.position.set(0, 0, 7);

const haloMaterial = new THREE.MeshStandardMaterial({
  color: 0x4bdcf2, emissive: 0x123d48, emissiveIntensity: .6,
  metalness: .2, roughness: .42, transparent: true, opacity: .38
});
const halo = new THREE.Mesh(new THREE.TorusGeometry(1.55, .055, 18, 128), haloMaterial);
halo.rotation.x = .72;
halo.rotation.y = -.24;
halo.position.set(1.7, .05, -1.4);
scene.add(halo);

const innerHalo = new THREE.Mesh(
  new THREE.TorusGeometry(1.12, .018, 12, 96),
  new THREE.MeshBasicMaterial({ color: 0x60efb3, transparent: true, opacity: .3 })
);
innerHalo.rotation.copy(halo.rotation);
innerHalo.position.copy(halo.position);
scene.add(innerHalo);
scene.add(new THREE.AmbientLight(0x7ccfe0, 1.2));
const light = new THREE.PointLight(0x60efb3, 4, 12);
light.position.set(2.4, 1.2, 2.8);
scene.add(light);

let state = {
  normalizedPeak: 0, normalizedRms: 0, normalizedCrest: 0, normalizedLoudness: 0,
  width: 0, correlation: 0, signalActive: false, elapsedSeconds: 0,
  spectrumBinWidthHz: 0, spectrumBins: []
};

const landmarks = [20, 40, 80, 160, 315, 630, 1000, 2000, 4000, 8000, 16000, 20000];
const xForFrequency = (frequency, left, width) => left + width * Math.log10(frequency / 20) / Math.log10(1000);
const frequencyLabel = frequency => frequency >= 1000 ? `${Math.round(frequency / 1000)}k` : `${frequency}`;

function resize() {
  const width = Math.max(1, sceneCanvas.clientWidth);
  const height = Math.max(1, sceneCanvas.clientHeight);
  renderer.setSize(width, height, false);
  camera.aspect = width / height;
  camera.updateProjectionMatrix();
  const ratio = Math.min(window.devicePixelRatio || 1, 2);
  spectrumCanvas.width = Math.round(width * ratio);
  spectrumCanvas.height = Math.round(height * ratio);
  const context = spectrumCanvas.getContext('2d');
  context.setTransform(ratio, 0, 0, ratio, 0, 0);
}

function drawSpectrum() {
  const context = spectrumCanvas.getContext('2d');
  const width = spectrumCanvas.clientWidth;
  const height = spectrumCanvas.clientHeight;
  context.clearRect(0, 0, width, height);
  const plot = { left: 54, top: 54, right: width - 18, bottom: height - 28 };
  const plotWidth = Math.max(1, plot.right - plot.left);
  const plotHeight = Math.max(1, plot.bottom - plot.top);
  context.font = '9px Segoe UI, Arial';
  context.lineWidth = 1;
  for (let db = -96; db <= 0; db += 12) {
    const y = plot.bottom - ((db + 96) / 96) * plotHeight;
    context.strokeStyle = db % 24 === 0 ? 'rgba(58,82,103,.58)' : 'rgba(58,82,103,.28)';
    context.beginPath(); context.moveTo(plot.left, y); context.lineTo(plot.right, y); context.stroke();
    if (db % 24 === 0) {
      context.fillStyle = 'rgba(141,165,181,.85)'; context.textAlign = 'right';
      context.fillText(`${db}`, plot.left - 8, y + 3);
    }
  }
  for (const frequency of landmarks) {
    const x = xForFrequency(frequency, plot.left, plotWidth);
    context.strokeStyle = 'rgba(58,82,103,.34)';
    context.beginPath(); context.moveTo(x, plot.top); context.lineTo(x, plot.bottom); context.stroke();
    context.fillStyle = '#8da5b5'; context.textAlign = frequency === 20 ? 'left' : frequency === 20000 ? 'right' : 'center';
    context.fillText(frequencyLabel(frequency), x, plot.bottom + 17);
  }

  if (!(state.spectrumBinWidthHz > 0) || !state.spectrumBins.length) return false;
  context.beginPath();
  let started = false;
  let firstX = plot.left;
  let lastX = plot.left;
  for (let index = 1; index < state.spectrumBins.length; index += 1) {
    const value = state.spectrumBins[index];
    const frequency = index * state.spectrumBinWidthHz;
    if (value == null || frequency < 20 || frequency > 20000) continue;
    const x = xForFrequency(frequency, plot.left, plotWidth);
    if (started && x - lastX < .6) continue;
    const y = plot.bottom - ((Math.max(-96, Math.min(0, value)) + 96) / 96) * plotHeight;
    if (!started) { context.moveTo(x, y); firstX = x; started = true; } else context.lineTo(x, y);
    lastX = x;
  }
  if (!started) return false;
  context.lineTo(lastX, plot.bottom); context.lineTo(firstX, plot.bottom); context.closePath();
  const gradient = context.createLinearGradient(0, plot.top, 0, plot.bottom);
  gradient.addColorStop(0, 'rgba(75,220,242,.34)'); gradient.addColorStop(1, 'rgba(96,239,179,.02)');
  context.fillStyle = gradient; context.fill();
  context.strokeStyle = '#4bdcf2'; context.lineWidth = 1.7; context.stroke();
  return true;
}

window.__JUCE__.backend.addEventListener('aifredVisualizationState', next => { state = next; });
window.addEventListener('resize', resize);
sceneCanvas.addEventListener('webglcontextlost', event => {
  event.preventDefault();
  window.__JUCE__.backend.emitEvent('aifredVisualizerFailed', { reason: 'webgl-context-lost' });
});
resize();
window.__JUCE__.backend.emitEvent('aifredVisualizerReady', { threeRevision: THREE.REVISION });

function animate(time) {
  const active = state.signalActive ? 1 : 0;
  halo.rotation.z = time * .00008 + state.width * .28;
  innerHalo.rotation.z = -time * .000055 - state.correlation * .18;
  const scale = .96 + active * (.04 + state.normalizedRms * .09);
  halo.scale.setScalar(scale);
  innerHalo.scale.setScalar(.98 + active * state.normalizedPeak * .1);
  haloMaterial.emissiveIntensity = .42 + active * (.25 + state.normalizedLoudness * .45);
  haloMaterial.opacity = .24 + active * (.1 + state.normalizedCrest * .12);
  light.intensity = 2.5 + active * (1 + state.normalizedPeak * 3);
  const hasSpectrum = drawSpectrum();
  stateLabel.hidden = hasSpectrum;
  stateLabel.textContent = state.signalActive ? 'BUILDING SPECTRUM' : 'WAITING FOR LIVE AUDIO';
  renderer.render(scene, camera);
  requestAnimationFrame(animate);
}
requestAnimationFrame(animate);
