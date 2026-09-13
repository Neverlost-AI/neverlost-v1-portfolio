import { defineConfig, globalIgnores } from "eslint/config";
import { fixupConfigRules } from "@eslint/compat";
import nextVitals from "eslint-config-next/core-web-vitals";
import nextTypeScript from "eslint-config-next/typescript";

export default defineConfig([
  // Next's React plugin still uses context APIs removed in ESLint 10.
  // The official adapter preserves the rules; none are disabled.
  ...fixupConfigRules([...nextVitals, ...nextTypeScript]),
  globalIgnores([".next/**", "out/**", "next-env.d.ts", "playwright-report/**", "test-results/**"]),
]);
