# 英文译文校对规范

## 输入

`build/i18n/review/<批次>.json`：数组，每项含

- `id`、`category`、`sa`（梵巴原语）、`zh_title`（中文名）
- `zh`：中文释义原文；`en`：英文译文
- `sources`：每条含 `zh`（中文出处题名）、`en`（英译题名）、`zh_q`（中文引文）、`en_q`（英文引文）

中文原文用 `\n\n` 分段、`- ` 列项、`**粗体**` 强调、`[[node_id|文字]]` 交叉引用。

## 你只做三件事

1. **术语**：核对英译是否用了学界通行译名；同一术语在全批次内是否写法一致。
   以梵文／巴利文为准，不以中文直译。例：
   - 缘起 = dependent origination（不是 causal arising）
   - 无我 = non-self（统一用 non-self，不用 no-self / not-self）
   - 如来藏 = tathāgatagarbha；阿赖耶识 = ālaya-consciousness
   - 二谛 = the two truths；三性 = the three natures
   - 判教 = doctrinal classification；止观 = śamatha-vipaśyanā
   - 五位七十五法 = the five categories and seventy-five dharmas
   - 诸行无常 = all formations are impermanent；诸法无我 = all dharmas are without self
2. **引文忠实度**：`en_q` 是否**完整、准确**地译出了 `zh_q`？重点查：
   - 有无遗漏、概括化、把具体变成笼统
   - 有无**添加原文没有的内容**（这是最严重的问题）
   - 数字、卷次、品名、人名是否与中文一致
3. **英文表达**：是否有语法错误、不通顺、术语混用、时态/单复数/冠词错误；
   是否有口语化或劝信语气（学术参考书应为中性、第三人称，不用 we/you）。

## 不要做的

- 不要改中文原文
- 不要重写整段英文（除非确有错误）；只指出**具体、可定位的问题**
- 不要报告「风格偏好」类意见（如 prefer A over B），除非属于上述三类问题
- 不要报告 `[[node_id|...]]` 交叉引用与 `**粗体**` 的位置问题——这些已由脚本全量校验，结构一致

## 输出

写入 `build/i18n/review/<批次>.findings.json`，JSON 数组，每项：

```json
{
  "id": "节点 id",
  "field": "en | en_q | en_title",
  "severity": "high | medium | low",
  "problem": "一句话说明问题（中文即可）",
  "zh_source": "对应的中文原文片段（英文问题时填）",
  "current": "当前英文（原样复制，便于精确定位）",
  "suggested": "建议改成"
}
```

- `severity`：`high` = 事实错误、遗漏关键内容、添加了原文没有的内容；`medium` = 术语不当、表达不通、误导性表述；`low` = 用词可更好
- `current` 必须与文件中的文本**逐字一致**（我要用它做精确替换），不要加省略号
- 没有问题的节点不必出现在结果里；整批无问题就写 `[]`

## 完成回报

输出文件路径、报告条数、按 severity 的分布，以及你认为最严重的 3 条。
