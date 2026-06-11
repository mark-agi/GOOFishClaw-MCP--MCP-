"""
GooFish MCP Tool CN
===================

面向闲鱼 / Goofish 的 MCP 自动化工具。支持扫码登录、竞品搜索、
商品草稿填写、发布确认、在售商品管理、封面图生成和商品文案生成。

默认以 stdio 模式运行，适配 Claude Desktop、Cursor、Cherry Studio 等 MCP 客户端。
"""
from __future__ import annotations

import asyncio
import concurrent.futures
import functools
import os
from pathlib import Path
from typing import Literal, Optional

from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP
from mcp.types import ToolAnnotations

from tools.generate_image_tools import GenerateImageTools
from tools.prompt_tools import PromptTools
from tools.xianyu_tools import GooFishTools

PROJECT_ROOT = Path(__file__).resolve().parent
load_dotenv(PROJECT_ROOT / ".env", override=True)


def _env_bool(name: str, default: bool = False) -> bool:
    raw = os.environ.get(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "y", "on"}


def _runtime_settings() -> dict[str, object]:
    return {
        "cookies_path": os.environ.get(
            "COOKIES_PATH",
            str(PROJECT_ROOT / ".cache" / "cookies" / "goofish_cookies.json"),
        ),
        "headless": _env_bool("PLAYWRIGHT_HEADLESS", False),
        "proxy": os.environ.get("PROXY") or None,
        "enable_farming": _env_bool("ENABLE_FARMING", False),
    }


def _mask(value: str) -> str:
    if not value:
        return "(empty)"
    return value[:6] + "***" if len(value) > 8 else "***"


mcp = FastMCP(
    "GooFish-MCP-Tool-CN",
    instructions=(
        "中文闲鱼 / Goofish MCP 自动化助手，支持扫码登录、市场调研、商品发布草稿、"
        "发布确认、在售商品管理、封面图生成和商品文案生成。\n"
        "推荐发布流程：generate_image_prompt -> generate_image -> "
        "generate_product_description -> draft_item -> 人工确认截图 -> publish_item。\n"
        "推荐管理流程：get_selling_items -> manage_item。\n"
        "涉及发布、下架、删除等动作前，请务必让用户确认。"
    ),
)

# sync_playwright 必须在没有 asyncio event loop 的线程里运行。
# 单线程可以保证同一 MCP 会话里的浏览器上下文串行复用。
_playwright_executor = concurrent.futures.ThreadPoolExecutor(max_workers=1)


async def _run_sync(fn, *args, **kwargs):
    loop = asyncio.get_running_loop()
    wrapper = functools.partial(fn, *args, **kwargs)
    return await loop.run_in_executor(_playwright_executor, wrapper)


_xianyu: Optional[GooFishTools] = None
_image_tools: Optional[GenerateImageTools] = None
_prompt_tools: Optional[PromptTools] = None


def _get_xianyu() -> GooFishTools:
    global _xianyu
    if _xianyu is None:
        settings = _runtime_settings()
        _xianyu = GooFishTools(**settings)
    return _xianyu


def _get_image_tools() -> GenerateImageTools:
    global _image_tools
    if _image_tools is None:
        _image_tools = GenerateImageTools()
    return _image_tools


def _get_prompt_tools() -> PromptTools:
    global _prompt_tools
    if _prompt_tools is None:
        _prompt_tools = PromptTools()
    return _prompt_tools


def _reload_config_sync() -> str:
    global _xianyu, _image_tools, _prompt_tools

    load_dotenv(PROJECT_ROOT / ".env", override=True)

    if _xianyu is not None:
        try:
            _xianyu.close()
        except Exception:
            pass
        finally:
            _xianyu = None

    _image_tools = None
    _prompt_tools = None

    settings = _runtime_settings()
    keys = [
        ("AGENT_LLM_MODEL", os.environ.get("AGENT_LLM_MODEL", "qwen-max")),
        ("AGENT_LLM_API_KEY", _mask(os.environ.get("AGENT_LLM_API_KEY", ""))),
        ("AGENT_LLM_BASE_URL", os.environ.get("AGENT_LLM_BASE_URL", "")),
        ("IMAGE_PROVIDER", os.environ.get("IMAGE_PROVIDER", "dashscope")),
        ("IMAGE_API_KEY", _mask(os.environ.get("IMAGE_API_KEY", ""))),
        ("MINIMAX_API_KEY", _mask(os.environ.get("MINIMAX_API_KEY", ""))),
        ("PLAYWRIGHT_HEADLESS", str(settings["headless"])),
        ("PROXY", os.environ.get("PROXY", "")),
        ("COOKIES_PATH", str(settings["cookies_path"])),
    ]

    lines = ["配置已重新加载，浏览器和 AI 工具实例已重置："]
    lines.extend(f"  {name} = {value}" for name, value in keys)
    if _env_bool("ENABLE_FARMING", False):
        lines.append("  ENABLE_FARMING = true（如启动时未启用，需重启 MCP 后才会注册养号工具）")
    return "\n".join(lines)


@mcp.tool()
async def reload_config() -> str:
    """重新加载 .env 并重置浏览器、文案生成、生图工具实例。"""
    return await _run_sync(_reload_config_sync)


@mcp.tool()
async def login(timeout_seconds: int = 180) -> str:
    """检查闲鱼登录状态；未登录时打开浏览器等待用户扫码登录。"""
    return await _run_sync(_get_xianyu().login, timeout_seconds=timeout_seconds)


@mcp.tool(annotations=ToolAnnotations(readOnlyHint=True))
async def search_market(keyword: str, max_results: int = 20) -> str:
    """搜索关键词下的闲鱼商品，返回标题、价格和链接，用于竞品调研。"""
    return await _run_sync(
        _get_xianyu().search_market,
        keyword=keyword,
        max_results=max_results,
    )


@mcp.tool()
async def draft_item(image: str, description: str, price: float = 100.0) -> str:
    """填写商品发布草稿并截图。调用 publish_item 前需要人工确认截图。"""
    return await _run_sync(
        _get_xianyu().draft_item,
        image=image,
        description=description,
        price=price,
    )


@mcp.tool(annotations=ToolAnnotations(destructiveHint=True))
async def publish_item() -> str:
    """点击发布按钮。此操作会正式发布商品，调用前必须确认草稿截图。"""
    return await _run_sync(_get_xianyu().publish_item)


@mcp.tool(annotations=ToolAnnotations(readOnlyHint=True))
async def get_selling_items() -> str:
    """获取当前账号在售商品列表。"""
    return await _run_sync(_get_xianyu().get_selling_items)


@mcp.tool(annotations=ToolAnnotations(destructiveHint=True))
async def manage_item(item_url: str, action: Literal["delist", "delete"]) -> str:
    """对指定商品执行下架或删除。delete 为永久删除，请谨慎调用。"""
    return await _run_sync(
        _get_xianyu().manage_item,
        item_url=item_url,
        action=action,
    )


@mcp.tool(annotations=ToolAnnotations(readOnlyHint=True))
async def get_page_content(max_chars: int = 3000) -> str:
    """读取当前浏览器页面可见文字，便于诊断页面状态。"""
    return await _run_sync(_get_xianyu().get_page_content, max_chars=max_chars)


@mcp.tool()
async def restart_browser() -> str:
    """关闭并重新创建 Playwright 浏览器实例。"""

    def _restart_sync() -> None:
        global _xianyu
        if _xianyu is not None:
            try:
                _xianyu.close()
            except Exception:
                pass
            finally:
                _xianyu = None
        _get_xianyu()._ensure_browser()

    await _run_sync(_restart_sync)
    return "浏览器已重新初始化。请先调用 login 验证登录状态，再继续发布或管理商品。"


if _env_bool("ENABLE_FARMING", False):

    @mcp.tool()
    async def simulate_farming(duration_minutes: int = 5) -> str:
        """模拟正常用户浏览行为。需启动 MCP 前设置 ENABLE_FARMING=true。"""
        return await _run_sync(
            _get_xianyu().simulate_farming,
            duration_minutes=duration_minutes,
        )


@mcp.tool()
def generate_image(prompt: str, size: str = "1024*1024", provider: str = "") -> str:
    """根据提示词生成商品封面图，并返回本地缓存路径。"""
    return _get_image_tools().generate_image(prompt=prompt, size=size, provider=provider)


@mcp.tool(annotations=ToolAnnotations(readOnlyHint=True))
def generate_image_prompt(topic: str) -> str:
    """根据技术主题生成英文科技感封面图提示词。"""
    return _get_prompt_tools().generate_image_prompt(topic=topic)


@mcp.tool(annotations=ToolAnnotations(readOnlyHint=True))
def generate_product_description(topic: str) -> str:
    """根据技术主题生成闲鱼商品描述文案。"""
    return _get_prompt_tools().generate_product_description(topic=topic)


if __name__ == "__main__":
    import sys

    transport = "streamable-http" if "--http" in sys.argv else "stdio"
    if transport == "streamable-http":
        print("GooFish MCP Tool CN 启动中（HTTP 模式）...")
        print("默认地址: http://localhost:8000/mcp")
        print("按 Ctrl+C 停止服务器\n")
    mcp.run(transport=transport)
