# OneEditor 项目目录结构调整计划

> **For Claude:** 使用 superpowers:executing-plans 来逐步执行此计划

**Goal:** 借鉴OPC001等成熟项目的最佳实践，将OneEditor项目目录结构规范化

**Architecture:** 采用前后端分离结构，代码与文档分离，测试独立

**Tech Stack:** Python (FastAPI) + HTML/CSS/JS + 飞书多维表格

---

## 当前结构分析

```
OneEditor-main/
├── app.py              # 主应用文件（混杂）
├── config/             # 配置
├── models/             # 数据模型
├── providers/          # LLM提供者
├── services/           # 服务层
├── skills/             # AI技能
├── storage/            # 存储层
├── utils/              # 工具函数
├── web/                # 前端页面
├── adapters/           # 适配器
├── README.md
└── __pycache__/        # Python缓存（应忽略）
```

**问题**：
1. 根目录混杂（app.py应放入backend）
2. 缺少docs/文档目录
3. 缺少tests/测试目录
4. 缺少scripts/脚本目录
5. __pycache__未忽略

---

## 目标结构

```
OneEditor/
├── backend/                    # 后端代码
│   ├── src/
│   │   ├── api/               # API路由
│   │   ├── models/            # 数据模型
│   │   ├── services/          # 业务服务
│   │   ├── skills/            # AI技能
│   │   ├── providers/         # LLM提供者
│   │   ├── storage/           # 存储层
│   │   ├── utils/             # 工具函数
│   │   └── config/            # 配置
│   ├── app.py                 # FastAPI入口
│   ├── main.py                # 启动文件
│   ├── requirements.txt       # 依赖
│   └── tests/                 # 后端测试
├── frontend/                   # 前端代码
│   ├── src/
│   │   ├── pages/            # 页面
│   │   ├── components/       # 组件
│   │   ├── styles/           # 样式
│   │   └── services/         # API服务
│   ├── public/               # 静态资源
│   ├── index.html            # 入口HTML
│   ├── package.json
│   └── vite.config.js        # 构建配置
├── docs/                      # 项目文档
│   ├── plans/                # 开发计划
│   ├── guides/               # 使用指南
│   ├── api/                  # API文档
│   └── architecture/         # 架构文档
├── scripts/                   # 脚本工具
│   ├── setup.sh              # 环境搭建
│   ├── deploy.sh             # 部署脚本
│   └── test.sh               # 测试脚本
├── .gitignore
├── README.md
└── LICENSE
```

---

## 任务清单

### Task 1: 创建目录结构

**Files:**
- Create: `backend/src/__init__.py`
- Create: `backend/tests/__init__.py`
- Create: `frontend/src/__init__.py`
- Create: `docs/plans/.gitkeep`
- Create: `docs/guides/.gitkeep`
- Create: `scripts/.gitkeep`

**Step 1: 创建基础目录**

```bash
mkdir -p backend/src/{api,models,services,skills,providers,storage,utils,config}
mkdir -p backend/tests
mkdir -p frontend/src/{pages,components,styles,services}
mkdir -p frontend/public
mkdir -p docs/{plans,guides,api,architecture}
mkdir -p scripts
```

**Step 2: 创建__init__.py**

```bash
touch backend/src/__init__.py
touch backend/tests/__init__.py
touch frontend/src/__init__.py
```

**Step 3: Commit**

```bash
git add .
git commit -m "chore: create project directory structure"
```

---

### Task 2: 移动后端代码

**Files:**
- Move: `app.py` → `backend/app.py`
- Move: `config/` → `backend/src/config/`
- Move: `models/` → `backend/src/models/`
- Move: `providers/` → `backend/src/providers/`
- Move: `services/` → `backend/src/services/`
- Move: `skills/` → `backend/src/skills/`
- Move: `storage/` → `backend/src/storage/`
- Move: `utils/` → `backend/src/utils/`

**Step 1: 移动文件**

```bash
mv app.py backend/
mv config backend/src/
mv models backend/src/
mv providers backend/src/
mv services backend/src/
mv skills backend/src/
mv storage backend/src/
mv utils backend/src/
```

**Step 2: 更新import路径**
（需要修改各文件的import路径）

**Step 3: Commit**

```bash
git add .
git commit -m "refactor: move backend code to backend/"
```

---

### Task 3: 整理前端代码

**Files:**
- Move: `web/` → `frontend/public/`

**Step 1: 移动文件**

```bash
mv web frontend/public/
```

**Step 2: 创建前端配置**
（根据需要创建package.json, vite.config.js等）

**Step 3: Commit**

```bash
git add .
git commit -m "refactor: move frontend code to frontend/"
```

---

### Task 4: 创建配置文件

**Files:**
- Create: `backend/requirements.txt`
- Create: `frontend/package.json`
- Create: `.gitignore`

**Step 1: 创建requirements.txt**

```bash
pip freeze > backend/requirements.txt
```

**Step 2: 创建.gitignore**

```bash
cat > .gitignore << EOF
__pycache__/
*.pyc
*.pyo
.pytest_cache/
venv/
env/
.env
*.log
node_modules/
dist/
.DS_Store
EOF
```

**Step 3: Commit**

```bash
git add .
git commit -m "chore: add requirements.txt and .gitignore"
```

---

### Task 5: 整理文档

**Files:**
- Move: `README.md` → `docs/`
- Create: `docs/README.md`（项目总览）
- Create: `docs/architecture/系统架构.md`

**Step 1: 移动并更新README**

```bash
mv README.md docs/
```

**Step 2: 创建架构文档**
（从OneEditorV2.0.md提取核心内容）

**Step 3: Commit**

```bash
git add .
git commit -c "docs: organize project documentation"
```

---

## 执行选择

**Plan complete and saved to `docs/plans/2026-03-11-directory-restructuring.md`.**

**两种执行方式：**

1. **当前会话逐步执行** - 我逐个任务执行，你在中间审核
2. **新会话执行** - 开新session并行执行

选哪个？🦞