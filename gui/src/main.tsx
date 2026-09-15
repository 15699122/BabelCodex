import React from "react";
import ReactDOM from "react-dom/client";
import App from "./App";
import "./styles.css";

async function bootstrap(): Promise<void> {
  // WebdriverIO E2E builds only: load the WDIO frontend plugin before the
  // app mounts so browser.tauri.execute/mock/log capture are available from
  // the first test command. Normal builds never include this import.
  if (import.meta.env.VITE_E2E === "1") {
    await import("@wdio/tauri-plugin");
  }

  ReactDOM.createRoot(document.getElementById("root")!).render(
    <React.StrictMode>
      <App />
    </React.StrictMode>,
  );
}

void bootstrap();