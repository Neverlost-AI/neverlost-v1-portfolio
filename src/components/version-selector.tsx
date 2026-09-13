import Link from "next/link";
import styles from "./version-selector.module.css";

export function VersionSelector({ current }: { current: "v1" | "v11" }) {
  return <nav className={styles.versions} aria-label="Portfolio version">
    <span>VERSION</span>
    <Link href="/" aria-current={current === "v1" ? "page" : undefined}>V1 · Frozen demo</Link>
    <Link href="/v1-1" aria-current={current === "v11" ? "page" : undefined}>V1.1 · Reconstruction</Link>
  </nav>;
}
