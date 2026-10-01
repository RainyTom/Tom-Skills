"""
MinerU Document Converter — Configuration Manager.

Manages YAML config files for MinerU API tokens and default settings.
Converts PDF, images, Office docs, HTML and more to Markdown.
Config file locations (first found wins):
  1. ./.anything-to-markdown.yaml (project-level)
  2. <skill_dir>/config.yaml (skill directory, default)
Environment variable MINERU_TOKEN overrides token from config.
"""

from __future__ import annotations

import os
import yaml
from pathlib import Path


# Default config paths
# <skill_dir>/config.yaml is the primary default (alongside this script's SKILL.md)
SKILL_DIR = Path(__file__).resolve().parent.parent
SKILL_CONFIG_PATH = SKILL_DIR / "config.yaml"
PROJECT_CONFIG_PATH = Path.cwd() / ".anything-to-markdown.yaml"

DEFAULT_CONFIG = {
    "mineru": {
        "token": "",
        "default_model": "vlm",
        "default_language": "ch",
        "default_enable_table": True,
        "default_enable_formula": True,
        "default_is_ocr": False,
        "poll_interval": 3,
        "poll_timeout": 300,
    }
}


class ConfigManager:
    """Manages MinerU configuration from YAML files and environment variables."""

    def __init__(self, config_path: str | Path | None = None):
        self._config = dict(DEFAULT_CONFIG)
        self._config_path = None

        if config_path:
            self._config_path = Path(config_path)
        elif PROJECT_CONFIG_PATH.exists():
            self._config_path = PROJECT_CONFIG_PATH
        elif SKILL_CONFIG_PATH.exists():
            self._config_path = SKILL_CONFIG_PATH

        if self._config_path:
            self._load()

    def _load(self):
        """Load config from YAML file."""
        try:
            with open(self._config_path, "r") as f:
                loaded = yaml.safe_load(f)
            if loaded:
                self._deep_merge(self._config, loaded)
        except Exception as e:
            print(f"Warning: Failed to load config from {self._config_path}: {e}")

    @staticmethod
    def _deep_merge(base: dict, override: dict):
        """Recursively merge override into base."""
        for key, value in override.items():
            if key in base and isinstance(base[key], dict) and isinstance(value, dict):
                ConfigManager._deep_merge(base[key], value)
            else:
                base[key] = value

    def get_token(self) -> str:
        """Get MinerU API token. Env var > config file > empty."""
        env_token = os.environ.get("MINERU_TOKEN")
        if env_token:
            return env_token
        return self._config.get("mineru", {}).get("token", "")

    def get(self, key: str, default=None):
        """Get a config value by dot-separated key (e.g., 'mineru.poll_interval')."""
        keys = key.split(".")
        value = self._config
        for k in keys:
            if isinstance(value, dict):
                value = value.get(k)
            else:
                return default
        return value if value is not None else default

    @property
    def config(self) -> dict:
        return dict(self._config)

    @property
    def config_path(self) -> Path | None:
        return self._config_path

    @staticmethod
    def init_interactive():
        """Interactive initialization of config file."""
        print("=" * 50)
        print("  MinerU 文档转换 — 配置初始化")
        print("=" * 50)

        token = input("\n请输入 MinerU 精准解析 API Token（留空跳过）: ").strip()
        model = (
            input("默认模型 [pipeline/vlm/MinerU-HTML] (默认 vlm): ").strip() or "vlm"
        )
        lang = input("默认语言 (默认 ch): ").strip() or "ch"
        interval = input("轮询间隔秒数 (默认 3): ").strip() or "3"
        timeout = input("轮询超时秒数 (默认 300): ").strip() or "300"

        config = {
            "mineru": {
                "token": token,
                "default_model": model,
                "default_language": lang,
                "default_enable_table": True,
                "default_enable_formula": True,
                "default_is_ocr": False,
                "poll_interval": int(interval),
                "poll_timeout": int(timeout),
            }
        }

        # Ask where to save
        print("\n保存位置:")
        print(f"  1) SKILL 目录: {SKILL_CONFIG_PATH}")
        print(f"  2) 项目本地: {PROJECT_CONFIG_PATH}")
        choice = input("请选择 (1/2, 默认 1): ").strip() or "1"

        if choice == "2":
            save_path = PROJECT_CONFIG_PATH
        else:
            save_path = SKILL_CONFIG_PATH

        save_path.parent.mkdir(parents=True, exist_ok=True)
        with open(save_path, "w") as f:
            yaml.dump(config, f, default_flow_style=False, allow_unicode=True)

        print(f"\n✅ 配置已保存到: {save_path}")
        return config

    @staticmethod
    def show():
        """Display current config (masking token)."""
        cm = ConfigManager()
        cfg = cm.config
        token = cm.get_token()
        masked = token[:4] + "****" + token[-4:] if len(token) > 8 else "****"

        print("=" * 50)
        print("  MinerU 文档转换 — 当前配置")
        print("=" * 50)
        print(f"  配置文件:      {cm.config_path or '未找到'}")
        print(f"  Token:         {masked if token else '(未设置)'}")
        print(f"  默认模型:      {cm.get('mineru.default_model')}")
        print(f"  默认语言:      {cm.get('mineru.default_language')}")
        print(f"  启用表格识别:  {cm.get('mineru.default_enable_table')}")
        print(f"  启用公式识别:  {cm.get('mineru.default_enable_formula')}")
        print(f"  启用 OCR:      {cm.get('mineru.default_is_ocr')}")
        print(f"  轮询间隔:      {cm.get('mineru.poll_interval')}s")
        print(f"  轮询超时:      {cm.get('mineru.poll_timeout')}s")
        print("=" * 50)


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "init":
        ConfigManager.init_interactive()
    elif len(sys.argv) > 1 and sys.argv[1] == "show":
        ConfigManager.show()
    else:
        print("用法: python3 config_manager.py [init|show]")
