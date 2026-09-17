import type { Metadata } from "next";
import { RunProvider } from "@/components/v2/run-context";

export const metadata: Metadata = {
  title: "Neverlost V2 · Longitudinal Evidence Analysis",
  description: "Live longitudinal evidence analysis with source-linked outputs, prioritization, deterministic validation, and human review. Curated synthetic cases only.",
  robots: { index: false, follow: false },
};
export default function Layout({ children }: { children: React.ReactNode }) {
  return <RunProvider>{children}</RunProvider>;
}
