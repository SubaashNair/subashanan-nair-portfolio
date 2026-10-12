"use client";

import { useRef, type KeyboardEvent, type ReactNode } from "react";

export interface TabItem {
  id: string;
  label: ReactNode;
}

interface TabListProps {
  items: readonly TabItem[];
  selected: string;
  onSelect: (id: string) => void;
  idPrefix: string;
  panelId: string;
  label?: string;
  labelledBy?: string;
  className?: string;
  tabClassName?: string;
}

export const tabId = (prefix: string, id: string): string => `${prefix}-tab-${id}`;

const STEP: Readonly<Record<string, number>> = { ArrowRight: 1, ArrowDown: 1, ArrowLeft: -1, ArrowUp: -1 };

export function TabList({ items, selected, onSelect, idPrefix, panelId, label, labelledBy, className = "controls", tabClassName = "pill" }: TabListProps) {
  const refs = useRef<Array<HTMLButtonElement | null>>([]);

  const moveTo = (index: number) => {
    const i = (index + items.length) % items.length;
    onSelect(items[i].id);
    refs.current[i]?.focus();
  };

  const onKeyDown = (event: KeyboardEvent<HTMLButtonElement>, index: number) => {
    if (event.key in STEP) moveTo(index + STEP[event.key]);
    else if (event.key === "Home") moveTo(0);
    else if (event.key === "End") moveTo(items.length - 1);
    else return;
    event.preventDefault();
  };

  return (
    <div role="tablist" aria-label={label} aria-labelledby={labelledBy} className={className}>
      {items.map((item, i) => {
        const on = item.id === selected;
        return (
          <button
            key={item.id}
            ref={(el) => {
              refs.current[i] = el;
            }}
            type="button"
            role="tab"
            id={tabId(idPrefix, item.id)}
            aria-controls={panelId}
            aria-selected={on}
            tabIndex={on ? 0 : -1}
            className={tabClassName}
            onClick={() => onSelect(item.id)}
            onKeyDown={(e) => onKeyDown(e, i)}
          >
            {item.label}
          </button>
        );
      })}
    </div>
  );
}
