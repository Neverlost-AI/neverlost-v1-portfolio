import type { Metadata } from "next";
import { RunProvider } from "@/components/v2/run-context";

export const metadata: Metadata = {
  title: "Neverlost V2 · Synthetic execution sandbox",
  description: "Actual historical Python execution against curated synthetic sources. Human review required.",
  robots: { index: false, follow: false },
};
export default function Layout({ children }: { children: React.ReactNode }) {
  return <RunProvider>{children}</RunProvider>;
}
