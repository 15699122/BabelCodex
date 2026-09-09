# Cross-platform Development and Windows Validation Workflow

## 1. Purpose

本项目主要在 Linux 环境进行开发。

Windows 环境主要用于：

- Windows-specific build verification；
- Windows runtime verification；
- Windows packaging / installer verification；
- filesystem / path / process / sidecar 等平台相关验证；
- 项目文档定义的其他 Windows 验证。

Linux 项目目录是主要开发工作区和项目事实来源。Windows 项目目录是验证工作副本。

本流程与 `AGENTS.md` 及 [`docs/validation/windows.md`](../validation/windows.md) 配合使用：本文件定义跨平台开发和状态管理原则，Windows 文档定义具体验证步骤和结果记录格式。

## 2. Source of Truth

Linux 项目目录是以下内容的主要事实来源：

- source code；
- project configuration；
- project documentation；
- implementation state；
- Plan / task state；
- validation documentation。

Windows 工作副本主要用于验证，不作为主要开发源。

代码同步方向默认必须为：

```text
Linux → Windows
```

除验证文档结果外，不应将 Windows 工作副本中的代码修改自动反向同步到 Linux。

## 3. Development / Validation Cycle

标准工作流：

1. Linux implementation；
2. Linux verification；
3. Mark Windows verification requirements；
4. Sync Linux project to Windows；
5. Windows validation；
6. Write Windows validation results back to Linux documentation；
7. Linux reads and reconciles Windows results；
8. Continue implementation or fixes；
9. Repeat Windows validation when required。

不得将“Linux 已修复”视为“Windows 已验证通过”。

## 4. Validation State Model

平台相关任务应尽可能使用以下状态：

- `IMPLEMENTED`；
- `LINUX_VERIFIED`；
- `WINDOWS_VERIFICATION_PENDING`；
- `WINDOWS_PASS`；
- `WINDOWS_FAIL`；
- `WINDOWS_BLOCKED`；
- `NOT_RUN`；
- `NOT_APPLICABLE`。

典型状态流：

```text
IMPLEMENTED
  → LINUX_VERIFIED
  → WINDOWS_VERIFICATION_PENDING
  → WINDOWS_PASS
```

若 Windows 验证失败：

```text
WINDOWS_FAIL
  → Linux fix
  → LINUX_VERIFIED
  → WINDOWS_VERIFICATION_PENDING
  → Windows re-validation
```

Linux 端不得在 Windows 实际重新验证之前，将修复后的项目标记为 `WINDOWS_PASS`。

## 5. Linux Development Responsibilities

Linux Codex 负责：

- 阅读当前仓库和项目文档；
- 执行主要开发工作；
- 执行 Linux 平台适用的验证；
- 分析 Windows 验证结果；
- 修复真正属于项目代码的问题；
- 更新 Plan 和项目文档；
- 标记需要下一轮 Windows 验证的内容。

Linux Codex 不应：

- 假装执行了 Windows-only 验证；
- 将 Linux 测试成功等同于 Windows 验证成功；
- 为纯 Windows 环境配置问题修改项目代码；
- 无依据扩大当前任务范围。

## 6. Windows Validation Responsibilities

Windows Codex 负责：

- 读取 Linux 项目及项目文档；
- 将需要验证的内容从 Linux 单向同步至 Windows 工作副本；
- 根据仓库、文档、构建配置和脚本确定验证范围；
- 执行适用的 Windows 验证；
- 记录 `PASS` / `FAIL` / `BLOCKED` / `NOT RUN` / `NOT APPLICABLE`；
- 分析失败原因；
- 将实际验证结果写回 Linux 项目的验证文档。

Windows Codex 默认执行验证，而不是功能开发。

除机器本地配置、构建产物或验证所需临时变化外，不应为了让验证通过而自行修改业务代码。

若发现代码问题，应记录：

- failure；
- reproduction；
- likely root cause；
- relevant code location；
- suggested follow-up；

并交由 Linux 开发阶段处理。

## 7. Windows Synchronization Rules

Windows 验证工作区应以当前 Linux 项目状态为准。

同步前应检查：

- Linux branch；
- Linux commit；
- Linux working tree；
- Windows target directory；
- 是否存在 Windows 本地需要保留的配置。

默认不要跨平台同步：

- `.git`，除非验证流程需要；
- `node_modules`；
- Python virtual environments；
- Rust `target`；
- build caches；
- IDE caches；
- temporary files；
- secrets；
- machine-specific configuration。

优先使用项目已有的：

- sync scripts；
- checkout procedures；
- worktree workflow；
- build preparation scripts。

同步必须是 Linux → Windows 的单向操作。同步前后不得无条件删除未知文件，也不得覆盖 Windows 本地凭据、配置、缓存或机器特定状态。

## 8. Windows Validation Result Classification

每个验证项目至少应使用以下结果之一。

### PASS

验证实际执行，并满足预期。

### FAIL

验证实际执行，但项目行为或输出不符合要求。

应记录：

- command；
- failure point；
- relevant error；
- likely cause；
- whether Windows-specific；
- follow-up recommendation。

### BLOCKED

由于前置条件缺失无法继续。

例如：

- required dependency unavailable；
- certificate unavailable；
- external service unavailable；
- credential unavailable；
- prerequisite test/build failed；
- unsupported environment。

必须记录阻塞原因。

### NOT RUN

本轮未执行，但理论上应执行。必须说明原因。

### NOT APPLICABLE

根据当前项目或平台状态明确不适用。

所有状态都必须基于实际证据。不得将跳过、失败或被阻塞的项目记录为 `PASS`。

## 9. Reconciliation of Windows Results on Linux

当 Windows 验证结果写回 Linux 项目后，Linux Codex 必须先重新读取：

- `git diff`；
- modified documentation；
- current Plan；
- validation result documents；
- relevant `AGENTS.md` instructions。

然后重新评估当前 Plan。

应区分：

- 已经 Windows 验证完成的事项；
- Windows 失败且属于代码问题的事项；
- 环境问题；
- `BLOCKED` 项目；
- 尚未执行项目；
- 已不再适用的项目；
- 需要下一轮 Windows re-validation 的项目。

不得机械继续旧 Plan。当前仓库和最新验证结果优先于旧任务假设。

## 10. Handling Windows Failures

Windows `FAIL` 后，Linux Codex 首先判断问题属于：

- project code；
- Windows compatibility；
- dependency；
- environment；
- credential；
- external service；
- test infrastructure；
- unknown。

只有真正属于项目代码或必要兼容性问题时才修改代码。

修复后：

1. 执行 Linux 适用的 regression tests；
2. 执行相关 Linux verification；
3. 更新文档；
4. 将 Windows 状态改为 `WINDOWS_VERIFICATION_PENDING`，而不是 `WINDOWS_PASS`。

同时记录下一轮 Windows 应重新执行哪些验证。

纯 Windows 环境配置问题、缺失凭据或外部服务不可用不应通过修改业务代码解决；应保留失败/阻塞记录并在验证文档中说明处理方式。

## 11. Documentation Rules

Windows 实际验证历史必须保留，不得为了反映最新代码状态而删除历史失败记录。

推荐使用以下结构：

```text
Previous Windows validation:
FAIL

Issue:
...

Linux fix:
...

Linux verification:
PASS

Current Windows status:
WINDOWS_VERIFICATION_PENDING
```

验证文档应区分：

- Windows validation result；
- Linux implementation/fix；
- Linux verification；
- pending Windows re-validation。

具体 Windows 验证步骤、环境、命令、错误和未执行项目应记录在 [`docs/validation/windows.md`](../validation/windows.md) 中，避免在多个文档中产生互相矛盾的报告。

## 12. Plan Management

Windows 验证可能影响原 Plan。Linux Codex 读取结果后，应对 Plan 中每个剩余步骤判断：

- completed；
- still required；
- modified；
- obsolete；
- blocked；
- requires Windows re-validation。

Plan 的总体目标不应因为验证结果自动扩大。

只有当前仓库、明确需求或实际验证事实证明必要时，才能新增工作。

## 13. Verification Principles

Codex 应优先从仓库自动确定验证命令，包括：

- `AGENTS.md`；
- project documentation；
- CI configuration；
- package scripts；
- `Cargo.toml`；
- `pyproject.toml`；
- `package.json`；
- build scripts；
- test configuration。

不得凭空创造项目不存在的验证流程。

验证范围应根据当前实现和目标平台能力确定，并明确区分 Required、Applicable、Not applicable 以及最终结果状态。与认证 Codex、外部服务或付费额度有关的检查必须显式标记依赖条件，不能由普通单元测试隐式执行。

## 14. Final Diff Review

每轮 Linux 开发结束时检查最终 `git diff`。

确保：

- 没有无关修改；
- Plan / validation documentation 已更新；
- Windows 状态没有被错误标记；
- 需要重新验证的项目已经明确列出。

每轮 Windows 验证结束时同样检查：

- Windows 工作副本没有意外成为新的代码事实来源；
- Linux 端只接收预期的验证文档更新；
- 没有未经确认的代码反向同步。

如果本轮任务是验证而不是开发，最终 Linux diff 应只包含预期的验证文档更新；任何功能代码变化都必须有明确的开发任务和审查记录。

## 15. Core Principle

始终区分三个不同事实：

1. `Code implemented`；
2. `Linux verified`；
3. `Windows verified`。

只有在 Windows 平台实际执行并通过相应验证后，才能声明：

```text
Windows verified
```

Linux 代码已实现或 Linux 测试已通过，只能分别支持 `IMPLEMENTED` 或 `LINUX_VERIFIED`，不能单独支持 `WINDOWS_PASS`。