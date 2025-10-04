import requests
from bs4 import BeautifulSoup
import json
import base64
import urllib.parse
import time
import random
from datetime import datetime
import os

def fetch_nodes():
    """
    从网站获取节点数据
    """
    url = "https://free.52it.de/"
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    }
    
    try:
        session = requests.Session()
        session.headers.update(headers)
        
        time.sleep(random.uniform(1, 3))
        
        response = session.get(url, timeout=30)
        
        if response.status_code == 403:
            return try_alternative_methods(url)
            
        response.raise_for_status()
        return parse_html_content(response.text)
            
    except Exception:
        return []

def try_alternative_methods(url):
    """尝试其他方法"""
    methods = [try_with_different_user_agents, try_with_cloudscraper]
    
    for method in methods:
        try:
            nodes = method(url)
            if nodes:
                return nodes
        except:
            continue
    
    return []

def try_with_different_user_agents(url):
    """使用不同的 User-Agent"""
    user_agents = [
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    ]
    
    for ua in user_agents:
        try:
            headers = {'User-Agent': ua}
            response = requests.get(url, headers=headers, timeout=30)
            if response.status_code == 200:
                return parse_html_content(response.text)
        except:
            continue
    
    return []

def try_with_cloudscraper(url):
    """尝试使用 cloudscraper 库"""
    try:
        import cloudscraper
        scraper = cloudscraper.create_scraper()
        response = scraper.get(url)
        if response.status_code == 200:
            return parse_html_content(response.text)
    except:
        pass
    
    return []

def parse_html_content(html_content):
    """解析HTML内容提取节点"""
    soup = BeautifulSoup(html_content, 'html.parser')
    
    code_container = soup.find('div', class_='code-container')
    if not code_container:
        return []
    
    code_tag = code_container.find('code')
    if code_tag:
        content = code_tag.get_text().strip()
        return parse_nodes(content)
    
    return []

def parse_nodes(content):
    """解析节点内容"""
    nodes = []
    lines = content.split('\n')
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
            
        node_info = parse_node_line(line)
        if node_info:
            nodes.append(node_info)
    
    return nodes

def parse_node_line(line):
    """解析单行节点数据"""
    try:
        line = line.replace('&amp;', '&')
        
        if line.startswith('vless://'):
            return {'raw': line, 'type': 'vless'}
        elif line.startswith('vmess://'):
            return {'raw': line, 'type': 'vmess'}
        elif line.startswith('ss://'):
            return {'raw': line, 'type': 'ss'}
        elif line.startswith('trojan://'):
            return {'raw': line, 'type': 'trojan'}
        else:
            return {'raw': line, 'type': 'unknown'}
    except:
        return None

def save_nodes(nodes):
    """保存节点数据到文件"""
    if not nodes:
        return
        
    os.makedirs('nodes', exist_ok=True)
    
    # 保存为 JSON
    with open('nodes/nodes.json', 'w', encoding='utf-8') as f:
        json.dump({
            'update_time': datetime.now().isoformat(),
            'total_count': len(nodes),
            'nodes': nodes
        }, f, ensure_ascii=False, indent=2)
    
    # 生成所有节点的 Base64 订阅文件（唯一用于订阅的文件）
    node_links = [node['raw'] for node in nodes]
    subscription_content = '\n'.join(node_links)
    base64_content = base64.b64encode(subscription_content.encode('utf-8')).decode('utf-8')
    
    with open('nodes/subscription_base64.txt', 'w', encoding='utf-8') as f:
        f.write(base64_content)
    
    # 按类型分类保存（仅用于查看）
    nodes_by_type = {}
    for node in nodes:
        node_type = node['type']
        if node_type not in nodes_by_type:
            nodes_by_type[node_type] = []
        nodes_by_type[node_type].append(node)
    
    for node_type, type_nodes in nodes_by_type.items():
        with open(f'nodes/{node_type}_nodes.txt', 'w', encoding='utf-8') as f:
            for node in type_nodes:
                f.write(f"{node['raw']}\n")

def main():
    nodes = fetch_nodes()
    if nodes:
        save_nodes(nodes)

if __name__ == "__main__":
    main()
