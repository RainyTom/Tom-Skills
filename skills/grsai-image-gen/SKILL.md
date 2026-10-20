---
name: grsai-image-gen
description: 通过 Grsai 的 nano-banana 或 gpt-image 系列接口生成图片、参考图改图、透明背景素材，并查询异步结果。用于用户指定 Grsai 生图，或当前项目的 PPT、报告、演示页面需要位图插画、封面和场景配图时；精确架构图、流程图和实验图优先使用可编辑矢量或绘图代码。
---

# Grsai 图片生成

为当前 DSH × WPS COMATE 科研协作演示项目制作可复用位图。遵守用户指定的模型、节点、尺寸、参考图和输出目录。调用前查阅 [参数参考](references/api.md)，不要套用 OpenAI `/v1/images/generations` 的请求格式。

## 工作方式

1. 从需求或现有材料确定用途、主体、构图、比例、文字与留白。PPT 背景可用 16:9，这是项目建议而非接口默认值。准确文字、流程节点和实验数值优先在 PPT/代码层叠加。概念配图不能冒充真实产品截图或实验结果。
2. 有参考图时先查看图片，在提示词中说明各图的角色及需保留/修改的内容。`images` 接受 URL 或 base64 字符串，不接受本地路径；本地图片先编码，不要为获取 URL 擅自上传到公共图床。base64 包装要求见参数参考。
3. 用户未指定模型时，可从文档示例 `nano-banana-2`、`1K` 开始；透明背景选择支持 `background` 的 GPT 变体，并说明选择。不要把 Grsai 模型别名视为模型原厂身份或能力的证明。
4. 从项目根目录 `.env` 或环境变量 `GRSAI_API_KEY` 读取密钥，已存在的环境变量优先。缺失时先完成提示词和请求文件，告知配置方法，不要求用户把密钥贴进对话。`GRSAI_BASE_URL` 默认全球节点，可设为国内节点。密钥不得写入请求 JSON、代码、日志或交付物。
5. 用脚本提交，推荐 `replyType: async`，及时保留任务 ID。每张图提交一次；网络超时可能发生在服务已受理之后，不自动重发 POST。已有 ID 时只查询原任务。
6. 对 `running` 任务按需间隔 5–10 秒查询，默认最多等待 10 分钟；这是本 skill 的轮询策略，不是服务 SLA。到时仍未完成则保留 ID，报告“仍在生成”，后续继续查。`failed`/`violation` 停止；未知状态、缺少 ID 或结果时报告异常。
7. 只有 `succeeded` 且 `results[].url` 有效才下载图片。下载结果 URL 时不附带 Grsai Bearer 密钥；使用唯一文件名，不覆盖现有资产。下载后检查格式并查看图片，核对内容、构图、文字、尺寸和透明通道。下载失败只重试下载，不重新生成。

## 调用脚本

需要 Python 3，仅用标准库。下面从项目根目录运行；其他工作目录改用实际 skill 路径。

先创建 UTF-8 `request.json`，例如：

```json
{
  "model": "nano-banana-2",
  "prompt": "科研协作平台技术汇报封面插画：多个智能助手围绕中央协作画板整理论文与实验资料，简洁科技风，绿色与白色，主体位于右侧，左侧留白供后续叠加标题，不包含文字、数字或品牌标志。概念插画。",
  "images": [],
  "aspectRatio": "16:9",
  "imageSize": "1K",
  "replyType": "async"
}
```

```bash
# 本地检查，不需要密钥，不联网。
python .github/skills/grsai-image-gen/scripts/grsai_image.py submit request.json --dry-run

# 配置 GRSAI_API_KEY 后提交；输出文件须尚不存在。
python .github/skills/grsai-image-gen/scripts/grsai_image.py submit request.json --output submit-response.json

# 用真实任务 ID 查询，每次采用新的输出文件名。
python .github/skills/grsai-image-gen/scripts/grsai_image.py result 'TASK_ID' --output result-001.json
```

脚本仅支持 `json`/`async`，不处理文档未定义帧格式的 `stream`。每次只提交或查询一次，不自动轮询、下载或重复计费请求。退出码：0 为已成功或已受理且仍在运行，1 为请求/服务错误，2 为参数错误。以响应 `status` 区分受理与生成完成。

## 项目交付

优先写入用户指定目录，未指定时建议 `汇报材料/图片/<任务名>/`。保留图片、提示词、非敏感参数、任务 ID、响应与来源说明。请求含私有 URL 或 base64 图像时，交付记录用参考图文件名替代原始图像内容，不把原始请求当作公开附件。

报告所选模型、实际完成状态、图片路径及检查结果。与 PPT 工作流衔接时提供独立图片文件；生成图片中的数字不能作为 `reporting_snapshot` 的事实来源。完成生成不代表已发布到 COMATE/WPS。
