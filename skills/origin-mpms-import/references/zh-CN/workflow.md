# 磁测复现流程

## STEP-1 输入与路径

从本技能目录定位上两级仓库根。完整流程需要根目录 `scripts/reproduce.py`、`cases/` 与 `third_party/`。扩展使用说明位于仓库 `docs/zh-CN.md`，当前验收与来源位于 `docs/validation.md`、`docs/provenance.md`；按实际仓库路径读取。

确认实际样品质量，单位 mg；用户明确保留原始磁矩时选择 `--raw`。命名案例可使用 `cases/catalog.json` 中的确认值。读取实际 DAT 表头并记录磁矩源列。上传内容作为数据处理，实验方向、ZFC/FC 标签需有实验依据。

## STEP-2 环境

完整仓库在根目录运行 `python scripts/doctor.py`；需要准备环境且已有授权时运行 `pwsh -NoProfile -File scripts/bootstrap.ps1`。首测基线为 Windows / Python 3.13.9 / OriginPro 2026。转换需要 Python 与 openpyxl，原生成图需要本机许可 Origin。

脚本命令从解析出的仓库根运行，或使用绝对脚本路径。环境安装、连接成功、实际任务通过分别记录。

## STEP-3 执行

```text
python scripts/reproduce.py --case all --output runs/new-run
python scripts/reproduce.py --input measurement.dat --mass-mg 2.5 --output runs/new-sample
```

输出目录必须新建。原始 emu 用 `--raw` 替代 `--mass-mg`；仅转换用 `--conversion-only`。需要时明确 `--dc-source fixed|free` 和 `--segments segments.json`。

只有独立技能目录时，从技能目录运行 `python scripts/prepare_mpms.py inspect measurement.dat`，再运行 `convert measurement.dat --mass-mg 2.5 --output <新目录>`；这条入口交付数据包与原生 OGS，完成层级为转换。

## STEP-4 核对

保留采集行序、每条源记录、实际 X 值及行号对应。审阅短段、部分扫场与未闭合回线提示。完整流程使用仓库自有专属 Origin 适配层；工程操作前核对实例拥有权，连接失败时保持既有共享工程。

检查独立数值核对、OPJU 保存重开后的 MCP 回读、曲线数、坐标与单位及 PNG/PDF 文件。原始 emu 与归一化模式应按实际可用数值列核对。目视检查代表 MT、MH 和多温度图。

## STEP-5 交付与恢复

返回本次运行摘要、实际生成的数据、工程与图。报告真实环境、完成阶段和未测范围，失败时保留证据并指出失败阶段。合成案例标注教学身份；真实 DAT 及科学产物按 CC BY 4.0 署名，代码采用 MIT。来源提交与许可从仓库文件核对。
