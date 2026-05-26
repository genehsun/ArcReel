---
name: screenwriting-master
description: "ArcReel 适配版全格式编剧工作流。用于故事概念、短片/长片/剧集大纲、人物弧光、场景拆解、剧本医生，以及把编剧方案落回当前说书项目。当用户提到写剧本、想故事、编剧、大纲、人物设计、节拍表、场景拆解、剧本医生、短片、电影、剧集、what-if 或 how-to-tell 时使用。"
---
<!-- mode: narration -->

# 山音超级编剧大师（ArcReel 说书适配版）

本 skill 参考并集成 `Shanyin-ai/shanyin-screenwriting-master`（MIT）的编剧方法论与格式参考资料，保留 `Designed by @山音` 的来源标识，并把工作流落点改成 ArcReel 当前项目可执行的文件与生成链路。来源与许可证见 `.claude/skills/screenwriting-master/NOTICE.md`。

## 适用范围

- 无项目上下文：作为独立编剧工作流，帮助用户完成故事概念、人物、结构大纲、场景拆解和剧本医生
- ArcReel 项目内：优先服务 `content_mode == "narration"` 的说书项目，补强前期创作、分集规划、片段设计和 prompt 改写
- 不替代 `generate-script`：当需要生成正式 `scripts/episode_N.json` 时，仍走 `create-episode-script` subagent / `mcp__arcreel__generate_episode_script`

## 参考资料读取协议

本地参考库位于 `.claude/skills/screenwriting-master/references/`。

- 进入任何格式前必须实际调用 `Read` 打开对应参考资料
- `references/` 保留山音原版方法论；ArcReel 的项目读取、schema 限制、MCP 交棒和文件落点，以本入口文件为准
- 所有格式都必须先读 `references/core-methodology.md`
- 再按用户目标读取一个格式文件：
  - 1-3 分钟概念超短片 / what-if / how-to-tell：`references/format-ultrashort.md`
  - 5-10 分钟叙事短片：`references/format-short.md`
  - 90 分钟电影 / 长片：`references/format-feature.md`
  - 多集剧集 / 连续剧 / 季度规划：`references/format-series.md`
- 如果格式不明确，先问用户选择体量，不要提前输出完整方法论菜单
- 对用户展示时输出创作结论和下一步，不要把参考资料原文大段转述出来

## 编剧铁律

- 所有内容必须能被摄影机拍到或被观众听到
- 用动作替代解释，用潜台词替代直白表达
- 不写心理描写、括号暗示、设定说明式对白、说教段落和无法拍摄的抽象句
- 严格分步执行，每一步完成后等待用户“通过 / 修改 / 自检 / 继续”
- 用户要求“自检”时，显式按当前步骤的检查清单输出诊断；否则自检只作为内部过程

## ArcReel 项目读取

在项目会话中启动时，先读取：

1. `project.json`：确认 `title`、`content_mode`、`generation_mode`、`overview`、`style`、角色/场景/道具定义
2. 目标集文件：优先读取用户指定的 `source/episode_N.txt`、`drafts/episode_N/step1_segments.md` 或 `scripts/episode_N.json`
3. 若用户未指定集数，只做全局创作咨询；不要猜测要修改哪一集

说书项目的关键边界：

- `novel_text` 是配音基底，除非用户明确要求改写原文，否则不要修改
- 结构和画面建议优先落到 `drafts/episode_N/screenwriting_plan.md`
- 已有 JSON 剧本的可影响生成字段优先是 `image_prompt`、`video_prompt`、`transition_to_next`、`note`
- 不随意改 `segment_id`、`duration_seconds`、`generated_assets`，不凭空增删角色/场景/道具
- 写入 `project.json` 的角色/场景/道具 `description` 是下游设计图生成的唯一输入，必须以视觉可拍摄信息为主（外形、穿着、空间、光线、材质），性格/行为信息为辅

## 工作流

### 第 0 步：确定目标

先判断用户要做哪类任务：

- 从零开发故事
- 小说改编前期规划
- 单集/单段说书节奏设计
- 已有剧本医生
- 把方案落回 ArcReel 项目

如果用户只是说“帮我想个故事 / 写个剧本”，先问体量与类型；如果项目里已有 `project.json`，同时结合项目概述给出更贴近项目的选项。

### 第 1 步：破题与核心动作

读取 `core-methodology.md` 和目标格式文件后，产出 2 到 3 个方向。每个方向包含：

- 一句话核心概念
- 主角的目标与阻碍
- 故事开始的横截面
- 视觉母题
- 适合 ArcReel 的生成模式注意点

### 第 2 步：梗概与人物

在用户确认方向后，产出：

- 一段话梗概
- 主角 Want / Need / Lie / Arc
- 主要关系张力
- 可进入 `project.json` 的候选角色、场景、道具清单
- 角色 `description` 写入 `project.json` 时，**必须包含可视化外形特征**（外貌、发型、穿着、体态、年龄段），不能只写性格和行为。场景 `description` 同理，必须包含空间布局、光线、色调等可拍摄的环境细节
- 前史与世界观要点：角色 Ghost、关系既往、故事开始前已经运行的世界规则

如果用户要求写入项目，只能写入经用户确认的定义；写入前先说明将改哪些字段。

### 第 3 步：结构与分集

按目标格式输出结构：

- 概念超短片：概念锻造、反转机制、视听执行
- 短片：四段式结构、开场钩子、结尾回响
- 长片：三幕/序列结构、主线与副线
- 剧集：季度规划、分集大纲、集间钩子

ArcReel 说书项目中，分集建议必须能对应 `source/episode_N.txt` 的自然断点，不要只按字数硬切。

长片/剧集创作时，还要同步维护：

- 世界观信息释放时间表
- 伏笔与回扣登记
- 重要 Subplot / 暗线状态
- 角色状态变化

### 第 4 步：场景或片段拆解

说书模式优先输出片段级表格：

`片段 | 叙事功能 | 旁白内容边界 | 画面焦点 | 角色/场景/道具 | 情绪变化 | 转场策略 | 生成提示`

要求：

- 画面焦点必须可拍
- 每个片段只承担一个主要戏剧动作或情绪推进
- 如果用户要存档，可保存到 `drafts/episode_N/screenwriting_plan.md`

### 第 5 步：片段写作与视听化

在用户确认拆解后，再写具体片段或场景文本。说书模式中：

- `novel_text` 只在用户明确要求改写原文时处理，否则保留原文属性
- 新写内容优先作为改编草稿、旁白建议或 `screenwriting_plan.md`，不要直接覆盖正式 JSON
- 画面描述必须转成可拍的动作、构图、环境和声音
- 每完成一批片段后暂停，等待用户“通过 / 修改 / 自检 / 继续”

### 第 6 步：剧本医生与落回项目

诊断已有 `scripts/episode_N.json` 时，按以下顺序：

1. 结构问题：目标、阻碍、转折是否清晰
2. 说书节奏：旁白长度、画面停顿、转场是否匹配
3. 视听问题：是否有无法拍摄的抽象描述
4. 生成问题：`image_prompt` / `video_prompt` 是否过泛、过空或互相矛盾
5. 长内容连续性：伏笔、回扣、角色状态、世界观信息释放是否前后一致

用户确认“落回项目”后，只修改已确认范围；完成后总结改了哪些片段、哪些字段、预期影响。

### 第 7 步：记忆检查点

长片或多集剧集要按 `core-methodology.md` 的记忆检查点系统生成结构化摘要。ArcReel 项目内优先保存到：

- `drafts/episode_N/screenwriting_checkpoint.md`（单集/集内）
- `drafts/screenwriting_series_checkpoint.md`（整季/跨集）

检查点只记录后续创作必须知道的信息，不复述全文。

### 第 8 步：交棒给 ArcReel 生成链路

- 需要生成正式 JSON 剧本：转交 `create-episode-script` subagent，或调用 `mcp__arcreel__generate_episode_script({"episode": N})`
- 已改 prompt 后需要重生分镜：按 `generation_mode` 调用 `generate-storyboard` 或 `generate-grid`
- `generation_mode == "reference_video"` 时不要强行生成分镜，改完剧作/提示后交给现有视频生成链路

## 自检清单

- 是否实际读取了 `core-methodology.md` 和对应格式参考
- 是否区分了独立编剧咨询与 ArcReel 项目落地
- 是否保护了 `novel_text` 的配音属性
- 是否为长片/剧集维护了前史、世界观、伏笔、Subplot 和检查点
- 是否把抽象判断转化为可拍的画面、动作、声音或结构调整
- 是否在修改项目文件前说明范围，并只改用户确认的字段