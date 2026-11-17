# 案例与验证 / Cases and validation

This page separates historical measurements from the current repository entry point. / 本页区分历史实测与当前仓库入口的执行结果。

## 可复现输入 / Reproducible inputs

| Case | Input | Confirmed mass | Valid records | Segments | Native graphs |
|---|---|---:|---:|---:|---:|
| `synthetic` | Generated teaching data | 2 mg | 41 | 3 | 5 |
| `real-0p5mg` | `cases/real-0p5mg/input/measurement.dat` | 0.5 mg | 1,809 | 27 | 30 |
| `real-24mg` | `cases/real-24mg/input/measurement.dat` | 24 mg | 4,242 | 32 | 37 |

The synthetic case is generated for learning and testing; it is not an experimental measurement. The two real cases are authorized measurements. / 合成示例用于教学与测试；两份真实案例为授权测量材料。

## 数值与图形契约 / Numerical and graphical contract

- Each input record appears once in acquisition order, with a source row mapping. / 每条输入记录按采集顺序覆盖一次，并保留源行对应。
- Raw moment and mass normalization follow the selected source column and confirmed mass. / 使用所选磁矩列和确认质量，保留原始与归一化值。
- An independent parser checks CSV and XLSX values. CSV uses exact numeric comparison for the same formula; XLSX allows `rel_tol=2e-12`, `abs_tol=1e-12`. / 独立解析器核对保存值；容差用于浮点保存差异。
- Origin projects are saved, reopened and read through MCP. Readback allows `rel_tol=2e-11`, `abs_tol=1e-11`. / Origin 工程保存重开后经 MCP 回读。
- Normalized runs verify four numerical columns: temperature, field, raw moment and normalized magnetization. Raw-emu runs verify the three populated numerical columns and the emu axis label. / 归一化模式回读温度、磁场、原始磁矩及归一化值四列；原始 emu 模式回读三列有效数值并核对 emu 轴标签。
- Tables, graph count, plotted series, axes and units are checked. PNGs must decode; each PDF must open as one page. Representative figures receive visual review. / 核对表、图与曲线数量及轴单位，检查导出文件并审阅代表图。
- Output must use a new directory. Test cases include invalid mass, raw emu, explicit boundaries and paths with spaces or Chinese characters. / 验证新目录保护、质量错误、原始 emu、显式段界和中文空格路径。

## 证据层级 / Evidence levels

| Layer | Status | Meaning |
|---|---|---|
| Historical real-case conversion | Passed, 2026-11-17 | Two complete DAT inputs; saved XLSX/CSV values and row coverage checked |
| Historical OriginPro 2026 | Passed, 2026-11-17 | Native import, graphs, OPJU save/reopen, full numerical readback and PNG/PDF export |
| Current entry point: synthetic case | Passed, 2026-11-18 | 41 records / 3 segments / 5 graphs; dedicated adapter and native export completed |
| Current entry point: real cases | Passed, 2026-11-18 | 1,809 / 27 / 30 and 4,242 / 32 / 37 records, segments and graphs; independent audits, OPJU reopening and MCP readback passed |
| Current entry point: raw emu | Passed, 2026-11-18 | 41 records / 3 segments / 5 graphs; independent audit, three-column Origin readback, emu axis, OPJU reopening and 5 PNG / 5 PDF exports passed |
| Existing-session protection | Passed, 2026-11-18 | Existing Origin PID retained; all 15 observed window titles unchanged; dedicated adapter exited |
| Environment and source integrity | Passed, 2026-11-18 | Read-only doctor verified required modules and unchanged MCP snapshot; doctor did not connect to Origin |
| Local tests and dependencies | Passed, 2026-11-18 | 5 tests passed, including rejection of an untrusted endpoint before connection; no broken installed requirements |
| Same-machine copied-source relocation | Passed, 2026-11-18 | Complete source copied to a new neutral directory; all three cases rebuilt using the same locked environment and installed Origin |
| Saved-project relocation | Passed, 2026-11-18 | Three projects opened and fully read back without saving at another location while original import-package locations were unavailable |
| Public OPJU metadata | Passed, 2026-11-18 | Native neutral-path rebuild; zero author-path matches in the three distributed projects |
| Fresh Git clone | Pending | Copied-source relocation and a fresh Git clone are separate checks |
| Origin 2018–2025 | Untested on hardware | Earlier OGS interfaces were designed for compatibility; no hardware claim |
| Other machines / clean OS | Untested | Current repository runs use the same machine and installed Origin; no clean-OS or second-machine claim |
| Other agent hosts | Untested | Packaging and installation do not establish task execution |
| README media review | Static checks passed | Referenced images decoded and reviewed; both architecture languages reviewed |
| Native-export result gallery | Passed, 2026-11-18 | Four actual exported plots; 3-second frames; GIF decoded and frames reviewed; source hashes and generation script included |
| Native UI recording | Not performed | README uses real exported plots and code-maintained static architecture diagrams |
| GitHub browser presentation | Not performed | Chrome navigation timed out; desktop/mobile and light/dark GitHub rendering were not verified |
| Hosted GitHub CI | Not observed | Local tests and source/API checks do not establish a hosted workflow result |

Historical conversion used Python 3.13.9 / openpyxl 3.1.5. Historical native runs used OriginPro 2026 (10.30018). The current three-case end-to-end run reported exact CSV agreement, maximum XLSX absolute error `7.11e-15`, and maximum Origin readback absolute error `1.36e-20`. These are observed values, not required output constants. / 当前三例实跑的 CSV 完全一致；上述浮点误差为实际观察值。

The raw-emu run used the same 41-record synthetic input as a custom case. Its independent audit and native three-column readback passed, followed by project reopening and five exports in each format. Existing-session checks observed unchanged titles for 15 windows, retained the original Origin process and confirmed adapter exit. / 原始 emu 小案例完成独立核对、三列回读、工程重开与全部导出，既有 Origin 会话保护检查通过。

Evidence: [three-case end-to-end report](../evidence/fresh-end-to-end.json), [raw-emu report](../evidence/raw-end-to-end.json), [environment and source integrity](../evidence/environment.json), [local tests](../evidence/unit-tests.txt), [dependency check](../evidence/dependency-check.txt). / 对应文件记录本次实际结果。

The current three-case report is one complete new run from source copied to a neutral location. It reuses the same locked Python environment and installed Origin on this machine. The earlier [layout-refinement run](../evidence/layout-refinement.json) remains historical evidence. / 当前三例报告来自中性目录完整源码副本的一次完整新跑，复用同机锁定环境和 Origin；先前刻度排版复跑另存为历史证据。

The [relocated-project report](../evidence/relocated-projects.json) covers all three saved projects at a further location, with original import-package locations unavailable. Projects were opened and read back without saving. The [metadata check](../evidence/project-metadata-check.json) records neutral-path native rebuilds and zero author-path matches. / 三份保存工程在另一位置打开并全量回读，原导入包位置暂不可用；公开工程经原生重建后，作者路径匹配为零。

## 本次复跑 / Running the checks

```powershell
.\.venv\Scripts\python.exe scripts/doctor.py
.\.venv\Scripts\python.exe scripts/reproduce.py --case all --output runs/validation
```

Use a fresh directory and inspect its run summary. The summary should identify the case, actual runtime, source hashes, selected mass and columns, completed stages and artifact paths. / 使用新目录，并检查摘要中的案例、环境、输入摘要、质量、源列、完成阶段与产物路径。

Before project-changing calls, the dedicated adapter must verify the newly created Origin instance and keep pre-existing sessions untouched. Failure to establish ownership is a failed native stage. / 工程操作前核对本次 Origin 实例拥有权；既有会话保持原样，拥有权不明即停止原生阶段。
