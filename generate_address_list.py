import requests
from pathlib import Path
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

OUTPUT_DIR = Path("output")

# IPv4
IPV4_URL = "http://www.iwik.org/ipcountry/mikrotik/CN"
IPV4_KEYWORD = "/ip firewall address-list"

# IPv6
IPV6_URL = "http://www.iwik.org/ipcountry/mikrotik_ipv6/CN"
IPV6_KEYWORD = "/ipv6 firewall address-list"

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

def download(session, url, keyword):
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }
        res = session.get(url, timeout=(5, 30), headers=headers)
        res.raise_for_status()

        res.encoding = 'utf-8'
        content = res.text.strip()
        
        if not content:
            raise ValueError("Downloaded content is empty")
        
        if keyword not in content:
            raise ValueError(f"Invalid RSC format: missing keyword '{keyword}'")
            
        return content
    except requests.exceptions.HTTPError as e:
        print(f"❌ HTTP Error for {url}: {e}")
        raise
    except requests.exceptions.ConnectionError as e:
        print(f"❌ Connection Error for {url}: {e}")
        raise
    except Exception as e:
        print(f"❌ Unexpected Error for {url}: {e}")
        raise

def main():
    try:
        OUTPUT_DIR.mkdir(exist_ok=True)
        session = create_session()

        print("⏳ Downloading IPv4 list...")
        ipv4 = download(session, IPV4_URL, IPV4_KEYWORD)
        
        print("⏳ Downloading IPv6 list...")
        ipv6 = download(session, IPV6_URL, IPV6_KEYWORD)

        combined = "\n".join([ipv4.strip(), ipv6.strip()])

        output_files = [
            OUTPUT_DIR / "CN.rsc",
            OUTPUT_DIR / "CN"
        ]

        for file_path in output_files:
            file_path.write_text(combined, encoding="utf-8")

        print(f"✅ Successfully generated: {[f.name for f in output_files]}")
        
        final_file = OUTPUT_DIR / "CN.rsc"
        if final_file.exists():
            print(f"📄 Final file size: {final_file.stat().st_size / 1024:.2f} KB")

    except Exception as e:
        print(f"🛑 Critical error occurred: {e}")
        exit(1)

if __name__ == "__main__":
    main()
