# Engineering Review (V2.0 - 飞书 Serverless DB 架构)

**Review Date:** 2026-03-20
**Target Spec:** `OneEditorV2.0_GLOBAL_REWRITE_SPEC.md`

## 1. Architecture & Flow Assessment
**Status:** ✅ APPROVED WITH ADJUSTMENTS

**Analysis:**
- 砍掉 SQLite 和 ChromaDB 是一个非常务实的决定。飞书 Bitable 的 API 足够支持 MVP 的 CRUD 操作。
- **瓶颈预警 (Bottleneck Warning):** LLM 解析（尤其是长文章）可能需要 20-60 秒。如果使用纯同步的 HTTP 请求，极易导致前端超时或 Nginx/网关切断连接。
- **解决方案 (Resolution):** 采用 **FastAPI BackgroundTasks + SSE (Server-Sent Events)**。
  - 用户提交 URL 后，后端立即返回一个 `task_id`。
  - 前端通过 `EventSource` 连接 `/api/tasks/{task_id}/stream`，实时接收进度（"抓取中..." -> "解析中..." -> "写入飞书中..." -> 最终结果）。

## 2. Data Models (Feishu Bitable Schema)
**Status:** ⚠️ REQUIRES STRICT SCHEMA DEFINITION

**Analysis:**
- 飞书多维表格作为关系型数据库，必须在代码中维护严格的 Field ID 映射。
- 5 张表的关联关系需要明确：

**Proposed Bitable Schema:**
1. **文章库 (Articles)**
   - `ArticleID` (文本, 主键)
   - `Title` (文本)
   - `URL` (超链接)
   - `QualityScore` (数字)
   - `Tags` (多选)
   - `RawMarkdown` (多行文本)
2. **观点库 (Arguments)**
   - `ArgumentID` (文本, 主键)
   - `Point` (文本)
   - `Evidence` (多行文本)
   - `SourceArticle` (单向关联 -> Articles)
3. **案例库 (Cases)**
   - `CaseID` (文本, 主键)
   - `Summary` (文本)
   - `Details` (多行文本)
   - `UsableAngle` (文本)
   - `SourceArticle` (单向关联 -> Articles)
4. **金句库 (Quotes)**
   - `QuoteID` (文本, 主键)
   - `Text` (多行文本)
   - `Context` (多行文本)
   - `SourceArticle` (单向关联 -> Articles)

## 3. Rate Limits & Bulk Operations
**Status:** ⚠️ MITIGATION REQUIRED

**Analysis:**
- 飞书 Bitable API 有严格的频率限制（通常是 100 QPS）。
- 一篇文章可能拆解出 5 个观点、3 个案例、5 条金句。如果逐条 Insert，单篇文章就会消耗 14 次 API 调用。
- **解决方案 (Resolution):** 必须在后端实现 **Batch Insert（批量插入）**。飞书 API 支持一次请求插入多条记录（最多 500 条）。后端在解析完一篇文章后，应该将属于同一张表的数据打包，发起一次批量写入请求。

## 4. LLM Extraction Reliability
**Status:** ✅ APPROVED (Pydantic Validation)

**Analysis:**
- 让 LLM 同时输出"结构化数据"和"非结构化长文本"时，最容易出现 JSON 格式错误或截断。
- **解决方案 (Resolution):** 
  - 必须使用 **Pydantic + `response_format` (或 Structured Outputs)** 来强制 LLM 返回符合 Schema 的 JSON。
  - 必须加入异常重试机制（如果 JSON 解析失败，附带错误信息让 LLM 重新生成）。

## 5. Security & Environment
**Status:** ✅ APPROVED
- 飞书 App ID 和 App Secret 必须严格存放在 `.env` 中，绝不能硬编码。
- 考虑到这是一个单用户/小团队工具，MVP 阶段可以通过在 `.env` 中配置一个 `ACCESS_TOKEN` 来做简单的 API 鉴权，防止接口被恶意调用。

---

## Action Items for Build Phase
1. [ ] 初始化 FastAPI 项目，配置 Pydantic V2 schemas。
2. [ ] 实现 `JinaReaderService` 用于网页转 Markdown。
3. [ ] 实现 `LLMExtractionService`，使用 Pydantic 强制约束输出格式。
4. [ ] 封装 `FeishuBitableClient`，重点实现 Batch Insert 和关系绑定。
5. [ ] 实现基于 SSE 的任务进度反馈 API。
6. [ ] 开发前端 Vanilla JS + Tailwind 页面，对接 SSE 流。
