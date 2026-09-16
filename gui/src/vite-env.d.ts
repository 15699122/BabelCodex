/// <reference types="vite/client" />

// Conditional type declarations for the WebdriverIO Tauri frontend plugin.
//
// The plugin is loaded only in E2E builds (VITE_E2E=1). These declarations let
// TypeScript type-check the dynamic import in main.tsx without pulling the
// runtime dependency into normal builds.

declare module "@wdio/tauri-plugin" {
  const plugin: unknown;
  export default plugin;
}
