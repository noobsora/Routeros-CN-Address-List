import requests
import ipaddress
from pathlib import Path
import re
import sys
from typing import Set, List, Tuple
from concurrent.futures import ThreadPoolExecutor, as_completed

# 数据源地址
IPV4_SCRIPT_URL = "http://www.iwik.org/ipcountry/mikrotik/CN"
IPV6_SCRIPT_URL = "http://www.iwik.org/ipcountry/mikrotik_ipv6/CN"
IPV4_PLAIN_URL = "https://raw.githubusercontent.com/gaoyifan/china-operator-ip/refs/heads/ip-lists/china.txt"
IPV6_PLAIN_URL = "https://raw.githubusercontent.com/gaoyifan/china-operator-ip/refs/heads/ip-lists/china6.txt"

OUTPUT_PATH = Path("output/CN_v2")
OUTPUT_RSC = Path("output/CN_v2.rsc")


def fetch_text(url: str, retries: int = 3) -> str:
    """从指定 URL 获取文本数据，带简单重试"""
    for attempt in range(1, retries + 1):
        try:
            resp = requests.get(url, timeout=30)
            resp.raise_for_status()
            return resp.text.strip()
        except Exception as e:
            print(f"⚠️ [错误] 第 {attempt} 次尝试获取 {url} 失败：{e}", file=sys.stderr)
    return ""


def parse_script_style_ips(text: str) -> Set[str]:
    """提取 script 风格的地址段"""
    pattern = re.compile(r'address=([\da-fA-F:/\.]+)')
    return {m.group(1) for line in text.splitlines() if (m := pattern.search(line))}


def parse_plain_ips(text: str) -> Set[str]:
    """提取纯文本格式的地址段"""
    return {line.strip() for line in text.splitlines() if line.strip() and not line.startswith("#")}


def normalize_networks(
    ipv4_strs: Set[str],
    ipv6_strs: Set[str]
) -> Tuple[List[ipaddress.IPv4Network], List[ipaddress.IPv6Network]]:
    """将字符串地址段转换为 IP 网络对象，并按版本分类"""
    ipv4, ipv6 = [], []
    for s in ipv4_strs:
        try:
            ipv4.append(ipaddress.ip_network(s, strict=False))
        except ValueError:
            print(f"⚠️ [跳过] 非法 IPv4 地址段：{s}", file=sys.stderr)
    for s in ipv6_strs:
        try:
            ipv6.append(ipaddress.ip_network(s, strict=False))
        except ValueError:
            print(f"⚠️ [跳过] 非法 IPv6 地址段：{s}", file=sys.stderr)
    return ipv4, ipv6


def merge_and_format(networks: List[ipaddress._BaseNetwork], is_ipv6: bool = False) -> Tuple[List[str], int]:
    """合并地址段并生成 RouterOS 脚本格式，返回(完整规则, 地址数)"""
    header = [
        f'/log info "Loading CN {"ipv6" if is_ipv6 else "ipv4"} address list"',
        f'/{ "ipv6" if is_ipv6 else "ip"} firewall address-list remove [/{ "ipv6" if is_ipv6 else "ip"} firewall address-list find list=CN]',
        f'/{ "ipv6" if is_ipv6 else "ip"} firewall address-list'
    ]
    collapsed = sorted(ipaddress.collapse_addresses(networks), key=lambda net: (int(net.network_address), net.prefixlen))
    rules = [f':do {{ add address={net.with_prefixlen} list=CN }} on-error={{}}' for net in collapsed]
    return header + rules, len(rules)


def main() -> None:
    print("📥 正在并发抓取 IP 数据源...")

    urls = {
        "ipv4_script": IPV4_SCRIPT_URL,
        "ipv6_script": IPV6_SCRIPT_URL,
        "ipv4_plain": IPV4_PLAIN_URL,
        "ipv6_plain": IPV6_PLAIN_URL,
    }

    results = {}

    # 并发抓取
    with ThreadPoolExecutor(max_workers=4) as executor:
        future_to_key = {executor.submit(fetch_text, url): key for key, url in urls.items()}
        for future in as_completed(future_to_key):
            key = future_to_key[future]
            results[key] = future.result()

    print("📦 正在解析原始地址段...")
    ipv4_strs = parse_script_style_ips(results["ipv4_script"]) | parse_plain_ips(results["ipv4_plain"])
    ipv6_strs = parse_script_style_ips(results["ipv6_script"]) | parse_plain_ips(results["ipv6_plain"])

    print(f"🔢 原始 IPv4 条目数：{len(ipv4_strs)}")
    print(f"🔢 原始 IPv6 条目数：{len(ipv6_strs)}")

    if not ipv4_strs and not ipv6_strs:
        print("❌ 没有获取到任何有效的 IP 地址段，已退出。", file=sys.stderr)
        sys.exit(1)

    ipv4_nets, ipv6_nets = normalize_networks(ipv4_strs, ipv6_strs)

    merged_ipv4, count_ipv4 = merge_and_format(ipv4_nets, is_ipv6=False)
    merged_ipv6, count_ipv6 = merge_and_format(ipv6_nets, is_ipv6=True)

    print(f"✅ 合并后 IPv4 条目数：{count_ipv4}")
    print(f"✅ 合并后 IPv6 条目数：{count_ipv6}")

    final_output = "\n".join(merged_ipv4 + [""] + merged_ipv6)

    output_dir = Path("output")
    output_dir.mkdir(exist_ok=True)

    OUTPUT_PATH.write_text(final_output, encoding="utf-8")
    OUTPUT_RSC.write_text(final_output, encoding="utf-8")

    print("💾 已保存文件：output/CN_v2 和 CN_v2.rsc")


if __name__ == "__main__":
    main()