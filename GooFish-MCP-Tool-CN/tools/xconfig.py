import logging
import os
from datetime import datetime
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
LOG_DIR = Path(os.environ.get("GOOFISH_LOG_DIR") or PROJECT_ROOT / "logs").expanduser()
LOG_DIR.mkdir(parents=True, exist_ok=True)

_log_file = LOG_DIR / f"goofish_mcp_{datetime.now().strftime('%Y%m%d')}.log"
_logger = logging.getLogger("goofish_mcp")
_logger.setLevel(logging.DEBUG)
_logger.propagate = False

if not any(
    isinstance(handler, logging.FileHandler)
    and Path(handler.baseFilename) == _log_file
    for handler in _logger.handlers
):
    _file_handler = logging.FileHandler(_log_file, encoding="utf-8")
    _file_handler.setLevel(logging.DEBUG)
    _file_handler.setFormatter(
        logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
    )
    _logger.addHandler(_file_handler)


def _log(message: str, level: str = "info") -> None:
    """统一日志入口。"""
    log_fn = {
        "debug": _logger.debug,
        "info": _logger.info,
        "warning": _logger.warning,
        "error": _logger.error,
    }.get(level, _logger.info)
    log_fn(message)
