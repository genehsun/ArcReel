---
name: director-master
description: "用导演方法论为当前说书剧本制定导演定调、镜头语言、节奏规划和分镜拆解。当用户提到“导演定调”、“分镜表”、“镜头语言”、“运镜”、“构图”、“景别”、“剪辑节奏”、“这一段怎么拍”或要求把导演意见落回 ArcReel 剧本时使用。完成方案后可把结论写回 scripts/episode_N.json，并按 generation_mode 继续调用 generate-storyboard 或 generate-grid。"
---
<!-- mode: narration -->

# 导演工作流（ArcReel 适配版）

本 skill 参考 `Shanyin-ai/shanyin-director-master`（MIT）的导演工作流思路重写，保留“导演定调 -> 节奏规划 -> 剧本微调 -> 分镜拆解”的骨架，但把输出和落地点改成 ArcReel 当前可执行的项目文件与 MCP 工具。

## 适用范围

- 优先用于 `content_mode == "narration"` 的 `scripts/episode_N.json`
- `generation_mode == "storyboard"` 或 `"grid"` 时，可直接衔接现有分镜生成链路
- `generation_mode == "reference_video"` 时，只做导演方案与 prompt 落地，不要求九列表或分镜图

## 参考资料读取协议

本 skill 的本地参考库位于 `.claude/skills/director-master/references/`。

- `references/` 保留山音原版方法论；ArcReel 的项目读取、schema 限制、MCP 交棒和不支持项，以本入口文件为准
- 进入某一步前，先实际调用 `Read` 打开该步要求的参考文件；不要只凭入口文件摘要假装完成 references 路由
- 不要一上来全量读取 9 个文件；先读 `core-methodology.md`，再按六维定调法补读 1 到 3 个相关 `genre-*.md`
- 第 1 步导演定调：必读 `core-methodology.md`，再按项目命中的维度补读 `genre-A` 到 `genre-F`
- 第 2 步节奏规划：重读 `core-methodology.md` 的节奏部分；涉及镜头时长时补读 `storyboard-format.md`
- 第 3 步微调落地：重读 `core-methodology.md` 的微调原则；需要强化某种风格时回看对应 `genre-*.md`
- 第 4 步分镜拆解：必读 `shot-design.md` 和 `storyboard-format.md`
- 对用户展示时输出“导演方向”和“执行策略”，不要把内部参考文件名或导演清单原封不动甩给用户

## 硬约束

- 先读取 `project.json` 和目标 `scripts/episode_N.json`，不要凭空假设角色、场景、时长或生成模式
- 如果用户输入的是粗糙文本、大纲或尚未生成 JSON 的草稿，先整理为片段/场景结构并标注核心事件，再进入导演定调；不要强行要求已有 `scripts/episode_N.json`
- 严格分步执行。每一步完成后暂停，等待用户的“通过 / 修改 / 自检 / 继续”
- 只写摄影机可见、可听的内容，不写心理描写、抽象感受或空洞议论
- narration 模式的 `novel_text` 是后期配音基底，不要改写原文；导演调整优先落在 `image_prompt`、`video_prompt`、`transition_to_next` 和 `note`
- 不承诺 `.xlsx` 导出。本项目内的有效交付物只有：导演定调、节奏规划、微调建议、Markdown 分镜拆解、脚本字段更新、MCP 入队结果
- 若用户要求“把导演方案落回项目”，只修改会影响 ArcReel 后续生成结果的字段：
  - `image_prompt.scene`
  - `image_prompt.composition.shot_type`
  - `image_prompt.composition.lighting`
  - `image_prompt.composition.ambiance`
  - `video_prompt.action`
  - `video_prompt.camera_motion`
  - `video_prompt.ambiance_audio`
  - `video_prompt.dialogue`
  - `transition_to_next`
  - `note`
- 不改 `segment_id`、`duration_seconds`、`generated_assets`，也不随意改角色、场景、道具集合；除非用户明确要求且现有脚本显然错误

## 第 0 步：定位目标集

1. 确认目标 `episode_N.json`
2. 读取 `project.json` 与剧本，提取：
   - `generation_mode`
   - `title`、`summary`
   - `segments[]` 中的 `segment_id`、`novel_text`、`characters_in_segment`、`image_prompt`、`video_prompt`、`transition_to_next`
3. 若用户未指定处理范围，默认先处理 2 到 4 个片段，避免一次性铺满整集

## 第 1 步：导演定调

先读取 `.claude/skills/director-master/references/core-methodology.md`，再按六维路由补读相关文件：

- 如果用户只要求“导演定调”这一步，也仍然必须先 `Read core-methodology.md`，再至少补读 1 个命中的 `genre-*.md`，然后才能回答
- A 情绪基调与 B 类型片通常优先判断；如果项目明显命中动作、关系、形式或社会视角，再补读对应 C 到 F 文件

- A 情绪基调：必判
- B 类型片：必判
- C 动作与对抗：项目存在追逐、战斗、生存或身体冲突时再判
- D 题材与关系：项目核心是爱情、家庭、成长、传记、竞技、悲剧关系时再判
- E 形式与叙事手法：伪纪录片、公路、动画、实验、歌舞等强形式项目再判
- F 社会视角：项目显著处理社会现实、历史、政治立场、主旋律时再判

从命中的维度里确定：

- 1 个主导参考：决定全片默认镜头语言
- 0 到 2 个调味参考：只在局部段落借用

输出 2 到 3 个差异明确的导演方向。每个方向都要交代：

- 情绪基调
- 类型参照
- 景别重心
- 镜头运动策略
- 光线与颜色倾向
- 节奏策略
- 本集应反复强化的视觉母题

如果用户已经给了参考片、导演、摄影风格或镜头语言偏好，直接吸收并收敛成一个方向，不要再做无意义的风格枚举。

## 第 2 步：节奏规划

先回读 `.claude/skills/director-master/references/core-methodology.md` 的“双轨节奏”“镜头组”“节奏诊断”部分；需要估时时再读 `.claude/skills/director-master/references/storyboard-format.md` 的时长规范。

按片段输出一张简洁表，至少包含以下列：

`segment_id | 叙事推进 | 情绪重量 | 镜头密度 | 主导景别 | 画面焦点 | 转场策略 | 备注`

要求：

- narration 更重视旁白节奏与画面调度的贴合，而不是对白表演的拆切
- 明确哪些片段应留白、停顿、拉远，哪些片段应压缩、推进、强化动作信息
- 若多个片段属于同一段情绪连续体，要标明是否建议形成视觉连拍感

## 第 3 步：剧本微调与 prompt 落地

先回读 `.claude/skills/director-master/references/core-methodology.md` 的“剧本微调原则”；如果当前片段的调性高度依赖某个维度，再回看对应 `genre-*.md`，保持主导风格一致。

只在以下场景修改脚本：

- 用户明确要求“帮我把这一段拍法改得更有画面”
- 当前 `image_prompt` 或 `video_prompt` 过空、过泛、不可拍
- 导演定调已经被用户确认

落地规则：

- 不改写 `novel_text`
- `image_prompt.scene` 只写静态画面和构图重点，不写连续动作
- 动作全部落到 `video_prompt.action`
- `video_prompt.camera_motion` 只能使用 schema 允许的枚举值
- `video_prompt.dialogue` 只保留原文本里真实存在、且适合被听到的对白
- `note` 只写一句短导演备注，例如“用远景留白，承接旁白停顿”
- 完成后必须总结：改了哪些 `segment_id`，每个片段改了哪些字段，预期影响是什么

## 第 4 步：分镜拆解

先读取 `.claude/skills/director-master/references/core-methodology.md` 的“叙事目的分析法”，再读取 `.claude/skills/director-master/references/shot-design.md` 和 `.claude/skills/director-master/references/storyboard-format.md`，确保镜头之间有动作 - 反应关系、切镜入口和九列结构映射。

输出 Markdown 表，列为：

`镜头号 | segment_id | 叙事目的 | 画面内容 | 景别 | 镜头运动 | 声音 | 估计镜头时长 | 对应旁白`

规则：

- 逐段或分批输出，不一次性生成整集
- 每个镜头都要有明确叙事目的，不要把“好看”当作目的
- 要说明镜头如何承接旁白节奏，而不是只罗列视觉元素
- 镜头时长只作为导演拆解参考，不强制回写剧本
- 如果用户明确要存档，可把确认后的拆解保存到 `drafts/episode_N/director_storyboard.md`

## 第 5 步：交棒给 ArcReel 生成链路

当用户确认“按这个方案继续生成”时：

- 若 `generation_mode == "storyboard"`，调用：
  - `mcp__arcreel__generate_storyboards({"script": "episode_N.json"})`
- 若只改了少数片段，优先定向重生：
  - `mcp__arcreel__generate_storyboards({"script": "episode_N.json", "segment_ids": ["E1S01", "E1S02"]})`
- 若 `generation_mode == "grid"`，调用：
  - `mcp__arcreel__generate_grid({"script": "episode_N.json"})`
- 若只改了少数片段且需要缩小范围，调用：
  - `mcp__arcreel__generate_grid({"script": "episode_N.json", "scene_ids": ["E1S01", "E1S02"]})`
  - 这里参数名仍然是 `scene_ids`，但在 narration 剧本里传的是目标 `segment_id`
- 若 `generation_mode == "reference_video"`，不要调用分镜工具；把结论落回脚本后，转交现有视频生成链路

## 自检清单

- 是否所有画面描述都可拍、可见、可听
- 是否把静态画面和连续动作分别落到了 `image_prompt` 与 `video_prompt`
- 是否尊重了 `novel_text` 的原文属性，没有把导演意见误写进旁白原文
- 是否修改了真正会影响 ArcReel 生成结果的字段，而不是只给出空泛评论
- 是否在每个关键步骤结束后停下来等待用户确认
- 如果用户要求 `xlsx`，是否明确说明当前项目内没有内建导出器，不能凭空声称已生成文件