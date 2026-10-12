"use client";

import type { ReactNode } from "react";

export interface ToggleItem {
  id: string;
  label: ReactNode;
}

interface ToggleGroupProps {
  label: string;
  items: readonly ToggleItem[];
  pressed: ReadonlySet<string>;
  onChange: (next: ReadonlySet<string>) => void;
  mode?: "multi" | "single";
  prefix?: string;
  className?: string;
}

export function ToggleGroup({ label, items, pressed, onChange, mode = "multi", prefix, className = "controls" }: ToggleGroupProps) {
  const toggle = (id: string) => {
    if (mode === "single") return onChange(new Set([id]));
    onChange(new Set(pressed.has(id) ? [...pressed].filter((x) => x !== id) : [...pressed, id]));
  };

  return (
    <div role="group" aria-label={label} className={className}>
      {prefix && <span className="label">{prefix}</span>}
      {items.map((item) => (
        <button key={item.id} type="button" className={mode === "multi" ? "pill toggle" : "pill"} aria-pressed={pressed.has(item.id)} onClick={() => toggle(item.id)}>
          {item.label}
        </button>
      ))}
    </div>
  );
}
