import requests
from pathlib import Path
import time

ipv4_url = "http://www.iwik.org/ipcountry/mikrotik/CN"
ipv6_url = "http://www.iwik.org/ipcountry/mikrotik_ipv6/CN"

def download(url, retries=3, delay=3):
    for attempt in range(1, retries + 1):
        try:
            res = requests.get(url, timeout=30)
            res.raise_for_status()
            return res.text.strip()
        except Exception as e:
            if attempt == retries:
                raise
            print(f"Warning: Failed to download {url} (attempt {attempt}), retrying in {delay}s...")
            time.sleep(delay)

def main():
    ipv4 = download(ipv4_url)
    ipv6 = download(ipv6_url)

    combined = "\n".join([ipv4, "", ipv6])

    output_dir = Path("output")
    output_dir.mkdir(exist_ok=True)

    file_rsc = output_dir / "CN.rsc"
    file_noext = output_dir / "CN"

    file_rsc.write_text(combined, encoding="utf-8")
    file_noext.write_text(combined, encoding="utf-8")

    print(f"✅ CN.rsc and CN files generated.")
    print(f"File size: {file_rsc.stat().st_size} bytes")

if __name__ == "__main__":
    main()
