import requests
import re
from typing import List, Tuple

# 定义输入链接和输出文件
INPUT_URLS = [
    #"https://raw.githubusercontent.com/pdd520/iptv-api/refs/heads/master/output/result.m3u"
    "https://raw.githubusercontent.com/suxuang/myIPTV/refs/heads/main/ipv4.m3u"
]
OUTPUT_FILE = "emerged_output.m3u"
# 验证链接时的超时设置 (秒)
TIMEOUT = 5

# 正则表达式用于匹配 M3U 中的 EXTINF 行及其紧随的 URL
# (.+?) 匹配 EXTINF 信息
# (http.+?) 匹配 http/https 开头的 URL，这是我们主要关注的播放源格式
M3U_PATTERN = re.compile(r'(#EXTINF:.*?\n)(http.*?)(?=\n#EXTINF|\n#EXTM3U|\Z)', re.DOTALL | re.IGNORECASE)


def download_and_extract(url: str) -> List[Tuple[str, str]]:
    """
    下载 M3U 内容并提取 EXTINF 信息和 URL。
    返回一个 (EXTINF_info, URL) 元组的列表。
    """
    print(f"\n📥 正在下载和解析: {url}")
    extracted_sources = []
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status() # 检查 HTTP 错误

        content = response.text
        
        # 使用正则表达式查找所有匹配项
        matches = M3U_PATTERN.findall(content)
        
        for extinf_info, source_url in matches:
            # 清理 URL，去除可能的空白字符
            source_url = source_url.strip()
            # EXTINF 信息的格式清理
            extinf_info = extinf_info.strip()
            
            if source_url.startswith("http"):
                extracted_sources.append((extinf_info, source_url))

        print(f"✅ 提取到 {len(extracted_sources)} 个潜在播放源。")
        
    except requests.exceptions.RequestException as e:
        print(f"❌ 下载或解析失败 {url}: {e}")

    return extracted_sources

def check_url_status(url: str) -> bool:
    """
    测试 IPTV 播放源是否可用。
    """
    # 部分播放源可能需要更像浏览器的 User-Agent
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
    try:
        # 使用 GET 请求并设置 stream=True，只下载头部信息和少量数据，更快
        response = requests.get(url, headers=headers, stream=True, timeout=TIMEOUT)
        
        # 检查状态码是否成功 (200-299)
        if 200 <= response.status_code < 300:
            return True
        else:
            print(f"    - HTTP Error {response.status_code}")
            return False
            
    except requests.exceptions.RequestException as e:
        # print(f"    - 错误: {e}")
        return False
        
def main():
    all_sources = []
    valid_sources = []
    
    # 1. 下载并提取所有源
    for url in INPUT_URLS:
        all_sources.extend(download_and_extract(url))

    if not all_sources:
        print("🤷 未找到任何播放源，退出。")
        return

    print(f"\n💡 总共发现 {len(all_sources)} 个源，开始验证...")
    
    # 2. 验证播放源
    # 使用 set 来存储验证通过的 URL，防止重复
    validated_urls = set()
    
    for i, (info, url) in enumerate(all_sources):
        # 进度显示 (只显示百分比)
        if (i + 1) % 50 == 0 or (i + 1) == len(all_sources):
             print(f"    ... 已验证 {i + 1}/{len(all_sources)} 个源 ({((i + 1) / len(all_sources) * 100):.1f}%)")

        # 跳过已验证过的链接，提高效率
        if url in validated_urls:
            continue
            
        if check_url_status(url):
            valid_sources.append((info, url))
            validated_urls.add(url) # 标记为已验证
            
    # 3. 合并输出
    print(f"\n🎉 验证完成! 找到 {len(valid_sources)} 个可用且不重复的播放源。")
    
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        f.write("#EXTM3U\n")
        for info, url in valid_sources:
            # 写入 EXTINF 信息
            f.write(info + "\n") 
            # 写入播放源 URL
            f.write(url + "\n")

    print(f"✨ 可用源已成功写入 {OUTPUT_FILE}")

if __name__ == "__main__":
    main()
