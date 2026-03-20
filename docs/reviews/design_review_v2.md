# Design Review (V2.0 - 零爹味与沉浸式交互)

**Review Date:** 2026-03-20
**Target Spec:** `OneEditorV2.0_GLOBAL_REWRITE_SPEC.md`

## 1. Anti-AI Slop (防爹味设计)
**Score:** 10/10

**Definition of a 10:** 
- 最终呈现在用户面前的内容中，**绝对没有任何** AI 常用的废话前缀/后缀（例如："好的，这是为您解析的..."、"总之..."、"这告诉我们..."）。
- 不暴露原始的 JSON 结构，也不直接把 AI 生成的 Markdown 甩在页面上（Markdown 极易混入爹味词汇）。

**How to Achieve a 10:**
- **Strict Data Mapping (严格数据映射)**：后端使用 Pydantic 解析出结构化 JSON 后，前端通过解析 JSON 字段，将数据 **强行塞入** 预设好的 UI 卡片（UI Card）中。
- 前端只渲染数据本身，例如：直接渲染一个 `<blockquote>` 标签里面放 `data.golden_sentences[0].text`，而不是让 AI 生成带有引用的 Markdown 文本。
- 这从根本上切断了 AI 在输出中夹带"自我意识"的可能。

## 2. Interactivity (交互性)
**Score:** 10/10

**Definition of a 10:**
- 用户不仅仅是一个"看客"，而是一个"编辑者"。
- 在数据被固化（同步到飞书）之前，用户可以对 AI 提取的内容进行修正和微调，消除"机器替我做决定"的失控感。

**How to Achieve a 10:**
- **Inline Editable Cards (内联可编辑卡片)**：当分析卡片生成并展示在网页上时，所有的核心字段（提取的观点、金句、案例、甚至标签）都应该是 **可编辑的 (contenteditable)**。
- 如果 AI 提取的某句金句多带了半个标点，或者某个案例的总结偏离了用户的预期，用户可以直接在网页卡片上点击修改。
- 只有当用户确认无误（或修改完毕）后，点击"确认并归档飞书"，系统才会将 **用户修正后的最终版本** 发送到飞书后端。

## 3. Visual & UX Details (视觉与体验细节)

**Loading State (等待状态)**
- 由于解析可能长达 20-60 秒，简单的菊花图（Spinner）会引发极大的焦虑。
- **改进方案**：结合工程视角的 SSE 流，实现一个**骨架屏 + 步骤高亮**。例如显示：
  - [x] 正在读取网页原文...
  - [x] Jina Reader 转换 Markdown 成功...
  - [ ] AI 正在深度拆解观点与案例 (这步加入打字机特效或思考光标)...

**Aha Moment (顿悟时刻)**
- 当解析完成，页面上不是平铺的文本，而是像 Notion/飞书画廊一样的 **精美灵感卡片瀑布流**。
- 每张卡片上有清晰的标签（如 💎 金句、📖 案例），并带有轻微的悬浮动效（Hover effects）。

---

## Action Items for Frontend Build
1. [ ] 搭建 Tailwind CSS 基础样式，确保卡片设计具有现代感、呼吸感。
2. [ ] 实现基于 SSE 的多阶段 Loading 动画（不只转圈，要有文字状态）。
3. [ ] 将后端的 JSON 响应严格映射到 React/Vanilla JS 的 DOM 节点上（严禁直接注入 AI 原始文本）。
4. [ ] 为观点、案例、金句的 DOM 节点添加 `contenteditable` 属性，并监听变化以更新内部 State。
5. [ ] 添加一个"确认归档"的悬浮按钮（FAB），收集最终的 State 发送给后端入库飞书。