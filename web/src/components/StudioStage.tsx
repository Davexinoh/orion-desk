import { PointerEvent, useEffect, useRef } from "react";

export default function StudioStage() {
  const root = useRef<HTMLDivElement>(null);
  const reduce = useRef(false);

  useEffect(() => {
    reduce.current = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  }, []);

  function onMove(e: PointerEvent<HTMLDivElement>) {
    if (reduce.current || !root.current) return;
    const r = root.current.getBoundingClientRect();
    const x = (e.clientX - r.left) / r.width - 0.5;
    const y = (e.clientY - r.top) / r.height - 0.5;
    root.current.style.setProperty("--mx", x.toFixed(3));
    root.current.style.setProperty("--my", y.toFixed(3));
  }

  function onLeave() {
    if (!root.current) return;
    root.current.style.setProperty("--mx", "0");
    root.current.style.setProperty("--my", "0");
  }

  return (
    <div
      ref={root}
      className="studio-stage"
      onPointerMove={onMove}
      onPointerLeave={onLeave}
      aria-hidden="true"
    >
      <img className="studio-void" src="/studio-void.jpg" alt="" />
      <div className="studio-light" />
      <img className="studio-fiber" src="/studio-fiber.jpg" alt="" />
      <img className="studio-receipt" src="/studio-receipt.jpg" alt="" />
      <div className="studio-grain" />
    </div>
  );
}
