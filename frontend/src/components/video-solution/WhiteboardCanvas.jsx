import React, { useEffect, useRef } from "react";

/**
 * WhiteboardCanvas
 * High-definition educational whiteboard with synchronized progressive handwriting animation.
 */
export default function WhiteboardCanvas({
  question,
  topic,
  scenes = [],
  currentTime = 0,
  totalDuration = 15,
  canvasRef,
}) {
  const localRef = useRef(null);
  const targetRef = canvasRef || localRef;

  // Calculate cumulative scene timelines
  const timeline = scenes.map((scene, idx) => {
    const startTime = scenes
      .slice(0, idx)
      .reduce((sum, s) => sum + (s.duration || 3.5), 0);
    const duration = scene.duration || 3.5;
    const endTime = startTime + duration;
    return {
      ...scene,
      startTime,
      endTime,
      duration,
    };
  });

  useEffect(() => {
    const canvas = targetRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    // Logical canvas dimensions: 1280 x 720 (16:9 standard HD)
    const W = 1280;
    const H = 720;

    if (canvas.width !== W || canvas.height !== H) {
      canvas.width = W;
      canvas.height = H;
    }

    // 1. Clear & Draw Whiteboard Background
    ctx.fillStyle = "#FFFFFF";
    ctx.fillRect(0, 0, W, H);

    // Subtle whiteboard dot grid pattern
    ctx.fillStyle = "#E5E7EB";
    const dotSpacing = 32;
    for (let x = 20; x < W; x += dotSpacing) {
      for (let y = 20; y < H; y += dotSpacing) {
        ctx.beginPath();
        ctx.arc(x, y, 1.2, 0, Math.PI * 2);
        ctx.fill();
      }
    }

    // Whiteboard outer subtle border
    ctx.strokeStyle = "#E2E8F0";
    ctx.lineWidth = 4;
    ctx.strokeRect(8, 8, W - 16, H - 16);

    // 2. Render Header (Question & Topic)
    const paddingX = 64;
    let currentY = 50;

    // Category / Topic pill
    ctx.fillStyle = "#6366F1";
    ctx.font = "bold 13px 'Inter', sans-serif";
    ctx.fillText((topic || "QUESTION / PROBLEM").toUpperCase(), paddingX, currentY);

    currentY += 34;

    // Question Text (Large, crisp, visible at all times)
    ctx.fillStyle = "#0F172A";
    ctx.font = "bold 26px 'Inter', system-ui, sans-serif";
    
    // Wrap question text if long
    const maxQWidth = W - paddingX * 2;
    const qWords = (question || "Problem").split(" ");
    let qLine = "";
    let qLines = [];

    for (let n = 0; n < qWords.length; n++) {
      const testLine = qLine + qWords[n] + " ";
      const metrics = ctx.measureText(testLine);
      if (metrics.width > maxQWidth && n > 0) {
        qLines.push(qLine);
        qLine = qWords[n] + " ";
      } else {
        qLine = testLine;
      }
    }
    qLines.push(qLine);

    // Draw question lines
    qLines.slice(0, 2).forEach((line) => {
      ctx.fillText(line.trim(), paddingX, currentY);
      currentY += 34;
    });

    // Thin separator bar
    currentY += 8;
    ctx.strokeStyle = "#CBD5E1";
    ctx.lineWidth = 1.5;
    ctx.beginPath();
    ctx.moveTo(paddingX, currentY);
    ctx.lineTo(W - paddingX, currentY);
    ctx.stroke();

    currentY += 45;

    // 3. Render Progressive Solution Steps
    const stepStartY = currentY;
    const availableHeight = H - stepStartY - 40;
    const stepSpacing = Math.min(100, availableHeight / Math.max(1, timeline.length));

    timeline.forEach((scene, index) => {
      if (currentTime < scene.startTime) {
        // Scene has not started yet
        return;
      }

      const sceneProgress = Math.min(
        1,
        Math.max(0, (currentTime - scene.startTime) / scene.duration)
      );

      const yPos = stepStartY + index * stepSpacing;

      // Draw Step Number / Label badge
      ctx.fillStyle = scene.isFinal ? "#10B981" : "#3B82F6";
      ctx.font = "600 14px 'Inter', sans-serif";
      const stepLabel = scene.isFinal ? "FINAL ANSWER" : `STEP ${scene.step || index + 1}`;
      ctx.fillText(stepLabel, paddingX, yPos - 6);

      // Character-by-character progressive writing
      const fullText = scene.content || "";
      const visibleCharCount = Math.floor(fullText.length * sceneProgress);
      const visibleText = fullText.slice(0, visibleCharCount);

      // If it is the final answer and writing is active or finished, draw accent box
      if (scene.isFinal && visibleCharCount > 0) {
        ctx.save();
        ctx.fillStyle = "#ECFDF5";
        ctx.strokeStyle = "#10B981";
        ctx.lineWidth = 2;
        ctx.beginPath();
        ctx.roundRect(paddingX - 12, yPos + 2, W - paddingX * 2 + 24, 52, 8);
        ctx.fill();
        ctx.stroke();
        ctx.restore();
      }

      // Draw Step Content
      ctx.fillStyle = scene.isFinal ? "#065F46" : "#1E293B";
      ctx.font = scene.isFinal
        ? "bold 28px 'Fira Code', 'Courier New', monospace"
        : "500 24px 'Fira Code', 'Courier New', monospace";
      ctx.fillText(visibleText, paddingX, yPos + 38);

      // Animated writing pen tip / cursor indicator
      if (sceneProgress > 0 && sceneProgress < 1) {
        const textMetrics = ctx.measureText(visibleText);
        const cursorX = paddingX + textMetrics.width + 3;
        const cursorY = yPos + 38;

        // Draw animated pen nib indicator
        ctx.save();
        ctx.fillStyle = "#6366F1";
        ctx.beginPath();
        ctx.arc(cursorX + 2, cursorY - 6, 3.5, 0, Math.PI * 2);
        ctx.fill();
        ctx.restore();
      }
    });

    // 4. Watermark / Footer
    ctx.fillStyle = "#94A3B8";
    ctx.font = "12px 'Inter', sans-serif";
    ctx.fillText("Fresher.AI • Whiteboard Explanation", paddingX, H - 24);

    // Timestamp indicator on canvas
    const timeText = `${Math.floor(currentTime)}s / ${Math.floor(totalDuration)}s`;
    const timeWidth = ctx.measureText(timeText).width;
    ctx.fillText(timeText, W - paddingX - timeWidth, H - 24);
  }, [question, topic, scenes, currentTime, totalDuration, targetRef, timeline]);

  return (
    <div className="relative w-full aspect-video rounded-2xl overflow-hidden shadow-2xl border border-black/10 bg-white">
      <canvas
        ref={targetRef}
        className="w-full h-full object-contain block select-none"
      />
    </div>
  );
}
