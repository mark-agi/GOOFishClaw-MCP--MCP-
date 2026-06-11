import os
import re
from typing import Optional

from dotenv import load_dotenv
from openai import OpenAI

from .xconfig import PROJECT_ROOT, _log

load_dotenv(PROJECT_ROOT / ".env", override=False)


class PromptTools:
    """提示词生成工具。"""

    _DEFAULT_IMAGE_SYSTEM = (
        "You are a professional image prompt engineer specializing in tech-aesthetic visuals.\n"
        "Generate a concise image generation prompt based on the given technology topic.\n\n"
        "Hard rules:\n"
        "- NO Chinese characters anywhere in the output\n"
        "- Visual style: clean tech commercial poster, dark background, neon / holographic accents, "
        "circuit patterns, tasteful glowing code\n"
        "- Naturally embed 3-5 short professional English tech terms as visible text elements in the scene "
        "(e.g., labels, HUDs, floating tags); keep each term under 3 words\n"
        "- Total prompt length: 60-120 words\n"
        "- Output ONLY the prompt, no explanation, no prefix"
    )

    _DEFAULT_DESCRIPTION_SYSTEM = (
        "你是一名在闲鱼长期接单的程序员，现在要写一段闲鱼服务商品描述。\n\n"
        "根据给定的技术主题，严格按照以下结构和格式输出，不要修改格式骨架。\n\n"
        "注意：\n"
        "1. 语气要客观描述，不要迎合客户，不要夸张承诺\n"
        "2. 禁止使用 emoji 表情\n"
        "3. 不要承诺绕过平台规则、代刷、违规引流或任何灰产行为\n\n"
        "【第一段，1~2行】\n"
        "简短自我介绍，点明专注方向，末尾说「帮你快速脱坑」。\n"
        "格式参考：本人 (互联网一线从业者)，专注 XX 方向，帮你快速脱坑，把时间花在更重要的事情上。\n\n"
        "【第二段，用下面的分隔线括起来】\n"
        "-----------------------------------------------------\n"
        "我能帮你解决这些事儿 (主打一个专注):\n"
        "【分类名】：用口语写，说清楚能做什么、具体怎么操作，不要泛泛而谈。\n"
        "（根据主题选 3~5 个最合适的分类，常见分类：环境配置、代码调试、模型训练、模型使用、"
        "参数调优、部署上线、数据处理、效果优化等）\n"
        "-----------------------------------------------------\n\n"
        "【第三段，用下面的分隔线括起来】\n"
        "-----------------------------------------------------\n"
        "主攻技术 (为了让你能搜到我):\n"
        "按 2~4 个维度分组，尽量多列相关的技术/框架/工具/模型名，用逗号分隔。\n"
        "格式参考：AIGC 生成框架：Stable Diffusion, Flux, ComfyUI\n"
        "-----------------------------------------------------\n\n"
        "严格禁止：\n"
        "- 禁止编造虚构用户场景（设计师、艺术家、老板、企业主等）\n"
        "- 禁止使用效率、赋能、解决方案、激发创意、节省时间等空洞词汇\n"
        "- 禁止介绍这个技术是什么或有什么意义\n"
        "- 禁止加多余的标题行、前言、结束语\n"
        "- 只输出正文，不加任何说明"
    )

    _EMOJI_RE = re.compile(
        r"[^\x09\x0A\x0D\x20-\x7E"
        r"\u2014\u2018\u2019\u201C\u201D"
        r"\u300A-\u300F\u3010\u3011\uFF08\uFF09"
        r"\u3000-\u303F"
        r"\u4E00-\u9FFF"
        r"\uFF00-\uFFEF]+"
    )

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        base_url: Optional[str] = None,
    ):
        self.api_key = api_key or os.environ.get("AGENT_LLM_API_KEY", "")
        self.model = model or os.environ.get("AGENT_LLM_MODEL", "qwen-max")
        self.base_url = base_url or os.environ.get(
            "AGENT_LLM_BASE_URL",
            "https://dashscope.aliyuncs.com/compatible-mode/v1",
        )

    @staticmethod
    def _temperature() -> float:
        try:
            return float(os.environ.get("AGENT_LLM_TEMPERATURE", "0.7"))
        except ValueError:
            return 0.7

    @classmethod
    def _strip_emoji(cls, text: str) -> str:
        """移除 emoji 及不可见字符，保留中英文、数字和常用标点。"""
        return cls._EMOJI_RE.sub("", text)

    @staticmethod
    def _strip_to_ascii(text: str) -> str:
        return text.encode("ascii", "ignore").decode("ascii")

    @staticmethod
    def _normalize_topic(topic: str) -> tuple[bool, str]:
        topic = (topic or "").strip()
        if not topic:
            return False, "topic 不能为空。"
        if len(topic) > 120:
            return False, "topic 过长，请控制在 120 字以内。"
        return True, topic

    def _call_llm(self, system_prompt: str, user_content: str) -> str:
        api_key = os.environ.get("AGENT_LLM_API_KEY", self.api_key)
        if not api_key:
            return "未配置 AGENT_LLM_API_KEY，请先复制 .env.example 为 .env 并填写 API Key。"

        model = os.environ.get("AGENT_LLM_MODEL", self.model)
        base_url = os.environ.get("AGENT_LLM_BASE_URL", self.base_url)

        try:
            client = OpenAI(api_key=api_key, base_url=base_url, timeout=60)
            resp = client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_content},
                ],
                temperature=self._temperature(),
            )
        except Exception as e:
            _log(f"[PromptTools] LLM 调用失败: {e}", "warning")
            return f"LLM 调用失败：{e}"

        content = resp.choices[0].message.content if resp.choices else ""
        content = (content or "").strip()
        if not content:
            return "LLM 返回为空，请稍后重试或检查模型配置。"
        return content

    def generate_image_prompt(self, topic: str) -> str:
        ok, topic_or_error = self._normalize_topic(topic)
        if not ok:
            return topic_or_error

        system = os.environ.get("PROMPT_IMAGE_SYSTEM", "").strip() or self._DEFAULT_IMAGE_SYSTEM
        _log(f"[PromptTools] 生成生图提示词，主题：{topic_or_error}")

        result = self._call_llm(system, f"Technology topic: {topic_or_error}")
        if result.startswith(("未配置", "LLM 调用失败", "LLM 返回为空")):
            return result

        result = self._strip_to_ascii(result).strip().strip("\"'")
        result = re.sub(r"\s+", " ", result)
        return result

    def generate_product_description(self, topic: str) -> str:
        ok, topic_or_error = self._normalize_topic(topic)
        if not ok:
            return topic_or_error

        system = os.environ.get("PROMPT_DESCRIPTION_SYSTEM", "").strip() or self._DEFAULT_DESCRIPTION_SYSTEM
        _log(f"[PromptTools] 生成商品描述，主题：{topic_or_error}")

        result = self._call_llm(system, f"技术主题：{topic_or_error}")
        if result.startswith(("未配置", "LLM 调用失败", "LLM 返回为空")):
            return result

        result = self._strip_emoji(result).strip()
        result = re.sub(r"\n{3,}", "\n\n", result)
        return result
