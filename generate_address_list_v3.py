import os
import requests
import ipaddress
from pathlib import Path
from datetime import datetime
import maxminddb

MMDB_URL = "https://raw.githubusercontent.com/NobyDa/geoip/release/Private-GeoIP-CN.mmdb"
OUTPUT_DIR = Path("Routeros-CN-Address-List/output/")
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

def get_all_networks(mmdb_path: Path):
    ipv4_list = []
    ipv6_list = []

    with maxminddb.open_database(str(mmdb_path)) as reader:
        # maxminddb.Reader 有 _tree 属性，可递归遍历
        def recurse_tree(node, prefix):
            if node is None:
                return
            if 'networks' in node:
                for network in node['networks']:
                    net = ipaddress.ip_network(network)
                    if net.version == 4:
                        ipv4_list.append(str(net))
                    else:
                        ipv6_list.append(str(net))
            if 'children' in node:
                for bit, child in node['children'].items():
                    recurse_tree(child, prefix + str(bit))

        # 使用内置方法遍历全部网络
        tree = reader._tree
        def traverse(node, prefix=''):
            if 'value' in node and node['value'] is not None:
                # node['value'] 有数据表示是个网络段
                if prefix:
                    # 把 prefix 转为网段
                    # prefix 是二进制字符串，比如 '1100000010101000' -> 192.168.0.0/16
                    # 但这样太复杂，直接用 reader._find_networks() 来获取 CIDR
                    pass
            if 'children' in node:
                for bit in node['children']:
                    traverse(node['children'][bit], prefix + bit)

        # 但直接用 reader._find_networks() 获取所有网络更简单：
        networks = reader._find_networks()
        for network, _ in networks:
            net = ipaddress.ip_network(network)
            if net.version == 4:
                ipv4_list.append(str(net))
            else:
                ipv6_list.append(str(net))

    return sorted(set(ipv4_list)), sorted(set(ipv6_list))

def generate_ros_script(ipv4_list, ipv6_list):
    lines = []

    # IPv4 header
    lines.append('/log info "Loading CN ipv4 address list"')
    lines.append('/ip firewall address-list remove [/ip firewall address-list find list=CN]')
    lines.append('/ip firewall address-list')
    for ip in ipv4_list:
        lines.append(f':do {{ add address={ip} list=CN }} on-error={{}}')

    # IPv6 header
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

    # 删除临时 mmdb 文件
    try:
        os.remove(mmdb_path)
    except Exception:
        pass

if __name__ == "__main__":
    main()
