import requests
import ipaddress
import gzip
import shutil
import os
from geoip2.database import Reader
from maxminddb import open_database
from datetime import datetime

MMDB_URL = "https://raw.githubusercontent.com/NobyDa/geoip/release/Private-GeoIP-CN.mmdb"
MMDB_FILE = "CN.mmdb"
OUTPUT_TXT = "CN_v3"
OUTPUT_RSC = "CN_v3.rsc"

def download_mmdb():
    print(f"Downloading MMDB from {MMDB_URL} ...")
    response = requests.get(MMDB_URL, timeout=60)
    response.raise_for_status()
    with open(MMDB_FILE, "wb") as f:
        f.write(response.content)
    print("Download completed.")

def extract_cidrs_from_mmdb():
    cidrs_v4 = set()
    cidrs_v6 = set()

    with open_database(MMDB_FILE) as reader:
        for network, data in reader:
            net = ipaddress.ip_network(network)
            if isinstance(net, ipaddress.IPv4Network):
                cidrs_v4.add(str(net))
            else:
                cidrs_v6.add(str(net))
    return sorted(cidrs_v4), sorted(cidrs_v6)

def generate_ros_script(cidrs_v4, cidrs_v6):
    header = (
        f"# RouterOS CN Address List\n"
        f"# Source: {MMDB_URL}\n"
        f"# Last Update: {datetime.utcnow().isoformat()}Z\n"
        f"# Total IPv4: {len(cidrs_v4)} | Total IPv6: {len(cidrs_v6)}\n"
        f"/ip firewall address-list\n"
    )

    ros_v4 = "\n".join(
        [f":do {{ add address={ip} list=CN }} on-error={{}}" for ip in cidrs_v4]
    )

    ros_v6 = (
        "\n/ipv6 firewall address-list\n" +
        "\n".join(
            [f":do {{ add address={ip} list=CN }} on-error={{}}" for ip in cidrs_v6]
        )
        if cidrs_v6 else ""
    )

    content = header + ros_v4 + ("\n" + ros_v6 if ros_v6 else "")
    return content

def main():
    download_mmdb()
    cidrs_v4, cidrs_v6 = extract_cidrs_from_mmdb()
    script = generate_ros_script(cidrs_v4, cidrs_v6)

    # 写入两个一致的文件
    for filename in [OUTPUT_TXT, OUTPUT_RSC]:
        with open(filename, "w", encoding="utf-8") as f:
            f.write(script)

if __name__ == "__main__":
    main()
