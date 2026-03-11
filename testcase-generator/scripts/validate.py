#!/usr/bin/env python3
"""
测试用例验证工具（v0.2）

基于 docs/specs/测试用例文本协议.md 规范（v0.2版本）

功能：
1. 格式验证：检查用例是否符合文本协议 v0.2 格式
2. 重复检测：基于标题和步骤相似度检测疑似重复用例

用法：
    python validate.py test-case/模块/测试点.md           # 验证单个文件
    python validate.py test-case/                         # 验证整个目录
    python validate.py test-case/ --check-duplicates      # 同时检测重复
    python validate.py test-case/ --duplicates-only       # 仅检测重复
"""

import sys
import argparse
from pathlib import Path
from typing import List, Tuple, Dict, Optional
from dataclasses import dataclass
from parse_text_protocol import TextProtocolParser, ParseError, TestCase


@dataclass
class DuplicatePair:
    """重复用例对"""
    case1: TestCase
    case2: TestCase
    file1: str
    file2: str
    similarity: float
    detail: Dict[str, float]


class ValidationResult:
    """验证结果"""
    def __init__(self):
        self.total_files = 0
        self.total_cases = 0
        self.errors: List[Tuple[str, ParseError]] = []
        self.warnings: List[Tuple[str, str]] = []
        self.duplicates: List[DuplicatePair] = []

    def add_error(self, file_path: str, error: ParseError):
        self.errors.append((file_path, error))

    def add_warning(self, file_path: str, message: str):
        self.warnings.append((file_path, message))

    def add_duplicate(self, dup: DuplicatePair):
        self.duplicates.append(dup)

    def is_success(self) -> bool:
        return len(self.errors) == 0

    def print_summary(self, show_duplicates: bool = True):
        print(f"\n{'='*60}")
        print(f"验证完成")
        print(f"{'='*60}")
        print(f"文件数: {self.total_files}")
        print(f"用例数: {self.total_cases}")
        print(f"错误数: {len(self.errors)}")
        print(f"警告数: {len(self.warnings)}")
        if show_duplicates:
            print(f"疑似重复: {len(self.duplicates)} 对")

        if self.errors:
            print(f"\n❌ 发现 {len(self.errors)} 个错误:")
            for file_path, error in self.errors:
                print(f"  {file_path}:{error.line_number} {error.message}")

        if self.warnings:
            print(f"\n⚠️  发现 {len(self.warnings)} 个警告:")
            for file_path, message in self.warnings:
                print(f"  {file_path}: {message}")

        if show_duplicates and self.duplicates:
            print(f"\n🔄 发现 {len(self.duplicates)} 对疑似重复:")
            for idx, dup in enumerate(self.duplicates, 1):
                print(f"\n  [{idx}] 相似度: {dup.similarity:.1%}")
                print(f"      用例1: {dup.case1.title}")
                print(f"        文件: {dup.file1}")
                print(f"      用例2: {dup.case2.title}")
                print(f"        文件: {dup.file2}")
                print(f"      细节: 标题 {dup.detail['title']:.1%} | "
                      f"步骤 {dup.detail['steps']:.1%} | "
                      f"预期 {dup.detail['expected']:.1%}")

        if self.is_success() and not self.duplicates:
            print(f"\n✅ 所有用例验证通过，无重复")
        elif self.is_success():
            print(f"\n✅ 格式验证通过，但存在疑似重复")
        else:
            print(f"\n❌ 验证失败")


# ============ 相似度计算 ============

def levenshtein_distance(s1: str, s2: str) -> int:
    """编辑距离"""
    if len(s1) < len(s2):
        return levenshtein_distance(s2, s1)
    if len(s2) == 0:
        return len(s1)
    previous_row = range(len(s2) + 1)
    for i, c1 in enumerate(s1):
        current_row = [i + 1]
        for j, c2 in enumerate(s2):
            insertions = previous_row[j + 1] + 1
            deletions = current_row[j] + 1
            substitutions = previous_row[j] + (c1 != c2)
            current_row.append(min(insertions, deletions, substitutions))
        previous_row = current_row
    return previous_row[-1]


def string_similarity(s1: str, s2: str) -> float:
    """字符串相似度（基于编辑距离）"""
    if not s1 and not s2:
        return 1.0
    max_len = max(len(s1), len(s2))
    if max_len == 0:
        return 1.0
    return 1 - (levenshtein_distance(s1, s2) / max_len)


def jaccard_similarity(set1: set, set2: set) -> float:
    """Jaccard 相似度"""
    if not set1 and not set2:
        return 1.0
    union = set1 | set2
    return len(set1 & set2) / len(union) if union else 0.0


def steps_to_set(steps: List[str]) -> set:
    """将步骤列表转换为集合（用于 Jaccard 计算）"""
    return set(step.strip().lower() for step in steps if step.strip())


def calculate_similarity(case1: TestCase, case2: TestCase) -> Tuple[float, Dict[str, float]]:
    """
    计算两个用例的相似度
    
    Returns:
        (综合相似度, {title, steps, expected})
    """
    # 标题相似度
    title_sim = string_similarity(case1.title, case2.title)
    
    # 步骤相似度（Jaccard）
    steps_sim = jaccard_similarity(steps_to_set(case1.steps), steps_to_set(case2.steps))
    
    # 预期结果相似度（Jaccard）
    expected_sim = jaccard_similarity(steps_to_set(case1.expected), steps_to_set(case2.expected))
    
    # 加权综合（标题 40%，步骤 40%，预期 20%）
    overall = title_sim * 0.4 + steps_sim * 0.4 + expected_sim * 0.2
    
    return overall, {
        'title': title_sim,
        'steps': steps_sim,
        'expected': expected_sim
    }


# ============ 验证逻辑 ============

def validate_file(file_path: Path, result: ValidationResult) -> List[Tuple[TestCase, str]]:
    """
    验证单个文件
    
    Returns:
        [(用例, 文件路径), ...] 用于后续重复检测
    """
    result.total_files += 1
    cases_with_path = []

    parser = TextProtocolParser(strict=False)

    try:
        cases = parser.parse_file(file_path)
        result.total_cases += len(cases)

        for error in parser.errors:
            result.add_error(str(file_path), error)

        for case in cases:
            cases_with_path.append((case, str(file_path)))

    except ParseError as e:
        result.add_error(str(file_path), e)
    except Exception as e:
        result.add_error(str(file_path), ParseError(f"未知错误: {e}"))

    return cases_with_path


def validate_directory(dir_path: Path, result: ValidationResult) -> List[Tuple[TestCase, str]]:
    """验证目录下的所有测试用例文件"""
    all_cases = []

    md_files = []
    for item_dir in dir_path.iterdir():
        if not item_dir.is_dir() or item_dir.name.startswith('.'):
            continue
        for md_file in item_dir.glob('*.md'):
            if md_file.name not in ['plan.md', 'all_cases.md']:
                md_files.append(md_file)

    # 也检查根目录下的 all_cases.md
    all_cases_file = dir_path / 'all_cases.md'
    if all_cases_file.exists():
        md_files.append(all_cases_file)

    if not md_files:
        print(f"⚠️  目录 {dir_path} 中没有找到测试用例文件")
        return all_cases

    print(f"找到 {len(md_files)} 个测试用例文件")

    for md_file in md_files:
        print(f"验证: {md_file}")
        cases = validate_file(md_file, result)
        all_cases.extend(cases)

    return all_cases


def detect_duplicates(cases_with_path: List[Tuple[TestCase, str]], 
                      threshold: float = 0.7) -> List[DuplicatePair]:
    """检测重复用例"""
    duplicates = []
    
    for i in range(len(cases_with_path)):
        for j in range(i + 1, len(cases_with_path)):
            case1, file1 = cases_with_path[i]
            case2, file2 = cases_with_path[j]
            
            similarity, detail = calculate_similarity(case1, case2)
            
            if similarity >= threshold:
                duplicates.append(DuplicatePair(
                    case1=case1,
                    case2=case2,
                    file1=file1,
                    file2=file2,
                    similarity=similarity,
                    detail=detail
                ))
    
    return duplicates


def main():
    parser = argparse.ArgumentParser(description="验证测试用例格式并检测重复")
    parser.add_argument("path", help="要验证的文件或目录路径")
    parser.add_argument("--check-duplicates", "-d", action="store_true",
                        help="同时检测重复用例")
    parser.add_argument("--duplicates-only", action="store_true",
                        help="仅检测重复，跳过格式验证")
    parser.add_argument("--threshold", "-t", type=float, default=0.7,
                        help="重复检测阈值 0-1 (默认 0.7)")
    args = parser.parse_args()

    path = Path(args.path)
    if not path.exists():
        print(f"❌ 路径不存在: {path}")
        sys.exit(1)

    result = ValidationResult()
    all_cases = []

    # 收集用例
    if path.is_file():
        all_cases = validate_file(path, result)
    elif path.is_dir():
        all_cases = validate_directory(path, result)
    else:
        print(f"❌ 无效的路径: {path}")
        sys.exit(1)

    # 重复检测
    check_dups = args.check_duplicates or args.duplicates_only
    if check_dups and all_cases:
        print(f"\n正在检测重复 (阈值 {args.threshold})...")
        duplicates = detect_duplicates(all_cases, args.threshold)
        for dup in duplicates:
            result.add_duplicate(dup)

    # 输出结果
    result.print_summary(show_duplicates=check_dups)
    
    # 退出码
    if args.duplicates_only:
        sys.exit(1 if result.duplicates else 0)
    else:
        sys.exit(0 if result.is_success() else 1)


if __name__ == "__main__":
    main()
