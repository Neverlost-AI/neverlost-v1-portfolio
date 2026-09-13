import type { Metadata } from "next";
import { Overview } from "@/components/overview";

export const metadata: Metadata = { title: "Capacity Windows — Neverlost V1 Synthetic Demo" };

export default function Page() {
  return <Overview view="Capacity Windows" />;
}
