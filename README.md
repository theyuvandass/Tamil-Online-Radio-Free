# 📻 Tamil Free Radio Premium Proxy Server

A dynamic, ad-blocking streaming proxy server and gorgeous searchable dark-mode web dashboard for **500+ live Tamil radio stations**. 

This server implements real-time client-synchronization, player handshake emulation, and ad-server bypasses to provide completely clean, uninterrupted music streams directly to **VLC Media Player** or any other network player.

🌐 **Live Website URL**: [freeradiotamil.onrender.com](https://freeradiotamil.onrender.com/)

---

## ✨ Features

* **Dynamic Database Load**: Automatically reads and routes 502 live stations mapped directly from `all_stations.json`.
* **Ad-Block Handshake Bypass**: Emulates Android player handshake permissions, synchronized session timestamps, and device callbacks to completely bypass playstore app advertisement walls on secure streams (like *Rajah Melody*, *Puradsi FM*, *Tamil Beat Radio*).
* **Domain Re-routing Bypass**: Dynamically rewrites `psrlive1`/`psrlive2` requests to `psrlive3` to bypass ad-injection cluster endpoints.
* **Smart Selective Routing (HTTP 302)**: 
  - Gated stations automatically route through our proxy handshake.
  - Standard/Direct streams (like *AIR Coimbatore*, *Barakath Radio*, *Vividh Bharati*) **bypass proxy overhead entirely** and stream natively via instant `302 Found` redirects or direct dashboard links. This fully supports `.m3u8` HLS segmented playlists!
* **Glassmorphic Web Dashboard**: Sleek Inter-font dark UI (`http://127.0.0.1:8080/`) featuring:
  - **Instant Javascript Search Bar**: Filter all stations instantly as you type.
  - **Genre Chip Filters**: Quickly jump to Devotional, Tamilradios, Air Tamil, Top Radios, etc.
  - **Copy buttons**: Automatically copies direct links for standard stations and local/cloud proxy links for secure stations.
* **100% Robust**: Includes encoding-safe console log prints to prevent Windows terminal emoji crashes.

---

## 📂 Repository Structure

* **`southradios_proxy.py`**: The core multi-threaded Python proxy server and dashboard router.
* **`scrape_all_data.py`**: A live scraper script to sync and pull the latest station database from the cloud API.
* **`all_stations.json`**: The complete list of 500+ live radio streams scraped from the active database.
* **`compiled_stations.md`**: A clean markdown report listing all stations organized by category.
* **`requirements.txt`**: Production dependency configurations.
* **`local_backup/`**: (Ignored by Git) Local backup of initial decompilation research, recorded `.aac` validation clips, and diagnostic testing scripts.

---

## 🚀 Running Locally

1. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Launch the server**:
   ```bash
   python southradios_proxy.py
   ```

3. **Access the Dashboard**:
   Open **`http://127.0.0.1:8080/`** in your browser.

4. **Stream in VLC**:
   Click **"📋 Copy VLC Link"** on any station card, open VLC Media Player, press **Ctrl + N** (Network Stream), paste the URL, and hit **Play**!

---

## ☁️ Deploying to the Cloud (Render.com)

This project is fully optimized for cloud hosting on **Render.com** (using their **Free Web Service** tier) with zero manual environment configuration:

1. **Push this repository to GitHub** (make sure `.gitignore` keeps the repo clean from large binaries/apk files).
2. Go to your **Render Dashboard** and select **New +** ➡️ **Web Service**.
3. Connect your GitHub repository.
4. Set the following configurations:
   - **Language**: `Python`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `python southradios_proxy.py`
   - **Instance Type**: `Free`
5. Click **Deploy Web Service**!

Render will build your environment and provide a public URL (e.g. `https://freeradiotamil.onrender.com/`). The dashboard automatically detects the cloud hosting and updates all copied links to your dynamic public URL.
