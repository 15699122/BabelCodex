# Codebase Map

单一职责来源：本表是“每个文件的功能、入口、维护描述”的唯一权威索引。新增/删除/重命名/变更职责的模块必须同步更新本表。
运行位置列说明：service = Python 服务进程；worker = BabelDOC worker 进程；gui = GUI 渲染进程（Tauri webview）；test = 测试进程；build = 构建脚本。

## src/codex_babeldoc — Python 服务端模块（service/worker 进程）

| 文件 | 职责 | 入口/公共符号 | 运行位置 | 主要依赖 | 测试 |
|---|---|---|---|---|---|
| `src/codex_babeldoc/__init__.py` | __init__ module | — | service | — | — |
| `src/codex_babeldoc/application/__init__.py` | __init__ module | — | service | — | — |
| `src/codex_babeldoc/application/mcp.py` | Minimal local stdio MCP server for scoped BabelCodex job operations | `McpError`; `McpServer`; `run_stdio`; `serve` | service | — | — |
| `src/codex_babeldoc/application/service.py` | service module | `InvocationSource`; `StartTranslationCommand`; `BabelCodexService` | service | — | — |
| `src/codex_babeldoc/application/sidecar.py` | Fixed JSONL sidecar boundary for the future GUI and MCP clients | `SidecarMethod`; `SidecarError`; `JsonlSidecar`; `run_jsonl`; `main` | service | — | — |
| `src/codex_babeldoc/backends/babeldoc_internal.py` | Backward-compatible facade over the versioned BabelDOC backend | `BabelDocInternalBackend` | service | — | — |
| `src/codex_babeldoc/backends/babeldoc_v064.py` | BabelDOC 0.6.x compatibility implementation | `detect_version`; `is_supported_version`; `assert_supported`; `normalize_watermark_mode`; `artifacts_from_result`; `convert_progress` | service | — | — |
| `src/codex_babeldoc/backends/babeldoc_worker.py` | BabelDOC worker process entry point | `main` | worker | — | — |
| `src/codex_babeldoc/backends/base.py` | base module | `PdfTranslateRequest`; `PdfTranslateResult`; `PdfBackend`; `ProgressEvent`; `EventSink` | service | — | — |
| `src/codex_babeldoc/backends/worker_client.py` | Main-process client for the BabelDOC worker subprocess | `worker_environment`; `WorkerClientError`; `worker_command`; `build_worker_request`; `run_worker` | service | — | — |
| `src/codex_babeldoc/backends/worker_protocol.py` | Versioned JSON protocol between the orchestrator and the BabelDOC worker | `TranslatorSpec`; `WorkerRequest`; `WorkerArtifact`; `WorkerProgress`; `WorkerResult`; `WorkerError` | service | — | — |
| `src/codex_babeldoc/cli.py` | cli module | `collect_doctor_checks`; `doctor`; `main` | service | — | — |
| `src/codex_babeldoc/core/artifact_manifest.py` | artifact_manifest module | `file_sha256`; `validate_artifacts` | service | — | — |
| `src/codex_babeldoc/core/artifacts.py` | artifacts module | `ArtifactType`; `Artifact` | service | — | — |
| `src/codex_babeldoc/core/config.py` | config module | `ProjectConfig`; `TranslationConfig`; `BabelDocConfig`; `CodexConfig`; `AppConfig`; `load_config` | service | — | — |
| `src/codex_babeldoc/core/errors.py` | errors module | `ErrorCategory`; `ErrorCode`; `BabelCodexError`; `classify_exception`; `safe_internal_error`; `resolve_retry_limits` | service | — | — |
| `src/codex_babeldoc/core/events.py` | events module | `EventType`; `JobEvent` | service | — | — |
| `src/codex_babeldoc/core/orchestrator.py` | orchestrator module | `Orchestrator` | service | — | — |
| `src/codex_babeldoc/core/pipeline_meta.py` | BabelDOC pipeline metadata recorded per job for operator inspection | `record_pipeline_meta` | service | — | — |
| `src/codex_babeldoc/core/private_data.py` | Best-effort permissions for local user document data | `ensure_private_dir`; `restrict_file` | service | — | — |
| `src/codex_babeldoc/core/state.py` | state module | `JobStatus`; `JobStage`; `JobState`; `file_fingerprint`; `job_id_for`; `StateStore` | service | — | — |
| `src/codex_babeldoc/core/workdir.py` | Safe, bounded removal of per-job BabelDOC working directories | `WorkdirError`; `remove_work_dir`; `resolve_work_dir`; `sweep_work_dirs` | service | — | — |
| `src/codex_babeldoc/qa/layout_checks.py` | Layout and visual heuristics for translated PDFs | `check_overflow`; `check_visual_blank` | service | — | — |
| `src/codex_babeldoc/qa/models.py` | QA data model for output PDF quality reports | `QaSeverity`; `QaFinding`; `QaReport`; `report_for` | service | — | — |
| `src/codex_babeldoc/qa/pdf_sanity.py` | L0 file-level and L1 structure-level sanity checks for output PDFs | `check_file_level`; `check_pdf_structure`; `check_pdf` | service | — | — |
| `src/codex_babeldoc/qa/report.py` | Assemble QA findings into a report and render human-safe views | `run_qa`; `to_text`; `save_report` | service | — | — |
| `src/codex_babeldoc/qa/resource_checks.py` | Resource and disk sanity checks run alongside output QA | `check_disk_space`; `check_output_size` | service | — | — |
| `src/codex_babeldoc/qa/text_checks.py` | L2 text-quality checks for translated PDFs | `page_texts`; `cjk_ratio`; `ascii_letter_ratio`; `check_blank_pages`; `check_translation_density`; `check_text_quality` | service | — | — |
| `src/codex_babeldoc/translation/__init__.py` | Translator-independent request, validation, batching and cache models | — | service | — | — |
| `src/codex_babeldoc/translation/batching.py` | Short-window batch queue for translation requests | `BatchWorker`; `build_batch_payload`; `parse_batch_response` | service | — | — |
| `src/codex_babeldoc/translation/cache.py` | SQLite-backed translation segment cache | `TranslationCache` | service | — | — |
| `src/codex_babeldoc/translation/context.py` | Bounded document context extraction | `DocumentContext`; `ContextExtractor` | service | — | — |
| `src/codex_babeldoc/translation/gateway.py` | Translation Gateway: the translator-independent core | `TranslationGateway` | service | — | — |
| `src/codex_babeldoc/translation/glossary.py` | Versioned glossary storage and bounded terminology guidance | `GlossaryEntry`; `read_csv`; `write_csv`; `version_for`; `glossary_prompt`; `GlossaryStore` | service | — | — |
| `src/codex_babeldoc/translation/models.py` | models module | `PlaceholderInventory`; `TranslationRequest`; `TranslationResult`; `TranslationBatch`; `ValidationResult` | service | — | — |
| `src/codex_babeldoc/translation/placeholders.py` | Structural token extraction and comparison | `extract_placeholder_counts`; `inventory_from_text`; `compare_inventories`; `tag_balance_errors`; `preserved_substrings`; `missing_preserved_substrings` | service | — | — |
| `src/codex_babeldoc/translation/retry.py` | Validation wrapper with exact-output repair retries | `ValidatingTranslator` | service | — | — |
| `src/codex_babeldoc/translation/thread_state.py` | Provider-neutral persistence contract for Codex translation thread IDs | `ThreadState`; `ThreadStateStore` | service | — | — |
| `src/codex_babeldoc/translation/validation.py` | Output cleanliness and placeholder validation for translations | `validate_translation` | service | — | — |
| `src/codex_babeldoc/translators/base.py` | base module | `TranslatorAdapter` | service | — | — |
| `src/codex_babeldoc/translators/codex_sdk.py` | codex_sdk module | `CodexSdkTranslator`; `build_developer_instructions`; `build_prime_prompt` | service | — | — |
| `src/codex_babeldoc/translators/factory.py` | Build translator instances from a JSON-serializable specification | `build_translator`; `build_validating_translator`; `build_gateway_translator` | service | — | — |
| `src/codex_babeldoc/translators/mock.py` | mock module | `MockTranslator` | service | — | — |
| `src/codex_babeldoc/translators/openai_compatible.py` | openai_compatible module | `OpenAICompatibleTranslator` | service | — | — |
| `src/codex_babeldoc/translators/scripted.py` | Deterministic scripted translator for tests and mock pipelines | `ScriptedTranslator` | service | — | — |

## tests — 测试模块（test 进程）

| 文件 | 职责 | 入口/公共符号 | 运行位置 | 主要依赖 | 测试 |
|---|---|---|---|---|---|
| `tests/test_application_service.py` | test_application_service module | `test_start_translation_records_invocation_source`; `test_get_and_list_jobs`; `test_validate_output_refreshes_manifest_and_detects_tampering`; `test_service_startup_recovers_legacy_active_job_without_runner_pid`; `test_run_qa_marks_failed_on_tampered_output` | test | — | — |
| `tests/test_babeldoc_compat.py` | Tests for the BabelDOC 0.6.x compatibility layer (no BabelDOC runtime needed) | `TestVersionDetection`; `TestWatermarkMapping`; `TestProgressConversion`; `TestArtifactsFromResult`; `TestLegacyFacade` | test | — | — |
| `tests/test_batching.py` | Tests for the batch worker and response parser | `test_batch_collects_items_and_flushes`; `test_batch_max_items_triggers_immediate_flush`; `test_batch_missing_id_raises`; `test_batch_shutdown_wakes_pending`; `test_build_batch_payload_structure`; `test_parse_batch_response_valid` | test | — | — |
| `tests/test_cache.py` | Tests for the SQLite translation cache | `test_cache_round_trip`; `test_cache_disabled_when_path_is_none`; `test_cache_key_includes_every_input`; `test_cache_ttl_expires`; `test_cache_stats_and_clear` | test | — | — |
| `tests/test_check_gui_bundle.py` | Regression tests for scripts/check_gui_bundle.py | `audit_module`; `test_https_urls_are_not_flagged_as_absolute_paths`; `test_windows_drive_path_is_flagged`; `test_unix_development_paths_are_flagged`; `test_file_scheme_url_path_is_still_flagged`; `test_url_strings_are_not_absolute_paths` | test | — | — |
| `tests/test_cli.py` | test_cli module | `test_collect_doctor_checks_detects_installed_runtime`; `test_doctor_succeeds_when_all_critical_checks_pass`; `test_doctor_fails_when_codex_is_not_authenticated`; `test_glossary_cli_import_and_list`; `test_toml_string_escapes_windows_path`; `test_inspect_and_validate_cli_for_missing_job` | test | — | — |
| `tests/test_config.py` | test_config module | `test_load_example_config` | test | — | — |
| `tests/test_docs_inventory.py` | Tests for scripts/check_docs_inventory.py | `test_repo_inventory_complete`; `test_repo_map_paths_exist`; `test_repo_readme_commands_registered`; `test_repo_doc_links_exist`; `test_repo_check_passes`; `test_repo_readme_has_cli_commands` | test | — | — |
| `tests/test_e2e_mock.py` | End-to-end tests: real BabelDOC pipeline driven through the orchestrator | `TestMockEndToEnd` | test | — | — |
| `tests/test_gateway.py` | Tests for the Translation Gateway pipeline | `test_gateway_passthrough_without_cache_or_batch`; `test_gateway_uses_cache_hit`; `test_gateway_cache_isolated_by_translator_metadata`; `test_gateway_repairs_invalid_output`; `test_gateway_invalid_source_returns_untranslated`; `test_gateway_translate_request_model` | test | — | — |
| `tests/test_glossary_context.py` | test_glossary_context module | `test_glossary_import_export_override_and_version`; `test_glossary_prompt_is_bounded_and_skips_disabled`; `test_context_extractor_is_bounded_and_stable`; `test_context_extractor_reads_pdf_metadata_and_opening_pages` | test | — | — |
| `tests/test_mcp.py` | Contract and security tests for the local stdio MCP adapter | `test_initialize_lists_scoped_tools_and_notifications_are_silent`; `test_stdio_round_trip_and_parse_error`; `test_start_get_validate_and_cleanup_are_scoped`; `test_cleanup_retries_transient_permission_error`; `test_run_qa_tool_is_scoped`; `test_cleanup_rejects_job_with_active_future` | test | — | — |
| `tests/test_mock.py` | test_mock module | `test_mock` | test | — | — |
| `tests/test_orchestrator_context.py` | test_orchestrator_context module | `test_orchestrator_builds_document_scoped_guidance`; `test_orchestrator_uses_pdf_context_when_no_sidecar_exists` | test | — | — |
| `tests/test_placeholders.py` | Placeholder extraction and multiset comparison tests | `test_extract_placeholder_counts`; `test_compare_inventories`; `test_inventory_round_trip_sorted`; `test_tag_balance`; `test_missing_preserved_substrings` | test | — | — |
| `tests/test_qa_checks.py` | Unit tests for the QA check layers (L0/L1 sanity, text, layout, resources) | `test_cjk_ratio_counts_unified_ideographs`; `test_file_level_checks_detect_missing_and_bad_header`; `test_structure_check_detects_corrupt_pdf`; `test_pdf_structure_accepts_generated_document`; `test_blank_pages_and_translation_density`; `test_text_quality_accepts_short_outputs_without_judging` | test | — | — |
| `tests/test_retry.py` | ValidatingTranslator retry behavior tests | `test_valid_output_passes_through_without_repair`; `test_placeholder_mismatch_triggers_repair_then_succeeds`; `test_repair_attempts_exhausted_raises_structured_error`; `test_markdown_fence_output_uses_invalid_output_code`; `test_max_repair_attempts_zero_fails_immediately` | test | — | — |
| `tests/test_retry_policy.py` | Error-category retry policy: pure resolution plus orchestrator no-loop gates | `test_auth_input_and_validation_categories_default_to_single_attempt`; `test_global_max_retries_is_the_ceiling_for_category_limits`; `test_operator_policy_lowers_a_category_and_ignores_unknown_keys`; `test_retry_limit_for_uses_defaults_for_unlisted_categories`; `test_auth_failure_never_auto_loops_even_if_marked_retryable`; `test_transient_translation_error_retries_to_category_limit` | test | — | — |
| `tests/test_sidecar.py` | Contract tests for the fixed GUI-sidecar JSONL boundary | `test_sidecar_rejects_path_outside_allowlist`; `test_sidecar_lists_jobs_without_exposing_shell`; `test_get_server_info_reports_protocol_version_and_capabilities`; `test_sidecar_reads_and_writes_scoped_glossary_and_context`; `test_sidecar_rejects_document_path_traversal`; `test_sidecar_rejects_windows_style_document_path_traversal` | test | — | — |
| `tests/test_state.py` | test_state module | `test_state_roundtrip`; `test_load_by_job_id_retries_transient_permission_error`; `test_load_by_job_id_raises_after_persistent_permission_error`; `test_transient_retry_budget_is_bounded` | test | — | — |
| `tests/test_state_v2.py` | test_state_v2 module | `test_job_state_v2_roundtrip`; `test_legacy_state_json_migrates`; `test_job_id_depends_on_config_fingerprint`; `test_classify_known_and_unknown_exceptions`; `test_config_fingerprint_stable_and_sensitive_to_change`; `test_atomic_save_no_tmp_left_and_file_is_json` | test | — | — |
| `tests/test_thread_state.py` | test_thread_state module | `test_thread_state_round_trip_and_rotation` | test | — | — |
| `tests/test_validation.py` | Output cleanliness validation tests | `test_validate_translation`; `test_error_codes_are_specific`; `test_clean_output_has_no_errors` | test | — | — |
| `tests/test_workdir.py` | Working-directory retention sweep and path-safe removal helpers | `test_sweep_removes_old_terminal_workdir`; `test_sweep_keeps_fresh_terminal_workdir_within_retention`; `test_sweep_keeps_active_job_workdir`; `test_sweep_dry_run_removes_nothing`; `test_sweep_refuses_symlinked_job_directory`; `test_resolve_work_dir_rejects_outside_root_and_root_itself` | test | — | — |
| `tests/test_worker.py` | Tests for the BabelDOC worker process protocol and subprocess client | `TestProtocolRoundTrip`; `TestWorkerEntry`; `TestRunWorker`; `TestWorkerEnvironment`; `TestWorkerCommand` | test | — | — |

## scripts — 构建与维护脚本（build/维护环境）

| 文件 | 职责 | 入口/公共符号 | 运行位置 | 主要依赖 | 测试 |
|---|---|---|---|---|---|
| `scripts/check_docs_inventory.py` | Documentation inventory checks | `documented_cli_commands`; `registered_cli_commands`; `mapped_source_paths`; `tracked_source_paths`; `broken_doc_links`; `main` | build | — | — |
| `scripts/check_gui_bundle.py` | Audit a staged BabelCodex GUI bundle without executing platform binaries | `contains_development_machine_absolute_path`; `sha256`; `newest_source_mtime`; `audit`; `main` | build | — | — |
| `scripts/generate_fixture.py` | Generate the self-made integration fixture PDF for BabelCodex | `build` | build | — | — |
| `scripts/generate_windows_icon.py` | Generate the Windows ``.ico`` application icon from the PNG source icon | `main` | build | — | — |
| `scripts/sidecar_entry.py` | Controlled top-level entry point for the PyInstaller-packaged sidecar | — | build | — | — |

## gui/src — GUI 前端模块（Tauri webview 渲染进程）

| 文件 | 职责 | 入口/公共符号 | 运行位置 | 主要依赖 | 测试 |
|---|---|---|---|---|---|
| `gui/src/filePicker.test.ts` | Tests for the Tauri/browser PDF file picker abstraction | — | gui | — | — |
| `gui/src/filePicker.ts` | PDF file picker abstraction: Tauri dialog vs browser fallback with PDF-only filter | `PickedPdf`; `FilePicker`; `isTauriRuntime`; `isPdfPath`; `createFilePicker` | gui | — | — |
| `gui/src/jobStore.test.ts` | Tests for the centralized GUI job state store with sidecar lifecycle | — | gui | — | — |
| `gui/src/jobStore.ts` | Centralized GUI state: sidecar lifecycle, job list sync, event cursor, polling, reconnect | `ConnectionState`; `JobStoreSnapshot`; `JobStore`; `isActiveJob`; `GlossaryEntry`; `GlossaryResult` | gui | — | — |
| `gui/src/protocol.test.ts` | Tests for the JSONL sidecar protocol types and (de)serialization | — | gui | — | — |
| `gui/src/protocol.ts` | JSONL sidecar protocol types: requests, responses, events, server info, compatibility assertion | `PROTOCOL_VERSION`; `JobStatus`; `JobStage`; `Artifact`; `JobState`; `JobEvent` | gui | — | — |
| `gui/src/sidecar.ts` | Sidecar transport abstraction: Tauri subprocess and mock transport for tests | `MockSidecarTransport`; `createSidecarTransport` | gui | — | — |
| `gui/src/test-setup.ts` | Vitest/React Testing Library global test setup with auto-cleanup | — | gui | — | — |

## 维护规则

1. 表格覆盖范围与 `scripts/check_docs_inventory.py` 的 tracked 集合一致：`src/**.py`、`tests/**.py`、`scripts/**.py`、`gui/src/**.ts`。
2. 文件必须以反引号路径出现（如 `` `src/codex_babeldoc/cli.py` ``），否则库存检查会判为 missing。
3. 不要引用 `.tsx` 路径——tracked 集合只含 `.py` 与 `.ts`。
4. 自动生成的“描述待补”条目应在下次修改该文件时补全。