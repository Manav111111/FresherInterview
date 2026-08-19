/**
 * VideoRecorder
 * Records whiteboard canvas rendering into a downloadable WebM video file using standard MediaRecorder.
 */
export class VideoRecorder {
  constructor(canvas) {
    this.canvas = canvas;
    this.mediaRecorder = null;
    this.recordedChunks = [];
    this.isRecording = false;
  }

  static isSupported() {
    return (
      typeof window !== "undefined" &&
      typeof HTMLCanvasElement !== "undefined" &&
      "captureStream" in HTMLCanvasElement.prototype &&
      typeof MediaRecorder !== "undefined"
    );
  }

  static getSupportedMimeType() {
    if (!this.isSupported()) return null;

    const types = [
      "video/webm;codecs=vp9,opus",
      "video/webm;codecs=vp8,opus",
      "video/webm",
      "video/mp4",
    ];

    for (const type of types) {
      if (MediaRecorder.isTypeSupported(type)) {
        return type;
      }
    }
    return "";
  }

  start() {
    if (!this.canvas || !VideoRecorder.isSupported()) {
      throw new Error("Video recording is not supported in this browser.");
    }

    this.recordedChunks = [];
    const stream = this.canvas.captureStream(30); // 30 FPS
    const mimeType = VideoRecorder.getSupportedMimeType();

    try {
      this.mediaRecorder = new MediaRecorder(stream, mimeType ? { mimeType } : {});
    } catch (e) {
      this.mediaRecorder = new MediaRecorder(stream);
    }

    this.mediaRecorder.ondataavailable = (event) => {
      if (event.data && event.data.size > 0) {
        this.recordedChunks.push(event.data);
      }
    };

    this.mediaRecorder.start(100);
    this.isRecording = true;
  }

  stop() {
    return new Promise((resolve, reject) => {
      if (!this.mediaRecorder || this.mediaRecorder.state === "inactive") {
        resolve(null);
        return;
      }

      this.mediaRecorder.onstop = () => {
        this.isRecording = false;
        const mimeType = this.mediaRecorder.mimeType || "video/webm";
        const blob = new Blob(this.recordedChunks, { type: mimeType });
        const extension = mimeType.includes("mp4") ? "mp4" : "webm";
        resolve({ blob, extension, mimeType });
      };

      this.mediaRecorder.onerror = (err) => {
        this.isRecording = false;
        reject(err);
      };

      this.mediaRecorder.stop();
    });
  }

  downloadBlob(blob, filename = "ai-solution-whiteboard.webm") {
    if (!blob) return;
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.style.display = "none";
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    setTimeout(() => {
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
    }, 2000);
  }
}
