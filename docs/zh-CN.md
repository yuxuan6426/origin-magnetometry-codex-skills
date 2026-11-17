# 使用指南

[English](en.md) · [仓库首页](../README.md)

## 环境与第一次复跑

完整流程的实机基线为 Windows / Python 3.13.9 / OriginPro 2026（10.30018）。需要已安装、已激活的 Origin/OriginPro。代码、依赖和 MCP 来自仓库；Origin 软件由使用者提供。引导脚本要求 Python 3.13.9；需要指定解释器时，给 `bootstrap.ps1` 传入 `-Python` 及其实际路径。

在完整仓库根目录执行：

```powershell
pwsh -NoProfile -File scripts/bootstrap.ps1
.\.venv\Scripts\python.exe scripts/doctor.py
.\.venv\Scripts\python.exe scripts/reproduce.py --case synthetic --output runs/first
```

先阅读 doctor 输出。包安装成功表示相应依赖就绪；Origin 成图、保存重开和回读以复跑报告为准。已有输出目录应保留，每次选择新目录。

完整复跑包含转换、独立核对和原生 Origin 验收。仅需要数据表时加 `--conversion-only`；该结果应标明转换完成的层级。

## 输入和质量

使用 MPMS3 测量汇总 DAT，脚本读取实际 `[Data]` 表头，并检查温度、磁场与磁矩列。原始扫描电压 `.rw.dat` 需要对应扫描处理流程。

质量以使用者确认的实际样品质量为准，单位 mg。文件名和仪器头部的 `Mass (grams)` 字段不能代替确认值。

```powershell
.\.venv\Scripts\python.exe scripts/reproduce.py --input "measurement.dat" --mass-mg 2.5 --output runs/measurement
.\.venv\Scripts\python.exe scripts/reproduce.py --input "measurement.dat" --raw --output runs/raw
```

归一化为 `magnetization_emu_g = moment_emu / mass_mg × 1000`。原始 emu 与归一化 emu/g 同时保留；`--raw` 明确选择原始磁矩。方向、ZFC/FC 等实验标签应有实验记录或使用者说明。

需要先检查表头、分段或选择 DC 源列，可直接调用技能的转换入口：

```powershell
.\.venv\Scripts\python.exe skills/origin-mpms-import/scripts/prepare_mpms.py inspect "measurement.dat"
.\.venv\Scripts\python.exe skills/origin-mpms-import/scripts/prepare_mpms.py convert "measurement.dat" --mass-mg 2.5 --dc-source fixed --output runs/table-only
```

VSM 使用 `Moment (emu)`；DC 在 `fixed` / `free` 中明确选择，默认 `fixed`。每次 manifest 记录实际源列。磁矩含义、实验方法与可用列不一致时，先核对实验记录再转换。

## 分段与核对

处理按采集行序划分连续模式、MT 升降温、MH 温度平台与独立扫场。保留各段实际温度和磁场，每条记录恰好覆盖一次。自动分组使用仓库的参数配置；需要人工段界时，可给转换入口传入 `--segments segments.json`。

```json
[
  {"first_record": 1, "last_record": 100, "category": "MT", "direction": "warming"},
  {"first_record": 101, "last_record": 200, "category": "MH_loop"}
]
```

区间采用从 1 开始、包含首尾的有效记录序号；必须按原序完整覆盖。上例仅说明格式，记录范围应按实际输入确定。类别为 `MT`、`MH_loop`、`MH_initial`、`MH_partial`。

| 提示 | 核对事项 |
|---|---|
| `short_segment_review` | 段内点数较少，核对测量边界 |
| `open_or_incomplete_cycle` | 回线可能未闭合，保留实测起止场 |
| `one_way_or_partial_sweep` | 单向或部分扫场，结合实验程序判断用途 |
| `explicit_segment_boundary` | 本段使用显式段界 |

这些提示不会平滑、补点或改变原始测量值。完整数据质量与物理解释应结合实验记录。

## 输出与 Origin

每份转换包包含宽表 `wide.xlsx`、逐段 `per_curve.xlsx`、`csv/`、`manifest.json`、`source_rows.csv` 和 `import_and_plot.ogs`。XLSX 前三行为名称、单位、条件，数值从第 4 行开始。MT 用温度作 X，MH 用磁场作 X。

完整复跑进一步生成可编辑 OPJU、单段图、分类总览、PNG/PDF 与验收摘要。脚本保存并重开工程，核对表内数值、曲线数与坐标标签。具体产物路径以当前运行摘要为准。

原生导入也可在 Origin 空白工程运行：按 Alt+3 打开命令窗口，执行以下命令并选择转换包目录：

```text
run.section("C:\your-package\import_and_plot.ogs", Main);
```

这里的路径是占位示例。已有工程或结果保护提示出现时，保留原文件并选用空白工程、新输出位置。

## 在 Codex 中使用

保留完整仓库。`plugin.json` 包含技能身份，`.agents/plugins/marketplace.json` 指向仓库根插件。可按当前 Codex 插件界面安装本地仓库插件，然后在新聊天调用：

```text
使用 $origin-mpms-import 复现 real-0p5mg，完整执行到 Origin 工程和 PNG/PDF，并报告数值核对与环境。
```

技能会从自身位置定位仓库及脚本。MCP 由本次复跑适配层启动；插件清单不硬编码本机解释器或共享 Origin 连接。安装后的首次运行检查技能目录、脚本、Python 与 Origin，再记录任务证据。[官方插件包装说明](https://developers.openai.com/plugins/build/plugins)

## 失败恢复

读运行摘要中失败阶段，保留原输入和该次证据。转换错误先核对表头、质量、源列与段界；Origin 连接问题先核对安装、许可、依赖与专属会话拥有权。适配层不得将连接失败转为操作既有共享工程。修复后使用新目录重跑相关阶段，最终结论以通过的实际检查为准。

## 工程移动后的回读

将完整单案例产物目录（含 OPJU、manifest、CSV 和 OGS）放到新位置后，可用以下入口检查保存工程；路径替换为实际位置，输出仍需新目录：

```powershell
.\.venv\Scripts\python.exe scripts/verify_relocated_projects.py --packages "moved/synthetic" "moved/real-0p5mg" "moved/real-24mg" --output runs/relocation-check
```

检查在专属 Origin 实例中打开和回读已有工程，保留工程文件原状；结果写入 `relocation-report.json`。本仓库已验证同机完整源码复制重定位及工程移动后回读，使用同一锁定环境与安装的 Origin；全新 Git 检出、全新 OS 和第二设备状态单独记录。
