"use client";
import { useState, useRef, useEffect } from "react";
import { ChevronDown } from "lucide-react";
import { cn } from "@/lib/utils";

type Mode = "normal" | "validation" | "protocol";

const modeConfig: Record<Mode, { label: string; className: string }> = {
  normal: {
    label: "Normal",
    className: "bg-indigo-500/15 text-indigo-400 border border-indigo-500/30 hover:bg-indigo-500/25",
  },
  validation: {
    label: "Validation",
    className: "bg-amber-400/15 text-amber-400 border border-amber-400/30 hover:bg-amber-400/25",
  },
  protocol: {
    label: "Protocol",
    className: "bg-cyan-500/15 text-cyan-400 border border-cyan-500/30 hover:bg-cyan-500/25",
  },
};

const modeOrder: Mode[] = ["normal", "validation", "protocol"];

export function Topbar() {
  const [mode, setMode] = useState<Mode>("normal");
  const [avatarOpen, setAvatarOpen] = useState(false);
  const avatarRef = useRef<HTMLDivElement>(null);

  const cycleMode = () => {
    const idx = modeOrder.indexOf(mode);
    setMode(modeOrder[(idx + 1) % modeOrder.length]);
  };

  // Close dropdown on outside click
  useEffect(() => {
    function handleClick(e: MouseEvent) {
      if (avatarRef.current && !avatarRef.current.contains(e.target as Node)) {
        setAvatarOpen(false);
      }
    }
    if (avatarOpen) {
      document.addEventListener("mousedown", handleClick);
      return () => document.removeEventListener("mousedown", handleClick);
    }
  }, [avatarOpen]);

  const currentMode = modeConfig[mode];

  return (
    <header className="h-14 bg-zinc-900 border-b border-zinc-800 flex items-center px-4 shrink-0 gap-4">
      {/* Left: Run selector */}
      <button
        type="button"
        className="flex items-center gap-2 bg-zinc-800 hover:bg-zinc-700 text-zinc-300 rounded-md px-3 py-1.5 text-sm transition-colors"
      >
        <span>Select Run</span>
        <ChevronDown size={14} className="text-zinc-500" />
      </button>

      {/* Center: Mode badge */}
      <div className="flex-1 flex items-center justify-center">
        <button
          type="button"
          onClick={cycleMode}
          className={cn(
            "text-xs font-medium px-3 py-1 rounded-full transition-colors cursor-pointer",
            currentMode.className
          )}
        >
          {currentMode.label}
        </button>
      </div>

      {/* Right: Avatar */}
      <div className="relative" ref={avatarRef}>
        <button
          type="button"
          onClick={() => setAvatarOpen((v) => !v)}
          className="w-8 h-8 rounded-full bg-indigo-600 flex items-center justify-center text-sm font-semibold text-white hover:bg-indigo-500 transition-colors focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:ring-offset-2 focus:ring-offset-zinc-900"
          aria-label="Account menu"
          aria-expanded={avatarOpen}
          aria-haspopup="true"
        >
          A
        </button>

        {avatarOpen && (
          <div className="absolute right-0 mt-2 w-52 bg-zinc-900 border border-zinc-700 rounded-lg shadow-xl z-50 overflow-hidden">
            <div className="px-4 py-3 border-b border-zinc-800">
              <p className="text-sm font-medium text-zinc-50">Admin</p>
              <p className="text-xs text-zinc-500 mt-0.5">Workspace: default</p>
            </div>
            <div className="py-1">
              <button
                type="button"
                className="w-full text-left px-4 py-2 text-sm text-zinc-400 hover:text-zinc-200 hover:bg-zinc-800 transition-colors"
                onClick={() => setAvatarOpen(false)}
              >
                Sign out
              </button>
            </div>
          </div>
        )}
      </div>
    </header>
  );
}
