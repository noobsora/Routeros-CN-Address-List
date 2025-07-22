import requests
import ipaddress
from pathlib import Path
import re

# 数据来源 URL
ipv4_script_url_1 = "http://www.iwik.org/ipcountry/mikrotik/CN"
ipv6_script_url_1 = "http://www.iwik.org/ipcountry/mikrotik_ipv6/CN"
ipv4_plain_url_2 = "https://raw.githubusercontent.com/gaoyifan/china-operator-ip/refs/heads/ip-lists/china.txt"
ipv6_plain_url_2 = "https://raw.githubusercontent.com/gaoyifan/china-operator-ip/refs/heads/ip-lists/china6.txt"

def fetch_text(url):
    resp = requests.get(url, timeout=30)
    resp.raise_for_status()
    return resp.text.strip()

def parse_script_style_ips(text):
    pattern = re.compile(r'address=([\da-fA-F:\./]+)')
    return {m.group(1) for m in map(pattern.search, text.splitlines()) if m}

def parse_plain_ips(text):
    return {line.strip() for line in text.splitlines() if line.strip() and not line.startswith("#")}

def normalize_networks(ip_strs):
    v4, v6 = [], []
    for s in ip_strs:
        try:
            net = ipaddress.ip_network(s, strict=False)
            (v4 if isinstance(net, ipaddress.IPv4Network) else v6).append(net)
        except ValueError:
            pass
    return v4, v6

def merge_and_format(networks, list_name, is_ipv6=False):
    header = []
    if is_ipv6:
        header = [
            '/log info "Loading CN ipv6 address list"',
            '/ipv6 firewall address-list remove [/ipv6 firewall address-list find list=CN]',
            '/ipv6 firewall address-list'
        ]
    else:
        header = [
            '/log info "Loading CN ipv4 address list"',
            '/ip firewall address-list remove [/ip firewall address-list find list=CN]',
            '/ip firewall address-list'
        ]
    merged = ipaddress.collapse_addresses(networks)
    rules = [f":do {{ add address={net.with_prefixlen} list=CN }} on-error={{}}" for net in merged]
    return header + rules

def main():
    ipv4_script = fetch_text(ipv4_script_url_1)
    ipv6_script = fetch_text(ipv6_script_url_1)
    ipv4_plain = fetch_text(ipv4_plain_url_2)
    ipv6_plain = fetch_text(ipv6_plain_url_2)

    ipv4_strs = parse_script_style_ips(ipv4_script) | parse_plain_ips(ipv4_plain)
    ipv6_strs = parse_script_style_ips(ipv6_script) | parse_plain_ips(ipv6_plain)

    ipv4_nets, _ = normalize_networks(ipv4_strs)
    _, ipv6_nets = normalize_networks(ipv6_strs)

    lines_v4 = merge_and_format(ipv4_nets, "CN", is_ipv6=False)
    lines_v6 = merge_and_format(ipv6_nets, "CN", is_ipv6=True)

    final_output = "\n".join(lines_v4 + [""] + lines_v6)

    output_dir = Path("output")
    output_dir.mkdir(exist_ok=True)

    # 输出两个文件：CN_v2（无扩展名）和 CN_v2.rsc
    (output_dir / "CN_v2").write_text(final_output, encoding="utf-8")
    (output_dir / "CN_v2.rsc").write_text(final_output, encoding="utf-8")

if __name__ == "__main__":
    main()
