---
name: origin-mpms-import
description: Reproduce MPMS3 magnetometry DAT processing through XLSX/CSV, native Origin OPJU projects and PNG/PDF, using confirmed sample mass, traceable segments, a pinned MCP snapshot and independent checks. 将 MPMS3 磁测数据复现至 Origin 工程与图形。
license: MIT
compatibility: Conversion requires Python and openpyxl. Full native plotting requires Windows and licensed Origin/OriginPro; the hardware baseline is OriginPro 2026.
---

# Origin Magnetometry

Follow the user's language and read [中文流程](references/zh-CN/workflow.md) or [English workflow](references/en/workflow.md). Both use the same STEP IDs and completion rules.

Resolve paths from this skill's actual location. Native end-to-end execution requires the complete repository/plugin, including root `scripts/`, `cases/` and `third_party/`. The repository root is two levels above the skill directory. An isolated skill folder provides its local conversion CLI only.

从技能实际位置解析路径。完整工程与绘图流程依赖完整仓库及本机 Origin；单独技能目录提供本技能的转换入口。先核对输入、实际样品质量或原始 emu 选择，再运行新输出目录；按实际证据报告完成层级。

Keep every source record in acquisition order, selected moment columns and actual X values. Verify dedicated Origin session ownership before project-changing calls. Return existing outputs and observed validation evidence, with the actual runtime and failure stages.
