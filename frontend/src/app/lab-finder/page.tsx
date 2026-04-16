"use client";

import dynamic from "next/dynamic";
import { PageShell } from "@/components/layout/PageShell";

const LabFinderClient = dynamic(
  () => import("@/components/lab-finder/LabFinderMap").then((m) => m.LabFinderClient),
  {
    ssr: false,
    loading: () => (
      <div className="flex items-center justify-center h-96 text-zinc-600 text-sm animate-pulse">
        Loading map…
      </div>
    ),
  }
);

export default function LabFinderPage() {
  return (
    <PageShell
      title="Lab Finder"
      subtitle="Find CROs and biological testing labs near you"
    >
      <LabFinderClient />
    </PageShell>
  );
}
