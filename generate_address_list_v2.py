import requests
import ipaddress
from pathlib import Path
import re
import sys
from typing import Set, Tuple, List

# 数据源地址
IPV4_SCRIPT_URL = "http://www.iwik.org/ipcountry/mikrotik/CN"
IPV6_SCRIPT_URL = "http://www.iwik.org/ipcountry/mikrotik_ipv6/CN"
IPV4_PLAIN_URL = "https://raw.githubusercontent.com/gaoyifan/china-operator-ip/refs/heads/ip-lists/china.txt"
IPV6_PLAIN_URL = "https://raw.githubusercontent.com/gaoyifan/china-operator-ip/refs/heads/ip-lists/china6.txt"

OUTPUT_PATH = Path("output/CN_v2")
OUTPUT_RSC = Path("output/CN_v2.rsc")


def fetch_text(url: str) -> str:
    """从指定 URL 获取文本数据"""
    try:
        resp = requests.get(url, timeout=30)
        resp.raise_for_status()
        return resp.text.strip()
    except Exception as e:
        print(f"⚠️ [错误] 无法获取 {url}：{e}", file=sys.stderr)
        return ""


def parse_script_style_ips(text: str) -> Set[str]:
    """提取 script 风格的地址段"""
    pattern = re.compile(r'address=([\da-fA-F:/\.]+)')
    return {m.group(1) for line in text.splitlines() if (m := pattern.search(line))}


def parse_plain_ips(text: str) -> Set[str]:
    """提取纯文本格式的地址段"""
    return {line.strip() for line in text.splitlines() if line.strip() and not line.startswith("#")}


def normalize_networks(ip_strs: Set[str]) -> Tuple[List[ipaddress.IPv4Network], List[ipaddress.IPv6Network]]:
    """将字符串地址段转换为 IP 网络对象，并按版本分类"""
    ipv4, ipv6 = [], []
    for s in ip_strs:
        try:
            net = ipaddress.ip_network(s, strict=False)
            if isinstance(net, ipaddress.IPv4Network):
                ipv4.append(net)
            else:
                ipv6.append(net)
        except ValueError:
            print(f"⚠️ [跳过] 非法地址段：{s}", file=sys.stderr)
    return ipv4, ipv6


def merge_and_format(networks: List[ipaddress._BaseNetwork], is_ipv6: bool = False) -> List[str]:
    """合并地址段并生成 RouterOS 脚本格式"""
    header = [
        f'/log info "Loading CN {"ipv6" if is_ipv6 else "ipv4"} address list"',
        f'/{ "ipv6" if is_ipv6 else "ip"} firewall address-list remove [/' +
        f'{ "ipv6" if is_ipv6 else "ip"} firewall address-list find list=CN]',
        f'/{ "ipv6" if is_ipv6 else "ip"} firewall address-list'
    ]
    collapsed = sorted(ipaddress.collapse_addresses(networks), key=lambda net: (net.network_address, net.prefixlen))
    rules = [f':do {{ add address={net.with_prefixlen} list=CN }} on-error={{}}' for net in collapsed]
    return header + rules


def main() -> None:
    print("📥 正在抓取 IP 数据源...")

    ipv4_script = fetch_text(IPV4_SCRIPT_URL)
    ipv6_script = fetch_text(IPV6_SCRIPT_URL)
    ipv4_plain = fetch_text(IPV4_PLAIN_URL)
    ipv6_plain = fetch_text(IPV6_PLAIN_URL)

    print("📦 正在解析原始地址段...")
    ipv4_strs = parse_script_style_ips(ipv4_script) | parse_plain_ips(ipv4_plain)
    ipv6_strs = parse_script_style_ips(ipv6_script) | parse_plain_ips(ipv6_plain)

    print(f"🔢 原始 IPv4 条目数：{len(ipv4_strs)}")
    print(f"🔢 原始 IPv6 条目数：{len(ipv6_strs)}")

    ipv4_nets, _ = normalize_networks(ipv4_strs)
    _, ipv6_nets = normalize_networks(ipv6_strs)

    merged_ipv4 = merge_and_format(ipv4_nets, is_ipv6=False)
    merged_ipv6 = merge_and_format(ipv6_nets, is_ipv6=True)

    print(f"✅ 合并后 IPv4 条目数：{len(merged_ipv4) - 3}")
    print(f"✅ 合并后 IPv6 条目数：{len(merged_ipv6) - 3}")

    final_output = "\n".join(merged_ipv4 + [""] + merged_ipv6)

    output_dir = Path("output")
    output_dir.mkdir(exist_ok=True)

    OUTPUT_PATH.write_text(final_output, encoding="utf-8")
    OUTPUT_RSC.write_text(final_output, encoding="utf-8")

    print("✅ 已保存文件：output/CN_v2 和 CN_v2.rsc")


if __name__ == "__main__":
    main()
