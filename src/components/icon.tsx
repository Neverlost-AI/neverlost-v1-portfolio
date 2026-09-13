import type { SVGProps } from "react";

export type IconName = "overview" | "timeline" | "evidence" | "bottleneck" | "hidden" | "capacity" | "reports" | "arrow" | "external" | "close" | "info" | "chevron" | "source";

const paths: Record<IconName, React.ReactNode> = {
  overview: <><rect x="3" y="3" width="7" height="7" rx="1.5" /><rect x="14" y="3" width="7" height="7" rx="1.5" /><rect x="3" y="14" width="7" height="7" rx="1.5" /><rect x="14" y="14" width="7" height="7" rx="1.5" /></>,
  timeline: <><path d="M6 3v18M10 6h10M10 12h7M10 18h10" /><circle cx="6" cy="6" r="1" /><circle cx="6" cy="12" r="1" /><circle cx="6" cy="18" r="1" /></>,
  evidence: <><rect x="3" y="4" width="18" height="16" rx="2" /><path d="M3 10h18M9 4v16M15 10v10" /></>,
  bottleneck: <><path d="M4 4h16l-6 8v7l-4 2v-9Z" /></>,
  hidden: <><path d="M2 12s4-7 10-7 10 7 10 7-4 7-10 7S2 12 2 12Z" /><circle cx="12" cy="12" r="3" /></>,
  capacity: <><rect x="3" y="5" width="16" height="14" rx="2" /><path d="M22 9v6M7 9v6M11 9v6M15 9v6" /></>,
  reports: <><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8Z" /><path d="M14 2v6h6M8 13h8M8 17h6" /></>,
  arrow: <path d="M4 12h16m-6-6 6 6-6 6" />,
  external: <><path d="M14 3h7v7M21 3 10 14M10 3H5a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-5" /></>,
  close: <path d="m6 6 12 12M6 18 18 6" />,
  info: <><circle cx="12" cy="12" r="9" /><path d="M12 11v6M12 7h.01" /></>,
  chevron: <path d="m9 5 7 7-7 7" />,
  source: <><path d="m10 13 4-4M8 16l-2 2a3 3 0 0 1-4-4l5-5a3 3 0 0 1 4 0M13 15a3 3 0 0 0 4 0l5-5a3 3 0 0 0-4-4l-2 2" /></>,
};

export function Icon({ name, ...props }: SVGProps<SVGSVGElement> & { name: IconName }) {
  return <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true" {...props}>{paths[name]}</svg>;
}
