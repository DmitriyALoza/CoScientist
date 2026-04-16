"use client";
import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  LayoutDashboard,
  MessageSquare,
  FileText,
  Lightbulb,
  FlaskConical,
  Target,
  MapPin,
  BookOpen,
  Settings,
  Lock,
} from "lucide-react";
import { cn } from "@/lib/utils";

interface NavItem {
  label: string;
  href: string;
  icon: React.ReactNode;
}

const mainNav: NavItem[] = [
  { label: "Dashboard", href: "/dashboard", icon: <LayoutDashboard size={16} /> },
  { label: "Chat", href: "/chat", icon: <MessageSquare size={16} /> },
  { label: "Documents", href: "/documents", icon: <FileText size={16} /> },
  { label: "Hypotheses", href: "/hypotheses", icon: <Lightbulb size={16} /> },
  { label: "Experiments", href: "/experiments", icon: <FlaskConical size={16} /> },
  { label: "Target Analysis", href: "/target-analysis", icon: <Target size={16} /> },
  { label: "Lab Finder", href: "/lab-finder", icon: <MapPin size={16} /> },
];

const secondaryNav: NavItem[] = [
  { label: "How It Works", href: "/how-it-works", icon: <BookOpen size={16} /> },
  { label: "Settings", href: "/settings", icon: <Settings size={16} /> },
];

const comingSoon = [
  { label: "Structure Analyst" },
  { label: "Virtual Lab" },
];

function NavLink({ item }: { item: NavItem }) {
  const pathname = usePathname();
  const isActive = pathname === item.href || pathname.startsWith(item.href + "/");

  return (
    <Link
      href={item.href}
      className={cn(
        "flex items-center gap-3 px-3 py-2 rounded-md text-sm transition-colors",
        isActive
          ? "bg-indigo-500/10 text-indigo-400 border-r-2 border-indigo-500"
          : "text-zinc-400 hover:text-zinc-200 hover:bg-zinc-800/50"
      )}
    >
      {item.icon}
      <span>{item.label}</span>
    </Link>
  );
}

export function Sidebar() {
  return (
    <aside className="w-[240px] shrink-0 h-screen bg-zinc-900 border-r border-zinc-800 flex flex-col overflow-y-auto">
      {/* Logo */}
      <div className="flex items-center gap-2 px-4 py-5 border-b border-zinc-800">
        <span className="text-xl" aria-hidden="true">🧬</span>
        <span className="text-zinc-50 font-bold text-base tracking-tight">CoScientist</span>
      </div>

      {/* Main nav */}
      <nav className="flex-1 px-2 py-4 space-y-0.5">
        {mainNav.map((item) => (
          <NavLink key={item.href} item={item} />
        ))}

        {/* Divider */}
        <div className="my-3 border-t border-zinc-800" />

        {secondaryNav.map((item) => (
          <NavLink key={item.href} item={item} />
        ))}

        {/* Divider */}
        <div className="my-3 border-t border-zinc-800" />

        {/* Coming soon items */}
        {comingSoon.map((item) => (
          <div
            key={item.label}
            className="flex items-center gap-3 px-3 py-2 rounded-md text-sm text-zinc-600 cursor-not-allowed select-none"
          >
            <Lock size={16} className="shrink-0" />
            <span className="flex-1">{item.label}</span>
            <span className="text-[10px] bg-zinc-800 text-zinc-500 rounded px-1 py-0.5 leading-tight">
              Soon
            </span>
          </div>
        ))}
      </nav>

      {/* Footer */}
      <div className="px-4 py-3 border-t border-zinc-800">
        <p className="text-[11px] text-zinc-600 font-mono">v0.1.0-alpha</p>
      </div>
    </aside>
  );
}
