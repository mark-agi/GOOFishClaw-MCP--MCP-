# GOOFishClaw-MCP--MCP-
GOOFishClaw-MCP-CN Version-CosmicAGI
GooFish-MCP-Tool-CN
<img width="940" height="940" alt="joey" src="https://github.com/user-attachments/assets/e98b07d4-35d3-48c5-bfa8-0d08e07ab1a6" />

A Chinese Goofish / Xianyu automation MCP tool.

This project uses Playwright to open and control a real browser session, exposing marketplace workflow tools to MCP clients such as Claude Desktop, Cursor, Cherry Studio, and other Model Context Protocol-compatible clients.

It provides capabilities for product search, QR-code login, listing draft creation, manual publish confirmation, active listing management, cover image generation, and product copy generation.

This project is intended for personal productivity, workflow automation, learning, and research purposes. Please follow the rules of Goofish / Xianyu. Do not use this tool for fake engagement, spam, harassment, illegal promotion, or any activity that violates platform terms.

Features

* QR-code login with local cookie storage
* Search Goofish / Xianyu listings for competitor research and pricing reference
* Automatically open the listing page, upload images, fill in descriptions, select categories, and set prices
* Save a screenshot before publishing for manual review
* Publish only after explicit manual confirmation
* Retrieve the current account’s active listings
* Delist or delete a specific item
* Generate product descriptions for technical service listings
* Generate tech-style cover image prompts
* Generate cover images with DashScope or MiniMax
* Browser restart, configuration reload, page text extraction, and other diagnostic tools

Requirements

* Python 3.11+
* Chromium / Playwright browser
* An MCP-compatible client
* Optional: an OpenAI Chat Completions-compatible LLM API key
* Optional: a DashScope or MiniMax image generation API key

Quick Start

cd GooFish-MCP-Tool-CN
python3.11 -m venv .venv
source .venv/bin/activate
pip install -e .
playwright install chromium
cp .env.example .env

Edit .env and fill in the required keys as needed:

AGENT_LLM_API_KEY=your_text_generation_model_key
IMAGE_API_KEY=your_dashscope_key

If you only use the Goofish / Xianyu automation tools and do not need copywriting or image generation, you can leave the API keys empty at first.

MCP Client Configuration

Replace the path below with your local absolute path:

{
  "mcpServers": {
    "goofish-mcp-tool-cn": {
      "command": "/your/path/GooFish-MCP-Tool-CN/.venv/bin/python",
      "args": ["/your/path/GooFish-MCP-Tool-CN/server.py"]
    }
  }
}

You can also put environment variables directly into the MCP client configuration, but using the project-level .env file is recommended.

Local Run

stdio mode:

python server.py

HTTP mode:

python server.py --http

Recommended Workflow

First-time login:

login

Create and publish a listing:

generate_image_prompt -> generate_image -> generate_product_description -> draft_item -> manually review screenshot -> publish_item

Manage listings:

get_selling_items -> manage_item

Page diagnostics:

get_page_content
restart_browser
reload_config

Tool List

Tool	Description
login	Checks login status. If not logged in, opens a browser and waits for QR-code login.
search_market	Searches listings by keyword and returns titles, prices, and links.
draft_item	Fills in a listing draft and saves a screenshot.
publish_item	Clicks the final publish button.
get_selling_items	Retrieves the current account’s active listings.
manage_item	Delists or deletes a specific item.
get_page_content	Reads visible text from the current page.
restart_browser	Restarts the Playwright browser session.
reload_config	Reloads .env and resets tool instances.
generate_image_prompt	Generates an English cover image prompt.
generate_image	Generates an image and caches it locally.
generate_product_description	Generates a Goofish / Xianyu product description.
simulate_farming	Optional tool. Requires ENABLE_FARMING=true before startup.

Configuration

All available configuration options are listed in .env.example.

Common options:

Variable	Default	Description
XIANYU_HOME_URL	https://www.goofish.com	Goofish / Xianyu homepage.
COOKIES_PATH	.cache/cookies/goofish_cookies.json	Local cookie storage path.
PLAYWRIGHT_HEADLESS	false	Whether to run the browser in headless mode. Keep it false for QR-code login.
PROXY	Empty	Proxy address, for example http://127.0.0.1:7890.
AGENT_LLM_MODEL	qwen-max	Model used for product copy generation.
AGENT_LLM_API_KEY	Empty	API key for product copy generation.
AGENT_LLM_BASE_URL	DashScope-compatible endpoint	OpenAI-compatible API base URL.
IMAGE_PROVIDER	dashscope	Image generation provider: dashscope or minimax.
IMAGE_API_KEY	Empty	DashScope image generation key.
MINIMAX_API_KEY	Empty	MiniMax image generation key.
ENABLE_FARMING	false	Whether to register the optional browsing simulation tool.

Reliability Improvements

This version includes the following cleanups and reliability improvements compared with the original project:

* Renamed the project to GooFish-MCP-Tool-CN
* Removed files that should not be committed to an open-source repository, including .env, cookies, virtual environments, logs, and caches
* reload_config now properly resets the browser, copywriting tools, and image generation tools
* Login detection now requires clear logged-in indicators before passing, reducing false positives
* draft_item returns the screenshot path and step-by-step status after completion
* manage_item includes login interception, URL validation, and safer error handling
* Search results now return complete product links
* Fixed the incremental count logic when scrolling active listings
* Image generation automatically uses the matching model when the provider is overridden
* Image generation failures now return diagnosable reasons and fall back to the default image
* Product copy generation now includes parameter validation, timeout handling, clearer error messages, and ASCII cleanup for image prompts
* Log paths, screenshot paths, and cache paths are fixed inside the project directory

FAQ

Why do I need to call login first?

Goofish / Xianyu relies on a real browser login session. On first use, you need to scan the QR code manually. After login, cookies are saved to:

.cache/cookies/goofish_cookies.json

Why do I need to manually confirm after draft_item?

Publishing a listing is a real platform action. The tool first fills in the draft and saves a screenshot. You should review the screenshot before calling publish_item.

Why did my .env changes not take effect?

Call reload_config.

If you changed ENABLE_FARMING=false to true, you need to restart the MCP server because tool registration happens during startup.

What happens if I do not provide an image generation API key?

generate_image will return the built-in default image path and explain why a new image was not generated.

Project Structure

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

Disclaimer

This project is not affiliated with Goofish, Xianyu, or Alibaba.

Page structures, login flows, and platform rules may change at any time. Automation features are not guaranteed to remain available.

Use this project responsibly and at your own risk. You are responsible for account safety, platform compliance, and any consequences resulting from your usage.
