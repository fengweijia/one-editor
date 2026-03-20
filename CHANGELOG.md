# Changelog

## [0.1.0.0] - 2026-03-20

### Added
- 通用抓取器 (`universal_fetcher.py`) - 4种方案自动切换（Jina Reader → URLtoMarkdown → 基础HTML → Playwright）
- 飞书自动创建表格 API (`/feishu/init-tables`)
- 完整流程 API (`/extract/full`, `/extract/save`)
- 前端可编辑功能

### Fixed
- `/ingest/url-universal` NameError: fetch_with_fallback not defined
- 异步改造支持15用户并发

---

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).