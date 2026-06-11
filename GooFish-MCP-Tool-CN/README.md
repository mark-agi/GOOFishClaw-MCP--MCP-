# GooFish-MCP-Tool-CN

中文闲鱼 / Goofish 自动化 MCP 工具。通过 Playwright 打开真实浏览器，给 Claude Desktop、Cursor、Cherry Studio 等 MCP 客户端提供商品搜索、扫码登录、发布草稿、发布确认、在售商品管理、封面图生成和商品文案生成能力。

> 本项目面向个人效率工具和学习研究场景。使用时请遵守闲鱼 / Goofish 平台规则，不要用于刷量、骚扰、违规引流或其他违反平台条款的行为。

## 功能

- 扫码登录并本地保存 cookies
- 搜索闲鱼商品，辅助竞品调研和定价参考
- 自动进入发布页，上传图片、填写描述、选择分类、填写价格
- 发布前保存截图，方便人工确认
- 人工确认后再调用正式发布
- 获取当前账号在售商品列表
- 对指定商品执行下架或删除
- 生成技术服务类商品描述
- 生成科技感封面图提示词
- 调用 DashScope / MiniMax 生成封面图
- 浏览器重启、配置热重载、页面文本读取等诊断工具

## 环境要求

- Python 3.11+
- Chromium / Playwright 浏览器
- 一个支持 MCP 的客户端
- 可选：兼容 OpenAI Chat Completions 的 LLM API Key
- 可选：DashScope 或 MiniMax 生图 API Key

## 快速开始

```bash
cd GooFish-MCP-Tool-CN

python3.11 -m venv .venv
source .venv/bin/activate

pip install -e .
playwright install chromium

cp .env.example .env
```

编辑 `.env`，至少按需填写：

```bash
AGENT_LLM_API_KEY=你的文案模型 Key
IMAGE_API_KEY=你的 DashScope Key
```

如果只使用闲鱼自动化，不生成文案和图片，也可以先不填 API Key。

## MCP 客户端配置

把下面路径替换成你的本地绝对路径：

```json
{
  "mcpServers": {
    "goofish-mcp-tool-cn": {
      "command": "/你的路径/GooFish-MCP-Tool-CN/.venv/bin/python",
      "args": ["/你的路径/GooFish-MCP-Tool-CN/server.py"]
    }
  }
}
```

也可以把环境变量直接写进客户端配置，但更推荐使用项目根目录的 `.env`。

## 本地运行

stdio 模式：

```bash
python server.py
```

HTTP 模式：

```bash
python server.py --http
```

## 推荐工作流

首次使用：

```text
login
```

发布商品：

```text
generate_image_prompt -> generate_image -> generate_product_description -> draft_item -> 人工查看截图 -> publish_item
```

管理商品：

```text
get_selling_items -> manage_item
```

诊断页面：

```text
get_page_content
restart_browser
reload_config
```

## 工具列表

| 工具 | 说明 |
| --- | --- |
| `login` | 检查登录状态，未登录时打开浏览器等待扫码 |
| `search_market` | 搜索关键词商品，返回标题、价格、链接 |
| `draft_item` | 填写商品草稿并保存截图 |
| `publish_item` | 正式点击发布按钮 |
| `get_selling_items` | 获取当前账号在售商品 |
| `manage_item` | 下架或删除指定商品 |
| `get_page_content` | 读取当前页面可见文本 |
| `restart_browser` | 重启 Playwright 浏览器 |
| `reload_config` | 重新加载 `.env` 并重置工具实例 |
| `generate_image_prompt` | 生成英文封面图提示词 |
| `generate_image` | 生成图片并缓存到本地 |
| `generate_product_description` | 生成闲鱼商品描述 |
| `simulate_farming` | 可选工具，需启动前设置 `ENABLE_FARMING=true` |

## 配置说明

`.env.example` 已列出全部配置。常用项如下：

| 变量 | 默认值 | 说明 |
| --- | --- | --- |
| `XIANYU_HOME_URL` | `https://www.goofish.com` | 闲鱼 / Goofish 首页 |
| `COOKIES_PATH` | `.cache/cookies/goofish_cookies.json` | cookies 保存位置 |
| `PLAYWRIGHT_HEADLESS` | `false` | 是否无头运行，扫码建议保持 false |
| `PROXY` | 空 | 代理地址，例如 `http://127.0.0.1:7890` |
| `AGENT_LLM_MODEL` | `qwen-max` | 文案生成模型 |
| `AGENT_LLM_API_KEY` | 空 | 文案生成 API Key |
| `AGENT_LLM_BASE_URL` | DashScope 兼容地址 | OpenAI 兼容接口地址 |
| `IMAGE_PROVIDER` | `dashscope` | 生图供应商：`dashscope` / `minimax` |
| `IMAGE_API_KEY` | 空 | DashScope 生图 Key |
| `MINIMAX_API_KEY` | 空 | MiniMax 生图 Key |
| `ENABLE_FARMING` | `false` | 是否注册模拟浏览工具 |

## 可靠性优化点

这一版相比原始工程做了这些整理：

- 项目重命名为 `GooFish-MCP-Tool-CN`
- 移除开源仓库不该提交的 `.env`、cookies、虚拟环境、日志和缓存
- `reload_config` 会真正重置浏览器、文案工具和生图工具
- 登录判断改为命中明确已登录特征才放行，降低误判
- `draft_item` 成功后返回截图路径和每一步状态
- `manage_item` 增加登录拦截、URL 校验和错误兜底
- 搜索结果返回完整商品链接
- 在售商品滚动采集修正新增计数逻辑
- 生图 provider 覆盖时自动使用对应模型
- 生图失败时返回可诊断原因，并回退到默认图片
- 文案生成增加参数校验、超时、异常提示和图片提示词 ASCII 清洗
- 日志路径、截图路径、缓存路径固定到项目目录内

## 常见问题

### 为什么必须先调用 `login`？

闲鱼页面依赖真实浏览器登录态。首次使用需要扫码登录，之后 cookies 会保存到 `.cache/cookies/goofish_cookies.json`。

### 为什么 `draft_item` 后还要人工确认？

发布商品是平台上的真实操作。工具会先填写草稿并截图，确认无误后再调用 `publish_item`。

### 修改 `.env` 后为什么没生效？

调用 `reload_config`。如果你是从 `ENABLE_FARMING=false` 改为 `true`，需要重启 MCP，因为工具注册发生在启动阶段。

### 没有生图 API Key 会怎样？

`generate_image` 会返回项目内置默认图片路径，并说明未生成新图片的原因。

## 目录结构

```text
.
├── server.py
├── tools/
│   ├── generate_image_tools.py
│   ├── prompt_tools.py
│   ├── xconfig.py
│   └── xianyu_tools.py
├── assets/
│   └── default_agent.png
├── .env.example
├── .gitignore
├── LICENSE
├── pyproject.toml
└── README.md
```

## 免责声明

本项目不隶属于闲鱼、Goofish 或阿里巴巴。页面结构、登录流程、平台规则可能变化，自动化能力不保证长期可用。请自行承担账号风控和平台合规风险。
