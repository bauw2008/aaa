import requests
from bs4 import BeautifulSoup
import json
import re
from datetime import datetime
import os

def fetch_nodes():
    url = "https://free.52it.de/"
    
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # 查找包含节点的 code 容器
        code_container = soup.find('div', class_='code-container')
        if not code_container:
            print("未找到代码容器")
            return None
            
        pre_tag = code_container.find('pre')
        code_tag = code_container.find('code')
        
        content = ""
        if pre_tag and code_tag:
            content = pre_tag.get_text() or code_tag.get_text()
        elif pre_tag:
            content = pre_tag.get_text()
        elif code_tag:
            content = code_tag.get_text()
        else:
            content = code_container.get_text()
            
        return parse_nodes(content.strip())
        
    except Exception as e:
        print(f"抓取失败: {e}")
        return None

def parse_nodes(content):
    """解析节点内容"""
    nodes = []
    lines = content.split('\n')
    
    for line in lines:
        line = line.strip()
        if not line or line.startswith('#'):
            continue
            
        # 匹配各种节点格式
        patterns = [
            # SSR 格式
            r'ss://(?P<ssr>[^@]+)@(?P<server>[^:]+):(?P<port>\d+)(?:#(?P<remark>.+))?',
            # VMess 格式
            r'vmess://(?P<vmess>[^#]+)(?:#(?P<remark>.+))?',
            # Trojan 格式
            r'trojan://(?P<trojan>[^@]+)@(?P<server>[^:]+):(?P<port>\d+)(?:\?[^#]+)?(?:#(?P<remark>.+))?',
            # SS 格式
            r'ss://(?P<ss>[^#]+)(?:#(?P<remark>.+))?'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, line)
            if match:
                node_info = {
                    'raw': line,
                    'type': get_node_type(pattern),
                    'remark': match.group('remark') if match.groupdict().get('remark') else '未命名节点'
                }
                nodes.append(node_info)
                break
        else:
            # 如果没有匹配到模式，但行包含有效内容，保存原始数据
            if line and len(line) > 10:
                nodes.append({
                    'raw': line,
                    'type': 'unknown',
                    'remark': '未知格式节点'
                })
    
    return nodes

def get_node_type(pattern):
    """根据正则模式确定节点类型"""
    type_map = {
        r'ss://(?P<ssr>[^@]+)@(?P<server>[^:]+):(?P<port>\d+)': 'ssr',
        r'vmess://(?P<vmess>[^#]+)': 'vmess',
        r'trojan://(?P<trojan>[^@]+)@(?P<server>[^:]+):(?P<port>\d+)': 'trojan',
        r'ss://(?P<ss>[^#]+)': 'ss'
    }
    return type_map.get(pattern, 'unknown')

def save_nodes(nodes):
    """保存节点数据到文件"""
    if not nodes:
        print("没有找到节点数据")
        return
        
    # 创建 nodes 目录
    os.makedirs('nodes', exist_ok=True)
    
    # 保存为 JSON
    with open('nodes/nodes.json', 'w', encoding='utf-8') as f:
        json.dump({
            'update_time': datetime.now().isoformat(),
            'total_count': len(nodes),
            'nodes': nodes
        }, f, ensure_ascii=False, indent=2)
    
    # 保存为纯文本
    with open('nodes/nodes.txt', 'w', encoding='utf-8') as f:
        f.write(f"# 节点数据更新时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"# 总节点数: {len(nodes)}\n\n")
        
        for i, node in enumerate(nodes, 1):
            f.write(f"# 节点 {i} - {node['type']} - {node['remark']}\n")
            f.write(f"{node['raw']}\n\n")
    
    # 按类型分类保存
    nodes_by_type = {}
    for node in nodes:
        node_type = node['type']
        if node_type not in nodes_by_type:
            nodes_by_type[node_type] = []
        nodes_by_type[node_type].append(node)
    
    for node_type, type_nodes in nodes_by_type.items():
        with open(f'nodes/{node_type}_nodes.txt', 'w', encoding='utf-8') as f:
            f.write(f"# {node_type.upper()} 节点列表\n")
            f.write(f"# 更新时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"# 数量: {len(type_nodes)}\n\n")
            
            for node in type_nodes:
                f.write(f"{node['raw']}\n")
    
    print(f"成功保存 {len(nodes)} 个节点数据")

def main():
    print("开始抓取节点数据...")
    nodes = fetch_nodes()
    
    if nodes:
        save_nodes(nodes)
        print("节点数据处理完成")
    else:
        print("未获取到节点数据")

if __name__ == "__main__":
    main()
