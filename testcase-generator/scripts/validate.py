#!/usr/bin/env python3
"""
测试用例验证工具（v0.2）

基于 docs/specs/测试用例文本协议.md 规范（v0.2版本）

功能：
1. 格式验证：检查用例是否符合文本协议 v0.2 格式
2. 重复检测：基于 TF-IDF + 余弦相似度检测疑似重复用例

改进说明（v0.2）：
- 统一使用 TF-IDF + 余弦相似度算法（与 generation_service.py 一致）
- 替代原有的 Levenshtein + Jaccard 算法（性能差、忽略顺序）
- 支持可选依赖：sklearn 未安装时回退到简易词频向量

用法：
    python validate.py test-case/模块/测试点.md           # 验证单个文件
    python validate.py test-case/                         # 验证整个目录
    python validate.py test-case/ --check-duplicates      # 同时检测重复
    python validate.py test-case/ --duplicates-only       # 仅检测重复
"""

import sys
import math
import re
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
            print("\nErrors:", len(self.errors))
            for file_path, error in self.errors:
                print(f"  {file_path}:{error.line_number} {error.message}")

        if self.warnings:
            print("\nWarnings:", len(self.warnings))
            for file_path, message in self.warnings:
                print(f"  {file_path}: {message}")

        if show_duplicates and self.duplicates:
            print("\nPossible duplicates:", len(self.duplicates))
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
            print("\nAll cases valid, no duplicates")
        elif self.is_success():
            print("\nFormat valid, but duplicates detected")
        else:
            print("\nValidation failed")


# ============ 相似度计算（TF-IDF + 余弦相似度）============

class SimilarityCalculator:
    """
    相似度计算器（TF-IDF + 余弦相似度）

    改进：替代原有的 Levenshtein + Jaccard 算法
    - Levenshtein O(n*m) 性能差
    - Jaccard 忽略步骤顺序
    - TF-IDF + 余弦相似度更准确且高效
    """

    def __init__(self, use_sklearn: bool = True):
        """
        初始化计算器

        Args:
            use_sklearn: 是否尝试使用 sklearn（性能更好）
        """
        self.use_sklearn = use_sklearn
        self._sklearn_available = False

        if use_sklearn:
            try:
                from sklearn.feature_extraction.text import TfidfVectorizer
                from sklearn.metrics.pairwise import cosine_similarity
                self.TfidfVectorizer = TfidfVectorizer
                self.cosine_similarity = cosine_similarity
                self._sklearn_available = True
            except ImportError:
                self._sklearn_available = False

    def _tokenize(self, text: str) -> str:
        """
        简单分词（中英文混合）

        改进：与 confidence_calculator.py 保持一致的分词策略
        """
        # 提取中文字符和英数字
        tokens = re.findall(r'[\u4e00-\u9fff]+|[a-zA-Z0-9]+', text.lower())
        # 中文字符级 unigram（每个汉字为一个词元）
        expanded = []
        for t in tokens:
            if re.match(r'^[\u4e00-\u9fff]+$', t):
                expanded.extend(list(t))
            else:
                expanded.append(t)
        return ' '.join(expanded)

    def calculate_similarity_sklearn(self, text1: str, text2: str) -> float:
        """使用 sklearn 计算 TF-IDF + 余弦相似度"""
        tokens1 = self._tokenize(text1)
        tokens2 = self._tokenize(text2)

        vectorizer = self.TfidfVectorizer()
        vectors = vectorizer.fit_transform([tokens1, tokens2])
        return float(self.cosine_similarity(vectors)[0][1])

    def _build_term_vector(self, text: str) -> Dict[str, int]:
        """构建词频向量"""
        tokens = re.findall(r'[\u4e00-\u9fff]+|[a-zA-Z0-9]+', text.lower())
        expanded = []
        for t in tokens:
            if re.match(r'^[\u4e00-\u9fff]+$', t):
                expanded.extend(list(t))
            else:
                expanded.append(t)

        vector: Dict[str, int] = {}
        for token in expanded:
            if len(token) > 1 or not re.match(r'[a-z0-9]', token):
                vector[token] = vector.get(token, 0) + 1
        return vector

    def _cosine_similarity(self, vec1: Dict[str, int], vec2: Dict[str, int]) -> float:
        """计算余弦相似度"""
        if not vec1 or not vec2:
            return 0.0
        common_keys = set(vec1.keys()) & set(vec2.keys())
        dot = sum(vec1[k] * vec2[k] for k in common_keys)
        norm1 = math.sqrt(sum(v * v for v in vec1.values()))
        norm2 = math.sqrt(sum(v * v for v in vec2.values()))
        if norm1 == 0 or norm2 == 0:
            return 0.0
        return min(dot / (norm1 * norm2), 1.0)

    def calculate_similarity_fallback(self, text1: str, text2: str) -> float:
        """使用简易词频向量计算余弦相似度（sklearn 不可用时）"""
        vec1 = self._build_term_vector(text1)
        vec2 = self._build_term_vector(text2)
        return self._cosine_similarity(vec1, vec2)

    def calculate_similarity(self, text1: str, text2: str) -> float:
        """
        计算两个文本的相似度

        Args:
            text1: 文本1
            text2: 文本2

        Returns:
            相似度分数 [0.0, 1.0]
        """
        if not text1 and not text2:
            return 1.0
        if not text1 or not text2:
            return 0.0

        if self._sklearn_available:
            return self.calculate_similarity_sklearn(text1, text2)
        else:
            return self.calculate_similarity_fallback(text1, text2)


def calculate_case_similarity(case1: TestCase, case2: TestCase,
                              calculator: SimilarityCalculator) -> Tuple[float, Dict[str, float]]:
    """
    计算两个用例的综合相似度

    改进：使用 TF-IDF + 余弦相似度替代 Levenshtein + Jaccard
    - 标题相似度 40%
    - 步骤相似度 40%
    - 预期结果相似度 20%

    Args:
        case1: 用例1
        case2: 用例2
        calculator: 相似度计算器

    Returns:
        (综合相似度, {title, steps, expected})
    """
    title_sim = calculator.calculate_similarity(case1.title, case2.title)
    steps_sim = calculator.calculate_similarity(
        ' '.join(case1.steps), ' '.join(case2.steps)
    )
    expected_sim = calculator.calculate_similarity(
        ' '.join(case1.expected), ' '.join(case2.expected)
    )

    # 加权综合
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
        print(f"目录 {dir_path} 中没有找到测试用例文件")
        return all_cases

    print(f"找到 {len(md_files)} 个测试用例文件")

    for md_file in md_files:
        print(f"验证: {md_file}")
        cases = validate_file(md_file, result)
        all_cases.extend(cases)

    return all_cases


def detect_duplicates(cases_with_path: List[Tuple[TestCase, str]],
                      threshold: float = 0.7,
                      use_sklearn: bool = True) -> List[DuplicatePair]:
    """
    检测重复用例

    改进：使用 TF-IDF + 余弦相似度替代 Levenshtein + Jaccard

    Args:
        cases_with_path: [(用例, 文件路径), ...]
        threshold: 相似度阈值
        use_sklearn: 是否尝试使用 sklearn

    Returns:
        重复用例对列表
    """
    calculator = SimilarityCalculator(use_sklearn=use_sklearn)
    duplicates = []

    for i in range(len(cases_with_path)):
        for j in range(i + 1, len(cases_with_path)):
            case1, file1 = cases_with_path[i]
            case2, file2 = cases_with_path[j]

            similarity, detail = calculate_case_similarity(case1, case2, calculator)

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
    # 避免 Windows 控制台 GBK 编码报错
    if sys.platform.startswith("win"):
        import os
        os.environ.setdefault("PYTHONIOENCODING", "utf-8")
    parser.add_argument("path", help="要验证的文件或目录路径")
    parser.add_argument("--check-duplicates", "-d", action="store_true",
                        help="同时检测重复用例")
    parser.add_argument("--duplicates-only", action="store_true",
                        help="仅检测重复，跳过格式验证")
    parser.add_argument("--threshold", "-t", type=float, default=0.7,
                        help="重复检测阈值 0-1 (默认 0.7)")
    parser.add_argument("--no-sklearn", action="store_true",
                        help="不使用 sklearn（使用简易词频向量）")
    args = parser.parse_args()

    path = Path(args.path)
    if not path.exists():
        print("Path not found:", path)
        sys.exit(1)

    result = ValidationResult()
    all_cases = []

    # 收集用例
    if path.is_file():
        all_cases = validate_file(path, result)
    elif path.is_dir():
        all_cases = validate_directory(path, result)
    else:
        print(f"无效的路径: {path}")
        sys.exit(1)

    # 重复检测
    check_dups = args.check_duplicates or args.duplicates_only
    if check_dups and all_cases:
        print(f"\n正在检测重复 (阈值 {args.threshold})...")
        duplicates = detect_duplicates(all_cases, args.threshold, use_sklearn=not args.no_sklearn)
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
