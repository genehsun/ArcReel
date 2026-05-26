---
name: director-master
description: "用导演方法论为当前剧集制定导演定调、镜头语言、节奏规划和分镜拆解。当用户提到“导演定调”、“分镜表”、“镜头语言”、“运镜”、“构图”、“景别”、“剪辑节奏”、“这场戏怎么拍”或要求把导演意见落回 ArcReel 剧本时使用。完成方案后可把结论写回 scripts/episode_N.json，并按 generation_mode 继续调用 generate-storyboard 或 generate-grid。"
---
<!-- mode: drama -->

# 导演工作流（ArcReel 适配版）

本 skill 参考 `Shanyin-ai/shanyin-director-master`（MIT）的导演工作流思路重写，保留“导演定调 -> 节奏规划 -> 剧本微调 -> 分镜拆解”的骨架，但把输出和落地点改成 ArcReel 当前可执行的项目文件与 MCP 工具。

## 适用范围

- 优先用于 `content_mode == "drama"` 的 `scripts/episode_N.json`
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
- 不改 `scene_id`、`duration_seconds`、`generated_assets`，也不随意改出场角色、场景、道具集合；除非用户明确要求且现有脚本显然错误

## 第 0 步：定位目标集

1. 确认目标 `episode_N.json`
2. 读取 `project.json` 与剧本，提取：
   - `generation_mode`
   - `title`、`summary`
   - `scenes[]` 中的 `scene_id`、`scene_type`、`characters_in_scene`、`image_prompt`、`video_prompt`、`transition_to_next`
3. 若用户未指定处理范围，默认先处理 1 到 3 个场景，避免一次性铺满整集

## 第 1 步：导演定调

先读取 `.claude/skills/director-master/references/core-methodology.md`，再按六维路由补读相关文件：

- 如果用户只要求“导演定调”这一步，也仍然必须先 `Read core-methodology.md`，再至少补读 1 个命中的 `genre-*.md`，然后才能回答
- A 情绪基调与 B 类型片通常优先判断；如果项目明显命中动作、关系、形式或社会视角，再补读对应 C 到 F 文件

- A 情绪基调：必判
- B 类型片：必判
- C 动作与对抗：项目存在打斗、追逐、战争、生存压力时再判
- D 题材与关系：项目卖点是爱情、家庭、成长、传记、竞技、悲剧关系时再判
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

按场景输出一张简洁表，至少包含以下列：

`scene_id | 情节力度 | 情感重量 | 镜头密度 | 主导景别 | 时长压力 | 转场策略 | 备注`

要求：

- `时长压力` 只用于判断镜头密度和剪辑松紧，不直接修改 `duration_seconds`
- 明确哪些场景需要留白和呼吸，哪些场景需要压缩和推进
- 对对白场景额外指出应避免单一正反打的段落

## 第 3 步：剧本微调与 prompt 落地

先回读 `.claude/skills/director-master/references/core-methodology.md` 的“剧本微调原则”；如果当前场景的调性高度依赖某个维度，再回看对应 `genre-*.md`，保持主导风格一致。

只在以下场景修改脚本：

- 用户明确要求“帮我把这一场改得更会拍”
- 当前 `image_prompt` 或 `video_prompt` 过空、过泛、不可拍
- 导演定调已经被用户确认

落地规则：

- `image_prompt.scene` 只写静态画面和构图重点，不写连续动作
- 动作全部落到 `video_prompt.action`
- `video_prompt.camera_motion` 只能使用 schema 允许的枚举值
- **对白必须完整写入 `shots.text`**：凡是有台词的镜头，必须把角色说的具体台词以「」引号形式嵌入（格式：`角色说：「具体台词」`）。
- 对话保持口语化，且只保留可听见的内容
- `note` 只写一句短导演备注，例如“压低机位，保持逼仄压迫感”
- 完成后必须总结：改了哪些 `scene_id`，每个场景改了哪些字段，预期影响是什么

## 第 4 步：分镜拆解

先读取 `.claude/skills/director-master/references/core-methodology.md` 的“叙事目的分析法”，再读取 `.claude/skills/director-master/references/shot-design.md` 和 `.claude/skills/director-master/references/storyboard-format.md`，确保镜头之间有动作 - 反应关系、切镜入口和九列结构映射。

输出 Markdown 表，列为：

`镜头号 | scene_id | 叙事目的 | 画面内容 | 景别 | 镜头运动 | 声音 | 估计镜头时长 | 与下一镜连接`

规则：

- 逐场或分批输出，不一次性生成整集
- 每个镜头都要有明确叙事目的，不要把“好看”当作目的
- 对白场景必须给出空间调度、遮挡、视点切换或动作反应，不要全部落成模板化正反打
- 镜头时长只作为导演拆解参考，不强制回写剧本
- 如果用户明确要存档，可把确认后的拆解保存到 `drafts/episode_N/director_storyboard.md`

## 第 5 步：交棒给 ArcReel 生成链路

当用户确认“按这个方案继续生成”时：

- 若 `generation_mode == "storyboard"`，调用：
  - `mcp__arcreel__generate_storyboards({"script": "episode_N.json"})`
- 若只改了少数场景，优先定向重生：
  - `mcp__arcreel__generate_storyboards({"script": "episode_N.json", "segment_ids": ["E1S01", "E1S02"]})`
- 若 `generation_mode == "grid"`，调用：
  - `mcp__arcreel__generate_grid({"script": "episode_N.json"})`
- 若只改了少数场景且需要缩小范围，调用：
  - `mcp__arcreel__generate_grid({"script": "episode_N.json", "scene_ids": ["E1S01", "E1S02"]})`
- 若 `generation_mode == "reference_video"`，不要调用分镜工具；把结论落回脚本后，转交现有视频生成链路

## 自检清单

- 是否所有画面描述都可拍、可见、可听
- 是否把静态画面和连续动作分别落到了 `image_prompt` 与 `video_prompt`
- 是否修改了真正会影响 ArcReel 生成结果的字段，而不是只给出空泛评论
- 是否在每个关键步骤结束后停下来等待用户确认
- 如果用户要求 `xlsx`，是否明确说明当前项目内没有内建导出器，不能凭空声称已生成文件