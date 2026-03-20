# Code Review & QA Report (V2.0 MVP)

**Review Date:** 2026-03-20

## 1. Backend Code Audit

### Structural Integrity
- ✅ **Pydantic Schemas:** `LLMExtractionResult` schema is well-defined and strictly enforced.
- ✅ **Async SSE:** `EventSourceResponse` properly yields JSON strings and correctly cleans up `tasks_db` upon completion/disconnection.
- ✅ **Feishu Client:** Refactored to support `batch_create`, efficiently circumventing the 100 QPS limit by bundling inserts.

### Edge Case Mitigations
- 🐛 **Markdown Codeblock Truncation (Fixed):** 
  - *Issue:* LLM output wrapped in ` ```json ... ``` ` was parsed using `txt[:-3]`, which fails if there are trailing whitespaces or newlines.
  - *Fix:* Replaced static string slicing with robust regex `re.sub(r"\s*```$", "", txt)`.
- ⚠️ **Timeout Thresholds:** 
  - Jina Reader API `timeout` set to `15.0s`. 
  - OpenAI `timeout` set to `120.0s`. These are appropriate for slow models handling long text.
- ⚠️ **Memory Leak in SSE:** 
  - The `tasks_db` dictionary handles cleanup by popping keys when `status` is `complete` or `error`. However, if the client disconnects *before* the task finishes, the task stays in memory indefinitely.
  - *Gap:* Need a TTL-based eviction mechanism for orphaned tasks in future iterations.

## 2. Frontend Code Audit

### UI & UX
- ✅ **Strict Data Mapping:** Zero raw markdown rendering. All `GoldenSentence` and `CoreArgument` data are mapped explicitly to HTML elements, effectively solving the "Anti-AI Slop" requirement.
- ✅ **Interactivity:** Elements correctly utilize `contenteditable` (via inputs/textareas) allowing users to modify content before triggering `saveToFeishu()`.
- ✅ **Resilience:** Basic URL validation is present.

### Security / Error Handling
- ⚠️ **Error Propagation:** If Feishu returns a `missing_app_or_table` error, the UI gracefully displays the error message without crashing.

## 3. Completeness Gaps (To be addressed in Phase 2)
1. **Feishu Table Relational Mapping:** Currently, all data is serialized as a JSON string into a single "Articles" table to bypass MVP complexity. To fully realize the "Database" potential, we need to map `Quotes` and `Cases` to separate Feishu tables and link them via the `SourceArticle` relationship field.
2. **Orphaned Task Cleanup:** Implement a background cron or Redis TTL to clear out `tasks_db` entries that were abandoned by disconnected clients.

---
**Status:** MVP is robust enough for production testing. No critical blockers.