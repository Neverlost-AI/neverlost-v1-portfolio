import { notFound } from "next/navigation";
import { V2Workspace } from "@/components/v2/workspace";
import { surfaces } from "@/lib/v2/contracts";

export default async function Page({ params }: { params: Promise<{ view?: string[] }> }) {
  const { view } = await params;
  const selected = view?.[0] ?? "run";
  if ((view?.length ?? 0) > 1 || !surfaces.some(([key]) => key === selected)) notFound();
  return <V2Workspace view={selected} />;
}
