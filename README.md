# 🇨🇳 RouterOS CN Address List

This project automatically generates a RouterOS-compatible address list for all IP ranges allocated to **China (CN)** — including both **IPv4** and **IPv6**.

## 🌐 Data Sources

- [iwik.org](http://www.iwik.org)

## 📦 What It Does

- Fetches data from:
  - [`iwik.org` CN IPv4 list](http://www.iwik.org/ipcountry/mikrotik/CN)
  - [`iwik.org` CN IPv6 list](http://www.iwik.org/ipcountry/mikrotik_ipv6/CN)
- Merges and outputs to a single RouterOS `.rsc` script
- Automatically updates **daily via GitHub Actions**
- Output file: [`output/CN.rsc`](output/CN.rsc)

## 🧠 Use Case

This script is useful if you want to:

- Build a RouterOS firewall rule to handle traffic to/from China
- Combine with routing or policy rules for selective bypass or blocking
- Maintain an up-to-date CN address list without manual effort

## 🛠️ How to Use

1. Download the latest [`CN.rsc`](output/CN.rsc) file
2. Import it into RouterOS via WinBox or CLI:

## ⚠️ Disclaimer

This project is intended for **personal use only**.  
We do not host or modify the original IP data, and all copyright belongs to their respective owners.

Please use at your own discretion. We are not responsible for any misuse or system misconfiguration caused by this list.

## 📝 License

This project is open-sourced under the [MIT License](LICENSE).
