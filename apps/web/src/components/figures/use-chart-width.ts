"use client";

import { useEffect, useState, type RefObject } from "react";

/** Width of the element in CSS pixels, so SVG text is drawn at its real size. The fallback is used for the server render. */
export function useChartWidth(ref: RefObject<HTMLElement | null>, fallback = 640): number {
  const [width, setWidth] = useState(fallback);
  useEffect(() => {
    const el = ref.current;
    if (!el || typeof ResizeObserver === "undefined") return;
    const observer = new ResizeObserver(() => {
      const w = Math.round(el.clientWidth);
      if (w > 0) setWidth(w);
    });
    observer.observe(el);
    return () => observer.disconnect();
  }, [ref]);
  return width;
}
