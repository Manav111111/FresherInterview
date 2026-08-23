/**
 * AudioNarrationEngine
 * Manages browser speech synthesis perfectly synchronized with the whiteboard video timeline.
 */
export class AudioNarrationEngine {
  constructor() {
    this.isSupported = typeof window !== "undefined" && "speechSynthesis" in window;
    this.currentUtterance = null;
    this.lastSpokenSceneId = null;
    this.isMuted = false;
    this.voices = [];
    this.selectedVoice = null;

    if (this.isSupported) {
      this.loadVoices();
      if (window.speechSynthesis.onvoiceschanged !== undefined) {
        window.speechSynthesis.onvoiceschanged = () => this.loadVoices();
      }
    }
  }

  loadVoices() {
    if (!this.isSupported) return;
    this.voices = window.speechSynthesis.getVoices() || [];
    this.selectedVoice =
      this.voices.find(
        (v) =>
          v.lang.startsWith("en") &&
          (v.name.includes("Natural") ||
            v.name.includes("Google") ||
            v.name.includes("Samantha") ||
            v.name.includes("Alex") ||
            v.name.includes("Guy") ||
            v.name.includes("Aria"))
      ) ||
      this.voices.find((v) => v.lang.startsWith("en")) ||
      this.voices[0] ||
      null;
  }

  setMuted(muted) {
    this.isMuted = muted;
    if (muted) {
      this.stop();
    }
  }

  pause() {
    if (this.isSupported && window.speechSynthesis.speaking) {
      window.speechSynthesis.pause();
    }
  }

  resume() {
    if (this.isSupported && window.speechSynthesis.paused) {
      window.speechSynthesis.resume();
    }
  }

  stop() {
    if (this.isSupported) {
      window.speechSynthesis.cancel();
    }
    this.currentUtterance = null;
  }

  reset() {
    this.stop();
    this.lastSpokenSceneId = null;
  }

  speakScene(scene) {
    if (!this.isSupported || this.isMuted || !scene || !scene.narration) return;
    if (this.lastSpokenSceneId === scene.id) return;

    this.stop();
    this.lastSpokenSceneId = scene.id;

    try {
      const text = scene.narration.trim();
      const utterance = new SpeechSynthesisUtterance(text);
      
      // Calculate rate dynamically so spoken narration duration matches the visual scene duration
      const wordCount = text.split(/\s+/).filter(Boolean).length;
      const sceneDuration = Math.max(2.5, scene.duration || 4.0);
      
      // Standard baseline is ~2.4 words per second
      const estimatedNormalDur = Math.max(1.0, wordCount / 2.4);
      const targetRate = estimatedNormalDur / (sceneDuration * 0.95);
      
      // Keep rate within natural sounding bounds
      utterance.rate = Math.max(0.9, Math.min(1.3, targetRate));
      utterance.pitch = 1.0;

      if (!this.selectedVoice && this.voices.length === 0) {
        this.loadVoices();
      }

      if (this.selectedVoice) {
        utterance.voice = this.selectedVoice;
      }

      utterance.onend = () => {
        this.currentUtterance = null;
      };

      utterance.onerror = (e) => {
        // Ignore canceled errors on user seek/pause
        if (e.error !== "canceled" && e.error !== "interrupted") {
          console.warn("Speech synthesis error:", e);
        }
      };

      this.currentUtterance = utterance;
      window.speechSynthesis.speak(utterance);
    } catch (err) {
      console.warn("Speech synthesis trigger exception:", err);
    }
  }
}
