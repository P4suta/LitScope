import { resolve } from "node:path";
import { defineConfig } from "vitest/config";

export default defineConfig({
  resolve: {
    alias: {
      "@": resolve(import.meta.dirname, "src"),
    },
  },
  test: {
    environment: "happy-dom",
    setupFiles: ["src/test-setup.ts"],
    coverage: {
      provider: "v8",
      include: ["src/**/*.{ts,tsx}"],
      exclude: [
        "src/main.tsx",
        "src/routeTree.gen.ts",
        "src/vite-env.d.ts",
        "src/**/*.test.{ts,tsx}",
        "src/test-setup.ts",
        "src/test-utils.tsx",
        "src/**/index.ts",
      ],
      thresholds: {
        branches: 100,
      },
    },
  },
});
