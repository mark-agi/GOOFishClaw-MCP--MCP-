import datetime
import math
import os
import re
from pathlib import Path
from typing import Any, Optional, Union

import requests
from dotenv import load_dotenv

from .xconfig import PROJECT_ROOT, _log

load_dotenv(PROJECT_ROOT / ".env", override=False)


class GenerateImageTools:
    """图像生成工具。

    支持多个生图供应商：
      - dashscope: 阿里云 DashScope
      - minimax:   MiniMax

    输出同时包含中文路径说明和 PATH=...，便于后续工具直接提取本地图片路径。
    """

    _DASHSCOPE_API_URL = (
        "https://dashscope.aliyuncs.com/api/v1/services/aigc/"
        "multimodal-generation/generation"
    )
    _MINIMAX_API_URL = "https://api.minimaxi.com/v1/image_generation"
    _SIZE_RE = re.compile(r"^(\d{2,4})\*(\d{2,4})$")
    _SUPPORTED_PROVIDERS = {"dashscope", "minimax"}

    def __init__(
        self,
        api_key: Optional[str] = None,
        minimax_api_key: Optional[str] = None,
        provider: Optional[str] = None,
        model: Optional[str] = None,
        default_size: str = "1024*1024",
        prompt_extend: Optional[bool] = None,
        cache_path: Optional[str] = None,
    ):
        self.api_key = api_key or os.environ.get("IMAGE_API_KEY", "")
        self.minimax_api_key = minimax_api_key or os.environ.get("MINIMAX_API_KEY", "")
        self.provider = (provider or os.environ.get("IMAGE_PROVIDER", "dashscope")).lower()
        self.model_override = model
        self.dashscope_model = os.environ.get("DASHSCOPE_IMAGE_MODEL", "z-image-turbo")
        self.minimax_model = os.environ.get("MINIMAX_IMAGE_MODEL", "image-01")
        self.default_size = default_size
        self.prompt_extend = (
            self._env_bool("DASHSCOPE_PROMPT_EXTEND", False)
            if prompt_extend is None
            else prompt_extend
        )

        self.default_image_path = PROJECT_ROOT / "assets" / "default_agent.png"
        self.cache_path = Path(cache_path).expanduser() if cache_path else PROJECT_ROOT / ".cache" / "cache_img"
        self.cache_path.mkdir(parents=True, exist_ok=True)

    @staticmethod
    def _env_bool(name: str, default: bool = False) -> bool:
        raw = os.environ.get(name)
        if raw is None:
            return default
        return raw.strip().lower() in {"1", "true", "yes", "y", "on"}

    @staticmethod
    def _path_response(path: Union[Path, str], note: str = "") -> str:
        resolved = str(Path(path).expanduser().resolve())
        lines = [f"图片路径已经保存到：{resolved}", f"PATH={resolved}"]
        if note:
            lines.append(f"说明：{note}")
        return "\n".join(lines)

    def _fallback_response(self, reason: str) -> str:
        _log(f"[GenerateImageTools] {reason}，使用默认图片", "warning")
        return self._path_response(self.default_image_path, f"未生成新图片，{reason}，已使用默认图片。")

    def _validate_prompt(self, prompt: str) -> Optional[str]:
        if not prompt or not prompt.strip():
            return "prompt 不能为空"
        if len(prompt.strip()) > 2000:
            return "prompt 过长，请控制在 2000 字以内"
        return None

    def _validate_size(self, size: str) -> tuple[bool, str]:
        match = self._SIZE_RE.match(size.strip())
        if not match:
            return False, 'size 格式错误，请使用 "宽*高"，例如 1024*1024'
        width, height = int(match.group(1)), int(match.group(2))
        if not (256 <= width <= 2048 and 256 <= height <= 2048):
            return False, "size 宽高建议在 256 到 2048 之间"
        return True, f"{width}*{height}"

    def _provider_model(self, provider: str) -> str:
        if self.model_override:
            return self.model_override
        return self.minimax_model if provider == "minimax" else self.dashscope_model

    def _download_image(self, image_url: str) -> str:
        if not image_url.startswith(("http://", "https://")):
            return self._fallback_response("生图接口返回的图片 URL 无效")

        try:
            resp = requests.get(image_url, timeout=60)
            resp.raise_for_status()
        except requests.exceptions.RequestException as e:
            return self._fallback_response(f"图片下载失败：{e}")

        content_type = resp.headers.get("Content-Type", "image/png").lower()
        if content_type and "image" not in content_type:
            return self._fallback_response(f"图片下载响应不是图片：{content_type}")

        ext = ".jpg" if "jpeg" in content_type else ".png"
        filename = datetime.datetime.now().strftime("%Y%m%d_%H%M%S_%f") + ext
        local_path = self.cache_path / filename
        local_path.write_bytes(resp.content)

        _log(f"[GenerateImageTools] 图像已缓存到本地: {local_path}")
        return self._path_response(local_path)

    @staticmethod
    def _extract_url_from_minimax(result: dict[str, Any]) -> str:
        data = result.get("data")
        if isinstance(data, list) and data:
            first = data[0]
            if isinstance(first, dict):
                return first.get("url") or first.get("image_url") or ""
            if isinstance(first, str):
                return first
        if isinstance(data, dict):
            for key in ("url", "image_url"):
                if isinstance(data.get(key), str):
                    return data[key]
            for key in ("image_urls", "images"):
                urls = data.get(key)
                if isinstance(urls, list) and urls:
                    first = urls[0]
                    if isinstance(first, str):
                        return first
                    if isinstance(first, dict):
                        return first.get("url") or first.get("image_url") or ""
        return ""

    @staticmethod
    def _extract_url_from_dashscope(result: dict[str, Any]) -> str:
        output = result.get("output", {})
        choices = output.get("choices", []) if isinstance(output, dict) else []
        if choices:
            content = choices[0].get("message", {}).get("content", [])
            for item in content:
                if isinstance(item, dict) and item.get("image"):
                    return item["image"]

        results = output.get("results", []) if isinstance(output, dict) else []
        if results:
            first = results[0]
            if isinstance(first, dict):
                return first.get("url") or first.get("image") or ""
            if isinstance(first, str):
                return first
        return ""

    def _call_minimax(self, prompt: str, size: str, model: str) -> str:
        api_key = os.environ.get("MINIMAX_API_KEY", self.minimax_api_key)
        if not api_key:
            return self._fallback_response("未配置 MINIMAX_API_KEY")

        width, height = map(int, size.split("*"))
        divisor = math.gcd(width, height)
        ratio = f"{width // divisor}:{height // divisor}"
        payload = {
            "model": model,
            "prompt": prompt,
            "aspect_ratio": ratio,
            "n": 1,
            "response_format": "url",
            "prompt_optimizer": True,
        }

        _log(f"[GenerateImageTools] 请求 MiniMax 生图，模型={model}，比例={ratio}")

        try:
            response = requests.post(
                self._MINIMAX_API_URL,
                headers={"Authorization": f"Bearer {api_key}"},
                json=payload,
                timeout=120,
            )
            response.raise_for_status()
            result = response.json()
        except requests.exceptions.Timeout:
            return self._fallback_response("MiniMax 请求超时")
        except requests.exceptions.HTTPError as e:
            body = response.text[:300] if "response" in locals() else ""
            return self._fallback_response(f"MiniMax HTTP 错误：{e} {body}")
        except requests.exceptions.RequestException as e:
            return self._fallback_response(f"MiniMax 网络错误：{e}")
        except ValueError:
            return self._fallback_response("MiniMax 响应不是 JSON")

        image_url = self._extract_url_from_minimax(result)
        if not image_url:
            return self._fallback_response(f"MiniMax 响应中未找到图片 URL：{str(result)[:300]}")
        return self._download_image(image_url)

    def _call_dashscope(self, prompt: str, size: str, model: str) -> str:
        api_key = os.environ.get("IMAGE_API_KEY", self.api_key)
        if not api_key:
            return self._fallback_response("未配置 IMAGE_API_KEY")

        payload = {
            "model": model,
            "input": {
                "messages": [
                    {"role": "user", "content": [{"text": prompt}]},
                ]
            },
            "parameters": {
                "prompt_extend": self.prompt_extend,
                "size": size,
            },
        }

        _log(f"[GenerateImageTools] 请求 DashScope 生图，模型={model}，尺寸={size}")

        try:
            response = requests.post(
                self._DASHSCOPE_API_URL,
                headers={"Authorization": f"Bearer {api_key}"},
                json=payload,
                timeout=120,
            )
            response.raise_for_status()
            result = response.json()
        except requests.exceptions.Timeout:
            return self._fallback_response("DashScope 请求超时")
        except requests.exceptions.HTTPError as e:
            body = response.text[:300] if "response" in locals() else ""
            return self._fallback_response(f"DashScope HTTP 错误：{e} {body}")
        except requests.exceptions.RequestException as e:
            return self._fallback_response(f"DashScope 网络错误：{e}")
        except ValueError:
            return self._fallback_response("DashScope 响应不是 JSON")

        image_url = self._extract_url_from_dashscope(result)
        if not image_url:
            return self._fallback_response(f"DashScope 响应中未找到图片 URL：{str(result)[:300]}")
        return self._download_image(image_url)

    def generate_image(
        self,
        prompt: str,
        size: Optional[str] = None,
        provider: Optional[str] = None,
    ) -> str:
        """根据文本提示词生成图像并缓存到本地。"""
        prompt_error = self._validate_prompt(prompt)
        if prompt_error:
            return prompt_error

        actual_provider = (provider or self.provider or "dashscope").strip().lower()
        if actual_provider not in self._SUPPORTED_PROVIDERS:
            return f"provider 参数错误：{actual_provider}。可选值：dashscope / minimax。"

        ok, image_size = self._validate_size(size or self.default_size)
        if not ok:
            return image_size

        model = self._provider_model(actual_provider)
        _log(f"[GenerateImageTools] 供应商={actual_provider}，模型={model}，尺寸={image_size}")

        if actual_provider == "minimax":
            return self._call_minimax(prompt.strip(), image_size, model)
        return self._call_dashscope(prompt.strip(), image_size, model)
