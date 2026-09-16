#![cfg_attr(not(debug_assertions), windows_subsystem = "windows")]

// Refuse to compile when both dev control surfaces are enabled: the MCP bridge
// and the WebdriverIO E2E plugin set must never appear in the same binary.
#[cfg(all(feature = "mcp-dev", feature = "e2e"))]
compile_error!("features `mcp-dev` and `e2e` are mutually exclusive");

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    let mut builder = tauri::Builder::default();

    // MCP development bridge: registered only with `--features mcp-dev`. It must
    // never be present in release builds or in E2E binaries.
    #[cfg(feature = "mcp-dev")]
    {
        builder = builder.plugin(
            tauri_plugin_mcp_bridge::Builder::new()
                .bind_address("127.0.0.1")
                .build(),
        );
    }

    // WebdriverIO E2E plugins: execute/mock/log APIs plus the embedded
    // WebDriver HTTP server. Compiled in only for `--features e2e` builds.
    #[cfg(feature = "e2e")]
    {
        builder = builder
            .plugin(tauri_plugin_wdio::init())
            .plugin(tauri_plugin_wdio_webdriver::init());
    }

    builder
        .plugin(tauri_plugin_dialog::init())
        .plugin(tauri_plugin_shell::init())
        .run(tauri::generate_context!())
        .expect("error while running BabelCodex GUI");
}
