#!/usr/bin/env python3
"""Submit/query Grsai once; credentials come only from environment variables."""
import argparse
import json
import os
from pathlib import Path
import re
import sys
import urllib.error
import urllib.parse
import urllib.request

NANO = set('nano-banana nano-banana-fast nano-banana-2 nano-banana-2-cl nano-banana-2-2k-cl nano-banana-2-4k-cl nano-banana-2.1 nano-banana-pro nano-banana-pro-vt nano-banana-pro-cl nano-banana-pro-vip nano-banana-pro-4k-vip'.split())
GPT = {
    'gpt-image-2': {'auto'}, 'gpt-image-2.5': {'auto'},
    'gpt-image-2-vip': {'medium'},
    'gpt-image-2.5-flare': {'low', 'medium', 'high'},
    'gpt-image-2.5-sunburst': {'low', 'medium', 'high', 'xhigh', 'max'},
}
ADVANCED = set(GPT) - {'gpt-image-2', 'gpt-image-2.5'}
BASES = {'https://grsaiapi.com', 'https://grsai.dakka.com.cn'}


def load_project_env():
    env_file = Path.cwd() / '.env'
    if not env_file.is_file():
        return
    for line in env_file.read_text(encoding='utf-8').splitlines():
        line = line.strip()
        if not line or line.startswith('#') or '=' not in line:
            continue
        name, value = line.split('=', 1)
        if name.strip() in ('GRSAI_API_KEY', 'GRSAI_BASE_URL'):
            os.environ.setdefault(name.strip(), value.strip().strip('"').strip("'"))


def validate(payload):
    if not isinstance(payload, dict):
        raise ValueError('请求必须是 JSON 对象')
    model = payload.get('model')
    if not isinstance(model, str) or model not in NANO | set(GPT):
        raise ValueError('未知模型；请核对 references/api.md 和最新文档')
    if not isinstance(payload.get('prompt'), str) or not payload['prompt'].strip():
        raise ValueError('prompt 必须是非空字符串')
    allowed = {'model', 'prompt', 'images', 'aspectRatio', 'replyType'}
    allowed |= {'imageSize'} if model in NANO else {'quality', 'background', 'mask'}
    if set(payload) - allowed:
        raise ValueError('存在该模型不支持的字段：' + ', '.join(sorted(set(payload) - allowed)))
    images = payload.get('images', [])
    if not isinstance(images, list) or any(not isinstance(i, str) or not i for i in images):
        raise ValueError('images 必须是非空字符串组成的数组，或空数组')
    payload.setdefault('replyType', 'async')
    if payload['replyType'] not in ('async', 'json'):
        raise ValueError('脚本仅支持 async/json，不支持 stream')
    for field in ('aspectRatio', 'imageSize', 'quality', 'background', 'mask'):
        if field in payload and (not isinstance(payload[field], str) or not payload[field]):
            raise ValueError(field + ' 必须是非空字符串')
    ratio = payload.get('aspectRatio')
    if model in NANO:
        ratios = set('auto 1:1 16:9 9:16 4:3 3:4 3:2 2:3 5:4 4:5 21:9'.split())
        if model.startswith('nano-banana-2'):
            ratios.update(('1:4', '4:1', '1:8', '8:1'))
        if ratio is not None and ratio not in ratios:
            raise ValueError('该 nano-banana 模型不支持此比例')
        if 'imageSize' in payload and payload['imageSize'] not in ('1K', '2K', '4K'):
            raise ValueError('imageSize 只能是 1K/2K/4K')
    else:
        if 'quality' in payload and payload['quality'] not in GPT[model]:
            raise ValueError('quality 与模型不匹配')
        if 'background' in payload and (model not in ADVANCED or payload['background'] != 'transparent'):
            raise ValueError('此模型或 background 值不支持透明背景')
        if ratio is not None:
            pixels = re.fullmatch(r'([1-9][0-9]*)x([1-9][0-9]*)', ratio)
            if model in ADVANCED and not pixels:
                raise ValueError('高级 GPT 变体请使用明确像素值，如 2048x1152')
            if model not in ADVANCED and not (pixels or ratio == 'auto' or re.fullmatch(r'[1-9][0-9]*:[1-9][0-9]*', ratio)):
                raise ValueError('aspectRatio 应为比例或像素值')
            if model == 'gpt-image-2-vip' and pixels:
                w, h = map(int, pixels.groups())
                if max(w, h) > 3840 or w % 16 or h % 16 or max(w, h) > 3 * min(w, h) or not 655360 <= w * h <= 8294400:
                    raise ValueError('像素值不满足 vip 自定义尺寸约束')
    return payload


class NoRedirect(urllib.request.HTTPRedirectHandler):
    # Never forward an Authorization header to a redirected host.
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def main():
    load_project_env()
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('submit', 'result'))
    parser.add_argument('input', help='提交用 UTF-8 JSON 文件；查询用任务 ID')
    parser.add_argument('--output', type=Path, help='新响应文件，不覆盖已有文件')
    parser.add_argument('--dry-run', action='store_true', help='只校验，不联网')
    parser.add_argument('--timeout', type=float, default=60)
    args = parser.parse_args()
    try:
        if not 0 < args.timeout <= 600:
            raise ValueError('timeout 须大于 0 且不超过 600 秒')
        base = os.environ.get('GRSAI_BASE_URL', 'https://grsaiapi.com').rstrip('/')
        if base not in BASES:
            raise ValueError('GRSAI_BASE_URL 必须为文档列出的全球或国内 HTTPS 节点')
        payload = validate(json.loads(Path(args.input).read_text(encoding='utf-8'))) if args.action == 'submit' else None
        if args.action == 'result' and not args.input.strip():
            raise ValueError('任务 ID 不能为空')
        if args.dry_run:
            print(json.dumps({'validated': True, 'action': args.action, 'base_url': base, 'model': payload['model'] if payload else None}, ensure_ascii=False))
            return 0
        key = os.environ.get('GRSAI_API_KEY', '').strip()
        if not key:
            raise ValueError('请在环境中设置 GRSAI_API_KEY，不要将密钥写入文件或对话')
        if not args.output:
            raise ValueError('联网调用必须提供 --output 以保存任务 ID 和响应')
        # Reserve output before submitting so a bad output path cannot lose a task ID.
        output = args.output.open('x', encoding='utf-8')
    except (OSError, ValueError) as exc:
        parser.error(str(exc))

    with output:
        endpoint = '/v1/api/generate' if payload else '/v1/api/result?' + urllib.parse.urlencode({'id': args.input})
        data = json.dumps(payload, ensure_ascii=False).encode('utf-8') if payload else None
        request = urllib.request.Request(base + endpoint, data=data, headers={
            'Authorization': 'Bearer ' + key, 'Content-Type': 'application/json',
        }, method='POST' if payload else 'GET')
        try:
            opener = urllib.request.build_opener(NoRedirect())
            try:
                with opener.open(request, timeout=args.timeout) as response:
                    status_code, raw = response.status, response.read()
            except urllib.error.HTTPError as exc:
                status_code, raw = exc.code, exc.read()
            # Redact credentials even if an upstream error echoes the header.
            decoded = raw.decode('utf-8', errors='replace').replace(key, '[REDACTED]')
            try:
                body = json.loads(decoded)
            except ValueError:
                body = {'error': '服务返回非 JSON 内容', 'body': decoded}
            record = {'http_status': status_code, 'response': body}
            ok = 200 <= status_code < 300 and isinstance(body, dict) and body.get('status') in ('running', 'succeeded') and bool(body.get('id'))
            if ok and body['status'] == 'succeeded':
                results = body.get('results')
                ok = isinstance(results, list) and bool(results) and all(isinstance(item, dict) and isinstance(item.get('url'), str) and item['url'].startswith(('https://', 'http://')) for item in results)
        except (OSError, ValueError) as exc:
            record = {'error': str(exc).replace(key, '[REDACTED]'), 'action': args.action,
                      'note': '未自动重试；提交结果可能未知，勿盲目重发。' if payload else '可稍后使用同一任务 ID 重新查询。'}
            if not payload:
                record['id'] = args.input
            ok = False
        output.write(json.dumps(record, ensure_ascii=False, indent=2) + '\n')
        output.flush()
    print(json.dumps(record, ensure_ascii=False, indent=2))
    return 0 if ok else 1


if __name__ == '__main__':
    sys.exit(main())
