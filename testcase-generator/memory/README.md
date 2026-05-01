# 经验记录模板

## 经验记录格式 (episodic)

每次质量评审后自动记录经验到 `memory/episodic/YYYY-MM-DD-{需求}.json`：

```json
{
  "id": "ep-2026-04-09-001",
  "timestamp": "2026-04-09T10:30:00Z",
  "skill": "testcase-generator",
  "requirements": "用户登录功能",
  "function_modules": ["用户管理", "账号登录"],
  "test_points": ["账号密码登录", "手机验证码登录"],
  "test_cases_count": 18,
  "outcome": "合格|不合格",
  "issues": [
    {
      "type": "数据占位符",
      "description": "使用了 {username} 占位符",
      "resolution": "替换为具体账号 test_user"
    },
    {
      "type": "预期模糊", 
      "description": "使用了'功能正常'描述",
      "resolution": "改为具体UI变化描述"
    }
  ],
  "patterns_extracted": [
    {
      "name": "数据占位符问题",
      "confidence": 0.9,
      "target": "更新 semantic-patterns.json"
    }
  ],
  "lessons_learned": [
    "需求中未明确验证码有效期时，应标记为待确认点"
  ]
}
```

## 模式提取规则

| 条件 | 模式级别 | 操作 |
|------|----------|------|
| 同一类问题出现3+次 | critical | 添加到引导错误清单 |
| 解决方案有效 | best_practice | 添加到最佳实践 |
| 用户评分>=7 | strength | 强化此方法 |
| 用户评分<=4 | weakness | 添加到避免事项 |

## 自我进化流程

```
用例生成 → 质量评审 → 记录经验 → 提取模式 → 更新知识库
                                    ↓
                            semantic-patterns.json
```

## 使用方式

1. 质量评审不通过时，自动记录经验到 episodic
2. 定期（每次会话结束）提取模式，更新 semantic-patterns
3. 模式置信度根据应用次数自动更新
