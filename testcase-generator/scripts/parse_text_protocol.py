#!/usr/bin/env python3
"""
测试用例文本协议解析器 (v0.2)

基于 docs/specs/测试用例文本协议.md 规范（v0.2版本）

格式示例：
    ## [P1] 验证首次登录成功
    [测试类型] 功能
    [前置条件] 用户未注册；短信服务正常
    [测试步骤] 1. 打开登录页面，输入未注册的11位手机号，点击"获取验证码"。2. 输入收到的验证码，点击"登录"按钮
    [预期结果] 1. 收到6位数字验证码短信，按钮变为60秒倒计时。2. 自动创建新账号，登录成功并跳转至首页

    ## [P2][反向] 验证输入错误验证码提示
    [测试类型] 功能
    [前置条件] 用户已获取验证码
    [测试步骤] 1. 输入错误的6位数字，点击"登录"按钮
    [预期结果] 1. 登录失败，停留在登录页，提示"验证码错误，请重新输入"

变更说明：
- v0.2 使用中文字段标签和 String 格式步骤
- 支持 `[测试类型]` `[前置条件]` `[测试步骤]` `[预期结果]` `[备注]`
- 反向用例仅在标题中使用 `[反向]` 标记，不需要单独字段
- 步骤格式：`1. xxx。2. xxx` 或 `1. xxx；2. xxx` 等
- 字段之间不要空行，保持紧凑格式
"""

import re
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass, field


@dataclass
class TestCase:
    """测试用例数据结构"""
    # 从标题提取
    priority: str  # P1-P5
    is_negative: bool  # 是否反向用例
    title: str  # 用例标题

    # 必填字段
    test_type: str  # [测试类型]
    steps: List[str] = field(default_factory=list)  # 从 [测试步骤] 提取
    expected: List[str] = field(default_factory=list)  # 从 [预期结果] 提取

    # 可选字段
    precondition: str = ""  # [前置条件]
    note: str = ""  # [备注]

    # 元数据
    line_number: int = 0  # 用例在文件中的行号
    raw_title: str = ""  # 原始标题行
    raw_steps: str = ""  # 原始步骤字符串
    raw_expected: str = ""  # 原始预期结果字符串


class ParseError(Exception):
    """解析错误"""
    def __init__(self, message: str, line_number: int = 0):
        self.message = message
        self.line_number = line_number
        super().__init__(f"Line {line_number}: {message}" if line_number else message)


class TextProtocolParser:
    """文本协议解析器（v0.2）"""

    # 正则表达式
    TITLE_PATTERN = re.compile(r'^##\s*(\[P[1-5]\])(\[反向\])?\s*(.+)$')
    FIELD_PATTERN = re.compile(r'^\[([^\]]+)\]\s*(.*)$')

    # 步骤分隔符（支持多种格式）
    STEP_SEPARATORS = ['。', '；', '，', '\n']

    # 有效的测试类型
    VALID_TEST_TYPES = [
        "功能", "兼容性", "易用性", "性能", "稳定性",
        "安全性", "可靠性", "效果（AI类、资源类）",
        "效果（硬件器件类）", "可维护性", "可移植性", "埋点"
    ]

    def __init__(self, strict: bool = True):
        """
        初始化解析器

        Args:
            strict: 是否严格模式（严格模式下会对所有错误抛出异常）
        """
        self.strict = strict
        self.errors: List[ParseError] = []

    def parse_file(self, file_path: Path) -> List[TestCase]:
        """
        解析测试用例文件

        Args:
            file_path: 文件路径

        Returns:
            测试用例列表
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
        except Exception as e:
            raise ParseError(f"无法读取文件: {e}")

        return self.parse_content(content)

    def parse_content(self, content: str) -> List[TestCase]:
        """
        解析测试用例内容

        Args:
            content: 文件内容

        Returns:
            测试用例列表
        """
        lines = content.split('\n')
        cases = []

        i = 0
        while i < len(lines):
            line = lines[i].strip()

            # 查找用例标题（## 开头）
            if line.startswith('##'):
                case, next_i = self._parse_case(lines, i)
                if case:
                    cases.append(case)
                i = next_i
            else:
                i += 1

        return cases

    def _parse_case(self, lines: List[str], start_idx: int) -> Tuple[Optional[TestCase], int]:
        """
        解析单个用例

        Args:
            lines: 所有行
            start_idx: 起始行索引

        Returns:
            (用例对象, 下一个用例的起始索引)
        """
        # 解析标题
        title_line = lines[start_idx].strip()
        line_num = start_idx + 1

        try:
            priority, is_negative, title = self._parse_title(title_line, line_num)
        except ParseError as e:
            if self.strict:
                raise
            self.errors.append(e)
            return None, start_idx + 1

        # 收集字段内容（直到下一个 ## 或文件结束）
        fields = {}
        i = start_idx + 1
        current_field = None
        current_content = []

        while i < len(lines):
            line = lines[i].strip()

            # 遇到下一个用例，结束当前用例
            if line.startswith('##'):
                break

            # 跳过空行
            if not line:
                i += 1
                continue

            # 检查是否是字段标签
            match = self.FIELD_PATTERN.match(line)
            if match:
                # 保存上一个字段
                if current_field:
                    fields[current_field] = '\n'.join(current_content).strip()

                # 开始新字段
                current_field = match.group(1)
                current_content = [match.group(2)] if match.group(2) else []
            else:
                # 多行内容
                if current_field:
                    current_content.append(line)

            i += 1

        # 保存最后一个字段
        if current_field:
            fields[current_field] = '\n'.join(current_content).strip()

        # 构建用例对象
        try:
            case = self._build_case(priority, is_negative, title, fields, line_num, title_line)
            self._validate_case(case, line_num)
            return case, i
        except ParseError as e:
            if self.strict:
                raise
            self.errors.append(e)
            return None, i

    def _parse_title(self, title_line: str, line_num: int) -> Tuple[str, bool, str]:
        """
        解析用例标题

        Args:
            title_line: 标题行
            line_num: 行号

        Returns:
            (优先级, 是否反向用例, 标题文本)
        """
        match = self.TITLE_PATTERN.match(title_line)
        if not match:
            raise ParseError(
                f"用例标题格式错误，应为 '## [P1..P5][反向可选] 标题'，实际: {title_line}",
                line_num
            )

        priority = match.group(1)[1:-1]  # 去掉方括号，如 [P1] -> P1
        is_negative = match.group(2) is not None
        title = match.group(3).strip()

        return priority, is_negative, title

    def _parse_steps(self, steps_str: str, line_num: int) -> List[str]:
        """
        解析步骤字符串

        支持格式：
        - 1. xxx。2. xxx
        - 1. xxx；2. xxx
        - 1. xxx\n2. xxx

        Args:
            steps_str: 步骤字符串
            line_num: 行号

        Returns:
            步骤列表
        """
        if not steps_str:
            return []

        # 先尝试按换行分割
        if '\n' in steps_str:
            lines = steps_str.strip().split('\n')
            steps = []
            for line in lines:
                m = re.match(r'(\d+)\.\s*(.+)', line.strip())
                if m:
                    num = int(m.group(1))
                    if num != len(steps) + 1:
                        raise ParseError(f"步骤编号不连续，期望 {len(steps) + 1}，实际 {num}", line_num)
                    steps.append(m.group(2).strip())
            if steps:
                return steps

        # 使用更精确的正则：步骤编号必须在开头或分隔符后
        # 匹配模式：开头或分隔符后的 "数字. "
        # 关键：步骤编号前面必须是开头、分隔符（。；，）或空格，而不是其他字符
        
        steps = []
        # 使用 findall 找到所有步骤
        # 模式：(^|[。；，\s])(\d+)\.\s*([^。；，]+(?:[。；，]|$))
        # 更简单的方法：按步骤编号分割，但要确保编号在正确位置
        
        # 先找到所有步骤编号的位置
        # 步骤编号特征：在开头或分隔符后，后面跟 ". "
        pattern = r'(?:^|[。；，])\s*(\d+)\.\s*'
        
        # 找到所有匹配
        matches = list(re.finditer(pattern, steps_str))
        
        if not matches:
            # 尝试简单格式：只有一个步骤，没有编号
            # 或者格式不标准，返回整个字符串作为一个步骤
            raise ParseError(f"无法解析步骤格式: {steps_str[:50]}...", line_num)
        
        for idx, match in enumerate(matches):
            num = int(match.group(1))
            if num != len(steps) + 1:
                raise ParseError(f"步骤编号不连续，期望 {len(steps) + 1}，实际 {num}", line_num)
            
            # 获取步骤内容：从当前匹配结束到下一个匹配开始（或字符串结束）
            start = match.end()
            if idx + 1 < len(matches):
                end = matches[idx + 1].start()
            else:
                end = len(steps_str)
            
            content = steps_str[start:end].strip().rstrip('。；，')
            if content:
                steps.append(content)

        if not steps:
            raise ParseError(f"无法解析步骤格式: {steps_str[:50]}...", line_num)

        return steps

    def _build_case(self, priority: str, is_negative: bool, title: str,
                    fields: Dict[str, str], line_num: int, raw_title: str) -> TestCase:
        """
        构建用例对象

        Args:
            priority: 优先级
            is_negative: 是否反向用例（从标题提取）
            title: 标题
            fields: 字段字典
            line_num: 行号
            raw_title: 原始标题行

        Returns:
            测试用例对象
        """
        # 解析步骤和预期结果
        raw_steps = fields.get('测试步骤', '')
        raw_expected = fields.get('预期结果', '')

        steps = self._parse_steps(raw_steps, line_num)
        expected = self._parse_steps(raw_expected, line_num)

        # 反向用例标记：优先从标题提取，其次从字段
        if '反向用例' in fields:
            is_negative = fields['反向用例'] in ['是', '是']

        # 构建用例
        case = TestCase(
            priority=priority,
            is_negative=is_negative,
            title=title,
            test_type=fields.get('测试类型', ''),
            steps=steps,
            expected=expected,
            precondition=fields.get('前置条件', ''),
            note=fields.get('备注', ''),
            line_number=line_num,
            raw_title=raw_title,
            raw_steps=raw_steps,
            raw_expected=raw_expected
        )

        return case

    def _validate_case(self, case: TestCase, line_num: int):
        """
        验证用例完整性

        Args:
            case: 测试用例对象
            line_num: 行号
        """
        # 验证必填字段
        if not case.test_type:
            raise ParseError("缺少必填字段 [测试类型]", line_num)

        if not case.steps:
            raise ParseError("缺少必填字段 [测试步骤]", line_num)

        if not case.expected:
            raise ParseError("缺少必填字段 [预期结果]", line_num)

        # 验证测试类型
        if case.test_type not in self.VALID_TEST_TYPES:
            raise ParseError(
                f"无效的测试类型: {case.test_type}，必须是以下之一: {', '.join(self.VALID_TEST_TYPES)}",
                line_num
            )

        # 验证步骤和预期结果数量一致
        if len(case.steps) != len(case.expected):
            raise ParseError(
                f"测试步骤数量({len(case.steps)})与预期结果数量({len(case.expected)})不一致",
                line_num
            )


def parse_test_cases(file_path: Path, strict: bool = True) -> List[TestCase]:
    """
    便捷函数：解析测试用例文件

    Args:
        file_path: 文件路径
        strict: 是否严格模式

    Returns:
        测试用例列表
    """
    parser = TextProtocolParser(strict=strict)
    return parser.parse_file(file_path)


# 测试代码
if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("用法: python parse_text_protocol.py <文件路径>")
        sys.exit(1)

    file_path = Path(sys.argv[1])
    try:
        cases = parse_test_cases(file_path)
        print(f"✅ 解析成功，共 {len(cases)} 个用例\n")
        for i, case in enumerate(cases, 1):
            print(f"用例 {i}: [{case.priority}] {case.title}")
            print(f"  测试类型: {case.test_type}")
            print(f"  反向用例: {'是' if case.is_negative else '否'}")
            print(f"  步骤数: {len(case.steps)}")
            for j, (step, exp) in enumerate(zip(case.steps, case.expected), 1):
                print(f"    {j}. {step} → {exp}")
            if case.precondition:
                print(f"  前置条件: {case.precondition}")
            if case.note:
                print(f"  备注: {case.note}")
            print()
    except ParseError as e:
        print(f"❌ 解析失败: {e}")
        sys.exit(1)
