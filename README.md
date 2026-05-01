# 🧪 Testing Skills Collection

AI Agent 测试技能集合，面向 iFlow CLI，覆盖软件测试全生命周期——从需求分析到测试执行，共 **11 个专业技能**。

## ✨ 技能一览

| 技能 | 用途 | 关键命令 |
|------|------|----------|
| **requirements-analyzer** | 从 Excel/PDF/PNG/Word/TXT 提取需求 | — |
| **requirements-analysis** | 多轮对话式需求分析，EPIC 分解与优先级排序 | — |
| **analyze-requirements** | 需求分析全流程编排（自动调度 Agent） | — |
| **testcase-planner** | 需求→测试规划（ITEM/POINT 层级拆解） | `parse_plan.py` |
| **testcase-generator** | 测试点→结构化测试用例（Markdown/Excel/XMind） | `validate.py`, `to_excel.py`, `testcase_to_xmind.py` |
| **doc-based-testcase-generator** | 基于 PRD/接口文档直接生成测试用例 | — |
| **test-effort-estimator** | 测试工作量评估与 Excel 报告 | `generate_excel.py` |
| **webapp-testing** | Playwright 驱动的 Web 应用测试 | `with_server.py` |
| **agent-browser** | 浏览器自动化 CLI（导航/填表/截图/数据提取） | `npx agent-browser` |
| **lanhu-design** | 蓝湖设计稿与 Axure 原型分析 | MCP Server |
| **skill-creator** | 创建、评估与迭代优化技能 | `run_eval.py`, `quick_validate.py` |

## 🔄 完整工作流

```
需求文档 ──→ 需求分析 ──→ 测试规划 ──→ 用例生成 ──→ 测试执行 ──→ 工作量评估
              │              │              │              │
   requirements-    testcase-     testcase-     webapp-     test-effort-
   analyzer/        planner       generator     testing     estimator
   analysis/
```

## 🚀 快速开始

### 环境要求

- Python 3.10+
- Node.js（agent-browser 需要）

### 安装依赖

```bash
pip install pandas openpyxl python-docx playwright
playwright install chromium
```

### 验证安装

```bash
python -c "import pandas, openpyxl, docx, playwright; print('All dependencies OK')"
```

## 📖 使用指南

### 1. 需求分析

从各类文档中提取结构化需求：

- **requirements-analyzer**：支持 Excel、PNG、PDF、Word、TXT 格式，输出功能需求、非功能需求、业务规则、依赖关系图
- **requirements-analysis**：对话式需求细化，支持 EPIC→需求→用户故事分解，MoSCoW/RICE/Kano 优先级排序
- **analyze-requirements**：全流程编排，自动判断复杂度并调度 Agent

### 2. 测试规划

将需求拆解为测试项（ITEM）和测试点（POINT）：

```bash
python testcase-planner/scripts/parse_plan.py --help
```

### 3. 测试用例生成

基于测试点生成结构化用例，支持计划驱动和文档驱动两种模式：

```bash
# 验证单条用例格式
python testcase-generator/scripts/validate.py --single "test-case/ITEM/POINT.md"

# 批量验证
python testcase-generator/scripts/validate.py "test-case/"

# 重复检查
python testcase-generator/scripts/validate.py "test-case/" --check-duplicates

# 导出为 Excel
python testcase-generator/scripts/to_excel.py "test-case/" -o "export.xlsx"

# 导出为 XMind 思维导图
python testcase-generator/scripts/testcase_to_xmind.py "test-case/"
```

#### 测试用例格式（Text Protocol v0.2）

```markdown
## [P0] 用例标题描述
[测试类型] 功能
[前置条件] 用户已登录；账号未锁定
[测试步骤] 1. 打开登录页面。2. 输入用户名test_user。3. 点击登录按钮。
[预期结果] 1. 页面跳转到首页。2. 显示用户信息。
```

**优先级**：P0（核心正向）> P1（基本正向）> P2（核心异常）> P3（边界/低频）

**测试类型（12 种）**：功能、兼容性、易用性、性能、稳定性、安全性、可靠性、效果（AI类）、效果（硬件器件类）、可维护性、可移植性、埋点

### 4. Web 应用测试

使用 Playwright 进行自动化测试：

```bash
# 单服务器模式
python webapp-testing/scripts/with_server.py --server "npm run dev" --port 5173 -- python test.py

# 多服务器模式（后端 + 前端）
python webapp-testing/scripts/with_server.py \
  --server "cd backend && python server.py" --port 3000 \
  --server "cd frontend && npm run dev" --port 5173 \
  -- python test.py
```

### 5. 测试工作量评估

基于需求分析测试工作量并生成 Excel 报告：

```bash
python test-effort-estimator/scripts/generate_excel.py
```

### 6. 技能评估与创建

评估和迭代优化技能：

```bash
# 运行评估
python skill-creator/scripts/run_eval.py

# 快速验证
python skill-creator/scripts/quick_validate.py

# 打包技能
python -m skill-creator.scripts.package_skill <path/to/skill-folder>
```

## 🏗️ 项目结构

```
testing_skills/
├── agent-browser/              # 浏览器自动化
│   ├── SKILL.md
│   ├── references/             # 认证、命令、性能分析等参考文档
│   └── templates/              # 认证会话、表单自动化等模板
├── analyze-requirements/       # 需求分析全流程编排
│   └── SKILL.md
├── doc-based-testcase-generator/  # 文档驱动用例生成
│   └── SKILL.md
├── lanhu-design/               # 蓝湖设计稿分析
│   └── SKILL.md
├── requirements-analysis/      # 对话式需求分析
│   ├── SKILL.md
│   └── references/             # EPIC模板、优先级方法、用户故事模板
├── requirements-analyzer/      # 文档需求提取
│   ├── SKILL.md
│   ├── evals/                  # 评估配置
│   └── references/             # 提示词、示例、格式标准
├── skill-creator/              # 技能创建与评估
│   ├── SKILL.md
│   ├── agents/                 # 分析器、比较器、评分器
│   ├── eval-viewer/            # 评估结果可视化
│   └── scripts/                # 评估、打包、报告脚本
├── test-effort-estimator/      # 测试工作量评估
│   ├── SKILL.md
│   └── scripts/                # Excel导出、验证脚本
├── testcase-generator/         # 测试用例生成
│   ├── SKILL.md
│   ├── references/             # 格式标准、提示词、理论
│   └── scripts/                # 验证、Excel导出、XMind导出
├── testcase-planner/           # 测试规划
│   ├── SKILL.md
│   └── scripts/                # 规划解析脚本
├── webapp-testing/             # Web应用测试
│   ├── SKILL.md
│   ├── examples/               # 控制台日志、元素发现等示例
│   └── scripts/                # 服务器生命周期管理
├── AGENTS.md                   # Agent 指南
└── CLAUDE.md                   # Claude Code 指南
```

### 技能内部结构

每个技能遵循统一结构：

```
skill-name/
├── SKILL.md           # 必需：技能定义（含 YAML frontmatter）
├── references/        # 可选：按需加载的参考文档
├── scripts/           # 可选：可执行 Python 脚本
├── templates/         # 可选：模板文件
├── assets/            # 可选：资源文件
└── examples/          # 可选：示例代码
```

### 三级加载机制

技能采用渐进式上下文管理：

1. **元数据**（name + description）— 始终在上下文中（~100 词）
2. **SKILL.md 正文** — 技能触发时加载（理想 <500 行）
3. **捆绑资源** — 按需加载（references/、scripts/）

## 🔧 环境变量

| 变量 | 用途 | 所属技能 |
|------|------|----------|
| `LANHU_COOKIE` | 蓝湖平台认证 Cookie | lanhu-design |
| `AGENT_BROWSER_ENCRYPTION_KEY` | 认证保险库加密密钥 | agent-browser |
| `AGENT_BROWSER_HEADED` | 启用可视化浏览器模式 | agent-browser |
| `AGENT_BROWSER_DEFAULT_TIMEOUT` | 默认超时时间 | agent-browser |

## 🛠️ 技术栈

- **语言**：Python 3.10+
- **核心库**：pandas（数据处理）、openpyxl（Excel I/O）、python-docx（Word 文档）、Playwright（浏览器自动化）
- **浏览器**：Chromium（通过 Playwright）
- **CLI 工具**：agent-browser（Node.js）

## 📝 代码规范

- Python 遵循 PEP8，4 空格缩进，单行最大 120 字符
- 函数/变量 `snake_case`，类 `PascalCase`，常量 `UPPER_SNAKE_CASE`
- 使用类型注解
- 异常捕获指定具体类型，不使用裸 `except`
- 导入顺序：标准库 → 第三方库 → 本地模块

## 📄 License

本项目中的 `skill-creator` 和 `webapp-testing` 模块包含各自的 LICENSE 文件，请参阅对应目录。
