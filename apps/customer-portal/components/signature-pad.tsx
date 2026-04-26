"use client";

import { useEffect, useRef, useState } from "react";

/**
 * Lightweight signature pad — no external library.
 *  - Draws strokes to a canvas, also records them as SVG path commands so
 *    we can persist a vector signature alongside the consent record.
 *  - Hidden <input name="consentSignatureSvg"> carries the SVG into the
 *    server action when the form submits.
 */
export function SignaturePad({ name = "consentSignatureSvg" }: { name?: string }) {
  const canvasRef = useRef<HTMLCanvasElement | null>(null);
  const [drawing, setDrawing] = useState(false);
  const [paths, setPaths] = useState<string[]>([]);
  const [current, setCurrent] = useState<string>("");

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;
    ctx.strokeStyle = "#0E1A24";
    ctx.lineWidth = 2;
    ctx.lineCap = "round";
  }, []);

  function pos(e: React.PointerEvent) {
    const r = canvasRef.current!.getBoundingClientRect();
    return { x: e.clientX - r.left, y: e.clientY - r.top };
  }
  function start(e: React.PointerEvent) {
    e.preventDefault();
    const { x, y } = pos(e);
    setDrawing(true);
    setCurrent(`M${x.toFixed(1)} ${y.toFixed(1)}`);
    const ctx = canvasRef.current!.getContext("2d")!;
    ctx.beginPath();
    ctx.moveTo(x, y);
  }
  function move(e: React.PointerEvent) {
    if (!drawing) return;
    const { x, y } = pos(e);
    setCurrent((c) => `${c} L${x.toFixed(1)} ${y.toFixed(1)}`);
    const ctx = canvasRef.current!.getContext("2d")!;
    ctx.lineTo(x, y);
    ctx.stroke();
  }
  function end() {
    if (!drawing) return;
    setDrawing(false);
    setPaths((p) => [...p, current]);
    setCurrent("");
  }
  function clear() {
    const c = canvasRef.current!;
    c.getContext("2d")!.clearRect(0, 0, c.width, c.height);
    setPaths([]);
    setCurrent("");
  }

  const svg = `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 480 160">${paths
    .map((d) => `<path d="${d}" fill="none" stroke="#0E1A24" stroke-width="2" stroke-linecap="round"/>`)
    .join("")}</svg>`;

  return (
    <div>
      <canvas
        ref={canvasRef}
        width={480}
        height={160}
        role="img"
        aria-label="Signature pad — sign with your finger or mouse"
        className="w-full max-w-[480px] h-40 rounded-md border border-rule bg-white touch-none"
        onPointerDown={start}
        onPointerMove={move}
        onPointerUp={end}
        onPointerLeave={end}
      />
      <div className="mt-2 flex items-center gap-3">
        <button type="button" onClick={clear} className="text-sm text-ink-muted hover:underline">
          Clear
        </button>
        <span className="text-xs text-ink-muted">
          {paths.length === 0 ? "Sign above" : "Signature captured"}
        </span>
      </div>
      <input type="hidden" name={name} value={svg} />
    </div>
  );
}
