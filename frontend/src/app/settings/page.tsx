"use client";
import { PageShell } from "@/components/layout/PageShell";
import { Lock } from "lucide-react";

const LLM_PROVIDERS = [
  { value: "anthropic", label: "Anthropic (Claude)" },
  { value: "openai", label: "OpenAI (GPT)" },
  { value: "gemini", label: "Google Gemini" },
  { value: "ollama", label: "Ollama (Local)" },
] as const;

const PREMIUM_FEATURES = [
  {
    id: "r_analysis",
    title: "R Analysis Runtime",
    description:
      "Execute R scripts, analyze statistical outputs, and import Rmd notebooks directly in CoScientist.",
    badge: "Premium",
  },
  {
    id: "colabfold",
    title: "ColabFold Integration",
    description:
      "Run AlphaFold2 structure predictions and analyze protein folding directly from your workflow.",
    badge: "Premium",
  },
] as const;

function SectionHeading({ children }: { children: React.ReactNode }) {
  return (
    <h2 className="text-sm font-semibold text-zinc-300 mb-4 pb-2 border-b border-zinc-800">
      {children}
    </h2>
  );
}

function SettingsCard({ children }: { children: React.ReactNode }) {
  return (
    <div className="bg-zinc-900 rounded-xl border border-zinc-800 p-6 space-y-5">
      {children}
    </div>
  );
}

export default function SettingsPage() {
  return (
    <PageShell title="Settings" subtitle="Configure your CoScientist workspace">
      <div className="max-w-2xl space-y-6">
        {/* LLM Provider */}
        <SettingsCard>
          <SectionHeading>LLM Provider</SectionHeading>
          <fieldset>
            <legend className="sr-only">Select LLM provider</legend>
            <div className="space-y-2">
              {LLM_PROVIDERS.map((provider) => (
                <label
                  key={provider.value}
                  className="flex items-center gap-3 p-3 rounded-lg border border-zinc-800 hover:border-zinc-700 hover:bg-zinc-800/40 cursor-pointer transition-colors group"
                >
                  <input
                    type="radio"
                    name="llm_provider"
                    value={provider.value}
                    defaultChecked={provider.value === "anthropic"}
                    className="w-4 h-4 accent-indigo-500"
                  />
                  <span className="text-sm text-zinc-300 group-hover:text-zinc-100">
                    {provider.label}
                  </span>
                </label>
              ))}
            </div>
          </fieldset>

          <div>
            <label htmlFor="default-model" className="block text-xs font-medium text-zinc-400 mb-1.5">
              Default Model
            </label>
            <input
              id="default-model"
              type="text"
              defaultValue="claude-opus-4-5"
              className="w-full bg-zinc-800 border border-zinc-700 rounded-lg px-3 py-2 text-sm text-zinc-200 font-mono focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
              placeholder="e.g. claude-opus-4-5, gpt-4o, gemini-2.0-flash"
            />
            <p className="text-xs text-zinc-600 mt-1.5">
              Override per-agent in agent config files.
            </p>
          </div>
        </SettingsCard>

        {/* Premium Features */}
        <SettingsCard>
          <SectionHeading>Premium Features</SectionHeading>
          <div className="space-y-3">
            {PREMIUM_FEATURES.map((feature) => (
              <div
                key={feature.id}
                className="flex items-start justify-between gap-4 p-4 rounded-lg border border-zinc-800 bg-zinc-800/20"
              >
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 mb-1">
                    <p className="text-sm font-medium text-zinc-300">{feature.title}</p>
                    <span className="text-[10px] font-medium bg-amber-400/10 text-amber-400 border border-amber-400/20 rounded px-1.5 py-0.5">
                      {feature.badge}
                    </span>
                  </div>
                  <p className="text-xs text-zinc-500 leading-relaxed">
                    {feature.description}
                  </p>
                  <p className="text-xs text-zinc-600 mt-2 flex items-center gap-1">
                    <Lock size={10} />
                    Contact us to enable this feature.
                  </p>
                </div>
                <div className="shrink-0">
                  <button
                    type="button"
                    disabled
                    aria-label={`${feature.title} is locked`}
                    title="Contact us to enable this feature"
                    className="relative w-10 h-6 bg-zinc-700 rounded-full cursor-not-allowed opacity-50"
                  >
                    <span className="absolute left-1 top-1 w-4 h-4 bg-zinc-500 rounded-full" />
                  </button>
                </div>
              </div>
            ))}
          </div>
        </SettingsCard>

        {/* Observability */}
        <SettingsCard>
          <SectionHeading>Observability</SectionHeading>
          <div className="flex items-start justify-between gap-4">
            <div>
              <p className="text-sm font-medium text-zinc-300">OpenTelemetry Tracing</p>
              <p className="text-xs text-zinc-500 mt-1">
                Export traces to an OTel-compatible backend (Jaeger, Tempo, Honeycomb).
              </p>
              <p className="text-xs text-zinc-600 mt-1.5">
                Configure OTEL_EXPORTER_OTLP_ENDPOINT in your environment.
              </p>
            </div>
            <div className="shrink-0">
              <button
                type="button"
                disabled
                aria-label="OpenTelemetry tracing toggle (disabled)"
                className="relative w-10 h-6 bg-zinc-700 rounded-full cursor-not-allowed opacity-50"
              >
                <span className="absolute left-1 top-1 w-4 h-4 bg-zinc-500 rounded-full" />
              </button>
            </div>
          </div>
        </SettingsCard>

        {/* Account */}
        <SettingsCard>
          <SectionHeading>Account</SectionHeading>
          <div className="space-y-3">
            <div>
              <label htmlFor="display-name" className="block text-xs font-medium text-zinc-400 mb-1.5">
                Display Name
              </label>
              <input
                id="display-name"
                type="text"
                defaultValue="Admin"
                className="w-full bg-zinc-800 border border-zinc-700 rounded-lg px-3 py-2 text-sm text-zinc-200 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
              />
            </div>
            <div>
              <label htmlFor="workspace" className="block text-xs font-medium text-zinc-400 mb-1.5">
                Workspace
              </label>
              <input
                id="workspace"
                type="text"
                defaultValue="default"
                readOnly
                className="w-full bg-zinc-800/50 border border-zinc-800 rounded-lg px-3 py-2 text-sm text-zinc-500 font-mono cursor-not-allowed"
              />
              <p className="text-xs text-zinc-600 mt-1.5">
                Workspace ID cannot be changed after creation.
              </p>
            </div>
          </div>
        </SettingsCard>

        {/* Save (placeholder) */}
        <div className="flex justify-end">
          <button
            type="button"
            onClick={() => alert("Settings are configured via environment variables and config files. See the documentation.")}
            className="px-5 py-2 bg-indigo-600 hover:bg-indigo-500 text-white text-sm font-medium rounded-lg transition-colors"
          >
            Save Changes
          </button>
        </div>
      </div>
    </PageShell>
  );
}
