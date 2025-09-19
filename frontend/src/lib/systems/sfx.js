// Lightweight SFX helper to avoid jsfxr runtime issues
// Exports a function that returns an HTMLAudioElement with a short beep sound.

function toBase64(bytes) {
  let binary = '';
  const len = bytes.length;
  for (let i = 0; i < len; i++) {
    binary += String.fromCharCode(bytes[i]);
  }
  // btoa is available in browsers
  return btoa(binary);
}

function generateBeepWav(freq = 880, duration = 0.12, sampleRate = 44100) {
  const samples = Math.floor(duration * sampleRate);
  const numChannels = 1;
  const bytesPerSample = 2; // 16-bit
  const blockAlign = numChannels * bytesPerSample;
  const byteRate = sampleRate * blockAlign;
  const dataSize = samples * blockAlign;
  const headerSize = 44;
  const buffer = new Uint8Array(headerSize + dataSize);
  const view = new DataView(buffer.buffer);

  // RIFF header
  let offset = 0;
  function writeString(str) {
    for (let i = 0; i < str.length; i++) buffer[offset++] = str.charCodeAt(i);
  }
  function writeUint32(val) { view.setUint32(offset, val, true); offset += 4; }
  function writeUint16(val) { view.setUint16(offset, val, true); offset += 2; }

  writeString('RIFF');
  writeUint32(36 + dataSize);
  writeString('WAVE');
  writeString('fmt ');
  writeUint32(16); // PCM chunk size
  writeUint16(1);  // PCM format
  writeUint16(numChannels);
  writeUint32(sampleRate);
  writeUint32(byteRate);
  writeUint16(blockAlign);
  writeUint16(16); // bits per sample
  writeString('data');
  writeUint32(dataSize);

  // Sine wave samples
  let amp = 0.3; // volume 0..1
  for (let i = 0; i < samples; i++) {
    const t = i / sampleRate;
    const sample = Math.sin(2 * Math.PI * freq * t) * amp;
    const s = Math.max(-1, Math.min(1, sample));
    const int16 = s < 0 ? s * 0x8000 : s * 0x7FFF;
    view.setInt16(headerSize + i * 2, int16, true);
  }

  const base64 = toBase64(buffer);
  return `data:audio/wav;base64,${base64}`;
}

export function createDealSfx(volumeSteps = 5) {
  try {
    const url = generateBeepWav(880, 0.12);
    const a = new Audio(url);
    const numericVolume = Number(volumeSteps);
    const clamped = Number.isFinite(numericVolume)
      ? Math.max(0, Math.min(10, numericVolume))
      : 0;
    a.volume = clamped / 10;
    return a;
  } catch {
    return null;
  }
}
