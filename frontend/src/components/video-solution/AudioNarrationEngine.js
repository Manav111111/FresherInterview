/**
 * AudioNarrationEngine
 * Manages browser speech synthesis synchronization with the video timeline.
 */
export class AudioNarrationEngine {
  constructor() {
    this.isSupported = typeof window !== "undefined" && "speechSynthesis" in window;
    this.currentUtterance = null;
    this.lastSpokenSceneId = null;
    this.isMuted = false;
    this.rate = 1.0;
    this.pitch = 1.0;
  }

  setMuted(muted) {
    this.isMuted = muted;
    if (muted) {
      this.stop();
    }
  }

  stop() {
    if (this.isSupported) {
      window.speechSynthesis.cancel();
    }
    this.currentUtterance = null;
    this.lastSpokenSceneId = null;
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
      const utterance = new SpeechSynthesisUtterance(scene.narration);
      utterance.rate = this.rate;
      utterance.pitch = this.pitch;

      // Select a natural voice if available
      const voices = window.speechSynthesis.getVoices();
      const preferredVoice = voices.find(
        (v) =>
          v.lang.startsWith("en") &&
          (v.name.includes("Natural") ||
            v.name.includes("Google") ||
            v.name.includes("Samantha") ||
            v.name.includes("Alex") ||
            v.name.includes("English"))
      ) || voices.find((v) => v.lang.startsWith("en")) || voices[0];

      if (preferredVoice) {
        utterance.voice = preferredVoice;
      }

      this.currentUtterance = utterance;
      window.speechSynthesis.speak(utterance);
    } catch (err) {
      console.warn("Speech synthesis error:", err);
    }
  }
}
