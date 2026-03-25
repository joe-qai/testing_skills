#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
测试用例格式校验脚本
检查所有测试用例是否符合格式要求
"""

import os
import re
from pathlib import Path
from typing import List, Dict, Tuple

# 测试用例正则表达式
CASE_PATTERN = r'^## \[P([0-3])\] (.+)$'
FIELD_PATTERNS = {
    '测试类型': r'^\[测试类型\] (.+)$',
    '前置条件': r'^\[前置条件\] (.+)$',
    '测试步骤': r'^\[测试步骤\] (.+)$',
    '预期结果': r'^\[预期结果\] (.+)$'
}

class TestCaseValidator:
    def __init__(self, base_path: str):
        self.base_path = Path(base_path)
        self.errors = []
        self.warnings = []
        self.stats = {
            'total_files': 0,
            'total_cases': 0,
            'valid_cases': 0,
            'invalid_cases': 0,
            'priority_counts': {'P0': 0, 'P1': 0, 'P2': 0, 'P3': 0}
        }

    def validate_all(self) -> bool:
        """验证所有测试用例文件"""
        print("=" * 60)
        print("开始校验测试用例格式...")
        print("=" * 60)

        # 查找所有 .md 文件（排除 all_cases.md 和 plan.md）
        md_files = list(self.base_path.glob("**/*.md"))
        md_files = [f for f in md_files if f.name not in ['all_cases.md', 'plan.md']]

        self.stats['total_files'] = len(md_files)

        for md_file in md_files:
            self.validate_file(md_file)

        self.print_summary()
        return len(self.errors) == 0

    def validate_file(self, file_path: Path):
        """验证单个文件"""
        print(f"\n验证文件: {file_path.relative_to(self.base_path)}")

        try:
            content = file_path.read_text(encoding='utf-8')
            lines = content.split('\n')

            cases = self.extract_cases(lines)
            self.stats['total_cases'] += len(cases)

            for i, (case_line, case_num) in enumerate(cases, 1):
                priority, title = self.parse_case_line(case_line)
                self.validate_case(file_path, case_num, priority, title, lines, i)

        except Exception as e:
            self.errors.append(f"{file_path.relative_to(self.base_path)}: 读取文件失败 - {str(e)}")

    def extract_cases(self, lines: List[str]) -> List[Tuple[str, int]]:
        """提取所有测试用例"""
        cases = []
        for i, line in enumerate(lines):
            if re.match(CASE_PATTERN, line.strip()):
                cases.append((line.strip(), i))
        return cases

    def parse_case_line(self, line: str) -> Tuple[str, str]:
        """解析测试用例行"""
        match = re.match(CASE_PATTERN, line.strip())
        if match:
            priority = f"P{match.group(1)}"  # 将数字转换为 P0 格式
            title = match.group(2)
            return priority, title
        return '', ''

    def validate_case(self, file_path: Path, line_num: int, priority: str, title: str, lines: List[str], case_index: int):
        """验证单个测试用例"""
        if not priority or not title:
            self.errors.append(f"{file_path.relative_to(self.base_path)}:第{line_num+1}行 - 测试用例格式错误，无法解析优先级或标题")
            self.stats['invalid_cases'] += 1
            return

        # 验证优先级
        if priority not in ['P0', 'P1', 'P2', 'P3']:
            self.errors.append(f"{file_path.relative_to(self.base_path)}:第{line_num+1}行 - 无效的优先级 '{priority}'")
            self.stats['invalid_cases'] += 1
            return

        self.stats['priority_counts'][priority] += 1

        # 验证必需字段
        required_fields = ['测试类型', '前置条件', '测试步骤', '预期结果']
        field_lines = self.find_field_lines(lines, line_num)

        missing_fields = []
        for field in required_fields:
            if field not in field_lines:
                missing_fields.append(field)

        if missing_fields:
            self.errors.append(f"{file_path.relative_to(self.base_path)}:测试用例'{title}' - 缺少必需字段: {', '.join(missing_fields)}")
            self.stats['invalid_cases'] += 1
        else:
            self.stats['valid_cases'] += 1

    def find_field_lines(self, lines: List[str], start_line: int) -> Dict[str, int]:
        """查找测试用例的字段行号"""
        field_lines = {}

        # 从当前行开始，查找下一个测试用例之前的所有行
        for i in range(start_line, len(lines)):
            line = lines[i].strip()

            # 检查是否是新的测试用例
            if i > start_line and re.match(CASE_PATTERN, line):
                break

            # 检查是否是必需字段
            for field_name, pattern in FIELD_PATTERNS.items():
                if re.match(pattern, line):
                    if field_name not in field_lines:  # 只记录第一次出现
                        field_lines[field_name] = i
                    break

        return field_lines

    def print_summary(self):
        """打印校验摘要"""
        print("\n" + "=" * 60)
        print("校验摘要")
        print("=" * 60)
        print(f"文件总数: {self.stats['total_files']}")
        print(f"测试用例总数: {self.stats['total_cases']}")
        print(f"有效用例: {self.stats['valid_cases']}")
        print(f"无效用例: {self.stats['invalid_cases']}")
        print(f"优先级分布:")
        for priority, count in self.stats['priority_counts'].items():
            print(f"  {priority}: {count} 个")
        print(f"错误数量: {len(self.errors)}")
        print(f"警告数量: {len(self.warnings)}")

        if self.errors:
            print("\n" + "=" * 60)
            print("错误详情")
            print("=" * 60)
            for error in self.errors:
                print(f"✗ {error}")

        if self.warnings:
            print("\n" + "=" * 60)
            print("警告详情")
            print("=" * 60)
            for warning in self.warnings:
                print(f"⚠ {warning}")

        print("\n" + "=" * 60)
        if len(self.errors) == 0:
            print("✓ 校验通过！所有测试用例格式正确。")
        else:
            print("✗ 校验失败！请修复上述错误。")
        print("=" * 60)


def main():
    """主函数"""
    # 获取测试用例目录
    base_path = Path(__file__).parent.parent.parent / "test-case"

    if not base_path.exists():
        print(f"错误: 测试用例目录不存在: {base_path}")
        return False

    validator = TestCaseValidator(base_path)
    success = validator.validate_all()

    return 0 if success else 1


if __name__ == "__main__":
    import sys
    sys.exit(main())