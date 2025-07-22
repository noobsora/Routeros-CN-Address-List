import requests
import ipaddress
from pathlib import Path
import re

# 四个源URL
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
    ips = set()
    for line in text.splitlines():
        m = pattern.search(line)
        if m:
            ips.add(m.group(1))
    return ips

def parse_plain_ips(text):
    ips = set()
    for line in text.splitlines():
        line = line.strip()
        if line and not line.startswith("#"):
            ips.add(line)
    return ips

def normalize_networks(ip_strs):
    nets_v4 = []
    nets_v6 = []
    for s in ip_strs:
        try:
            net = ipaddress.ip_network(s, strict=False)
            if isinstance(net, ipaddress.IPv4Network):
                nets_v4.append(net)
            else:
                nets_v6.append(net)
        except ValueError:
            pass
    return nets_v4, nets_v6

def merge_networks(networks):
    merged = list(ipaddress.collapse_addresses(networks))
    merged.sort(key=lambda net: (net.version, int(net.network_address)))
    return merged

def format_to_routeros(net):
    return f":do {{ add address={net.with_prefixlen} list=CN_v2 }} on-error={{}}"

def main():
    print("Fetching source data...")
    ipv4_script = fetch_text(ipv4_script_url_1)
    ipv6_script = fetch_text(ipv6_script_url_1)
    ipv4_plain = fetch_text(ipv4_plain_url_2)
    ipv6_plain = fetch_text(ipv6_plain_url_2)

    print("Parsing IPs...")
    ipv4_ips1 = parse_script_style_ips(ipv4_script)
    ipv6_ips1 = parse_script_style_ips(ipv6_script)
    ipv4_ips2 = parse_plain_ips(ipv4_plain)
    ipv6_ips2 = parse_plain_ips(ipv6_plain)

    all_ipv4_strs = ipv4_ips1.union(ipv4_ips2)
    all_ipv6_strs = ipv6_ips1.union(ipv6_ips2)

    print(f"Total IPv4 ranges before merge: {len(all_ipv4_strs)}")
    print(f"Total IPv6 ranges before merge: {len(all_ipv6_strs)}")

    ipv4_nets, _ = normalize_networks(all_ipv4_strs)
    _, ipv6_nets = normalize_networks(all_ipv6_strs)

    merged_ipv4 = merge_networks(ipv4_nets)
    merged_ipv6 = merge_networks(ipv6_nets)

    print(f"Total IPv4 ranges after merge: {len(merged_ipv4)}")
    print(f"Total IPv6 ranges after merge: {len(merged_ipv6)}")

    merged_all = merged_ipv4 + merged_ipv6
    lines = [format_to_routeros(net) for net in merged_all]

    output_dir = Path("output")
    output_dir.mkdir(exist_ok=True)
    file_rsc = output_dir / "CN_v2.rsc"
    file_noext = output_dir / "CN_v2"

    file_rsc.write_text("\n".join(lines), encoding="utf-8")
    file_noext.write_text("\n".join(lines), encoding="utf-8")

    print(f"✅ Generated {file_rsc} and {file_noext} with {len(lines)} entries.")

if __name__ == "__main__":
    main()
