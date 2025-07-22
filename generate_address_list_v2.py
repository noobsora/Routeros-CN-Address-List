import requests
import ipaddress
from pathlib import Path
import re
import sys

ipv4_script_url_1 = "http://www.iwik.org/ipcountry/mikrotik/CN"
ipv6_script_url_1 = "http://www.iwik.org/ipcountry/mikrotik_ipv6/CN"
ipv4_plain_url_2 = "https://raw.githubusercontent.com/gaoyifan/china-operator-ip/refs/heads/ip-lists/china.txt"
ipv6_plain_url_2 = "https://raw.githubusercontent.com/gaoyifan/china-operator-ip/refs/heads/ip-lists/china6.txt"

def fetch_text(url):
    try:
        resp = requests.get(url, timeout=30)
        resp.raise_for_status()
        return resp.text.strip()
    except Exception as e:
        print(f"⚠️ Warning: Failed to fetch {url} due to {e}", file=sys.stderr)
        return ""

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
            print(f"⚠️ Warning: Invalid IP network {s}", file=sys.stderr)
    return v4, v6

def merge_and_format(networks, is_ipv6=False):
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
    merged = list(ipaddress.collapse_addresses(networks))
    merged.sort(key=lambda net: (net.network_address, net.prefixlen))
    rules = [f":do {{ add address={net.with_prefixlen} list=CN }} on-error={{}}" for net in merged]
    return header + rules

def main():
    ipv4_script = fetch_text(ipv4_script_url_1)
    ipv6_script = fetch_text(ipv6_script_url_1)
    ipv4_plain = fetch_text(ipv4_plain_url_2)
    ipv6_plain = fetch_text(ipv6_plain_url_2)

    ipv4_strs = parse_script_style_ips(ipv4_script) | parse_plain_ips(ipv4_plain)
    ipv6_strs = parse_script_style_ips(ipv6_script) | parse_plain_ips(ipv6_plain)

    print(f"Total IPv4 ranges before merge: {len(ipv4_strs)}")
    print(f"Total IPv6 ranges before merge: {len(ipv6_strs)}")

    ipv4_nets, _ = normalize_networks(ipv4_strs)
    _, ipv6_nets = normalize_networks(ipv6_strs)

    merged_ipv4 = merge_and_format(ipv4_nets, is_ipv6=False)
    merged_ipv6 = merge_and_format(ipv6_nets, is_ipv6=True)

    print(f"Total IPv4 ranges after merge: {len(merged_ipv4) - 3}")  # 减去header行数
    print(f"Total IPv6 ranges after merge: {len(merged_ipv6) - 3}")

    final_output = "\n".join(merged_ipv4 + [""] + merged_ipv6)

    output_dir = Path("output")
    output_dir.mkdir(exist_ok=True)

    (output_dir / "CN_v2").write_text(final_output, encoding="utf-8")
    (output_dir / "CN_v2.rsc").write_text(final_output, encoding="utf-8")

if __name__ == "__main__":
    main()
