import requests
import ipaddress
from pathlib import Path
import re
import sys
from typing import Set, List, Tuple
from concurrent.futures import ThreadPoolExecutor, as_completed
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

IPV4_SCRIPT_URL = "http://www.iwik.org/ipcountry/mikrotik/CN"
IPV6_SCRIPT_URL = "http://www.iwik.org/ipcountry/mikrotik_ipv6/CN" 
IPV4_PLAIN_URL = "https://raw.githubusercontent.com/gaoyifan/china-operator-ip/refs/heads/ip-lists/china.txt"
IPV6_PLAIN_URL = "https://raw.githubusercontent.com/gaoyifan/china-operator-ip/refs/heads/ip-lists/china6.txt"

OUTPUT_DIR = Path("output")
OUTPUT_FILE_NAME = "CN_v2"

def create_session(retries=3, backoff_factor=1, status_forcelist=(500, 502, 503, 504)):
    session = requests.Session()
    retry = Retry(
        total=retries, read=retries, connect=retries,
        backoff_factor=backoff_factor, status_forcelist=status_forcelist,
        raise_on_status=False,
    )
    adapter = HTTPAdapter(max_retries=retry)
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    return session

def fetch_text(session, url: str) -> str:
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }
        resp = session.get(url, timeout=(5, 30), headers=headers)
        resp.raise_for_status()
        content = resp.text.strip()
        
        if not content:
            print(f"⚠️ [Warning] {url} returned empty content")
            return ""
        return content
    except Exception as e:
        print(f"❌ [Error] Failed to fetch {url}: {e}", file=sys.stderr)
        return ""

def parse_script_style_ips(text: str) -> Set[str]:
    if not text: return set()
    pattern = re.compile(r'address=([\da-fA-F:/\.]+)')
    return {m.group(1) for line in text.splitlines() if (m := pattern.search(line))}

def parse_plain_ips(text: str) -> Set[str]:
    if not text: return set()
    return {line.strip() for line in text.splitlines() if line.strip() and not line.startswith("#")}

def normalize_networks(ipv4_strs: Set[str], ipv6_strs: Set[str]) -> Tuple[List[ipaddress.IPv4Network], List[ipaddress.IPv6Network]]:
    ipv4, ipv6 = [], []
    for s in ipv4_strs:
        try:
            ipv4.append(ipaddress.ip_network(s, strict=False))
        except ValueError:
            print(f"⚠️ [Skip] Invalid IPv4 network: {s}", file=sys.stderr)
    for s in ipv6_strs:
        try:
            ipv6.append(ipaddress.ip_network(s, strict=False))
        except ValueError:
            print(f"⚠️ [Skip] Invalid IPv6 network: {s}", file=sys.stderr)
    return ipv4, ipv6

def merge_and_format(networks: List[ipaddress._BaseNetwork], is_ipv6: bool = False) -> Tuple[List[str], int]:
    prefix = "ipv6" if is_ipv6 else "ip"
    header = [
        f'/log info "Loading CN {prefix} address list"',
        f'/{prefix} firewall address-list remove [/{prefix} firewall address-list find list=CN]',
        f'/{prefix} firewall address-list'
    ]
    
    collapsed = sorted(ipaddress.collapse_addresses(networks), key=lambda net: (int(net.network_address), net.prefixlen))
    rules = [f':do {{ add address={net.with_prefixlen} list=CN }} on-error={{}}' for net in collapsed]
    
    return header + rules, len(rules)

def main() -> None:
    print("📥 Fetching IP data sources concurrently...")
    
    urls = {
        "ipv4_script": IPV4_SCRIPT_URL,
        "ipv6_script": IPV6_SCRIPT_URL,
        "ipv4_plain": IPV4_PLAIN_URL,
        "ipv6_plain": IPV6_PLAIN_URL,
    }

    session = create_session()
    results = {}

    with ThreadPoolExecutor(max_workers=4) as executor:
        future_to_key = {executor.submit(fetch_text, session, url): key for key, url in urls.items()}
        for future in as_completed(future_to_key):
            key = future_to_key[future]
            results[key] = future.result()

    print("📦 Parsing raw address segments...")
    ipv4_strs = parse_script_style_ips(results["ipv4_script"]) | parse_plain_ips(results["ipv4_plain"])
    ipv6_strs = parse_script_style_ips(results["ipv6_script"]) | parse_plain_ips(results["ipv6_plain"])

    print(f"Original IPv4 count: {len(ipv4_strs)}")
    print(f"Original IPv6 count: {len(ipv6_strs)}")

    if not ipv4_strs and not ipv6_strs:
        print("❌ No valid IP ranges found, exiting.", file=sys.stderr)
        sys.exit(1)

    ipv4_nets, ipv6_nets = normalize_networks(ipv4_strs, ipv6_strs)

    merged_ipv4, count_ipv4 = merge_and_format(ipv4_nets, is_ipv6=False)
    merged_ipv6, count_ipv6 = merge_and_format(ipv6_nets, is_ipv6=True)

    print(f"Merged IPv4 count: {count_ipv4}")
    print(f"Merged IPv6 count: {count_ipv6}")

    final_output = "\n".join(merged_ipv4 + [""] + merged_ipv6)

    OUTPUT_DIR.mkdir(exist_ok=True)

    file_rsc = OUTPUT_DIR / f"{OUTPUT_FILE_NAME}.rsc"
    file_noext = OUTPUT_DIR / OUTPUT_FILE_NAME

    file_rsc.write_text(final_output, encoding="utf-8")
    file_noext.write_text(final_output, encoding="utf-8")

    print(f"💾 Files saved: {file_noext.name} and {file_rsc.name} (Total size: {file_rsc.stat().st_size / 1024:.2f} KB)")

if __name__ == "__main__":
    main()
