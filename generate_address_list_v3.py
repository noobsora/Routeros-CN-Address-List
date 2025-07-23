import os
import requests
import ipaddress
from pathlib import Path
import maxminddb

MMDB_URL = "https://raw.githubusercontent.com/NobyDa/geoip/release/Private-GeoIP-CN.mmdb"
OUTPUT_DIR = Path("Routeros-CN-Address-List/output")
OUTPUT_NAME = "CN_v3"

def download_mmdb(url: str) -> Path:
    print(f"Downloading MMDB from {url} ...")
    response = requests.get(url, stream=True, timeout=30)
    response.raise_for_status()
    mmdb_path = Path("Private-GeoIP-CN.mmdb")
    with open(mmdb_path, "wb") as f:
        for chunk in response.iter_content(chunk_size=8192):
            f.write(chunk)
    print("Download completed.")
    return mmdb_path

def traverse_node(node, prefix, depth, results):
    if node is None:
        return
    # node.value 表示该节点有数据，prefix就是二进制字符串
    if hasattr(node, 'value') and node.value is not None:
        ip_net = bits_to_network(prefix, depth)
        results.append(ip_net)
    if hasattr(node, 'children'):
        for bit, child in node.children.items():
            traverse_node(child, prefix + bit, depth + 1, results)

def bits_to_network(bits: str, length: int):
    # bits是字符串形式的0/1，length是前缀长度
    # 先补齐到128位
    bits = bits.ljust(128, '0')
    # 转成bytes
    b = int(bits, 2).to_bytes(16, byteorder='big')
    if length <= 32:
        net = ipaddress.ip_network((ipaddress.IPv4Address(b[:4]), length))
    else:
        net = ipaddress.ip_network((ipaddress.IPv6Address(b), length))
    return str(net)

def get_all_networks(mmdb_path: Path):
    ipv4_list = []
    ipv6_list = []
    with maxminddb.open_database(str(mmdb_path)) as reader:
        results = []
        traverse_node(reader._tree, '', 0, results)
        for net in results:
            ip_net = ipaddress.ip_network(net)
            if ip_net.version == 4:
                ipv4_list.append(str(ip_net))
            else:
                ipv6_list.append(str(ip_net))
    return sorted(set(ipv4_list)), sorted(set(ipv6_list))

def generate_ros_script(ipv4_list, ipv6_list):
    lines = []
    lines.append('/log info "Loading CN ipv4 address list"')
    lines.append('/ip firewall address-list remove [/ip firewall address-list find list=CN]')
    lines.append('/ip firewall address-list')
    for ip in ipv4_list:
        lines.append(f':do {{ add address={ip} list=CN }} on-error={{}}')

    lines.append('/log info "Loading CN ipv6 address list"')
    lines.append('/ipv6 firewall address-list remove [/ipv6 firewall address-list find list=CN]')
    lines.append('/ipv6 firewall address-list')
    for ip in ipv6_list:
        lines.append(f':do {{ add address={ip} list=CN }} on-error={{}}')

    return "\n".join(lines)

def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    mmdb_path = download_mmdb(MMDB_URL)
    ipv4_list, ipv6_list = get_all_networks(mmdb_path)
    script = generate_ros_script(ipv4_list, ipv6_list)

    for ext in ['', '.rsc']:
        out_file = OUTPUT_DIR / f"{OUTPUT_NAME}{ext}"
        with open(out_file, 'w', encoding='utf-8') as f:
            f.write(script)
        print(f"Saved {out_file}")

    try:
        os.remove(mmdb_path)
    except Exception:
        pass

if __name__ == "__main__":
    main()
