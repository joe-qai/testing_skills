# -*- coding: utf-8 -*-
"""
测试用例转XMind思维导图生成脚本
功能：将测试用例转换为XMind格式的思维导图文件
"""

import json
import zipfile
import uuid
import os
import re

# 生成唯一ID
def generate_id():
    return str(uuid.uuid4())

# 创建节点（带class标识）
def create_node(title, children=None, node_class="topic"):
    node = {
        "id": generate_id(),
        "class": node_class,
        "title": title,
        "structureClass": "org.xmind.ui.map.unbalanced"
    }
    if children:
        node["children"] = {"attached": children}
    return node

# 处理带序号的内容，将数字序号替换为换行+序号
def format_numbered_content(content):
    """将 '1. xxx 2. xxx' 格式的内容转换为 '1. xxx\n2. xxx'"""
    import re
    # 匹配数字+点+空格的模式，在其前面添加换行（除了第一个）
    # 先标准化空格
    content = re.sub(r'(\d+)\.\s+', r'\1. ', content)
    # 在序号前添加换行
    content = re.sub(r'(?<!^)(?<!\n)(\d+)\. ', r'\n\1. ', content)
    return content.strip()

# 创建测试用例节点（层级：测试标题 -> 前置条件 -> 操作步骤 -> 预期结果 -> 优先级）
def create_test_case_node(title, pre_condition, steps, expected, priority):
    # 处理带序号的内容
    formatted_steps = format_numbered_content(steps)
    formatted_expected = format_numbered_content(expected)
    
    priority_node = create_node(priority, None, "priority")
    expected_node = create_node(formatted_expected, [priority_node], "expected")
    steps_node = create_node(formatted_steps, [expected_node], "steps")
    precond_node = create_node(pre_condition, [steps_node], "precondition")
    return create_node(title, [precond_node], "testcase")

# 创建测试点节点
def create_test_point_node(title, test_cases):
    return create_node(title, test_cases, "testpoint")

# 创建测试项节点
def create_test_item_node(title, test_points):
    return create_node(title, test_points, "testitem")

# 创建固定表头节点（作为第一条数据展示字段结构）
def create_header_item_node():
    """创建表头节点，展示字段结构：模块、测试点、测试标题、前置条件、操作步骤、预期结果、优先级"""
    # 优先级
    priority_node = create_node("优先级", None, "priority")
    # 预期结果
    expected_node = create_node("预期结果", [priority_node], "expected")
    # 操作步骤
    steps_node = create_node("操作步骤", [expected_node], "steps")
    # 前置条件
    precond_node = create_node("前置条件", [steps_node], "precondition")
    # 测试标题
    testcase_node = create_node("测试标题", [precond_node], "testcase")
    # 测试点
    testpoint_node = create_node("测试点", [testcase_node], "testpoint")
    # 模块（表头整体）
    return create_test_item_node("模块名称", [testpoint_node])

# 解析单个Markdown测试用例文件
def parse_testcase_file(filepath):
    """
    解析单个测试用例Markdown文件
    返回: [(priority, title, test_type, precondition, steps, expected), ...]
    """
    cases = []
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 匹配测试用例格式
    # ## [P1] 标题
    # [测试类型] xxx
    # [前置条件] xxx
    # [测试步骤] xxx
    # [预期结果] xxx
    pattern = r'##\s*\[(P\d+)\]\s*(.+?)\n\[测试类型\]\s*(.+?)\n\[前置条件\]\s*(.+?)\n\[测试步骤\]\s*(.+?)\n\[预期结果\]\s*(.+?)(?=\n##|\Z)'
    matches = re.findall(pattern, content, re.DOTALL)
    
    for match in matches:
        priority, title, test_type, precondition, steps, expected = match
        cases.append({
            'priority': priority.strip(),
            'title': title.strip(),
            'type': test_type.strip(),
            'precondition': precondition.strip(),
            'steps': steps.strip(),
            'expected': expected.strip()
        })
    
    return cases

# 从目录读取所有测试用例
def parse_testcase_directory(testcase_dir):
    """
    遍历测试用例目录，读取所有Markdown文件
    返回: [{'title': 模块名, 'points': [{'title': 测试点名, 'cases': [...]}, ...]}, ...]
    """
    test_items = []
    
    if not os.path.exists(testcase_dir):
        print(f"错误: 目录不存在 {testcase_dir}")
        return test_items
    
    # 遍历目录下的所有子目录（模块）
    for item_name in sorted(os.listdir(testcase_dir)):
        item_path = os.path.join(testcase_dir, item_name)
        
        # 跳过文件，只处理目录
        if not os.path.isdir(item_path):
            continue
        
        # 这是一个测试项（模块）
        test_item = {
            'title': item_name,
            'points': []
        }
        
        # 遍历模块下的所有Markdown文件（测试点）
        for point_file in sorted(os.listdir(item_path)):
            if not point_file.endswith('.md'):
                continue
            
            point_name = point_file.replace('.md', '')
            filepath = os.path.join(item_path, point_file)
            
            # 解析测试用例
            cases = parse_testcase_file(filepath)
            
            if cases:
                test_item['points'].append({
                    'title': point_name,
                    'cases': cases
                })
                print(f"  解析: {item_name}/{point_name} - {len(cases)} 个用例")
        
        if test_item['points']:
            test_items.append(test_item)
            print(f"✅ 模块: {item_name} - {len(test_item['points'])} 个测试点")
    
    return test_items

# 主函数：生成XMind文件
def generate_xmind_file(test_data, output_path, title="测试用例"):
    """
    生成XMind文件
    
    Args:
        test_data: 测试数据列表 [{'title': ..., 'points': [...]}, ...]
        output_path: 输出文件路径
        title: 思维导图标题
    """
    root_id = generate_id()
    sheet_id = generate_id()
    
    # 构建测试项列表
    test_items = []
    for item in test_data:
        test_points = []
        for point in item['points']:
            test_cases = []
            for case in point['cases']:
                test_cases.append(create_test_case_node(
                    case['title'],
                    case['precondition'],
                    case['steps'],
                    case['expected'],
                    case['priority']
                ))
            test_points.append(create_test_point_node(point['title'], test_cases))
        test_items.append(create_test_item_node(item['title'], test_points))
    
    # 插入表头节点作为第一条数据
    header_node = create_header_item_node()
    test_items.insert(0, header_node)
    
    # 构建根节点
    root_topic = {
        "id": root_id,
        "class": "topic",
        "title": title,
        "structureClass": "org.xmind.ui.map.unbalanced",
        "children": {
            "attached": test_items
        }
    }
    
    # 构建sheet
    sheet = {
        "id": sheet_id,
        "class": "sheet",
        "title": title,
        "rootTopic": root_topic
    }
    
    # 构建content.json
    content = [sheet]
    
    # 创建metadata.json
    metadata = {
        "creator": {
            "name": "iFlow CLI",
            "version": "1.0.0"
        },
        "activeSheetId": sheet_id
    }
    
    # 创建manifest.json
    manifest = {
        "file-entries": [
            {
                "path": "content.json",
                "media-type": "application/json"
            },
            {
                "path": "metadata.json",
                "media-type": "application/json"
            },
            {
                "path": "manifest.json",
                "media-type": "application/json"
            }
        ]
    }
    
    # 创建xmind文件
    with zipfile.ZipFile(output_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        # 写入content.json
        zipf.writestr('content.json', json.dumps(content, ensure_ascii=False, indent=2))
        
        # 写入metadata.json
        zipf.writestr('metadata.json', json.dumps(metadata, ensure_ascii=False, indent=2))
        
        # 写入manifest.json
        zipf.writestr('manifest.json', json.dumps(manifest, ensure_ascii=False, indent=2))
        
        # 创建空Thumbnails目录
        zipf.writestr('Thumbnails/.placeholder', '')
    
    print(f"XMind文件已成功生成: {output_path}")
    print(f"包含 {len(content)} 个sheet")
    print(f"根节点: {root_topic['title']}")
    print(f"测试项数量: {len(root_topic['children']['attached'])}")
    
    # 统计测试用例总数
    total_cases = 0
    for item in test_items:
        for point in item['children']['attached']:
            total_cases += len(point['children']['attached'])
    print(f"总测试用例数: {total_cases}")

# 命令行入口
if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='将测试用例目录转换为XMind思维导图')
    parser.add_argument('testcase_dir',default=r"C:\pythonworkspace\openclaw\test-case", help='测试用例目录路径')
    parser.add_argument('-o', '--output', default='testcase.xmind', help='输出XMind文件路径')
    parser.add_argument('-t', '--title', default='测试用例', help='思维导图标题')
    
    args = parser.parse_args()
    
    print(f"开始解析测试用例目录: {args.testcase_dir}")
    
    # 解析目录获取测试数据
    test_data = parse_testcase_directory(args.testcase_dir)
    
    if not test_data:
        print("错误: 未找到任何测试用例")
        exit(1)
    
    print(f"\n共解析 {len(test_data)} 个模块")
    
    # 生成XMind文件
    generate_xmind_file(test_data, args.output, args.title)
    print(f"\n✅ XMind文件已生成: {args.output}")

# 保持向后兼容的示例调用
elif __name__ == "__example__":
    # 示例数据（直接调用时使用）
    test_data = [
        {
            "title": "数字键功能",
            "points": [
                {
                    "title": "密码输入",
                    "cases": [
                        {
                            "title": "输入正确密码成功开锁",
                            "precondition": "设备已开机，门锁已设置密码123456",
                            "steps": "1、触摸数字键区域\n2、输入密码123456\n3、输入完成后等待系统响应",
                            "expected": "1、数字键亮白光\n2、密码输入正常显示\n3、门锁成功开启，锁体转动",
                            "priority": "P0"
                        }
                    ]
                }
            ]
        }
    ]
    
    output_path = r"C:\pythonworkspace\openclaw\示例测试用例.xmind"
    generate_xmind_file(test_data, output_path, "示例测试用例")