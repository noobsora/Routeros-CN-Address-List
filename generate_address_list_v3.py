import os
import requests
import ipaddress
from pathlib import Path
from tempfile import NamedTemporaryFile
import geoip2.database

MMDB_URL = "https://raw.githubusercontent.com/NobyDa/geoip/release/Private-GeoIP-CN.mmdb"
OUTPUT_DIR = Path("Routeros-CN-Address-List/output/")
OUTPUT_NAME = "CN_v3"

def download_mmdb(url: str) -> Path:
    print(f"Downloading MMDB from {url} ...")
    response = requests.get(url, stream=True, timeout=30)
    response.raise_for_status()
    with NamedTemporaryFile(delete=False, suffix=".mmdb") as tmp_file:
        for chunk in response.iter_content(chunk_size=8192):
            tmp_file.write(chunk)
    print("Download completed.")
    return Path(tmp_file.name)

def extract_cn_ip_networks(mmdb_path: Path) -> tuple[list[str], list[str]]:
    ipv4_list = []
    ipv6_list = []
    with geoip2.database.Reader(str(mmdb_path)) as reader:
        metadata = reader.metadata()
        for network in metadata.ip_version == 4 and reader._ipv4_start or reader._ipv6_start:
            # We don't iterate using internal pointers; use reader's internal method via database segments
            pass
        for record in reader._get_all_records():
            net = ipaddress.ip_network(record["network"])
            if net.version == 4:
                ipv4_list.append(str(net))
            else:
                ipv6_list.append(str(net))
    return ipv4_list, ipv6_list

def generate_ros_script(ipv4_list: list[str], ipv6_list: list[str]) -> str:
    lines = []

    # IPv4 Header
    lines.append('/log info "Loading CN ipv4 address list"')
    lines.append('/ip firewall address-list remove [/ip firewall address-list find list=CN]')
    lines.append('/ip firewall address-list')
    for ip in ipv4_list:
        lines.append(f':do {{ add address={ip} list=CN }} on-error={{}}')

    # IPv6 Header
    lines.append('/log info "Loading CN ipv6 address list"')
    lines.append('/ipv6 firewall address-list remove [/ipv6 firewall address-list find list=CN]')
    lines.append('/ipv6 firewall address-list')
    for ip in ipv6_list:
        lines.append(f':do {{ add address={ip} list=CN }} on-error={{}}')

    return "\n".join(lines)

def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    mmdb_path = download_mmdb(MMDB_URL)

    with geoip2.database.Reader(str(mmdb_path)) as reader:
        networks = reader.get_with_prefix_len()
        ipv4_list = []
        ipv6_list = []
        for ip, prefix in networks:
            net = ipaddress.ip_network(f"{ip}/{prefix}")
            if net.version == 4:
                ipv4_list.append(str(net))
            elif net.version == 6:
                ipv6_list.append(str(net))

    script = generate_ros_script(ipv4_list, ipv6_list)

    for ext in ["", ".rsc"]:
        output_file = OUTPUT_DIR / f"{OUTPUT_NAME}{ext}"
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(script)
        print(f"Saved to: {output_file}")

    os.unlink(mmdb_path)

if __name__ == "__main__":
    main()
