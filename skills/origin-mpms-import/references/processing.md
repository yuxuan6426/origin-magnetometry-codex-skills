# 分组与参考规则

## MPMS3 输入

识别 `[Data]`，按表头匹配 Temperature (K)、Magnetic Field (Oe) 及磁矩列。VSM 与 DC 行分别处理。支持 UTF-8/UTF-8 BOM 和 GB18030，保留有效记录号、实际文件行号及时间戳。缺少关键列、磁矩模式不明确或数值缺失时返回具体错误。

仪器 `Mass (grams)` 是运动部件总质量。用户实际样品质量单独输入，单位 mg。

## 切段

1. 先按连续的 VSM/DC 模式区间处理。
2. 恒场跨度在5Oe内、至少10个点且温度跨度至少3K的区间归为 MT；温度方向持续反转时在实际极值后切分。
3. 其余记录按温度平台切分，当前平台与温度中位数偏差超过0.5K时开始新平台。
4. 同温平台内，磁场跳变超过近期步长5倍、该平台总磁场跨度10%和500Oe，且时间间隔超过30秒，视为独立扫场重置。时间间隔单独不触发切段。
5. 按扫场形态标注回线、近零起始单向扫场和其他单向/部分扫场。每条记录在所有段中按原采集顺序出现一次。

对边界修正，提供包含以下条目的 JSON 列表：

```json
[
  {"first_record": 1, "last_record": 300, "category": "MT", "direction": "warming"},
  {"first_record": 301, "last_record": 598, "category": "MT", "direction": "cooling"}
]
```

示例只展示格式。实际列表必须覆盖输入全部记录且每段只含一种模式。category 可取 MT、MH_loop、MH_initial、MH_partial。区间为从1开始的有效记录号，首尾都包含。

## 参考核验

本项目的参考 OPJU 已通过 Origin 2026 只读检查并与对应 DAT 数值匹配：VSM 使用 Moment，DC 使用 DC Moment Fixed Ctr；显示值为原始磁矩乘2000（样品0.5mg）。参考中的一部分 in-plane 数据来自其他输入，因此默认技能仅给当前上传数据生成可追溯结果。

参考表中 56K 标签复用了55K数值、多组 X 列复用了48K磁场、70K列有一个前导空格位置。转换程序分别提取各温度实际记录并使用对应磁场值，完整保留这份DAT末尾的70K独立回线。后续新样例若要求不同磁矩来源，可用显式选项或独立配置文件定义。

## 官方资料

- [Quantum Design：MPMS/SVSM 数据列定义](https://qdusa.com/siteDocs/appNotes/1500-008.pdf)
- [Quantum Design：DC Scan 固定/自由中心](https://qdusa.com/siteDocs/appNotes/1500-018.pdf)
- [Quantum Design：磁学基础与单位](https://qdusa.com/siteDocs/appNotes/FundPrimer.pdf)
