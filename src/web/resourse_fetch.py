'''
根据llm输出获取相关推荐资源
'''
#代码需要和gradio端口配套实现
def search_semantic_scholar(query):
    if not query or query.isspace(): return "请输入有效关键词进行文献搜索。"
    cache = search_cache["Semantic Scholar"]
    if query in cache: print(f"命中缓存 (Semantic Scholar): {query}"); return cache[query]
    enforce_rate_limit()
    print(f"执行新查询 (Semantic Scholar): {query}")
    headers = {}; api_key = user_api_config.get('semantic_scholar_api_key')
    if api_key: headers['x-api-key'] = api_key
    url = f"https://api.semanticscholar.org/graph/v1/paper/search?query={query}&limit=5&fields=title,authors,year,url"
    try:
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()
        data = response.json(); papers = data.get("data", [])
        if not papers: result_str = "未找到相关文献。"
        else: results = [f"📘 **{p['title']}** ({p['year']})\n*👥 {', '.join([a['name'] for a in p['authors']])}*\n🔗 [链接]({p['url']})" for p in papers]; result_str = "\n\n".join(results)
        cache[query] = result_str; return result_str
    except requests.exceptions.RequestException as e:
        if e.response and e.response.status_code == 429: return "[Semantic Scholar 请求过于频繁] 已触发API速率限制，请等待几分钟或更换搜索引擎。"
        return f"[Semantic Scholar 请求失败] 网络错误: {str(e)}"
    except Exception as e: return f"[Semantic Scholar 未知错误] {str(e)}"

def search_google_scholar(query):
    if not query or query.isspace(): return "请输入有效关键词进行文献搜索。"
    cache = search_cache["Google Scholar"]
    if query in cache: print(f"命中缓存 (Google Scholar): {query}"); return cache[query]
    enforce_rate_limit(min_interval=10)
    print(f"执行新查询 (Google Scholar): {query}")
    try:
        search_query = scholarly.search_pubs(query)
        results = []
        for i, pub in enumerate(search_query):
            if i >= 5: break
            title = pub.get('bib', {}).get('title', 'N/A'); authors = ', '.join(pub.get('bib', {}).get('author', ['N/A'])); year = pub.get('bib', {}).get('pub_year', 'N/A'); url = pub.get('pub_url', '#')
            results.append(f"📗 **{title}** ({year})\n*👥 {authors}*\n🔗 [链接]({url})")
        if not results: result_str = "未找到相关文献。"
        else: result_str = "\n\n".join(results)
        cache[query] = result_str; return result_str
    except Exception as e: return f"[Google Scholar 请求失败] 可能是由于网络问题或被Google暂时屏蔽。请稍后重试或切换搜索引擎。错误: {str(e)}"
