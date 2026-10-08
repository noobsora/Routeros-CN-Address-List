import requests
from pathlib import Path
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

OUTPUT_DIR = Path("output")
IPV4_URL = "http://www.iwik.org/ipcountry/mikrotik/CN"
IPV6_URL = "http://www.iwik.org/ipcountry/mikrotik_ipv6/CN"
VALIDATION_KEYWORD = "/ip firewall address-list" 

def create_session(retries=3, backoff_factor=1, status_forcelist=(500, 502, 503, 504)):
    session = requests.Session()
    retry = Retry(
        total=retries,
        read=retries,
        connect=retries,
        backoff_factor=backoff_factor,
        status_forcelist=status_forcelist,
        raise_on_status=False,
    )
    adapter = HTTPAdapter(max_retries=retry)
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    return session

def download(session, url):
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }
        res = session.get(url, timeout=30, headers=headers)
        res.raise_for_status()
        content = res.text.strip()
        
        if not content:
            raise ValueError(f"Downloaded content from {url} is empty")
        
        if VALIDATION_KEYWORD not in content:
            raise ValueError(f"Downloaded content from {url} does not look like a valid RSC file (missing keyword: {VALIDATION_KEYWORD})")
            
        return content
    except Exception as e:
        print(f"❌ Failed to download {url}: {e}")
        raise

def main():
    try:
        OUTPUT_DIR.mkdir(exist_ok=True)
        session = create_session()

        print("⏳ Downloading IPv4 list...")
        ipv4 = download(session, IPV4_URL)
        
        print("⏳ Downloading IPv6 list...")
        ipv6 = download(session, IPV6_URL)

        combined = f"{ipv4}\n{ipv6}"

        file_rsc = OUTPUT_DIR / "CN.rsc"
        file_noext = OUTPUT_DIR / "CN"

        file_rsc.write_text(combined, encoding="utf-8")
        file_noext.write_text(combined, encoding="utf-8")

        print(f"✅ CN.rsc and CN files generated successfully.")
        print(f"📄 File size: {file_rsc.stat().st_size / 1024:.2f} KB")

    except Exception as e:
        print(f"🛑 Critical error occurred: {e}")
        exit(1)

if __name__ == "__main__":
    main()
