# Grsai 接口参数参考

核对日期：2026-10-13。来源：[nano-banana 接口](https://qmy27nhsd9.apifox.cn/452392911e0)、[gpt-image 接口](https://qmy27nhsd9.apifox.cn/452409160e0)，以及它们链接的 [异步结果查询接口](https://qmy27nhsd9.apifox.cn/452409577e0)。页面表格加载不全时，访问相同地址加 `.md` 获取 OpenAPI 文本；入口为站点 `/llms.txt`。服务更新时重新核对。

## 公共约定

- 全球节点 `https://grsaiapi.com`；国内节点 `https://grsai.dakka.com.cn`。
- 提交 `POST /v1/api/generate`，JSON 请求体。
- 查询 `GET /v1/api/result?id=<任务ID>`，ID 要 URL 编码，使用提交时的同一节点。
- 鉴权 `Authorization: Bearer <APIKEY>`；提交使用 `Content-Type: application/json`。文档把鉴权标成非必填，实际仍携带密钥，不假定匿名可用。密钥管理入口：`https://grsai.ai/zh/dashboard/api-keys`。
- `base_url` 是节点占位符，不是额外路径或请求体字段。不要复制页面自动生成的缺失主机名的 `https://v1/api/generate`。
- 必填 `model`、`prompt`。可选 `images` 为字符串数组（URL/base64），无参考图可省略或传 `[]`。
- `replyType`：`json`、`stream`、`async`。脚本默认 `async`，接口默认值未说明。文档未定义 stream 事件结构，不能假定兼容 OpenAI SSE。
- base64 是否要求 `data:image/...;base64,` 前缀、参考图数量/体积上限均未明确。直接编码为 base64 字符串符合字段描述，但包装兼容性需实测；不要宣称 data URL 已验证。

## nano-banana

模型别名：

```text
nano-banana
nano-banana-fast
nano-banana-2
nano-banana-2-cl
nano-banana-2-2k-cl
nano-banana-2-4k-cl
nano-banana-2.1
nano-banana-pro
nano-banana-pro-vt
nano-banana-pro-cl
nano-banana-pro-vip
nano-banana-pro-4k-vip
```

| 字段 | 可用值／约束 |
| --- | --- |
| `aspectRatio` | `auto`、`1:1`、`16:9`、`9:16`、`4:3`、`3:4`、`3:2`、`2:3`、`5:4`、`4:5`、`21:9` |
| 扩展比例 | nano-banana-2 系列额外支持 `1:4`、`4:1`、`1:8`、`8:1`；文档未逐个界定子型号，不外推给其他系列 |
| `imageSize` | `1K`、`2K`、`4K`；文档未给出完整的型号×尺寸支持矩阵 |

此接口未列出 `quality`、`background`、`mask`，不要加入这些字段。

## gpt-image

这些名称是 Grsai 接口模型标识。

| 模型 | `aspectRatio` | `quality` | `background` |
| --- | --- | --- | --- |
| `gpt-image-2` | 比例或 1K 像素值 | `auto` | 未支持 |
| `gpt-image-2.5` | 比例或 1K 像素值 | `auto` | 未支持 |
| `gpt-image-2-vip` | 1–4K 像素值，不传比例字符串 | `medium` | `transparent` |
| `gpt-image-2.5-flare` | 1–4K 像素值，不传比例字符串 | `low`、`medium`、`high` | `transparent` |
| `gpt-image-2.5-sunburst` | 1–4K 像素值，不传比例字符串 | `low`、`medium`、`high`、`xhigh`、`max` | `transparent` |

GPT 系列不用 `imageSize`。透明背景只在需要时传 `"background": "transparent"`，不要发 `opaque`。文档还列有 `mask` 字符串，例子为 HTTPS PNG URL，但未说明遮罩黑白/透明语义、尺寸匹配和模型支持矩阵；精确局部编辑前确认这些限制，不自行假定。

常用像素选项（vip/flare/sunburst）：

| 比例 | 1K | 2K | 4K |
| --- | --- | --- | --- |
| 1:1 | 1024x1024 | 2048x2048 | 2880x2880 |
| 16:9 | 1280x720 | 2048x1152 | 3840x2160 |
| 9:16 | 720x1280 | 1152x2048 | 2160x3840 |
| 4:3 | 1152x864 | 2304x1728 | 3264x2448 |
| 3:4 | 864x1152 | 1728x2304 | 2448x3264 |

自定义像素约束明确标注“仅限 vip 模型”：最大边 ≤3840；两边均为 16 的倍数；长短边比 ≤3；总像素 655360–8294400。不要无依据推广到所有模型。高级型号列表也出现 `auto`，但同段又强调像素值；为减少歧义，显式发送上表像素值。

透明素材示例：

```json
{
  "model": "gpt-image-2-vip",
  "prompt": "绿色科研助手吉祥物，单个主体居中，全身可见，透明背景，无文字",
  "aspectRatio": "1024x1024",
  "quality": "medium",
  "background": "transparent",
  "replyType": "async"
}
```

## 响应与恢复

提交与查询均返回对象，关注 `id`、`status`、可选 `progress`（0–100）、`results`（含 `url` 的数组）和 `error`。

| `status` | 处理 |
| --- | --- |
| `running` | 仅表示进行中；保留 ID 后查询 |
| `succeeded` | 检查结果 URL，下载并验图 |
| `failed` | 保留 ID 与错误，停止；不要静默切模型重提 |
| `violation` | 停止，报告服务拒绝；不要自动改写提示词绕过 |

HTTP 200 不等于成功出图，HTTP 400 也可能带任务 ID 和错误对象。连接错误或 POST 超时无法证明任务未创建，不要盲目重发。查询连接错误可稍后用同一 ID 继续查；服务未提供的状态、计费方式、幂等性和 URL 有效期不作推断。
