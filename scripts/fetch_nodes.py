import requests
from bs4 import BeautifulSoup
import json
import re
from datetime import datetime
import os
import base64
import urllib.parse
import time
import random

def fetch_nodes():
    """
    从网站获取节点数据，使用更强大的反反爬虫策略
    """
    url = "https://free.52it.de/"
    
    # 更完整的浏览器头信息
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
        'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
        'Accept-Encoding': 'gzip, deflate, br',
        'Cache-Control': 'no-cache',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
        'Sec-Fetch-Dest': 'document',
        'Sec-Fetch-Mode': 'navigate',
        'Sec-Fetch-Site': 'none',
        'Sec-Fetch-User': '?1',
        'Pragma': 'no-cache',
        'sec-ch-ua': '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"Windows"',
        'DNT': '1',
    }
    
    try:
        print("尝试从网站抓取节点数据...")
        
        # 使用 Session 保持会话
        session = requests.Session()
        session.headers.update(headers)
        
        # 添加随机延迟，模拟人类行为
        time.sleep(random.uniform(1, 3))
        
        # 尝试直接访问
        response = session.get(url, timeout=30)
        print(f"响应状态码: {response.status_code}")
        
        if response.status_code == 403:
            print("检测到 Cloudflare 保护，尝试其他方法...")
            return try_alternative_methods(url)
            
        response.raise_for_status()
        
        # 解析HTML内容
        return parse_html_content(response.text)
            
    except Exception as e:
        print(f"抓取失败: {e}")
        return []

def try_alternative_methods(url):
    """
    尝试其他方法来绕过 Cloudflare
    """
    methods = [
        try_with_different_user_agents,
        try_with_proxy,
        try_with_cloudscraper
    ]
    
    for method in methods:
        try:
            print(f"尝试方法: {method.__name__}")
            nodes = method(url)
            if nodes:
                print(f"方法 {method.__name__} 成功!")
                return nodes
        except Exception as e:
            print(f"方法 {method.__name__} 失败: {e}")
            continue
    
    print("所有方法都失败了")
    return []

def try_with_different_user_agents(url):
    """使用不同的 User-Agent"""
    user_agents = [
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/121.0',
    ]
    
    for ua in user_agents:
        try:
            headers = {'User-Agent': ua}
            response = requests.get(url, headers=headers, timeout=30)
            if response.status_code == 200:
                return parse_html_content(response.text)
            time.sleep(random.uniform(1, 2))
        except:
            continue
    
    return []

def try_with_proxy(url):
    """尝试使用代理（在 GitHub Actions 中可能不可用）"""
    # 在 GitHub Actions 环境中，代理通常不可用
    # 这里只是占位，实际可能无法工作
    return []

def try_with_cloudscraper(url):
    """尝试使用 cloudscraper 库（需要安装）"""
    try:
        import cloudscraper
        scraper = cloudscraper.create_scraper()
        response = scraper.get(url)
        if response.status_code == 200:
            return parse_html_content(response.text)
    except ImportError:
        print("cloudscraper 未安装，跳过此方法")
    except Exception as e:
        print(f"cloudscraper 失败: {e}")
    
    return []

def parse_html_content(html_content):
    """解析HTML内容提取节点"""
    soup = BeautifulSoup(html_content, 'html.parser')
    
    # 查找包含节点的 code 容器
    code_container = soup.find('div', class_='code-container')
    if not code_container:
        print("未找到代码容器")
        return []
    
    # 查找 pre 和 code 标签
    code_tag = code_container.find('code')
    if code_tag:
        content = code_tag.get_text().strip()
        print(f"找到代码内容，长度: {len(content)}")
        nodes = parse_nodes(content)
        print(f"解析出 {len(nodes)} 个节点")
        return nodes
    else:
        print("未找到代码标签")
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
        # 解码HTML实体
        line = line.replace('&amp;', '&')
        
        if line.startswith('vless://'):
            return parse_vless_node(line)
        elif line.startswith('vmess://'):
            return parse_vmess_node(line)
        elif line.startswith('ss://'):
            return parse_ss_node(line)
        elif line.startswith('trojan://'):
            return parse_trojan_node(line)
        else:
            return {
                'raw': line,
                'type': 'unknown',
                'remark': '未知格式节点'
            }
    except Exception as e:
        print(f"解析节点失败: {e}")
        return None

def parse_vless_node(line):
    """解析VLess节点"""
    try:
        content = line[8:]  # 移除协议头
        
        # 分割主要部分和参数
        parts = content.split('?', 1)
        main_part = parts[0]
        params_part = parts[1] if len(parts) > 1 else ''
        
        # 解析主要部分
        uuid_part, server_part = main_part.split('@', 1)
        server, port = server_part.split(':', 1)
        
        # 获取备注
        remark = 'VLess节点'
        if '#' in params_part:
            params_part, remark_part = params_part.split('#', 1)
            remark = urllib.parse.unquote(remark_part)
        
        return {
            'raw': line,
            'type': 'vless',
            'server': server,
            'port': int(port),
            'uuid': uuid_part,
            'remark': remark
        }
    except Exception as e:
        print(f"解析VLess节点失败: {e}")
        return {
            'raw': line,
            'type': 'vless',
            'remark': 'VLess节点'
        }

def parse_vmess_node(line):
    """解析VMess节点"""
    try:
        encoded_content = line[8:]
        padding = 4 - len(encoded_content) % 4
        if padding != 4:
            encoded_content += '=' * padding
        
        decoded_content = base64.b64decode(encoded_content).decode('utf-8')
        config = json.loads(decoded_content)
        
        remark = config.get('ps', 'VMess节点')
        
        return {
            'raw': line,
            'type': 'vmess',
            'server': config.get('add', ''),
            'port': config.get('port', 0),
            'uuid': config.get('id', ''),
            'remark': remark
        }
    except Exception as e:
        print(f"解析VMess节点失败: {e}")
        return {
            'raw': line,
            'type': 'vmess',
            'remark': 'VMess节点'
        }

def parse_ss_node(line):
    """解析SS节点"""
    try:
        content = line[5:]
        
        if '#' in content:
            main_part, remark = content.split('#', 1)
            remark = urllib.parse.unquote(remark)
        else:
            main_part = content
            remark = 'SS节点'
        
        if '@' in main_part:
            auth_part, server_part = main_part.split('@', 1)
            server, port = server_part.split(':', 1)
            
            padding = 4 - len(auth_part) % 4
            if padding != 4:
                auth_part += '=' * padding
            
            try:
                decoded_auth = base64.b64decode(auth_part).decode('utf-8')
                method, password = decoded_auth.split(':', 1)
            except:
                method, password = 'unknown', 'unknown'
        else:
            method, password, server, port = 'unknown', 'unknown', 'unknown', '0'
        
        return {
            'raw': line,
            'type': 'ss',
            'server': server,
            'port': int(port),
            'method': method,
            'password': password,
            'remark': remark
        }
    except Exception as e:
        print(f"解析SS节点失败: {e}")
        return {
            'raw': line,
            'type': 'ss',
            'remark': 'SS节点'
        }

def parse_trojan_node(line):
    """解析Trojan节点"""
    try:
        content = line[9:]
        parts = content.split('?', 1)
        main_part = parts[0]
        params_part = parts[1] if len(parts) > 1 else ''
        
        password, server_part = main_part.split('@', 1)
        server, port = server_part.split(':', 1)
        
        remark = 'Trojan节点'
        if '#' in params_part:
            params_part, remark_part = params_part.split('#', 1)
            remark = urllib.parse.unquote(remark_part)
        
        return {
            'raw': line,
            'type': 'trojan',
            'server': server,
            'port': int(port),
            'password': password,
            'remark': remark
        }
    except Exception as e:
        print(f"解析Trojan节点失败: {e}")
        return {
            'raw': line,
            'type': 'trojan',
            'remark': 'Trojan节点'
        }

def save_nodes(nodes):
    """保存节点数据到文件"""
    if not nodes:
        print("没有找到节点数据")
        return
        
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
    
    # 生成订阅文件
    generate_subscription_files(nodes)
    
    print(f"成功保存 {len(nodes)} 个节点数据")

def generate_subscription_files(nodes):
    """生成订阅链接文件"""
    with open('nodes/subscription.txt', 'w', encoding='utf-8') as f:
        for node in nodes:
            f.write(f"{node['raw']}\n")
    
    nodes_by_type = {}
    for node in nodes:
        node_type = node['type']
        if node_type not in nodes_by_type:
            nodes_by_type[node_type] = []
        nodes_by_type[node_type].append(node)
    
    for node_type, type_nodes in nodes_by_type.items():
        with open(f'nodes/{node_type}_subscription.txt', 'w', encoding='utf-8') as f:
            for node in type_nodes:
                f.write(f"{node['raw']}\n")

def main():
    print("开始抓取节点数据...")
    nodes = fetch_nodes()
    
    if nodes:
        save_nodes(nodes)
        print(f"节点数据处理完成，共 {len(nodes)} 个节点")
        
        type_count = {}
        for node in nodes:
            node_type = node['type']
            type_count[node_type] = type_count.get(node_type, 0) + 1
        
        print("节点类型统计:")
        for node_type, count in type_count.items():
            print(f"  {node_type}: {count} 个")
    else:
        print("未获取到节点数据")

if __name__ == "__main__":
    main()
