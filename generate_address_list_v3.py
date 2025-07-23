import maxminddb
import ipaddress
import requests
from datetime import datetime

MMDB_URL = "https://raw.githubusercontent.com/NobyDa/geoip/release/Private-GeoIP-CN.mmdb"
MMDB_FILE = "Private-GeoIP-CN.mmdb"

OUTPUT_RAW = "CN_v3"         # 无后缀纯地址列表
OUTPUT_RSC = "CN_v3.rsc"     # RouterOS 脚本格式

def download_mmdb():
    print(f"Downloading MMDB from {MMDB_URL} ...")
    response = requests.get(MMDB_URL)
    response.raise_for_status()
    with open(MMDB_FILE, "wb") as f:
        f.write(response.content)
    print("Download completed.")

def main():
    download_mmdb()

    with maxminddb.open_database(MMDB_FILE) as reader:
        networks = reader.get_with_prefix_len_all()
        ipv4_list = []
        ipv6_list = []

        for network, prefix_len, _ in networks:
            ipnet = ipaddress.ip_network(f"{network}/{prefix_len}", strict=False)
            if ipnet.version == 4:
                ipv4_list.append(str(ipnet))
            else:
                ipv6_list.append(str(ipnet))

    # 写入 CN_v3（纯列表）
    with open(OUTPUT_RAW, 'w', encoding='utf-8') as f:
        for ip in sorted(ipv4_list + ipv6_list):
            f.write(ip + "\n")

    # 写入 CN_v3.rsc（MikroTik 脚本格式）
    with open(OUTPUT_RSC, 'w', encoding='utf-8') as f:
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        f.write(f'/log info "Loading CN address list - generated at {now}"\n')

        # IPv4
        f.write('/ip firewall address-list remove [/ip firewall address-list find list=CN]\n')
        f.write('/ip firewall address-list\n')
        for ip in sorted(ipv4_list):
            f.write(f':do {{ add address={ip} list=CN }} on-error={{}}\n')
        f.write('\n')

        # IPv6
        f.write('/ipv6 firewall address-list remove [/ipv6 firewall address-list find list=CN]\n')
        f.write('/ipv6 firewall address-list\n')
        for ip in sorted(ipv6_list):
            f.write(f':do {{ add address={ip} list=CN }} on-error={{}}\n')

    print(f"Done. IPv4: {len(ipv4_list)}, IPv6: {len(ipv6_list)}")

if __name__ == "__main__":
    main()
