# Contributing

感谢你愿意改进 GooFish-MCP-Tool-CN。

## 开发流程

1. Fork 仓库并创建新分支。
2. 使用 Python 3.11+ 创建虚拟环境。
3. 安装依赖并安装 Playwright Chromium。
4. 修改代码后至少运行语法检查。
5. 提交 PR 时说明变更点、测试方式和已知风险。

```bash
python3.11 -m venv .venv
source .venv/bin/activate
pip install -e .
playwright install chromium
python -m compileall server.py tools
```

## 注意事项

- 不要提交 `.env`、cookies、日志、截图和缓存。
- 不要提交真实账号信息、API Key、手机号、订单信息或聊天记录。
- 涉及发布、下架、删除等真实平台操作时，请保留人工确认步骤。
- 页面选择器变更时，尽量保留旧选择器作为 fallback。
