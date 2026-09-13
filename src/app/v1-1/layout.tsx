import type { Metadata } from "next";

export const metadata: Metadata = {
  title: { default: "V1.1 Foundation — Neverlost Synthetic Reconstruction", template: "%s — Neverlost V1.1 Reconstruction" },
  description: "A new deterministic reconstruction of selected recovered V1.1 rules, using independently invented synthetic inputs. Not the historical interface.",
};
export default function Layout({ children }: { children: React.ReactNode }) {
  return children;
}
