# 来源与许可 / Provenance and licensing

## Repository code

The skill instructions, conversion scripts and repository-owned adapter are maintained by [yuxuan6426](https://github.com/yuxuan6426) under [MIT](../LICENSE). / 技能、转换脚本与仓库自有适配层采用 MIT。

## Origin MCP snapshot

| Field | Value |
|---|---|
| Upstream | [Ge-Shun/origin-mcp](https://github.com/Ge-Shun/origin-mcp) |
| Commit | [`ddab4420ccc7d17c056285b3b75191b1b81e48e5`](https://github.com/Ge-Shun/origin-mcp/commit/ddab4420ccc7d17c056285b3b75191b1b81e48e5) |
| Tree | `16431318ec8829deedb0452f7f460d4c52c5c10e` |
| Location | `third_party/origin-mcp/` |
| License | Upstream MIT and NOTICE, preserved in that directory |

The source snapshot is kept separate from repository-owned integration code. Use the complete commit and snapshot manifest when checking its identity. Dependency locks and installed runtime evidence are distinct: a source commit alone does not identify every installed package version. / 上游源码与自有集成代码分开；源码提交和依赖环境分别记录。

## Measurement data and generated artifacts

Authorized DAT inputs, generated teaching data, tables, OPJU projects and scientific figures are distributed under [CC BY 4.0](../DATA-LICENSE). Attribute this repository, the case and the license; identify changes. Input hashes retain numerical provenance. / 使用时署名仓库与案例、保留许可链接并注明修改。

The real case filenames are normalized to `measurement.dat` within separate case directories; source hashes establish file identity. The synthetic case is generated and labeled as teaching data. The original reference OPJU is outside this distribution. / 真实输入以分目录统一命名，摘要保持身份追溯；教学数据明确标注来源身份。

## README media

| Asset | Source / identity | Terms |
|---|---|---|
| `assets/real-0p5mg-mt.png` | Native OriginPro 2026 export of the real 0.5 mg MT case | CC BY 4.0 |
| `assets/real-0p5mg-mh.png` | Native export of the real 0.5 mg, 3 K DC loop | CC BY 4.0 |
| `assets/real-0p5mg-multitemperature.png` | Native export of the real 0.5 mg multitemperature case | CC BY 4.0 |
| `assets/real-24mg-multitemperature.png` | Native export of the real 24 mg multitemperature case | CC BY 4.0 |
| `assets/origin-results-gallery.gif` | Labeled slideshow of the four native scientific exports above; 3 seconds per figure | CC BY 4.0 |

The current scientific plots were exported during the complete 2026-11-18 three-case run from source copied to a neutral location. They show actual outputs, with English axis labels in both README languages. Distributed OPJU files were rebuilt natively there and checked for author paths; see `evidence/project-metadata-check.json`. / 当前图形来自 2026-11-18 中性目录源码副本的三例完整实机复跑；公开 OPJU 在该位置原生重建，并核对作者路径。

The GIF is a result gallery, not a native UI recording. `assets/render_gallery.py` builds it reproducibly from the four PNG files; `assets/gallery.sources.json` records their hashes, frame timing and output hash. The code-maintained architecture SVG/PNG and Mermaid text remain separate explanatory diagrams. / GIF 为真实导出结果轮播，原生界面录像未执行；生成脚本与来源摘要随仓库保留。

## Reference documentation

- [OriginPro project API](https://github.com/originlab/originpro/blob/main/_autodocs/api-reference/project.md): project open/save behavior.
- [OriginPro graph API](https://github.com/originlab/originpro/blob/main/_autodocs/api-reference/graph.md): native graph export.
- [OriginPro runtime configuration](https://github.com/originlab/originpro/blob/main/_autodocs/api-reference/config.md): external instance creation and attachment.
- [Origin LabTalk files and sections](https://docs.originlab.com/labtalk/guide/from-files/): native OGS execution.
- [OpenAI plugin packaging](https://developers.openai.com/plugins/build/plugins): root plugin manifest and local marketplace layout.

External documentation is linked for reference and retains its own terms. Origin/OriginPro is proprietary software obtained separately. / 外部文档保留原许可；Origin 软件需另行取得。
