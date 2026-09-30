# 英文版翻译规范（Translation Specification）

本文件是英文版译制的唯一规范。所有批次译者必须完整遵守。

## 1. 任务

把一批中文译文单元译成英文。输入是 JSON 数组，输出是 JSONL（每行一个 JSON 对象），**行序与输入一致**，每个输入单元的 `id` 都必须出现。

输入单元字段：

| 字段 | 说明 |
|---|---|
| `id` | 节点标识，原样保留 |
| `zh_name` | 中文概念名 |
| `sa` | 梵文／巴利文（无对应时为 `—`，多见于汉地自撰概念） |
| `cat` | 分类键 |
| `zh_desc` | 待译释义。用 `\n\n` 分段、`- ` 列项、`**粗体**` 强调、`[[node_id\|显示文字]]` 作内部交叉引用 |
| `src` | 出处数组，每项 `{t: 中文书名或条目, q: 古典汉文引文}` |
| `tt` | 年代栏 `{form, fix, trans}`，可能缺项 |
| `rel` | 该节点的关系，每项 `{to, type, note}`，`note` 可能为中文短语或空串 |

输出对象（**不要回抄任何 `zh_*` 字段**）：

```json
{"id":"four_truths","name":"Four Noble Truths","aka":["si sheng di","catvari aryasatyani","Four Truths"],"desc":"...","src":[{"t":"...","q":"..."}],"tt":{"form":"...","fix":"...","trans":"..."},"rel":{"dukkha":"..."}}
```

- `rel`：把关系目标节点 id 映射到该关系 `note` 的英译；`note` 为空则**省略**该项。
- `tt`：只保留输入中存在的键。
- 文件内不得有任何注释、说明或额外文字。

## 2. 译名原则

**以梵文／巴利文为准**，用学界通行英译，不按中文直译。

| 中文 | 英文 | 中文 | 英文 |
|---|---|---|---|
| 四圣谛 | Four Noble Truths | 三法印 | the three seals of the Dharma |
| 苦谛 | the truth of suffering | 集谛 | the truth of the origin of suffering |
| 灭谛 | the truth of cessation | 道谛 | the truth of the path |
| 八正道 | the noble eightfold path | 缘起 | dependent origination |
| 十二因缘 | the twelve links of dependent origination | 无明 | ignorance |
| 行（支） | formations | 识 | consciousness |
| 名色 | name-and-form | 六入 | the six sense bases |
| 触 | contact | 受 | feeling |
| 爱 | craving | 取 | clinging |
| 有 | becoming | 生 | birth |
| 老死 | aging-and-death | 业 | karma |
| 异熟 | ripening (vipāka) | 轮回 | saṃsāra |
| 五蕴 | the five aggregates | 十二处 | the twelve sense bases |
| 十八界 | the eighteen elements | 有为法 | conditioned dharmas |
| 无为法 | unconditioned dharmas | 真如 | suchness (tathatā) |
| 心所法 | mental factors (caitta) | 无我 | non-self |
| 诸行无常 | all formations are impermanent | 诸行是苦 | all formations are suffering |
| 诸法无我 | all dharmas are without self | 涅槃寂静 | nirvāṇa is peace |
| 空 | emptiness (śūnyatā) | 二谛 | the two truths |
| 世俗谛 | conventional truth | 胜义谛 | ultimate truth |
| 三性 | the three natures | 遍计所执性 | the imagined nature |
| 依他起性 | the dependent nature | 圆成实性 | the perfected nature |
| 八识 | the eight consciousnesses | 阿赖耶识 | ālaya-consciousness (storehouse consciousness) |
| 末那识 | manas (the seventh consciousness) | 转识成智 | transformation of consciousness into wisdom |
| 如来藏 | tathāgatagarbha | 佛性 | Buddha-nature |
| 一阐提 | icchantika | 常乐我净 | permanence, bliss, self, purity |
| 因明 | Buddhist logic (hetuvidyā) | 现量 | direct perception (pratyakṣa) |
| 比量 | inference (anumāna) | 判教 | doctrinal classification |
| 五时八教 | the five periods and eight teachings | 五教十宗 | the five teachings and ten schools |
| 一念三千 | three thousand realms in a single moment of mind | 三谛圆融 | the perfect interfusion of the three truths |
| 一心三观 | threefold contemplation in one mind | 六即佛 | the six identities |
| 一真法界 | the one true dharma-realm | 法界缘起 | dharmadhātu dependent origination |
| 四法界 | the four dharma-realms | 十玄门 | the ten mysterious gates |
| 六相圆融 | the six characteristics in mutual interfusion | 见性成佛 | seeing one's nature and becoming Buddha |
| 无念 · 无相 · 无住 | no-thought, no-mark, no-abiding | 持名念佛 | recitation of the Buddha's name |
| 二道二力 | the two paths and two powers | 戒体 | the essence of the precepts |
| 三密 | the three mysteries | 曼荼罗 | maṇḍala |
| 即身成佛 | attaining Buddhahood in this very body | 四部密续 | the four classes of tantra |
| 三十七道品 | the thirty-seven aids to enlightenment | 四念处 | the four establishments of mindfulness |
| 止观 | śamatha-vipaśyanā (calming and insight) | 四禅八定 | the four dhyānas and eight concentrations |
| 五位修道 | the five stages of the path | 声闻四果 | the four fruits of the hearers |
| 三乘与一乘 | the three vehicles and the one vehicle | 四摄法 | the four means of gathering |
| 四无量心 | the four immeasurable attitudes | 三界二十八天 | the three realms and twenty-eight heavens |
| 成住坏空 | formation, abiding, destruction, emptiness | 四依与四依法 | the four reliances |
| 布萨 · 安居 · 羯磨 | uposatha, the rains retreat, and karma (monastic procedure) | 默照与话头 | silent illumination and the critical phrase |

**汉地自撰概念**无梵文对应，用通行英译（见上表）。

## 3. 人名与宗派名（罗马化）

Tiantai, Huayan, Sanlun, Faxiang (Yogācāra), Chan, Pure Land, Vinaya, Esoteric (Tantra), Jushe (Kośa), Chengshi (Satyasiddhi), Tibetan, Theravāda / Southern tradition.

Zhiyi, Guanding, Jizang, Fazang, Chengguan, Zongmi, Dushun, Zhiyan, Daoxuan, Shandao, Tanluan, Daochuo, Huineng, Shenxiu, Daosheng, Sengzhao, Zhu Daosheng, Xuanzang, Kuiji, Paramārtha, Kumārajīva, Yijing, Fazang, Bodhidharma, Nāgārjuna, Āryadeva, Asaṅga, Vasubandhu, Maitreya, Dignāga, Dharmakīrti, Buddhapālita, Bhāviveka, Candrakīrti, Tsongkhapa, Atiśa, Padmasambhava, Buddhaghosa, Aśoka, Mahākāśyapa, Ānanda, Upāli, Śāriputra.

## 4. 经典名

首次出现时给通行英文／梵文名，其后括注中文名；同一节点内不重复括注。

《俱舍论》= *Abhidharmakośa-bhāṣya* (Jushe lun)　《杂阿含经》= *Saṃyukta-āgama* (Za Ahan Jing)
《相应部》= *Saṃyutta Nikāya*　《中部》= *Majjhima Nikāya*　《长部》= *Dīgha Nikāya*　《增支部》= *Aṅguttara Nikāya*
《大毗婆沙论》= *Abhidharma-mahāvibhāṣā*　《成唯识论》= *Cheng Weishi Lun*　《瑜伽师地论》= *Yogācārabhūmi-śāstra*
《大智度论》= *Mahāprajñāpāramitā-śāstra*　《中论》= *Mūlamadhyamakakārikā* (Zhong lun)　《百论》= *Śataśāstra*
《十二门论》= *Dvādaśamukha-śāstra*　《解深密经》= *Saṃdhinirmocana-sūtra*　《法华经》= *Lotus Sūtra* (Saddharmapuṇḍarīka)
《华严经》= *Avataṃsaka Sūtra*　《大般涅槃经》= *Mahāparinirvāṇa Sūtra*　《胜鬘经》= *Śrīmālādevī Sūtra*
《宝性论》= *Ratnagotravibhāga*　《摄大乘论》= *Mahāyānasaṃgraha*　《清净道论》= *Visuddhimagga*
《四分律》= *Dharmaguptaka Vinaya* (Sifen lü)　《梵网经》= *Brahmajāla Sūtra*　《大日经》= *Mahāvairocana-abhisaṃbodhi-tantra*
《金刚顶经》= *Vajraśekhara-tantra*　《因明正理门论》= *Nyāyamukha*　《集量论》= *Pramāṇasamuccaya*
《释量论》= *Pramāṇavārttika*　《异部宗轮论》= *Samayabhedoparacanacakra*　《出三藏记集》= *Chu Sanzang Jiji*
《开元释教录》= *Kaiyuan Shijiao Lu*　《高僧传》= *Gaoseng Zhuan*　《岛史》= *Dīpavaṃsa*　《大史》= *Mahāvaṃsa*
《菩提道次第广论》= *Lamrim Chenmo*　《密宗道次第广论》= *Ngakrim Chenmo*　《土观宗派源流》= *Thu'u bkwan's History of the Schools*

## 5. 古典引文

**全文译出**，不省略、不概括、不改写为大意。译文要能被拿回汉文逐句核对，同时读得通。

例：
- 「此有故彼有，此生故彼生」→ "When this exists, that comes to be; with the arising of this, that arises."
- 「诸行无常，诸行是苦，诸法无我」→ "All formations are impermanent; all formations are suffering; all dharmas are without self."
- 「若顺此印，即是佛经；若违此印，即非佛说」→ "If a teaching accords with this seal, it is the Buddha's word; if it contradicts it, it is not the Buddha's teaching."
- 「一切众生悉有佛性」→ "All sentient beings possess the Buddha-nature."

## 6. 文体

学术参考书文体，用佛教研究的规范术语。避免口语、避免劝信语气、避免第一人称与第二人称。不添加原文没有的背景与年代。

**保留结构**：`\n\n` 分段、`- ` 列项、`**粗体**` 位置、所有 `[[node_id|文字]]` 的 node_id 原样不变（只译显示文字）。

例：`[[sila|戒学]]` → `[[sila|the training in ethics]]`；`[[nonself_seal|诸法无我]]` → `[[nonself_seal|the selflessness of all dharmas]]`。

## 7. `aka`：双语检索别名

每个节点 3–8 项，**全小写**，用于页面内中英通搜：

1. 汉语拼音，不标声调，音节间空格（`si sheng di`、`shi er yin yuan`）；
2. 英文通行名及常见异拼（`Four Noble Truths`、`Four Truths`）；
3. 梵文／巴利文，去变音符（`catvari aryasatyani`）；
4. 读者可能输入的英文关键词（`suffering`、`eightfold path`、`rebirth`）。

不要重复该节点自己的 `name`。

## 8. 验收标准

- 每个 `id` 都在，行序与输入一致，每行都是合法 JSON，无多余文字；
- 输出值中不得残留中文字符（书名括注与 `[[node_id|…]]` 内亦然——一律用罗马化或梵文）；
- 同一批次内术语前后一致。

完成后回报：输出文件路径、写入行数、以及你不确定的 id 列表。
