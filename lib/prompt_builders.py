"""图像 / 视频 / 资产 prompt 的统一真相源。

WebUI（server/services/generation_tasks.py）和 Skill（agent_runtime_profile/.claude/skills/generate-assets）
都从这里取最终 prompt 文本，确保入口一致、不漂移。

设计要点：
- 无 backend 锁定：纯文本拼接，由调用方决定走哪个 image/video provider。
- 反向提示词统一以「画面避免：xxx」追加到 prompt 末尾，不再使用各 backend 的 negative_prompt 参数通道
  （image backends 大多 silent 丢弃，参数化反而增加分叉）。
- 防崩短语精简：扁平 4 项内核，避免 CFG 权重稀释。
"""

from __future__ import annotations

# ---------------------------------------------------------------------------
# 内部常量：防崩 / 反向 / 布局 / 风格前缀
# ---------------------------------------------------------------------------

# 角色图采用 issue #353 的四视图 16:9 布局。
_CHARACTER_LAYOUT = (
    "横版 16:9 四格布局，纯白 (#FFFFFF) 背景。三个等宽面板分别为正面全身视图、侧面全身视图、背面全身视图。"
    "正面全身视图：清晰展示面部细节、发型、眼神、配饰与上装，眼睛清晰锐利，注视镜头，自然情绪。"
    "侧面全身视图：展示角色侧面轮廓与服装细节，保持自然姿态。"
    "背面全身视图：展示角色背面细节与服装，保持自然姿态。"
)
_SCENE_LAYOUT = "主画面展示环境整体外观与氛围。"
_PROP_LAYOUT = "三视图水平排列于纯净浅灰背景：左侧正面全视图、中间 45° 侧视图体现立体感、右侧关键细节特写。"

# 正向防崩（按资产类型差异化）。
_CHARACTER_GUARD = "正面视图不要完全证件照式站姿，身体轻微放松，避免僵硬绝对对称。角色面部、发型、服装、配饰完全一致。人脸必须保持真实五官结构，不得出现青光眼、绿光眼。"
_SCENE_GUARD = "空间透视正常，陈设固定，光影统一。"
_PROP_GUARD = "外观结构完整，焦点清晰。"

# 反向提示词：精简到核心 4 项，避免 CFG 权重稀释。
_NEGATIVE_TAIL_ASSET = "画面避免：水印、多余文字、低分辨率、手指畸形。"
_NEGATIVE_TAIL_VIDEO = "禁止出现：BGM、文字字幕、水印。"


def _style_prefix(style: str = "", style_description: str = "") -> str:
    """组合视觉风格前缀。两者都为空时返回空串。"""
    parts = []
    if style:
        parts.append(f"风格：{style}")
    if style_description:
        parts.append(f"描述：{style_description}")
    if not parts:
        return ""
    return "\n".join(parts) + "\n\n"


# ---------------------------------------------------------------------------
# 资产 prompt（character / scene / prop）
# ---------------------------------------------------------------------------


def build_character_prompt(name: str, description: str, style: str = "", style_description: str = "") -> str:
    """角色设计图 prompt（issue #353 四视图 16:9）。"""
    style_block = _style_prefix(style, style_description)
    return (
        f"{style_block}"
        f"角色「{name}」的设计参考图。\n\n"
        f"{description}\n\n"
        f"{_CHARACTER_LAYOUT}\n\n"
        f"{_CHARACTER_GUARD}\n\n"
        f"{_NEGATIVE_TAIL_ASSET}"
    )


def build_scene_prompt(name: str, description: str, style: str = "", style_description: str = "") -> str:
    """场景设计图 prompt（主+细节）。"""
    style_block = _style_prefix(style, style_description)
    return (
        f"{style_block}"
        f"标志性场景「{name}」的视觉参考。\n\n"
        f"{description}\n\n"
        f"{_SCENE_LAYOUT}\n\n"
        f"{_SCENE_GUARD}\n\n"
        f"{_NEGATIVE_TAIL_ASSET}"
    )


def build_prop_prompt(name: str, description: str, style: str = "", style_description: str = "") -> str:
    """道具设计图 prompt（三视图）。"""
    style_block = _style_prefix(style, style_description)
    return (
        f"{style_block}"
        f"道具「{name}」的多视角展示。\n\n"
        f"{description}\n\n"
        f"{_PROP_LAYOUT}\n\n"
        f"{_PROP_GUARD}\n\n"
        f"{_NEGATIVE_TAIL_ASSET}"
    )


# ---------------------------------------------------------------------------
# 分镜 / 视频 prompt 末尾增强
# ---------------------------------------------------------------------------


def append_video_negative_tail(prompt: str) -> str:
    """给视频生成 prompt 追加统一的反向提示词。

    调用方拿到分镜 video_prompt 文本后，在交给 video backend 之前过一遍此函数；
    避免在每个 caller 各自拼接、导致漂移。
    """
    if not prompt or not prompt.strip():
        return _NEGATIVE_TAIL_VIDEO
    if _NEGATIVE_TAIL_VIDEO in prompt:
        return prompt
    return f"{prompt.rstrip()}\n\n{_NEGATIVE_TAIL_VIDEO}"


def build_storyboard_suffix(content_mode: str = "narration", *, aspect_ratio: str | None = None) -> str:
    """分镜图构图后缀。优先 aspect_ratio，缺省按 content_mode 推导。"""
    if aspect_ratio is None:
        ratio = "9:16" if content_mode == "narration" else "16:9"
    else:
        ratio = aspect_ratio
    if ratio == "9:16":
        return "竖屏构图。"
    if ratio == "16:9":
        return "横屏构图。"
    return ""
