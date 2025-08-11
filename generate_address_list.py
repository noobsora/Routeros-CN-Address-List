import requests
from pathlib import Path
import time
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

OUTPUT_DIR = Path("output")
IPV4_URL = "http://www.iwik.org/ipcountry/mikrotik/CN"
IPV6_URL = "http://www.iwik.org/ipcountry/mikrotik_ipv6/CN"

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
        res = session.get(url, timeout=30)
        res.raise_for_status()
        content = res.text.strip()
        if not content:
            raise ValueError(f"Downloaded content from {url} is empty")
        return content
    except Exception as e:
        print(f"❌ Failed to download {url}: {e}")
        raise

def main():
    OUTPUT_DIR.mkdir(exist_ok=True)
    session = create_session()

    ipv4 = download(session, IPV4_URL)
    ipv6 = download(session, IPV6_URL)

    combined = "\n".join(part for part in (ipv4, ipv6) if part)

    file_rsc = OUTPUT_DIR / "CN.rsc"
    file_noext = OUTPUT_DIR / "CN"

    file_rsc.write_text(combined, encoding="utf-8")
    file_noext.write_text(combined, encoding="utf-8")

    print(f"✅ CN.rsc and CN files generated.")
    print(f"File size: {file_rsc.stat().st_size} bytes")

if __name__ == "__main__":
    main()