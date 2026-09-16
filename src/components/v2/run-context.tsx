"use client";
import { createContext, useContext, useState, type ReactNode } from "react";
import type { Run } from "@/lib/v2/contracts";

const RunContext = createContext<{ run: Run | null; setRun: (run: Run | null) => void } | null>(null);
export function RunProvider({ children }: { children: ReactNode }) {
  const [run, setRun] = useState<Run | null>(null);
  return <RunContext.Provider value={{ run, setRun }}>{children}</RunContext.Provider>;
}
export function useRun() {
  const context = useContext(RunContext);
  if (!context) throw new Error("V2 run context is unavailable.");
  return context;
}
