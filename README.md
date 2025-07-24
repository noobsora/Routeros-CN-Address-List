# 🇨🇳 RouterOS CN Address List

This project automatically generates China (CN) IP address lists in **RouterOS-compatible RSC format**, including **IPv4** and **IPv6** segments.

It provides two versions:

- ✅ `CN.rsc`: Based only on IP ranges from [iwik.org]
- ✅ `CN_v2.rsc`: Includes everything in `CN.rsc`, plus merged IP data from [gaoyifan/china-operator-ip] (based on ASNs from major Chinese ISPs)

---

## 📌 Address List Versions

### 🧩 `CN.rsc` (Basic Version)

- Data sources:
  - [`iwik.org` CN IPv4 list](http://www.iwik.org/ipcountry/mikrotik/CN)
  - [`iwik.org` CN IPv6 list](http://www.iwik.org/ipcountry/mikrotik_ipv6/CN)
- Features:
  - Suitable for general routing and firewall scenarios

### 🧬 `CN_v2.rsc` (Enhanced Version)

- Based on `CN.rsc`, with additional data from:
  - [gaoyifan/china-operator-ip](https://github.com/gaoyifan/china-operator-ip): IP segments derived from major Chinese ISPs
- Features:
  - More comprehensive and precise
  - Suitable for advanced routing and traffic segmentation

### 🤡 `BAZINGA`

- There're not too much differences between two versions.
- Whatever, I tried and both of them can work properly on my router.

---

## 📂 Output Structure

- Output files:
  - `output/CN.rsc`
  - `output/CN_v2.rsc`
- GitHub Actions workflows:
  - `.github/workflows/generate_address_list.yml`
  - `.github/workflows/generate_address_list_v2.yml`
- Update frequency: **Daily** via GitHub Actions

---

## 🚀 Usage

1. Go to the [`output`](output/) folder.
2. Download either `CN.rsc` or `CN_v2.rsc`.
3. Import into RouterOS via CLI or WinBox:
   ```shell
   /import file-name=CN.rsc
   ```

---

## 🧠 Use Cases

- Create RouterOS address-lists for:
  - Firewall filtering
  - Policy routing
  - Split tunneling
- Apply in:
  - Domestic/International traffic separation
  - China-optimized routing acceleration
  - Selective DNS proxying

---

## ⚠️ Disclaimer

- This project does **not** host any original IP data.
- All copyrights belong to the respective upstream providers.
- For personal use only. Use at your own risk.

---

## 📝 License

This project is licensed under the [MIT License](LICENSE).
