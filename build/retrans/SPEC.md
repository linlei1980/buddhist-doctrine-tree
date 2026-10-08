# 重译规范

中文释义经过一轮「判准补正」（补上了原先只列名、未给判准的内容），
英文译文仍是旧版，故须重译以与中文一致。

## 输入

`build/retrans/<批次>.json`，每项：

- `id`、`name_zh`、`name_en`（节点名，已译好，不要改）、`sa`（梵巴原语）
- `zh_desc`：**当前中文释义（最新）**
- `en_desc`：当前英文释义（**已过时**，仅供参考旧译的用词与语气）
- `sources_zh` / `sources_en`：中英出处题名（已对齐，不要改）

## 你要做的

把 `zh_desc` 完整、准确地译为英文，写入 `build/retrans/<批次>.en.json`，
格式为 JSON 对象：`{ "节点id": "英文译文", ... }`。

## 必须遵守

1. **完整**——中文的每一条判准、每一个条目、每一处括注都要译出，不得省略、不得概括。
   这轮补的正是一句句判准，漏掉任何一句就失去意义。
2. **保留 Markdown 结构**，与中文一一对应：
   - `**粗体**` 的位置与数量须与中文**完全一致**（脚本会逐节点比对粗体数）
   - `\n\n` 分段、`- ` 列项、`1. ` 编号，须与中文同构
   - `[[node_id|文字]]` 交叉引用**必须原样保留节点 id**，只译显示文字
3. **术语**用规范英译（与页面其余部分一致）：
   - 缘起 dependent origination；无我 non-self；如来藏 tathāgatagarbha
   - 阿赖耶识 ālaya-consciousness；二谛 the two truths；三性 the three natures
   - 判教 doctrinal classification；止观 śamatha-vipaśyanā；四念处 the four establishments of mindfulness
   - 三十七道品 the thirty-seven aids to enlightenment；五位七十五法 the five categories and seventy-five dharmas
   - 卷次 fascicle；品 chapter；经 sūtra
   - 人名用通行拼写：Zhiyi、Fazang、Chengguan、Jizang、Xuanzang、Kuiji、Tsongkhapa、Buddhaghosa
4. **文风**：中性学术语体，不用 we／you，不劝信；与 `en_desc` 旧译的语气保持一致。
5. **不得添加中文没有的内容**，也不得把具体判准化约为笼统说法。
6. **不得出现任何中文字符**（脚本会硬性检查）。

## 输出

`build/retrans/<批次>.en.json`——JSON 对象，键为节点 id，值为英文译文。
译文内的换行请用真实的换行转义（即 JSON 字符串里的 `\n`），与 `zh_desc` 同构。

完成后回报：输出路径、条数、以及你认为最难译的两处及其处理方式。
