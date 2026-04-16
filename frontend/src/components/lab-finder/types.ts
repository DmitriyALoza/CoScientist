export type SearchStatus =
  | "idle"
  | "locating"
  | "searching"
  | "results"
  | "empty"
  | "error"
  | "no-key";

export interface AssayCategory {
  id: string;
  label: string;
  keywords: string[];
  color: string;
}

export const ASSAY_CATEGORIES: AssayCategory[] = [
  {
    id: "flow_cytometry",
    label: "Flow Cytometry",
    keywords: ["flow cytometry lab CRO", "FACS core facility"],
    color: "bg-blue-500/10 text-blue-400 border-blue-500/20",
  },
  {
    id: "elisa",
    label: "ELISA / Immunoassay",
    keywords: ["ELISA laboratory", "immunoassay CRO"],
    color: "bg-purple-500/10 text-purple-400 border-purple-500/20",
  },
  {
    id: "genomics",
    label: "Genomics / Sequencing",
    keywords: ["genomics sequencing lab", "next generation sequencing core"],
    color: "bg-indigo-500/10 text-indigo-400 border-indigo-500/20",
  },
  {
    id: "proteomics",
    label: "Proteomics / Mass Spec",
    keywords: ["proteomics mass spectrometry laboratory", "LC-MS CRO"],
    color: "bg-emerald-500/10 text-emerald-400 border-emerald-500/20",
  },
  {
    id: "cell_culture",
    label: "Cell Culture / In Vitro",
    keywords: ["cell culture laboratory", "in vitro CRO"],
    color: "bg-cyan-500/10 text-cyan-400 border-cyan-500/20",
  },
  {
    id: "histology",
    label: "Histology / IHC",
    keywords: ["histology laboratory", "immunohistochemistry core"],
    color: "bg-rose-500/10 text-rose-400 border-rose-500/20",
  },
  {
    id: "pharmacokinetics",
    label: "PK / ADME",
    keywords: ["pharmacokinetics CRO ADME", "bioanalytical laboratory"],
    color: "bg-amber-500/10 text-amber-400 border-amber-500/20",
  },
  {
    id: "toxicology",
    label: "Toxicology / Safety",
    keywords: ["toxicology laboratory CRO", "GLP safety testing"],
    color: "bg-orange-500/10 text-orange-400 border-orange-500/20",
  },
  {
    id: "microbiology",
    label: "Microbiology",
    keywords: ["microbiology testing lab", "biosafety laboratory"],
    color: "bg-lime-500/10 text-lime-400 border-lime-500/20",
  },
  {
    id: "imaging",
    label: "Imaging / Microscopy",
    keywords: ["confocal microscopy core facility", "preclinical imaging CRO"],
    color: "bg-sky-500/10 text-sky-400 border-sky-500/20",
  },
  {
    id: "cro_general",
    label: "General CRO",
    keywords: ["contract research organization biology", "CRO laboratory services"],
    color: "bg-zinc-500/10 text-zinc-400 border-zinc-600/20",
  },
];
