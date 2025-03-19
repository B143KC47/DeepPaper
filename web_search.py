import requests
from urllib.parse import quote_plus
import re
import time
from bs4 import BeautifulSoup

def search_for_references(query, max_results=5):
    """搜索相关参考资料
    
    Args:
        query: 搜索查询词，通常是论文标题
        max_results: 最大结果数量
        
    Returns:
        包含参考资料描述的列表
    """
    try:
        # 尝试使用Google Scholar进行学术搜索
        results = search_google_scholar(query, max_results)
        
        # 如果Google Scholar搜索失败或结果太少，使用一般搜索引擎
        if not results or len(results) < 2:
            results.extend(search_general(query, max_results - len(results)))
            
        return results
    except Exception as e:
        print(f"网络搜索出错: {str(e)}")
        return [f"搜索参考资料时出错: {str(e)}"]

def search_google_scholar(query, max_results=5):
    """从Google Scholar搜索学术参考资料
    
    Args:
        query: 搜索查询词
        max_results: 最大结果数量
        
    Returns:
        搜索结果列表
    """
    try:
        # 注意：实际部署时，应考虑使用代理或API服务，因为Google可能会封锁频繁的搜索请求
        encoded_query = quote_plus(query)
        url = f"https://scholar.google.com/scholar?q={encoded_query}&hl=zh-CN"
        
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8"
        }
        
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code != 200:
            return []
        
        # 使用BeautifulSoup解析结果
        soup = BeautifulSoup(response.text, 'html.parser')
        results = []
        
        # 查找论文条目
        entries = soup.select('.gs_ri')
        for entry in entries[:max_results]:
            title_elem = entry.select_one('.gs_rt')
            authors_elem = entry.select_one('.gs_a')
            desc_elem = entry.select_one('.gs_rs')
            
            title = title_elem.text.strip() if title_elem else "无标题"
            authors = authors_elem.text.strip() if authors_elem else "未知作者"
            desc = desc_elem.text.strip() if desc_elem else ""
            
            # 清理HTML标签
            title = re.sub(r'<[^>]+>', '', title)
            
            # 格式化为参考信息
            ref_info = f"{title} - {authors}"
            if desc:
                ref_info += f"\n摘要: {desc}"
                
            results.append(ref_info)
            
        return results
            
    except Exception as e:
        print(f"Google Scholar搜索失败: {str(e)}")
        return []

def search_general(query, max_results=5):
    """从一般搜索引擎搜索相关信息
    
    Args:
        query: 搜索查询词
        max_results: 最大结果数量
        
    Returns:
        搜索结果列表
    """
    # 这里使用模拟搜索结果，实际部署时应替换为真实的搜索API调用
    # 例如可以使用Bing Search API, SerpAPI等服务
    
    # 为了演示，返回一些模拟结果
    time.sleep(1)  # 模拟网络延迟
    
    return [
        f"相关参考: '{query}' 的研究进展与应用 - 学术期刊网",
        f"'{query}' 领域的最新研究综述 - 中国知网",
        f"国际上关于 '{query}' 的研究现状分析 - ResearchGate",
        f"'{query}' 相关技术的产业化应用案例 - 科技创新网"
    ][:max_results]

def extract_key_terms(text, max_terms=3):
    """从文本中提取关键术语，用于改进搜索
    
    Args:
        text: 输入文本
        max_terms: 最大术语数量
        
    Returns:
        关键术语列表
    """
    # 这是一个简化的实现，实际应用中可以使用NLP库如jieba进行更准确的提取
    # 移除常见的停用词和标点符号
    stop_words = ['的', '了', '和', '与', '或', '及', '在', '是', '我们', '他们', '这个', '那个', 'the', 'a', 'an', 'in', 'on', 'at', 'for', 'with']
    cleaned_text = re.sub(r'[^\w\s]', ' ', text)
    words = cleaned_text.split()
    
    # 过滤掉停用词和过短的词
    filtered_words = [w for w in words if w.lower() not in stop_words and len(w) > 1]
    
    # 简单计算词频
    word_freq = {}
    for word in filtered_words:
        word_freq[word] = word_freq.get(word, 0) + 1
    
    # 按频率排序取前N个
    sorted_words = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)
    key_terms = [word for word, freq in sorted_words[:max_terms]]
    
    return key_terms