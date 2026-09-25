/**
 * AudioNarrationEngine
 * Manages browser speech synthesis synchronized with the whiteboard video timeline.
 * Engineered for cross-browser resilience (Chromium cancel-race, garbage collection,
 * user gesture autoplay unlock, and asynchronous voice loading).
 */

export class AudioNarrationEngine {
  constructor() {
    this.isSupported = typeof window !== "undefined" && "speechSynthesis" in window;
    this.currentUtterance = null;
    this.lastSpokenSceneId = null;
    this.isMuted = false;
    this.voices = [];
    this.selectedVoice = null;
    this.unlocked = false;
    this.pendingSpeakTimeout = null;
    this.watchdogInterval = null;

    if (typeof window !== "undefined") {
      window.__activeUtterances = window.__activeUtterances || new Set();
    }

    if (this.isSupported) {
      this.loadVoices();

      // Listen for voice catalog updates across different browser engines
      if (window.speechSynthesis.onvoiceschanged !== undefined) {
        window.speechSynthesis.onvoiceschanged = () => this.loadVoices();
      }
      try {
        window.speechSynthesis.addEventListener("voiceschanged", () => this.loadVoices());
      } catch (_) {}

      // Start watchdog to keep Chrome speech queue active
      this.startWatchdog();
    }
  }

  /**
   * Loads and selects the best natural sounding voice available in the browser.
   */
  loadVoices() {
    if (!this.isSupported) return;
    try {
      const allVoices = window.speechSynthesis.getVoices() || [];
      if (allVoices.length > 0) {
        this.voices = allVoices;

        // Priority 1: High quality natural/cloud English voices
        const naturalVoice = allVoices.find((v) => {
          const name = v.name.toLowerCase();
          const lang = v.lang.toLowerCase();
          const isEn = lang.startsWith("en");
          const isNatural =
            name.includes("natural") ||
            name.includes("google") ||
            name.includes("samantha") ||
            name.includes("alex") ||
            name.includes("guy") ||
            name.includes("aria") ||
            name.includes("jenny") ||
            name.includes("daniel");
          return isEn && isNatural;
        });

        // Priority 2: Any English voice
        const anyEnglish = allVoices.find((v) => v.lang.toLowerCase().startsWith("en"));

        this.selectedVoice = naturalVoice || anyEnglish || allVoices[0] || null;
      }
    } catch (e) {
      console.warn("Could not load speech voices:", e);
    }
  }

  /**
   * Unlocks browser audio policy on user interaction (clicks on Play/Generate/etc).
   */
  unlock() {
    if (!this.isSupported) return;
    try {
      window.speechSynthesis.resume();
      if (!this.unlocked) {
        // Prime with an empty utterance during direct user click
        const primer = new SpeechSynthesisUtterance("");
        primer.volume = 0;
        primer.rate = 2.0;
        primer.onend = () => {
          this.unlocked = true;
        };
        primer.onerror = () => {
          this.unlocked = true;
        };
        window.speechSynthesis.speak(primer);
      }
    } catch (_) {}
  }

  /**
   * Periodic watchdog to prevent Chrome from freezing speech on longer timelines
   */
  startWatchdog() {
    if (this.watchdogInterval || !this.isSupported) return;
    this.watchdogInterval = setInterval(() => {
      try {
        if (window.speechSynthesis.speaking && window.speechSynthesis.paused) {
          window.speechSynthesis.resume();
        }
      } catch (_) {}
    }, 4000);
  }

  setMuted(muted) {
    this.isMuted = muted;
    if (muted) {
      this.stop();
    } else {
      // Allow speaking the current scene upon unmuting
      this.lastSpokenSceneId = null;
    }
  }

  pause() {
    if (!this.isSupported) return;
    try {
      if (window.speechSynthesis.speaking) {
        window.speechSynthesis.pause();
      }
    } catch (_) {}
  }

  resume() {
    if (!this.isSupported) return;
    try {
      if (window.speechSynthesis.paused) {
        window.speechSynthesis.resume();
      }
    } catch (_) {}
  }

  stop() {
    if (this.pendingSpeakTimeout) {
      clearTimeout(this.pendingSpeakTimeout);
      this.pendingSpeakTimeout = null;
    }

    if (this.isSupported) {
      try {
        window.speechSynthesis.cancel();
      } catch (_) {}
    }

    if (this.currentUtterance && typeof window !== "undefined" && window.__activeUtterances) {
      window.__activeUtterances.delete(this.currentUtterance);
    }
    this.currentUtterance = null;
  }

  reset() {
    this.stop();
    this.lastSpokenSceneId = null;
  }

  /**
   * Speaks narration for the active scene.
   * Uses debounced invocation after cancel to avoid Chromium's synchronous cancel-race bug.
   *
   * @param {Object} scene - The active scene with narration and duration.
   * @param {boolean} force - Force re-speaking even if scene.id matches lastSpokenSceneId (e.g. on seek/replay).
   */
  speakScene(scene, force = false) {
    if (!this.isSupported || this.isMuted || !scene || !scene.narration) return;
    if (!force && this.lastSpokenSceneId === scene.id) return;

    this.lastSpokenSceneId = scene.id;

    if (this.pendingSpeakTimeout) {
      clearTimeout(this.pendingSpeakTimeout);
      this.pendingSpeakTimeout = null;
    }

    // Cancel any previous speech
    try {
      if (window.speechSynthesis.speaking || window.speechSynthesis.pending) {
        window.speechSynthesis.cancel();
      }
    } catch (_) {}

    // Delay speech by 35ms to let Chromium process cancel IPC before speaking new utterance
    this.pendingSpeakTimeout = setTimeout(() => {
      this._executeSpeak(scene);
    }, 35);
  }

  _executeSpeak(scene) {
    if (!this.isSupported || this.isMuted || !scene || !scene.narration) return;

    try {
      const text = scene.narration.trim();
      if (!text) return;

      // Always ensure the speech queue is unpaused
      if (window.speechSynthesis.paused) {
        window.speechSynthesis.resume();
      }

      const utterance = new SpeechSynthesisUtterance(text);

      // Refresh voices if not loaded
      if (!this.selectedVoice || this.voices.length === 0) {
        this.loadVoices();
      }

      if (this.selectedVoice) {
        utterance.voice = this.selectedVoice;
        utterance.lang = this.selectedVoice.lang || "en-US";
      } else {
        utterance.lang = "en-US";
      }

      // Calculate speech rate dynamically so speech completes comfortably within scene duration
      const wordCount = text.split(/\s+/).filter(Boolean).length;
      const sceneDuration = Math.max(3.0, scene.duration || 4.0);

      // Standard spoken speed is ~2.3 words/second
      const normalDuration = Math.max(1.0, wordCount / 2.3);
      const computedRate = normalDuration / (sceneDuration * 0.9);

      // Safe, natural bounds
      utterance.rate = Math.max(0.9, Math.min(1.25, computedRate));
      utterance.pitch = 1.0;
      utterance.volume = this.isMuted ? 0.0 : 1.0;

      // Pin utterance to global set to prevent V8 garbage collection mid-speech
      if (typeof window !== "undefined" && window.__activeUtterances) {
        window.__activeUtterances.add(utterance);
      }

      utterance.onend = () => {
        if (typeof window !== "undefined" && window.__activeUtterances) {
          window.__activeUtterances.delete(utterance);
        }
        if (this.currentUtterance === utterance) {
          this.currentUtterance = null;
        }
      };

      utterance.onerror = (e) => {
        if (typeof window !== "undefined" && window.__activeUtterances) {
          window.__activeUtterances.delete(utterance);
        }
        if (this.currentUtterance === utterance) {
          this.currentUtterance = null;
        }
        // If voice synthesis was blocked due to autoplay restriction, resume next time
        if (e.error === "not-allowed") {
          this.unlocked = false;
        } else if (e.error !== "canceled" && e.error !== "interrupted") {
          console.warn("Speech synthesis notice:", e.error);
        }
      };

      this.currentUtterance = utterance;

      // Explicitly resume before speak in Chrome
      window.speechSynthesis.resume();
      window.speechSynthesis.speak(utterance);
    } catch (err) {
      console.warn("Speech synthesis trigger exception:", err);
    }
  }

  destroy() {
    this.stop();
    if (this.watchdogInterval) {
      clearInterval(this.watchdogInterval);
      this.watchdogInterval = null;
    }
  }
}
