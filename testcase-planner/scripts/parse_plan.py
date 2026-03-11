#!/usr/bin/env python3
"""
测试规划解析器

基于 docs/specs/测试规划格式.md 规范

格式示例：
    # 测试规划

    ## 用户登录模块

    ### 手机号验证码登录
    > 风险等级: Critical
    > 测试关注点: 验证码过期（60s）、错误次数限制（5次）

    ### 第三方登录
    > 风险等级: Medium
    > 测试关注点: 微信/支付宝授权失败、token过期处理

用途:
- 解析 plan.md 文件，提取 ITEM 和 POINT 结构
- 验证格式是否符合规范
- 生成目录结构映射
"""

import re
import sys
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass, field


@dataclass
class TestPoint:
    """测试点数据结构"""
    name: str  # 测试点名称
    risk_level: str = ""  # 风险等级
    test_focus: str = ""  # 测试关注点
    line_number: int = 0  # 行号


@dataclass
class TestItem:
    """测试项数据结构"""
    name: str  # 测试项名称
    points: List[TestPoint] = field(default_factory=list)  # 测试点列表
    line_number: int = 0  # 行号


@dataclass
class TestPlan:
    """测试规划数据结构"""
    items: List[TestItem] = field(default_factory=list)  # 测试项列表
    total_items: int = 0  # ITEM 总数
    total_points: int = 0  # POINT 总数


class ParseError(Exception):
    """解析错误"""
    def __init__(self, message: str, line_number: int = 0):
        self.message = message
        self.line_number = line_number
        super().__init__(f"Line {line_number}: {message}" if line_number else message)


class PlanParser:
    """测试规划解析器"""

    # 正则表达式
    TITLE_PATTERN = re.compile(r'^#\s+(.+)$')  # 一级标题
    ITEM_PATTERN = re.compile(r'^##\s+(.+)$')  # 二级标题 (ITEM)
    POINT_PATTERN = re.compile(r'^###\s+(.+)$')  # 三级标题 (POINT)
    RISK_LEVEL_PATTERN = re.compile(r'^>\s*风险等级[：:]\s*(.+)$')  # 风险等级
    TEST_FOCUS_PATTERN = re.compile(r'^>\s*测试关注点[：:]\s*(.+)$')  # 测试关注点

    def __init__(self, strict: bool = True):
        """
        初始化解析器

        Args:
            strict: 是否严格模式
        """
        self.strict = strict
        self.errors: List[ParseError] = []

    def parse_file(self, file_path: Path) -> TestPlan:
        """
        解析测试规划文件

        Args:
            file_path: plan.md 文件路径

        Returns:
            TestPlan 对象
        """
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()

        return self._parse_lines(lines)

    def _parse_lines(self, lines: List[str]) -> TestPlan:
        """
        解析文件行

        Args:
            lines: 文件行列表

        Returns:
            TestPlan 对象
        """
        plan = TestPlan()
        current_item: Optional[TestItem] = None
        current_point: Optional[TestPoint] = None
        has_title = False

        for line_num, line in enumerate(lines, start=1):
            line = line.rstrip()

            # 跳过空行
            if not line.strip():
                continue

            # 一级标题
            title_match = self.TITLE_PATTERN.match(line)
            if title_match and not line.startswith('##'):
                title = title_match.group(1).strip()
                if title == "测试规划":
                    has_title = True
                continue

            # 二级标题 (ITEM)
            item_match = self.ITEM_PATTERN.match(line)
            if item_match and not line.startswith('###'):
                item_name = item_match.group(1).strip()

                # 保存上一个 ITEM
                if current_item:
                    if current_point:
                        current_item.points.append(current_point)
                        current_point = None
                    plan.items.append(current_item)

                # 创建新 ITEM
                current_item = TestItem(name=item_name, line_number=line_num)
                continue

            # 三级标题 (POINT)
            point_match = self.POINT_PATTERN.match(line)
            if point_match:
                point_name = point_match.group(1).strip()

                # 保存上一个 POINT
                if current_point and current_item:
                    current_item.points.append(current_point)

                # 创建新 POINT
                current_point = TestPoint(name=point_name, line_number=line_num)
                continue

            # 风险等级
            risk_match = self.RISK_LEVEL_PATTERN.match(line)
            if risk_match and current_point:
                current_point.risk_level = risk_match.group(1).strip()
                continue

            # 测试关注点
            focus_match = self.TEST_FOCUS_PATTERN.match(line)
            if focus_match and current_point:
                current_point.test_focus = focus_match.group(1).strip()
                continue

        # 保存最后一个 ITEM 和 POINT
        if current_point and current_item:
            current_item.points.append(current_point)
        if current_item:
            plan.items.append(current_item)

        # 计算统计
        plan.total_items = len(plan.items)
        plan.total_points = sum(len(item.points) for item in plan.items)

        # 验证
        if not has_title:
            self._add_error("缺少一级标题 '# 测试规划'", 1)

        if plan.total_items == 0:
            self._add_error("未找到任何测试项 (ITEM)", 0)

        if plan.total_points == 0:
            self._add_error("未找到任何测试点 (POINT)", 0)

        return plan

    def validate(self, plan: TestPlan) -> Tuple[bool, List[str]]:
        """
        验证测试规划

        Args:
            plan: TestPlan 对象

        Returns:
            (is_valid, error_messages)
        """
        errors = []

        # 检查 ITEM 数量
        if plan.total_items == 0:
            errors.append("❌ 未找到任何测试项 (ITEM)")

        # 检查 POINT 数量
        if plan.total_points == 0:
            errors.append("❌ 未找到任何测试点 (POINT)")

        # 检查每个 ITEM
        for item in plan.items:
            # ITEM 名称长度
            if len(item.name) < 2:
                errors.append(f"❌ ITEM '{item.name}' 名称过短 (Line {item.line_number})")
            elif len(item.name) > 20:
                errors.append(f"⚠️  ITEM '{item.name}' 名称过长 (Line {item.line_number})")

            # POINT 数量
            if len(item.points) == 0:
                errors.append(f"❌ ITEM '{item.name}' 没有测试点 (Line {item.line_number})")

            # 检查每个 POINT
            for point in item.points:
                # POINT 名称长度
                if len(point.name) < 4:
                    errors.append(f"❌ POINT '{point.name}' 名称过短 (Line {point.line_number})")
                elif len(point.name) > 30:
                    errors.append(f"⚠️  POINT '{point.name}' 名称过长 (Line {point.line_number})")

        # 如果有严重错误（❌），返回 False
        is_valid = not any(err.startswith("❌") for err in errors)

        return is_valid, errors

    def generate_directory_structure(self, plan: TestPlan) -> Dict[str, List[str]]:
        """
        生成目录结构映射

        Args:
            plan: TestPlan 对象

        Returns:
            {item_name: [point_name1, point_name2, ...]}
        """
        structure = {}
        for item in plan.items:
            structure[item.name] = [point.name for point in item.points]
        return structure

    def print_summary(self, plan: TestPlan):
        """打印测试规划摘要"""
        print("\n" + "="*60)
        print("测试规划摘要")
        print("="*60)
        print(f"\n📊 统计:")
        print(f"  - 测试项 (ITEM): {plan.total_items} 个")
        print(f"  - 测试点 (POINT): {plan.total_points} 个")

        print(f"\n📋 测试项列表:")
        for i, item in enumerate(plan.items, 1):
            print(f"\n  {i}. {item.name} ({len(item.points)} 个测试点)")
            for j, point in enumerate(item.points, 1):
                risk = f" [{point.risk_level}]" if point.risk_level else ""
                focus = f"\n       → {point.test_focus}" if point.test_focus else ""
                print(f"     {j}. {point.name}{risk}{focus}")

    def _add_error(self, message: str, line_number: int):
        """添加错误"""
        error = ParseError(message, line_number)
        self.errors.append(error)
        if self.strict:
            raise error


def main():
    """命令行入口"""
    import argparse

    parser = argparse.ArgumentParser(
        description="解析和验证测试规划文件 (plan.md)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 解析并验证
  python parse_plan.py test-case/plan.md

  # 显示详细摘要
  python parse_plan.py test-case/plan.md --verbose

  # 生成目录结构 JSON
  python parse_plan.py test-case/plan.md --json
        """
    )

    parser.add_argument("file", type=Path, help="plan.md 文件路径")
    parser.add_argument("-v", "--verbose", action="store_true", help="显示详细信息")
    parser.add_argument("--json", action="store_true", help="输出 JSON 格式")
    parser.add_argument("--no-strict", action="store_true", help="非严格模式")

    args = parser.parse_args()

    # 解析
    parser_obj = PlanParser(strict=not args.no_strict)

    try:
        plan = parser_obj.parse_file(args.file)
    except ParseError as e:
        print(f"❌ 解析失败: {e}", file=sys.stderr)
        sys.exit(1)
    except FileNotFoundError as e:
        print(f"❌ 文件不存在: {e}", file=sys.stderr)
        sys.exit(1)

    # 验证
    is_valid, errors = parser_obj.validate(plan)

    if args.json:
        # JSON 输出
        import json
        structure = parser_obj.generate_directory_structure(plan)
        output = {
            "total_items": plan.total_items,
            "total_points": plan.total_points,
            "structure": structure,
            "is_valid": is_valid,
            "errors": errors
        }
        print(json.dumps(output, ensure_ascii=False, indent=2))
    else:
        # 文本输出
        if args.verbose:
            parser_obj.print_summary(plan)

        # 验证结果
        if errors:
            print("\n" + "="*60)
            print("验证结果")
            print("="*60)
            for error in errors:
                print(f"  {error}")

        # 最终状态
        print("\n" + "="*60)
        if is_valid:
            print("✅ 测试规划格式正确")
        else:
            print("❌ 测试规划存在严重错误")
        print("="*60 + "\n")

        sys.exit(0 if is_valid else 1)


if __name__ == "__main__":
    main()
