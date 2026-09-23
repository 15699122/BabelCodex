# Git-based Cross-platform Handoff Workflow

> **正式开发状态通过 Git 交接；直接文件同步只用于临时诊断，不产生正式项目状态。**

本文定义 BabelCodex 双 Owner 模式下的正式跨平台交接机制。所有权与路由规则见 `platform-ownership.md`，风险验证策略见 `../validation/validation-policy.md`，当前批次状态见 `../status/platform-handoff.md`，Windows 验证执行细节见 `cross-platform-validation.md`。

## 1. Purpose

本项目的正式跨平台协作使用 Git-based handoff。

长期正式流程：

`Linux → Git remote → Windows`

以及：

`Windows → Git remote → Linux`

直接 `Linux → Windows filesystem` 仅作为快速实验和诊断通道。

本规范用于明确：

- canonical state；
- platform handoff；
- workspace ownership；
- direct-sync boundary；
- branch/revision tracking；
- platform reconciliation。

## 2. Workspace Model

项目维护两个独立 working tree。

### Linux Working Tree

用途：

- Cross-platform development；
- shared architecture；
- shared tests；
- Linux/cross-platform validation。

应位于 Linux-native filesystem，例如 `~/projects/<project>`。不应从 `/mnt/<drive>` 进行常规开发。

### Windows Working Tree

用途：

- Windows-specific development；
- Windows runtime validation；
- Windows GUI；
- packaging / installer；
- Windows-native integration。

应位于 Windows-native filesystem，例如：

`E:\Projects\<project>`

两个 working tree：

- 各自拥有 `.git`；
- 各自维护自己的 build artifacts 和 dependency cache；
- 不通过文件镜像保持实时一致；
- 通过 Git revision 交换正式项目状态。

## 3. Canonical State

正式项目状态由 Git history、已提交项目文档、当前 Plan/task state 和平台验证记录共同定义。机器本地工作目录本身不是 canonical project state。

每次 platform handoff 必须能回答：

- 当前 branch 是什么？
- handoff source commit 是什么？
- 是否包含未提交修改？
- 谁是当前 Owner？
- 下一 Owner 应从哪个 revision 开始？

正式 handoff 默认不得依赖未提交修改。如果确实存在必须保留的 uncommitted state，应先：

- commit；
- 或建立明确的 temporary/WIP commit；

再进行正式 platform handoff。

## 4. Formal Linux -> Windows Handoff

Linux Cross-platform Owner 完成当前 batch 后：

1. 完成当前所有不依赖 Windows blocking result 的 Cross-platform 工作；
2. 执行最小必要 Linux/cross-platform validation；
3. 检查 `git diff`；
4. 更新当前 Plan 和 `platform-handoff.md`；
5. commit 当前 batch；
6. push 到 configured Git remote；
7. 在 handoff 文档中记录 source revision；
8. 将 ownership 转交给 Windows Platform Owner。

Windows Owner：

1. fetch remote；
2. 确认当前 Windows working tree 无未处理本地修改；
3. checkout/update 到 handoff revision；
4. 对照 handoff 文档确认 revision；
5. 开始 Windows batch。

## 5. Formal Windows -> Linux Handoff

Windows Owner 完成 Windows batch 后：

1. 完成 Windows-owned implementation；
2. 完成最小必要 Windows validation；
3. 处理 Windows-owned failures；
4. 标记（如适用）：
   - `CROSS_PLATFORM_CHANGE_REQUIRED`
   - `CROSS_PLATFORM_REVIEW_REQUIRED`
5. 更新 handoff / validation documentation；
6. 检查 final diff；
7. commit Windows batch；
8. push 到 Git remote。

如果没有 Cross-platform follow-up：

Windows batch 可以直接结束。

如果存在 Cross-platform follow-up：

Linux Owner：

1. fetch remote；
2. 更新 Linux working tree；
3. 阅读 Windows handoff；
4. review Windows shared changes；
5. 处理 Cross-platform follow-up。

## 6. Branch Strategy

默认优先保持简单。

同一逻辑 batch 可以使用同一个 feature/task branch：

`feature/<task>`

典型流程：

Linux: `A → B` → handoff to Windows → Windows: `B → C` → handoff to Linux when required → Linux: `C → D`

不要仅因为切换平台自动创建大量平台分支。

如果 Windows 实验具有较高风险或可能被丢弃，可以使用临时分支，例如：

`windows/experiment-<topic>`

实验稳定后再整合。

## 7. Handoff Revision

每次 handoff 都必须记录明确 revision。例如：

```text
Branch:
feature/foo

Source revision:
abc1234

Owner:
Cross-platform -> Windows
```

Windows 验证结果必须对应一个明确 revision。不能只记录“最新代码”。

如果 Windows 在验证前进行了 Windows-owned 修改，应记录：

```text
Input revision:
abc1234

Windows implementation revision:
def5678

Validation revision:
def5678
```

这样可以明确测试真正覆盖了哪个状态。

## 8. Direct Sync Fast Path

直接 `Linux → E:` 同步只用于：

- diagnostic experiment；
- exploratory Windows testing；
- blocking compatibility investigation；
- quick GUI/runtime check；
- 尚不值得形成正式 Git handoff 的临时状态。

Direct-sync workspace 必须：

- 是 disposable workspace；
- 或明确标记为 scratch；
- 与正式 Windows Owner repo 分离。

推荐约定：

```text
E:\Projects\<project>  = 正式 Windows Owner repository（只允许通过 Git 更新）
E:\Scratch\<project>   = direct-sync experimental workspace（唯一允许 Linux 直接同步的目标）
```

## 9. Direct Sync Restrictions

禁止 Linux direct sync 覆盖正式 Windows Owner working tree。

特别是在 Windows working tree 存在：

- uncommitted changes；
- Windows-owned implementation；
- local platform configuration；
- pending handoff；

时。

Direct sync 不得成为：

- formal commit history 的替代品；
- Windows-owned code 的长期存储位置；
- canonical validation revision；
- release source。

## 10. Experimental Result Promotion

如果 direct-sync experiment 得到有价值的结果：

### Result only

如果只是得到平台事实，例如：

“Windows API X 在该条件下不可用”

将证据写入 handoff / issue / validation documentation。然后由相应 Owner 根据 canonical Git state 正式实施。

### Experimental code worth keeping

不要直接把 scratch workspace 整体反向复制到正式项目。应：

1. 识别真正需要保留的 change；
2. 在正式 Owner repo 中重新应用或有控制地迁移；
3. review diff；
4. test；
5. commit；
6. 通过正常 Git workflow 集成。

## 11. Dirty Workspace Protection

任何正式 handoff 前都必须检查：

`git status`

如果目标 workspace 存在未提交修改：

不要直接 pull/reset/覆盖。

先判断：

- 当前修改属于谁；
- 是否已完成；
- 是否应 commit；
- 是否应 stash；
- 是否可安全丢弃。

不要自动使用 destructive reset 来解决 handoff 冲突。

## 12. Conflict Handling

如果 Linux 和 Windows 修改了相同 shared files：

使用 Git merge/rebase conflict 作为显式 reconciliation point。不要通过文件同步工具选择“较新的文件”来解决冲突。

解决冲突时应检查：

- ownership；
- intended behavior；
- shared contract；
- platform-specific requirements。

## 13. Cross-platform Review

如果 Windows commit 包含：

`CROSS_PLATFORM_REVIEW_REQUIRED`

Linux Owner 必须检查：

- shared API 是否改变；
- cross-platform behavior 是否改变；
- Linux behavior 是否受影响；
- shared tests 是否足够；
- Windows fix 是否泄漏平台逻辑到 shared core。

审查完成后：

- 接受；
- 调整；
- 或重新设计。

## 14. Validation and Revision Reuse

验证结果必须绑定到 revision。例如：

```text
WIN-BUILD-001
PASS
revision: def5678
```

后续 revision 如果没有影响该验证项相关的：

- files；
- dependencies；
- contracts；
- environment assumptions；

可以根据 validation policy 复用结果。

如果相关影响发生变化：

标记 `REVALIDATION_REQUIRED`。

详细规则见 `../validation/validation-policy.md`。

## 15. Platform Handoff Status

推荐状态：

- `CROSS_PLATFORM_IN_PROGRESS`
- `READY_FOR_WINDOWS`
- `WINDOWS_IN_PROGRESS`
- `WINDOWS_WORK_PENDING`
- `WINDOWS_VERIFICATION_PENDING`
- `WINDOWS_BLOCKING`
- `CROSS_PLATFORM_CHANGE_REQUIRED`
- `CROSS_PLATFORM_REVIEW_REQUIRED`
- `COMPLETE`

这些表示 workflow state，不代替测试结果：

- `PASS`
- `FAIL`
- `BLOCKED`
- `NOT_RUN`
- `NOT_APPLICABLE`

## 16. platform-handoff.md Template

`docs/status/platform-handoff.md` 建议保持为当前批次状态：

```text
# Current Platform Handoff

## Batch

Task:
Branch:
Current owner:
Current state:

## Revisions

Cross-platform input revision:
Cross-platform handoff revision:

Windows input revision:
Windows implementation revision:
Windows validation revision:

## Cross-platform Work Completed

-

## Windows Work Required

-

## Windows Validation Required

-

## Expected Behavior

-

## Known Risks

-

## Windows Results

Implementation:
-

PASS:
-

FAIL:
-

BLOCKED:
-

Manual validation required:
-

## Cross-platform Follow-up

CROSS_PLATFORM_CHANGE_REQUIRED:
-

CROSS_PLATFORM_REVIEW_REQUIRED:
-

## Next Owner

Owner:

Required actions:
-
```

只记录当前有效 handoff。历史验证放入独立历史文档，不要无限追加到 handoff 文件。

## 17. Batch Principle

平台交接应该按 batch 发生。

推荐：

```text
Linux A + B + C
→ Git handoff
→ Windows D + E + validation
→ Git handoff if required
```

不要采用：

```text
Linux A → Git → Windows → Git → Linux B → Git → Windows
```

除非存在真正的 `WINDOWS_BLOCKING`。

## 18. Core Rules

1. Git history defines formal project state.
2. Git remote is the normal platform exchange point.
3. Linux and Windows maintain independent native working trees.
4. Direct filesystem sync is diagnostic-only.
5. Direct sync must not overwrite the formal Windows Owner repository.
6. Platform handoff must identify a revision.
7. Validation results should identify the revision they tested.
8. Windows-owned code may be developed and committed on Windows.
9. Shared-contract changes belong to the Cross-platform Owner.
10. Prefer batch handoff over platform ping-pong.

## 19. Daily Operating Prompts

规则固化之后，日常 Prompt 无需重复说明 Git 的全部细节。

### Linux — Cross-platform Owner

接手当前 Cross-platform batch。

读取：

- `AGENTS.md`
- `docs/development/platform-ownership.md`
- `docs/development/git-platform-handoff.md`
- `docs/validation/validation-policy.md`
- `docs/status/platform-handoff.md`
- 当前 Plan

首先 fetch/reconcile 最新 canonical Git state，并确认当前 branch、revision、working tree 与 handoff 状态。

然后：

- reconcile Windows 上一轮 implementation / validation；
- review `CROSS_PLATFORM_REVIEW_REQUIRED`；
- 处理 `CROSS_PLATFORM_CHANGE_REQUIRED`；
- 继续所有仍属于 Cross-platform Owner 的工作；
- 不接管仍属于 Windows Owner 的 Windows-specific implementation；
- 采用最小必要 validation；
- 将非阻塞 Windows work / verification 累积到下一 Windows batch；
- 完成所有非 Windows-dependent 工作后，再形成正式 Windows handoff。

正式 handoff 前：

1. 检查 final `git diff`；
2. 更新 Plan 和 `docs/status/platform-handoff.md`；
3. 确认 handoff revision；
4. commit 当前 Cross-platform batch；
5. push 到 configured Git remote；
6. 将状态更新为 `READY_FOR_WINDOWS`。

不要通过直接覆盖 `E:` 盘正式 Windows repo 来完成 handoff。

如果仅需要快速 Windows 实验且不值得形成正式 handoff，可以使用 direct-sync scratch path；该结果必须视为 experimental，不得作为 canonical project state。

最后报告：

- branch；
- input revision；
- Cross-platform handoff revision；
- 完成的 Cross-platform work；
- validation scope/results；
- Windows work queue；
- Windows validation queue；
- 是否存在 `WINDOWS_BLOCKING`；
- 下一 Owner。

### Windows — Windows Platform Owner

接手当前 Windows Platform batch。

读取：

- `AGENTS.md`
- `docs/development/platform-ownership.md`
- `docs/development/git-platform-handoff.md`
- `docs/validation/validation-policy.md`
- `docs/status/platform-handoff.md`
- 当前 Plan

首先：

1. fetch configured Git remote；
2. 检查 Windows working tree 是否存在未提交修改；
3. 将正式 Windows repo 更新到 handoff revision；
4. 确认实际 revision 与 `platform-handoff.md` 一致。

不要通过 Linux 目录直接覆盖正式 Windows working tree。

然后：

- 完成所有当前 Windows-owned implementation；
- 完成最小必要 Windows validation；
- Windows-owned failure 直接修复并重新验证；
- shared/contract 问题标记 `CROSS_PLATFORM_CHANGE_REQUIRED`；
- 小型 shared implementation change 标记 `CROSS_PLATFORM_REVIEW_REQUIRED`；
- Computer Use 不可用时使用 `BLOCKED + Manual Windows Validation Queue`；
- 尽量完成整个 Windows batch，避免无必要的平台往返。

Windows batch 完成后：

1. 检查 final `git diff`；
2. 更新 validation / handoff documentation；
3. 记录实际 Windows validation revision；
4. commit Windows-owned changes；
5. push 到 configured Git remote；
6. 仅在存在 Cross-platform follow-up 时将 ownership 返回 Linux。

如果不存在 Cross-platform follow-up，可以直接结束当前 batch。

如果需要快速测试尚未正式 handoff 的 Linux 中间状态，只能使用独立 scratch workspace。此类 direct-sync 测试：

- 不得覆盖正式 Windows repo；
- 不得成为正式 Windows implementation；
- 不得将 scratch state 标记为 canonical；
- 有价值的代码必须通过正常 Git workflow 重新集成。

最后报告：

- input branch/revision；
- Windows implementation revision；
- Windows validation revision；
- 完成的 Windows-owned work；
- PASS / FAIL / BLOCKED；
- Manual Validation Queue；
- `CROSS_PLATFORM_CHANGE_REQUIRED`；
- `CROSS_PLATFORM_REVIEW_REQUIRED`；
- 是否需要新的 Git handoff；
- 下一 Owner。

### 正式循环

```text
Linux Cross-platform Owner
        ↓
   batch development
        ↓
 targeted validation
        ↓
   commit + push
        ↓
   Git remote (GitHub)
        ↓
Windows Platform Owner
        ↓
 implementation + validation
        ↓
   commit + push
        ↓
   Git remote (GitHub)
        ↓
Linux only when cross-platform follow-up exists
```

同时保留一个完全独立的快速通道：

```text
Linux unfinished state
        ↓
direct sync
        ↓
E:\Scratch\<project>
        ↓
diagnostic experiment
        ↓
discard / record evidence
```

### 核心硬规则

**`E:\Projects\<project>` 永远只通过 Git 更新；`E:\Scratch\<project>` 才允许 Linux 直接同步。**

这一条最大限度避免在两种同步机制之间混淆正式状态与实验状态。