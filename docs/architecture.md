# 数据流与图源 / Data flow and diagram source

[中文 SVG](../assets/pipeline.zh.svg) · [English SVG](../assets/pipeline.en.svg)

The diagrams show capability relationships. They do not represent a UI screenshot or a recorded execution. / 本图说明能力与数据关系。

## 中文

```mermaid
flowchart LR
    A[DAT + 用户确认的质量] --> B[解析与连续分段]
    B --> C[XLSX / CSV / OGS / 源行追溯]
    C --> D[独立数值核对]
    D --> E[专属 Origin 实例]
    E --> F[OPJU 保存重开与 MCP 回读]
    F --> G[PNG / PDF / 验收摘要]
```

## English

```mermaid
flowchart LR
    A[DAT + confirmed mass] --> B[Parse and segment]
    B --> C[XLSX / CSV / OGS / row provenance]
    C --> D[Independent numerical audit]
    D --> E[Dedicated Origin instance]
    E --> F[Save and reopen OPJU with MCP readback]
    F --> G[PNG / PDF / validation summary]
```

`assets/render_architecture.py` maintains the bilingual SVG and PNG files. Run it with Pillow on Windows; its text is ordinary editable source. The diagrams use repository-authored content under MIT. / 图解由可编辑脚本维护，采用 MIT；Windows 上使用 Pillow 重生成。

The individual Origin plots linked from the README are scientific outputs under CC BY 4.0, as recorded in [provenance](provenance.md). / README 的科学图形另按 CC BY 4.0 署名。
