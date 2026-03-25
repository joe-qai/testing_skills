#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
测试工作量估算 Excel 生成脚本
根据测试用例的优先级和复杂度估算工作量，并生成 Excel 报告
"""

import os
import re
from pathlib import Path
from typing import List, Dict, Tuple
import pandas as pd
from datetime import datetime

# 测试用例正则表达式
CASE_PATTERN = r'^## \[P([0-3])\] (.+)$'
FIELD_PATTERNS = {
    '测试类型': r'^\[测试类型\] (.+)$',
    '前置条件': r'^\[前置条件\] (.+)$',
    '测试步骤': r'^\[测试步骤\] (.+)$',
    '预期结果': r'^\[预期结果\] (.+)$'
}

# 复杂度标准
COMPLEXITY_STANDARDS = {
    'P0': {
        'name': '复杂',
        'case_design_min': 0.50,
        'case_design_max': 0.50,
        'first_run_min': 0.30,
        'first_run_max': 0.40
    },
    'P1': {
        'name': '中等',
        'case_design_min': 0.35,
        'case_design_max': 0.40,
        'first_run_min': 0.25,
        'first_run_max': 0.30
    },
    'P2': {
        'name': '简单',
        'case_design_min': 0.20,
        'case_design_max': 0.30,
        'first_run_min': 0.15,
        'first_run_max': 0.20
    },
    'P3': {
        'name': '简单',
        'case_design_min': 0.20,
        'case_design_max': 0.30,
        'first_run_min': 0.15,
        'first_run_max': 0.20
    }
}


class TestCaseEstimator:
    def __init__(self, base_path: str):
        self.base_path = Path(base_path)
        self.test_cases = []

    def collect_all_cases(self):
        """收集所有测试用例"""
        print("=" * 60)
        print("开始收集测试用例...")
        print("=" * 60)

        # 查找所有 .md 文件（排除 all_cases.md 和 plan.md）
        md_files = list(self.base_path.glob("**/*.md"))
        md_files = [f for f in md_files if f.name not in ['all_cases.md', 'plan.md']]

        for md_file in md_files:
            self.collect_cases_from_file(md_file)

        print(f"\n共收集到 {len(self.test_cases)} 个测试用例")

    def collect_cases_from_file(self, file_path: Path):
        """从单个文件收集测试用例"""
        try:
            content = file_path.read_text(encoding='utf-8')
            lines = content.split('\n')

            # 提取所有测试用例
            cases = self.extract_cases(lines)
            item_name = file_path.parent.name
            point_name = file_path.stem

            for i, (case_line, case_num) in enumerate(cases, 1):
                priority, title = self.parse_case_line(case_line)
                fields = self.extract_fields(lines, case_num)

                self.test_cases.append({
                    'item': item_name,
                    'point': point_name,
                    'priority': priority,
                    'title': title,
                    'test_type': fields.get('测试类型', ''),
                    'precondition': fields.get('前置条件', ''),
                    'test_steps': fields.get('测试步骤', ''),
                    'expected_result': fields.get('预期结果', '')
                })

        except Exception as e:
            print(f"警告: 读取文件失败 {file_path.relative_to(self.base_path)}: {str(e)}")

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
            priority = f"P{match.group(1)}"
            title = match.group(2)
            return priority, title
        return '', ''

    def extract_fields(self, lines: List[str], start_line: int) -> Dict[str, str]:
        """提取测试用例的字段"""
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
                    if field_name not in field_lines:
                        match = re.match(pattern, line)
                        field_lines[field_name] = match.group(1)
                    break

        return field_lines

    def estimate_effort(self, case: Dict) -> Dict:
        """估算单个测试用例的工作量"""
        priority = case['priority']
        complexity = COMPLEXITY_STANDARDS[priority]

        # 取中间值作为估算
        case_design = (complexity['case_design_min'] + complexity['case_design_max']) / 2
        first_run = (complexity['first_run_min'] + complexity['first_run_max']) / 2

        # Retest: 33%-67% of first run, round to 0.10 minimum
        retest_ratio = 0.50  # 使用中间值 50%
        retest = round(first_run * retest_ratio, 2)
        retest = max(0.10, retest)  # 确保至少 0.10

        # Regression: 48%-67% of first run, round to two decimals
        regression_ratio = 0.58  # 使用中间值
        regression = round(first_run * regression_ratio, 2)
        regression = max(0.10, regression)  # 确保至少 0.10

        # 四舍五入到两位小数
        case_design = round(case_design, 2)
        first_run = round(first_run, 2)
        retest = round(retest, 2)
        regression = round(regression, 2)

        total = case_design + first_run + retest + regression

        return {
            'priority': priority,
            'complexity': complexity['name'],
            'case_design': case_design,
            'first_run': first_run,
            'retest': retest,
            'regression': regression,
            'total': total,
            'rationale': f"{complexity['name']}复杂度: 设计{case_design}人日 + 首次执行{first_run}人日 + 回归{retest_ratio*100:.0f}% + 回归{regression_ratio*100:.0f}%"
        }

    def generate_excel(self, output_path: str):
        """生成 Excel 报告"""
        print("\n" + "=" * 60)
        print("开始生成 Excel 报告...")
        print("=" * 60)

        # 估算所有测试用例的工作量
        estimated_cases = []
        for case in self.test_cases:
            effort = self.estimate_effort(case)
            estimated_cases.append({
                'ITEM': case['item'],
                'POINT': case['point'],
                '优先级': case['priority'],
                '复杂度': effort['complexity'],
                '测试用例标题': case['title'],
                '测试类型': case['test_type'],
                '用例设计(人日)': effort['case_design'],
                '首次执行(人日)': effort['first_run'],
                '回归测试(人日)': effort['retest'],
                '回归(人日)': effort['regression'],
                '总计(人日)': effort['total'],
                '估算依据': effort['rationale']
            })

        # 创建 DataFrame
        df = pd.DataFrame(estimated_cases)

        # 按 ITEM 和 POINT 分组汇总
        summary_df = df.groupby(['ITEM', 'POINT']).agg({
            '用例设计(人日)': 'sum',
            '首次执行(人日)': 'sum',
            '回归测试(人日)': 'sum',
            '回归(人日)': 'sum',
            '总计(人日)': 'sum',
            '优先级': 'count'
        }).reset_index()
        summary_df.columns = ['ITEM', 'POINT', '用例设计(人日)', '首次执行(人日)', '回归测试(人日)', '回归(人日)', '总计(人日)', '用例数量']

        # 计算总汇总
        total_summary = {
            'ITEM': '总计',
            'POINT': '全部',
            '用例设计(人日)': summary_df['用例设计(人日)'].sum(),
            '首次执行(人日)': summary_df['首次执行(人日)'].sum(),
            '回归测试(人日)': summary_df['回归测试(人日)'].sum(),
            '回归(人日)': summary_df['回归(人日)'].sum(),
            '总计(人日)': summary_df['总计(人日)'].sum(),
            '用例数量': summary_df['用例数量'].sum()
        }

        # 将总汇总添加到 summary_df
        summary_df = pd.concat([summary_df, pd.DataFrame([total_summary])], ignore_index=True)

        # 写入 Excel
        with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
            # 详细测试用例表
            df.to_excel(writer, sheet_name='详细测试用例', index=False)

            # 汇总表
            summary_df.to_excel(writer, sheet_name='汇总', index=False)

            # 按优先级汇总
            priority_summary = df.groupby(['优先级', '复杂度']).agg({
                '用例设计(人日)': 'sum',
                '首次执行(人日)': 'sum',
                '回归测试(人日)': 'sum',
                '回归(人日)': 'sum',
                '总计(人日)': 'sum',
                '测试用例标题': 'count'
            }).reset_index()
            priority_summary.columns = ['优先级', '复杂度', '用例设计(人日)', '首次执行(人日)', '回归测试(人日)', '回归(人日)', '总计(人日)', '用例数量']
            priority_summary.to_excel(writer, sheet_name='按优先级汇总', index=False)

        print(f"\nExcel 报告已生成: {output_path}")
        print(f"\n总工作量汇总:")
        print(f"  用例设计: {total_summary['用例设计(人日)']:.2f} 人日")
        print(f"  首次执行: {total_summary['首次执行(人日)']:.2f} 人日")
        print(f"  回归测试: {total_summary['回归测试(人日)']:.2f} 人日")
        print(f"  回归: {total_summary['回归(人日)']:.2f} 人日")
        print(f"  总计: {total_summary['总计(人日)']:.2f} 人日")
        print(f"  用例数量: {total_summary['用例数量']} 个")


def main():
    """主函数"""
    # 获取测试用例目录
    base_path = Path(__file__).parent.parent.parent / "test-case"

    if not base_path.exists():
        print(f"错误: 测试用例目录不存在: {base_path}")
        return False

    # 输出文件路径
    output_path = Path(__file__).parent.parent.parent / "test-effort-estimation.xlsx"

    # 创建估算器并生成报告
    estimator = TestCaseEstimator(base_path)
    estimator.collect_all_cases()
    estimator.generate_excel(str(output_path))

    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())