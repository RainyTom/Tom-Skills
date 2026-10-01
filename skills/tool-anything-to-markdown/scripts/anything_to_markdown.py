#!/usr/bin/env python3
"""
MinerU Document to Markdown Converter (Precision API only).

Converts PDF, images (png/jpg/jpeg/jp2/webp/gif/bmp), Office documents (doc/docx/ppt/pptx/xls/xlsx),
and HTML files to Markdown via MinerU Precision API.

Requires a token configured via YAML or MINERU_TOKEN environment variable.

Usage:
  # Precision API (token required)
  python3 anything_to_markdown.py precision-url --url <URL> --model vlm --output ./dir/
  python3 anything_to_markdown.py precision-batch-url --files '[...]' --model vlm
  python3 anything_to_markdown.py precision-batch-file --files f1.pdf f2.pdf --model vlm

  # Config management
  python3 anything_to_markdown.py config init
  python3 anything_to_markdown.py config show
"""

from __future__ import annotations

import argparse
import io
import json
import os
import sys
import time
import zipfile
from pathlib import Path

import requests

# Add parent dir to path for config_manager import
sys.path.insert(0, str(Path(__file__).resolve().parent))
from config_manager import ConfigManager


BASE_URL = "https://mineru.net"


class MinerUConverter:
    """MinerU 文档 → Markdown 转换器（支持 PDF/图片/Office/HTML 等格式）"""

    def __init__(self, config_path: str | None = None):
        self.config = ConfigManager(config_path)
        self.token = self.config.get_token()
        self.session = requests.Session()

    # ═══════════════════════════════════════════════════════════
    #  精准解析 API（需 Token）
    # ═══════════════════════════════════════════════════════════

    # ═══════════════════════════════════════════════════════════
    #  精准解析 API（需 Token）
    # ═══════════════════════════════════════════════════════════

    def _precision_headers(self) -> dict:
        """构建精准 API 请求头。"""
        if not self.token:
            raise ValueError(
                "精准解析 API 需要 Token。请配置 config.yaml 或设置 MINERU_TOKEN 环境变量。"
            )
        return {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.token}",
        }

    def parse_url_precision(
        self,
        url: str,
        model_version: str = "vlm",
        is_ocr: bool | None = None,
        enable_formula: bool | None = None,
        enable_table: bool | None = None,
        language: str | None = None,
        data_id: str | None = None,
        page_ranges: str | None = None,
        callback: str | None = None,
        seed: str | None = None,
        extra_formats: list[str] | None = None,
        no_cache: bool | None = None,
        cache_tolerance: int | None = None,
        timeout: int | None = None,
        interval: int | None = None,
    ) -> dict:
        """精准解析 API — 单文件 URL 模式。返回包含 task_id, full_zip_url 等的 dict。"""
        data = {"url": url, "model_version": model_version}

        if is_ocr is not None:
            data["is_ocr"] = is_ocr
        if enable_formula is not None:
            data["enable_formula"] = enable_formula
        if enable_table is not None:
            data["enable_table"] = enable_table
        if language:
            data["language"] = language
        if data_id:
            data["data_id"] = data_id
        if page_ranges:
            data["page_ranges"] = page_ranges
        if callback:
            data["callback"] = callback
        if seed:
            data["seed"] = seed
        if extra_formats:
            data["extra_formats"] = extra_formats
        if no_cache is not None:
            data["no_cache"] = no_cache
        if cache_tolerance is not None:
            data["cache_tolerance"] = cache_tolerance

        headers = self._precision_headers()
        resp = self.session.post(
            f"{BASE_URL}/api/v4/extract/task", headers=headers, json=data
        )
        resp.raise_for_status()
        result = resp.json()

        if result["code"] != 0:
            raise Exception(f"提交任务失败: {result.get('msg', '未知错误')}")

        task_id = result["data"]["task_id"]
        print(f"[Precision/URL] 任务已提交, task_id: {task_id}")

        return self._poll_precision(task_id, timeout, interval)

    def parse_url_batch(
        self,
        files: list[dict],
        model_version: str = "vlm",
        is_ocr: bool | None = None,
        enable_formula: bool | None = None,
        enable_table: bool | None = None,
        language: str | None = None,
        callback: str | None = None,
        seed: str | None = None,
        extra_formats: list[str] | None = None,
        no_cache: bool | None = None,
        cache_tolerance: int | None = None,
        timeout: int | None = None,
        interval: int | None = None,
    ) -> list[dict]:
        """精准解析 API — 批量 URL 模式。files: [{"url": "...", "data_id": "..."}, ...]"""
        data = {"files": files, "model_version": model_version}

        if is_ocr is not None:
            data["is_ocr"] = is_ocr
        if enable_formula is not None:
            data["enable_formula"] = enable_formula
        if enable_table is not None:
            data["enable_table"] = enable_table
        if language:
            data["language"] = language
        if callback:
            data["callback"] = callback
        if seed:
            data["seed"] = seed
        if extra_formats:
            data["extra_formats"] = extra_formats
        if no_cache is not None:
            data["no_cache"] = no_cache
        if cache_tolerance is not None:
            data["cache_tolerance"] = cache_tolerance

        headers = self._precision_headers()
        resp = self.session.post(
            f"{BASE_URL}/api/v4/extract/task/batch", headers=headers, json=data
        )
        resp.raise_for_status()
        result = resp.json()

        if result["code"] != 0:
            raise Exception(f"提交批量任务失败: {result.get('msg', '未知错误')}")

        batch_id = result["data"]["batch_id"]
        print(f"[Precision/BatchURL] 批量任务已提交, batch_id: {batch_id}")

        return self._poll_precision_batch(batch_id, timeout, interval)

    def parse_file_batch(
        self,
        file_paths: list[str],
        model_version: str = "vlm",
        is_ocr: bool | None = None,
        enable_formula: bool | None = None,
        enable_table: bool | None = None,
        language: str | None = None,
        callback: str | None = None,
        seed: str | None = None,
        extra_formats: list[str] | None = None,
        timeout: int | None = None,
        interval: int | None = None,
    ) -> list[dict]:
        """精准解析 API — 本地文件批量上传模式。"""
        headers = self._precision_headers()

        # Prepare file list with data_ids
        files_payload = []
        for fp in file_paths:
            p = Path(fp)
            if not p.exists():
                raise FileNotFoundError(f"文件不存在: {p}")
            files_payload.append({"name": p.name, "data_id": p.stem})

        data = {"files": files_payload, "model_version": model_version}
        if is_ocr is not None:
            data["is_ocr"] = is_ocr
        if enable_formula is not None:
            data["enable_formula"] = enable_formula
        if enable_table is not None:
            data["enable_table"] = enable_table
        if language:
            data["language"] = language
        if callback:
            data["callback"] = callback
        if seed:
            data["seed"] = seed
        if extra_formats:
            data["extra_formats"] = extra_formats

        # Step 1: 申请上传链接
        resp = self.session.post(
            f"{BASE_URL}/api/v4/file-urls/batch", headers=headers, json=data
        )
        resp.raise_for_status()
        result = resp.json()

        if result["code"] != 0:
            raise Exception(f"获取上传链接失败: {result.get('msg', '未知错误')}")

        batch_id = result["data"]["batch_id"]
        upload_urls = result["data"]["file_urls"]
        print(f"[Precision/BatchFile] 上传链接已获取, batch_id: {batch_id}")

        # Step 2: 上传文件到 OSS
        for i, upload_url in enumerate(upload_urls):
            file_path = file_paths[i]
            with open(file_path, "rb") as f:
                put_resp = requests.put(upload_url, data=f)
                if put_resp.status_code not in (200, 201, 204):
                    raise Exception(
                        f"文件上传失败: {file_path}, HTTP {put_resp.status_code}"
                    )
                print(f"  ✅ 上传成功: {Path(file_path).name}")

        print("[Precision/BatchFile] 所有文件上传完成，等待解析...")
        return self._poll_precision_batch(batch_id, timeout, interval)

    def _poll_precision(
        self, task_id: str, timeout: int | None = None, interval: int | None = None
    ) -> dict:
        """轮询精准解析 API 单文件结果。"""
        timeout = timeout or self.config.get("mineru.poll_timeout", 300)
        interval = interval or self.config.get("mineru.poll_interval", 3)
        headers = self._precision_headers()

        state_labels = {
            "pending": "排队中",
            "running": "正在解析",
            "converting": "格式转换中",
        }
        start = time.time()

        while time.time() - start < timeout:
            resp = self.session.get(
                f"{BASE_URL}/api/v4/extract/task/{task_id}",
                headers=headers,
            )
            resp.raise_for_status()
            result = resp.json()
            data = result["data"]
            state = data["state"]
            elapsed = int(time.time() - start)

            if state == "done":
                print(f"[{elapsed}s] 解析完成")
                return data

            if state == "failed":
                err = data.get("err_msg", "未知错误")
                raise Exception(f"解析失败: {err}")

            # Show progress
            progress = data.get("extract_progress", {})
            if progress:
                print(
                    f"[{elapsed}s] {state_labels.get(state, state)}... "
                    f"({progress.get('extracted_pages', '?')}/{progress.get('total_pages', '?')} 页)"
                )
            else:
                print(f"[{elapsed}s] {state_labels.get(state, state)}...")
            time.sleep(interval)

        raise TimeoutError(f"轮询超时 ({timeout}s)，请稍后手动查询 task_id: {task_id}")

    def _poll_precision_batch(
        self, batch_id: str, timeout: int | None = None, interval: int | None = None
    ) -> list[dict]:
        """轮询精准解析 API 批量结果。"""
        timeout = timeout or self.config.get("mineru.poll_timeout", 300)
        interval = interval or self.config.get("mineru.poll_interval", 3)
        headers = self._precision_headers()

        state_labels = {
            "waiting-file": "等待文件上传",
            "pending": "排队中",
            "running": "正在解析",
            "converting": "格式转换中",
        }
        start = time.time()

        while time.time() - start < timeout:
            resp = self.session.get(
                f"{BASE_URL}/api/v4/extract-results/batch/{batch_id}",
                headers=headers,
            )
            resp.raise_for_status()
            result = resp.json()
            data = result["data"]
            elapsed = int(time.time() - start)

            results = data.get("extract_result", [])
            all_done = all(r["state"] == "done" for r in results)
            any_failed = any(r["state"] == "failed" for r in results)

            # Print progress
            done_count = sum(1 for r in results if r["state"] == "done")
            failed_count = sum(1 for r in results if r["state"] == "failed")
            running_count = sum(1 for r in results if r["state"] == "running")
            total = len(results)

            print(
                f"[{elapsed}s] 进度: {done_count}/{total} 完成, "
                f"{running_count} 进行中, {failed_count} 失败"
            )

            if all_done:
                print(f"[{elapsed}s] 全部解析完成")
                return results

            if any_failed and running_count == 0:
                failed_files = [
                    r.get("file_name", "?") for r in results if r["state"] == "failed"
                ]
                raise Exception(f"部分文件解析失败: {', '.join(failed_files)}")

            time.sleep(interval)

        raise TimeoutError(
            f"轮询超时 ({timeout}s)，请稍后手动查询 batch_id: {batch_id}"
        )

    # ═══════════════════════════════════════════════════════════
    #  工具方法
    # ═══════════════════════════════════════════════════════════

    @staticmethod
    def download_zip(zip_url: str, output_dir: str = "./output"):
        """下载并解压精准 API 的 Zip 结果包。"""
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        print(f"下载中: {zip_url}")
        resp = requests.get(zip_url, stream=True)
        resp.raise_for_status()

        z = zipfile.ZipFile(io.BytesIO(resp.content))
        z.extractall(output_path)
        print(f"解压完成 → {output_path.resolve()}")

        # List extracted files
        for f in output_path.iterdir():
            size = f.stat().st_size
            print(f"  {'📄' if f.is_file() else '📁'} {f.name} ({size:,} bytes)")

        return output_path

    @staticmethod
    def save_markdown(md_text: str, output_path: str):
        """保存 Markdown 文本到文件。"""
        path = Path(output_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(md_text, encoding="utf-8")
        print(f"✅ Markdown 已保存到: {path.resolve()}")


# ═══════════════════════════════════════════════════════════════
#  CLI
# ═══════════════════════════════════════════════════════════════


def main():
    parser = argparse.ArgumentParser(
        description="MinerU 文档 → Markdown 转换器（支持 PDF/图片/Office/HTML 等格式）",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用示例:
  # 精准解析 API（需 Token）
  %(prog)s precision-url --url https://example.com/doc.pdf --output ./output/
  %(prog)s precision-batch-url --files '[{"url":"https://..."}]' --output ./output/
  %(prog)s precision-batch-file --files a.pdf b.pdf --output ./output/

  # 配置管理
  %(prog)s config init
  %(prog)s config show
        """,
    )
    parser.add_argument("--config", help="配置文件路径")

    subparsers = parser.add_subparsers(dest="mode", help="可用命令")

    # --- precision-url ---
    pu = subparsers.add_parser("precision-url", help="精准解析 API — URL 提交")
    pu.add_argument("--url", required=True, help="文件 URL")
    pu.add_argument("--output", "-o", help="输出目录（下载并解压 Zip）")
    pu.add_argument(
        "--model",
        default="vlm",
        choices=["pipeline", "vlm", "MinerU-HTML"],
        help="模型版本",
    )
    pu.add_argument("--language", default="ch", help="文档语言")
    pu.add_argument(
        "--no-table", action="store_false", dest="enable_table", help="禁用表格识别"
    )
    pu.add_argument("--ocr", action="store_true", dest="is_ocr", help="启用 OCR")
    pu.add_argument(
        "--no-formula", action="store_false", dest="enable_formula", help="禁用公式识别"
    )
    pu.add_argument("--page-ranges", help="页码范围，如 2,4-6")
    pu.add_argument("--data-id", help="业务数据 ID")
    pu.add_argument(
        "--extra-formats",
        nargs="+",
        choices=["docx", "html", "latex"],
        help="额外导出格式",
    )

    # --- precision-batch-url ---
    pbu = subparsers.add_parser(
        "precision-batch-url", help="精准解析 API — 批量 URL 提交"
    )
    pbu.add_argument(
        "--files", required=True, help='JSON 字符串: [{"url":"...","data_id":"..."}]'
    )
    pbu.add_argument("--output", "-o", help="输出目录")
    pbu.add_argument(
        "--model",
        default="vlm",
        choices=["pipeline", "vlm", "MinerU-HTML"],
        help="模型版本",
    )
    pbu.add_argument("--language", default="ch", help="文档语言")

    # --- precision-batch-file ---
    pbf = subparsers.add_parser(
        "precision-batch-file", help="精准解析 API — 本地文件批量上传"
    )
    pbf.add_argument("--files", "-f", nargs="+", required=True, help="本地文件路径列表")
    pbf.add_argument("--output", "-o", help="输出目录")
    pbf.add_argument(
        "--model",
        default="vlm",
        choices=["pipeline", "vlm", "MinerU-HTML"],
        help="模型版本",
    )
    pbf.add_argument("--language", default="ch", help="文档语言")

    # --- config ---
    config_parser = subparsers.add_parser("config", help="配置管理")
    config_sub = config_parser.add_subparsers(dest="config_action", help="配置操作")
    config_sub.add_parser("init", help="初始化配置文件")
    config_sub.add_parser("show", help="查看当前配置")

    args = parser.parse_args()

    if not args.mode:
        parser.print_help()
        return

    # Config commands
    if args.mode == "config":
        if args.config_action == "init":
            ConfigManager.init_interactive()
        elif args.config_action == "show":
            ConfigManager.show()
        else:
            config_parser.print_help()
        return

    # Initialize converter
    converter = MinerUConverter(args.config)

    try:
        if args.mode == "precision-url":
            result = converter.parse_url_precision(
                url=args.url,
                model_version=args.model,
                language=args.language,
                enable_table=getattr(args, "enable_table", None),
                is_ocr=getattr(args, "is_ocr", None),
                enable_formula=getattr(args, "enable_formula", None),
                page_ranges=getattr(args, "page_ranges", None),
                data_id=getattr(args, "data_id", None),
                extra_formats=getattr(args, "extra_formats", None),
            )
            zip_url = result.get("full_zip_url")
            if zip_url:
                output_dir = args.output or "./output"
                MinerUConverter.download_zip(zip_url, output_dir)
            else:
                print("结果:", json.dumps(result, ensure_ascii=False, indent=2))

        elif args.mode == "precision-batch-url":
            files = json.loads(args.files)
            results = converter.parse_url_batch(
                files=files,
                model_version=args.model,
                language=args.language,
            )
            output_dir = args.output or "./output"
            for r in results:
                zip_url = r.get("full_zip_url")
                if zip_url:
                    file_output = (
                        Path(output_dir) / Path(r.get("file_name", "unk")).stem
                    )
                    MinerUConverter.download_zip(zip_url, str(file_output))
                else:
                    print(f"  {r.get('file_name', '?')}: state={r['state']}")

        elif args.mode == "precision-batch-file":
            results = converter.parse_file_batch(
                file_paths=args.files,
                model_version=args.model,
                language=args.language,
            )
            output_dir = args.output or "./output"
            for r in results:
                zip_url = r.get("full_zip_url")
                if zip_url:
                    file_output = (
                        Path(output_dir) / Path(r.get("file_name", "unk")).stem
                    )
                    MinerUConverter.download_zip(zip_url, str(file_output))
                else:
                    print(f"  {r.get('file_name', '?')}: state={r['state']}")

    except Exception as e:
        print(f"❌ 错误: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
