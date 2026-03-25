---
name: testcase-generator
description: 测试用例生成器 - 同时支持“计划驱动”和“文档驱动”。计划驱动：基于业务流程与用户场景分析、等价类划分、边界值分析、因果图分析等理论，按测试点(POINT)分批生成高质量测试用例，输出为 Markdown 与 Excel。文档驱动：当用户粘贴 PRD/需求/接口文档时，默认运用通用测试设计策略（正向/反向/边界/等价/状态/场景），并可结合 references 与 assets 模板组织输出。当用户执行 /testcase-gen 命令或请求生成测试用例时触发。
allowed-tools: Read, Write, Bash, Glob
---

# 测试用例生成器(testcase-generator)

## 1. 目标

根据测试点生成结构化测试用例，覆盖核心业务、正向、反向、边界、异常等场景。

## 2. 输入输出

- **输入**：`test-case/plan.md`、`clarified-requirements/index.md`、`CLAUDE.md`
- **输出**：`test-case/{ITEM}/{POINT}.md`、`test-case/all_cases_测试用例.xlsx`、`test-case/all_cases_思维导图.xmind`

## 3. 核心原则

1. **策略指导**：提供判断标准，而非强制数量
2. **场景驱动**：基于实际场景复杂度生成用例
3. **数据具体**：测试数据必须具体不用占位符
4. **可验证性**：预期结果必须明确可验证执行

---

### 工作流

当用户提供 PRD、需求说明或接口文档文本，并请求“根据文档生成测试用例”时，按如下流程执行：

1. 识别文档类型与结构
   - 功能/业务需求、接口说明、性能/SLA、安全要求或其组合
   - 提取：模块/接口清单、约束（必填/可选、长度/格式/范围）、状态与角色、错误码、性能指标等

2. 默认测试设计策略（始终启用）
   - 正向用例（正常路径/happy path）
   - 反向/异常用例（非法输入、越权、错误码、不产生副作用）
   - 边界值（最小/最大/临界/空/极值）
   - 等价类（有效/无效代表值，必要时与边界结合）
   - 状态与流程（合法迁移、非法操作、回退/中断、角色切换）
   - 场景法/端到端（典型用户目标串联多模块）

3. references 与模板协同
   - **`references/theory.md`** - 测试理论详解（等价类、边界值、因果图、场景法）
   - **`references/format-standard.md`** - 格式规范详细说明
   - **`references/prompts.md`** - 提示词模板（文档驱动模式）

4. 输出要求
   - 严格遵循本技能“用例格式规范/文本协议”与“测试类型枚举（12种）”
   - 步骤与预期结果编号从 1 连续递增，数量一致；字段间不留空行
   - 预期结果需可验证，错误场景对应明确错误码/提示/状态不变

5. 质量自检
   - 每个核心功能/接口至少 1 条正向用例
   - 关键输入约束具备异常/反向覆盖
   - 所有范围/长度/数量限制具备边界用例
   - 如涉及状态机/流程，覆盖合法迁移与非法操作
   - 测试类型与优先级明确，便于导出与后续执行

---

## 4. 检验流程

### Step 1: 每个测试项生成完毕后

调用校验脚本检查格式：

**校验项**:
- Schema格式
- 必填字段(优先级、测试类型、测试步骤、预期结果)
- 测试类型枚举(12种)
- 步骤编号连续性
- 步骤与预期结果数量一致性
- 等价类覆盖检查(`--check-equivalence`)
- 边界值覆盖检查(`--check-boundary`)
- 重复检测(`--check-duplicates`)

#### validate.py(一定执行该技能scripts目录下的脚本)

```bash
# 单文件校验
python .agent/skills/testcase-generator/scripts/validate.py --single "test-case/{模块}/{测试点}.md"

# 全局校验
python .agent/skills/testcase-generator/scripts/validate.py "test-case/"

# 仅重复检测
python .agent/skills/testcase-generator/scripts/validate.py "test-case/" --duplicates-only
```

脚本会输出日志，指出格式问题（如优先级错误、字段缺失等）。AI 分析日志，决定是否需要修改。


### Step 2: 全部生成完毕后

再次调用校验脚本进行整体检查：

```bash
python .agent/skills/testcase-generator/scripts/validate.py "test-case/" --check-duplicates
```

脚本会检查重复用例、格式一致性等。脚本只提供日志，不直接修改文件。AI 分析日志，决定是否需要调整。

### Step 3: 生成质量报告

- 统计用例数量（按 ITEM、按优先级）
- 统计等价类覆盖率
- 统计边界值覆盖率
- 列出重复用例（如果有）
- - 如果有重复用例，就直接剔除
- 列出描述不清晰、不确定的测试用例（如果有）
- - 如果有不清晰、不确定的测试用例需要标记为待定

### Step 4:  导出文件(to_excel.py、to_xmind.py)(一定执行该技能scripts目录下的脚本)

```bash
# 从目录导出
python .agent/skills/testcase-generator/scripts/to_excel.py "test-case/" -o "test-case/export.xlsx"

# 从单个文件导出
python .agent/skills/testcase-generator/scripts/to_excel.py "test-case/{模块}/{测试点}.md" -o "output.xlsx"

# 导出xmind格式的思维导图
python  .agent/skills/testcase-generator/scripts/testcase_to_xmind.py  "test-case/"
```

---

## 5. 检查清单

### 生成前检查

- [ ] 已读取 `test-case/plan.md`
- [ ] 已读取 `clarified-requirements/index.md`
- [ ] 已读取 `CLAUDE.md` 业务背景
- [ ] 理解测试项(ITEM)和测试点(POINT)的层级关系
- [ ] 理解需求文档或测试计划
- [ ] 识别所有功能模块
- [ ] 明确输入约束和业务规则

### 每个POINT生成时检查

- [ ] 每个 POINT 都已生成用例文件
- [ ] 用例数量合理（基于场景复杂度）
- [ ] 所有用例都有优先级（P0-P3）
- [ ] 所有用例都有测试类型（12种之一）
- [ ] 测试数据具体（无占位符）
- [ ] 预期结果可验证（无模糊描述）
- [ ] 测试步骤与预期结果数量一致
- [ ] 用例标题可以不用"验证"开头，但是必须要自然语言描述清楚用例的目的

### 治理阶段检查

- [ ] 执行了全局校验脚本（已通过 validate.py 检查）
- [ ] 检查了重复用例（已通过 validate.py  --check-duplicates 检查）
- [ ] 格式符合规范（已通过 validate.py 检查）
- [ ] 已生成质量报告
- [ ] Excel导出成功
- [ ] Xmind导出成功

---

## 6. 异常处理

| 错误 | 处理方式 |
|------|----------|
| 单文件校验失败 | 重试3次，仍失败则跳过并记录 |
| 用例数过多(>15) | 提示检查是否有冗余等价类 |
| 缺少边界用例 | 警告并建议补充 |
| 缺少无效等价类 | 警告并建议补充异常场景 |
| 步骤编号不连续 | 报错并要求修正 |
| 测试类型不在枚举 | 报错并要求修正 |
| 步骤与预期数量不一致 | 报错并要求修正 |
| 导出失败 | 检查openpyxl依赖 |

---

## 7. 停止点

✅ **用例生成完成**

**产物**:
- `test-case/{ITEM}/{POINT}.md` - 各测试点的用例文件
- `test-case/all_cases.md` - 所有用例汇总
- `test-case/all_cases_测试用例.xlsx` - Excel格式
- `test-case/all_cases_思维导图.xmind` - Xmind格式

**质量保证**:
- 核心功能场景化覆盖所有业务场景
- 基于等价类理论生成
- 边界值全覆盖
- 用例数量合理（基于场景复杂度）
- 因果图分析法

**统计示例**:
```
📊 生成统计:
  - 测试项: 8个
  - 测试点: 20个
  - 测试用例: 75个

  覆盖率:
  - 有效等价类: 100% (每POINT至少1个)
  - 无效等价类: 80% (主要异常全覆盖)
  - 边界值: 90% (所有范围型输入)

  用例分布:
  - P0(核心正向): 27个(35%)
  - P1(基本正向): 15个(20%)
  - P2(核心异常): 18个(25%)
  - P3(边界条件/低频场景): 15个(20%)
```

**下一步**:
- 人工审核测试用例，根据业务理解调整用例
- 导出为 Excel 格式（必选）
- 导出为 Xmind 格式（必选）
