/**
 * Production-ready Audio Recorder Service using MediaRecorder and Web Audio API.
 * Provides recording controls, live volume & waveform analyzers, and audio blob generation.
 */

export class AudioRecorder {
  constructor() {
    this.mediaRecorder = null;
    this.audioChunks = [];
    this.stream = null;
    this.audioContext = null;
    this.analyser = null;
    this.sourceNode = null;
    this.startTime = null;
    this.durationInterval = null;
    this.durationSeconds = 0;
    this.onDurationUpdate = null;
  }

  async start(onDurationUpdate = null) {
    this.audioChunks = [];
    this.durationSeconds = 0;
    this.onDurationUpdate = onDurationUpdate;

    if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
      throw new Error("Microphone access is not supported on this browser.");
    }

    try {
      this.stream = await navigator.mediaDevices.getUserMedia({
        audio: {
          echoCancellation: true,
          noiseSuppression: true,
          autoGainControl: true,
        },
      });

      // Initialize Web Audio API Analyser for waveform visualization
      try {
        const AudioCtx = window.AudioContext || window.webkitAudioContext;
        if (AudioCtx) {
          this.audioContext = new AudioCtx();
          this.analyser = this.audioContext.createAnalyser();
          this.analyser.fftSize = 64;
          this.sourceNode = this.audioContext.createMediaStreamSource(this.stream);
          this.sourceNode.connect(this.analyser);
        }
      } catch (audioCtxErr) {
        console.warn("Web Audio Analyser setup warning:", audioCtxErr);
      }

      // Determine supported MIME type
      let mimeType = "audio/webm;codecs=opus";
      if (!MediaRecorder.isTypeSupported(mimeType)) {
        mimeType = "audio/webm";
      }
      if (!MediaRecorder.isTypeSupported(mimeType)) {
        mimeType = "audio/mp4";
      }
      if (!MediaRecorder.isTypeSupported(mimeType)) {
        mimeType = ""; // Browser default
      }

      const options = mimeType ? { mimeType } : {};
      this.mediaRecorder = new MediaRecorder(this.stream, options);

      this.mediaRecorder.ondataavailable = (event) => {
        if (event.data && event.data.size > 0) {
          this.audioChunks.push(event.data);
        }
      };

      this.mediaRecorder.start(250); // 250ms chunks
      this.startTime = Date.now();

      this.durationInterval = setInterval(() => {
        this.durationSeconds = Math.floor((Date.now() - this.startTime) / 1000);
        if (this.onDurationUpdate) {
          this.onDurationUpdate(this.durationSeconds);
        }
      }, 500);

      return true;
    } catch (err) {
      this.cleanup();
      throw err;
    }
  }

  pause() {
    if (this.mediaRecorder && this.mediaRecorder.state === "recording") {
      this.mediaRecorder.pause();
    }
  }

  resume() {
    if (this.mediaRecorder && this.mediaRecorder.state === "paused") {
      this.mediaRecorder.resume();
    }
  }

  async stop() {
    return new Promise((resolve, reject) => {
      if (!this.mediaRecorder || this.mediaRecorder.state === "inactive") {
        this.cleanup();
        return resolve({ blob: null, duration: 0 });
      }

      this.mediaRecorder.onstop = () => {
        const mimeType = this.mediaRecorder.mimeType || "audio/webm";
        const audioBlob = new Blob(this.audioChunks, { type: mimeType });
        const finalDuration = this.durationSeconds;
        this.cleanup();
        resolve({ blob: audioBlob, duration: finalDuration });
      };

      this.mediaRecorder.onerror = (err) => {
        this.cleanup();
        reject(err);
      };

      try {
        this.mediaRecorder.stop();
      } catch (err) {
        this.cleanup();
        reject(err);
      }
    });
  }

  cancel() {
    this.cleanup();
  }

  getVolume() {
    if (!this.analyser) return 0;
    const dataArray = new Uint8Array(this.analyser.frequencyBinCount);
    this.analyser.getByteFrequencyData(dataArray);
    let sum = 0;
    for (let i = 0; i < dataArray.length; i++) {
      sum += dataArray[i];
    }
    return sum / dataArray.length;
  }

  cleanup() {
    if (this.durationInterval) {
      clearInterval(this.durationInterval);
      this.durationInterval = null;
    }

    if (this.stream) {
      this.stream.getTracks().forEach((track) => track.stop());
      this.stream = null;
    }

    if (this.sourceNode) {
      try { this.sourceNode.disconnect(); } catch (_) {}
      this.sourceNode = null;
    }

    if (this.audioContext && this.audioContext.state !== "closed") {
      try { this.audioContext.close(); } catch (_) {}
      this.audioContext = null;
    }

    this.analyser = null;
    this.mediaRecorder = null;
    this.audioChunks = [];
  }
}

export const createAudioRecorder = () => new AudioRecorder();
