import type { Metadata } from "next";
import { V11Workspace } from "@/components/v11/workspace";
export const metadata: Metadata = { title: "Run Review" };
export default function Page() { return <V11Workspace view="review" />; }
