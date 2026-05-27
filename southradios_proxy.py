import http.server
import socketserver
import requests
import time
import random
import urllib.parse
import sys
import json
import os

PORT = int(os.environ.get("PORT", 8080))

# Slugs mapping for all stations in the database
STATIONS_DB = {}
POPULAR_IDS = [
    "rajahmelody", "puradsifm", "tamilbeatradio", "raajankam3d", 
    "rahmaniyam3d", "devaradio", "tamil90shitradio", "tamil80shitsradio", 
    "goldensouthradios", "kadhalradio", "tamilmelodyradio", "spbradio", 
    "kschitra", "swarnalatharadio", "shreyaradio", "kjyesudas", "manoradio"
]

def make_slug(name):
    # Strip non-alphanumeric, replace spaces/underscores with hyphens
    cleaned = "".join(c if c.isalnum() or c in " _-" else "" for c in name)
    cleaned = cleaned.lower().replace(" ", "-").replace("_", "-")
    while "--" in cleaned:
        cleaned = cleaned.replace("--", "-")
    return cleaned.strip("-")

def should_proxy_station(station_obj):
    url = station_obj.get("streamUrl", "").lower()
    genres = station_obj.get("genre", [])
    if isinstance(genres, str):
        genres = [genres]
    is_southradios_genre = any("southradios" in g.lower() for g in genres)
    return "apipermission.southradios" in url or "southradios" in url or is_southradios_genre

def load_all_stations():
    global STATIONS_DB
    stations_path = "all_stations.json"
    if not os.path.exists(stations_path):
        # Fallback to local Windows absolute path
        stations_path = "c:/Users/Yuvandass/Downloads/southradios/all_stations.json"
        
    if not os.path.exists(stations_path):
        print(f"\n[WARNING] Could not find {stations_path}! Proxy will run with mock data.")
        return False
        
    try:
        with open(stations_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            
        results = data.get("results", [])
        for s in results:
            name = s.get("name", "Unknown").strip()
            stream_url = s.get("streamUrl", "").strip()
            sub_title = s.get("subTitle", "").strip()
            genre_list = s.get("Genre", ["General"])
            
            if not stream_url:
                continue
                
            # Create a base station object
            station_obj = {
                "name": name,
                "streamUrl": stream_url,
                "subTitle": sub_title,
                "genre": genre_list
            }
            
            # Map by slug
            slug = make_slug(name)
            if slug:
                STATIONS_DB[slug] = station_obj
                
            # Map by apipermission id if applicable
            if "apipermission.southradios.net/play/" in stream_url:
                api_id = stream_url.split("/play/")[-1].strip().lower()
                if api_id:
                    STATIONS_DB[api_id] = station_obj
                    
            # Map by identifier if applicable
            ident = s.get("identifier", "").strip().lower()
            if ident and ident != "none":
                STATIONS_DB[ident] = station_obj
                
        print(f"[INIT] Successfully loaded and mapped {len(STATIONS_DB)} station routing paths!")
        return True
    except Exception as e:
        print(f"[INIT] [ERROR] Failed to parse stations JSON: {e}")
        return False

# Initialize database
load_all_stations()

class RadioProxyHandler(http.server.BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        pass

    def do_GET(self):
        parsed_path = urllib.parse.urlparse(self.path)
        path_parts = parsed_path.path.strip("/").split("/")
        
        if len(path_parts) == 2 and path_parts[0] == "play":
            station_key = path_parts[1].lower()
            self.handle_stream(station_key)
        elif self.path == "/" or self.path == "":
            self.handle_index()
        else:
            self.send_error(404, "Not Found")

    def handle_index(self):
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.end_headers()
        
        # Get protocol and host dynamically to support cloud hosting on Render
        proto = self.headers.get("X-Forwarded-Proto", "http")
        host = self.headers.get("Host", f"127.0.0.1:{PORT}")
        
        # Build unique genre list
        genres = set()
        for s in STATIONS_DB.values():
            for g in s["genre"]:
                if g:
                    genres.add(g.strip())
        sorted_genres = sorted(list(genres))
        
        # Build structured stations JSON for front-end search
        web_stations = []
        seen_names = set()
        for slug, s in STATIONS_DB.items():
            # Avoid duplicating same station in web cards (since we map slugs & identifiers to same obj)
            if s["name"] in seen_names:
                continue
            seen_names.add(s["name"])
            
            is_popular = any(pid in s["streamUrl"].lower() for pid in POPULAR_IDS) or slug in POPULAR_IDS
            play_url = f"{proto}://{host}/play/{slug}" if should_proxy_station(s) else s["streamUrl"]
            web_stations.append({
                "name": s["name"],
                "subTitle": s["subTitle"],
                "genre": s["genre"],
                "playUrl": play_url,
                "popular": is_popular
            })
            
        # Sort so popular ones are displayed first, then alphabetically
        web_stations.sort(key=lambda x: (not x["popular"], x["name"]))
        stations_json = json.dumps(web_stations, ensure_ascii=False)
        
        html = f"""
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="utf-8">
            <meta name="viewport" content="width=device-width, initial-scale=1">
            <title>Tamil Free Radio Clean Proxy Server</title>
            <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700&display=swap" rel="stylesheet">
            <style>
                :root {{
                    --bg-main: #0b0b0f;
                    --bg-card: #14141e;
                    --bg-chip: #1e1e2d;
                    --accent: #ff5722;
                    --accent-glow: rgba(255, 87, 34, 0.4);
                    --text-main: #f0f0f5;
                    --text-sub: #8e8e9a;
                    --border: rgba(255, 255, 255, 0.05);
                }}
                
                body {{
                    font-family: 'Inter', sans-serif;
                    background-color: var(--bg-main);
                    color: var(--text-main);
                    margin: 0;
                    padding: 0;
                    display: flex;
                    flex-direction: column;
                    align-items: center;
                    min-height: 100vh;
                    overflow-x: hidden;
                }}
                
                header {{
                    width: 100%;
                    max-width: 1200px;
                    padding: 40px 20px;
                    box-sizing: border-box;
                    display: flex;
                    flex-direction: column;
                    align-items: center;
                    text-align: center;
                }}
                
                h1 {{
                    font-size: 2.8em;
                    font-weight: 700;
                    margin: 0 0 10px 0;
                    background: linear-gradient(135deg, #ff8a65, var(--accent));
                    -webkit-background-clip: text;
                    -webkit-text-fill-color: transparent;
                }}
                
                p.tagline {{
                    font-size: 1.15em;
                    color: var(--text-sub);
                    max-width: 600px;
                    margin: 0 0 30px 0;
                    line-height: 1.6em;
                }}
                
                .instructions {{
                    background: rgba(255, 87, 34, 0.05);
                    border: 1px solid rgba(255, 87, 34, 0.15);
                    padding: 16px 24px;
                    border-radius: 12px;
                    max-width: 700px;
                    text-align: left;
                    margin-bottom: 40px;
                    box-shadow: 0 8px 32px rgba(0, 0, 0, 0.5);
                }}
                
                .instructions h3 {{
                    margin: 0 0 8px 0;
                    color: var(--accent);
                }}
                
                .instructions ol {{
                    margin: 0;
                    padding-left: 20px;
                    color: var(--text-main);
                    line-height: 1.6em;
                }}
                
                .search-container {{
                    width: 100%;
                    max-width: 600px;
                    margin-bottom: 25px;
                    position: relative;
                }}
                
                .search-bar {{
                    width: 100%;
                    padding: 16px 24px;
                    font-size: 1.1em;
                    border-radius: 30px;
                    border: 1px solid var(--border);
                    background-color: var(--bg-card);
                    color: var(--text-main);
                    box-sizing: border-box;
                    outline: none;
                    transition: all 0.3s ease;
                    box-shadow: 0 4px 20px rgba(0,0,0,0.3);
                }}
                
                .search-bar:focus {{
                    border-color: var(--accent);
                    box-shadow: 0 0 15px var(--accent-glow);
                }}
                
                .filter-container {{
                    display: flex;
                    flex-wrap: wrap;
                    justify-content: center;
                    gap: 10px;
                    max-width: 900px;
                    margin-bottom: 40px;
                    padding: 0 20px;
                }}
                
                .chip {{
                    padding: 8px 16px;
                    background-color: var(--bg-chip);
                    border: 1px solid var(--border);
                    border-radius: 20px;
                    cursor: pointer;
                    font-size: 0.9em;
                    font-weight: 600;
                    color: var(--text-sub);
                    transition: all 0.2s ease;
                }}
                
                .chip:hover {{
                    border-color: var(--accent);
                    color: var(--text-main);
                }}
                
                .chip.active {{
                    background-color: var(--accent);
                    color: #fff;
                    border-color: var(--accent);
                    box-shadow: 0 4px 10px var(--accent-glow);
                }}
                
                .grid-container {{
                    width: 100%;
                    max-width: 1200px;
                    padding: 0 20px 60px 20px;
                    box-sizing: border-box;
                    display: grid;
                    grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
                    gap: 20px;
                }}
                
                .card {{
                    background-color: var(--bg-card);
                    border: 1px solid var(--border);
                    border-radius: 16px;
                    padding: 24px;
                    display: flex;
                    flex-direction: column;
                    position: relative;
                    transition: all 0.3s ease;
                    box-shadow: 0 8px 16px rgba(0,0,0,0.2);
                }}
                
                .card:hover {{
                    transform: translateY(-5px);
                    border-color: rgba(255, 87, 34, 0.3);
                    box-shadow: 0 12px 24px rgba(255, 87, 34, 0.1);
                }}
                
                .card-title {{
                    font-size: 1.25em;
                    font-weight: 600;
                    margin: 0 0 8px 0;
                    color: #fff;
                    display: flex;
                    align-items: center;
                    justify-content: space-between;
                }}
                
                .popular-badge {{
                    font-size: 0.55em;
                    background-color: var(--accent);
                    color: #fff;
                    padding: 4px 8px;
                    border-radius: 12px;
                    text-transform: uppercase;
                    font-weight: 700;
                    letter-spacing: 0.5px;
                }}
                
                .card-subtitle {{
                    font-size: 0.9em;
                    color: var(--text-sub);
                    margin: 0 0 20px 0;
                    line-height: 1.4em;
                    flex-grow: 1;
                }}
                
                .card-tags {{
                    display: flex;
                    flex-wrap: wrap;
                    gap: 6px;
                    margin-bottom: 20px;
                }}
                
                .tag {{
                    font-size: 0.75em;
                    padding: 4px 8px;
                    background-color: rgba(255,255,255,0.03);
                    border: 1px solid var(--border);
                    border-radius: 4px;
                    color: var(--text-sub);
                }}
                
                .copy-btn {{
                    width: 100%;
                    padding: 12px;
                    border-radius: 8px;
                    border: none;
                    background-color: #1e1e2d;
                    color: #fff;
                    font-weight: 600;
                    font-size: 0.95em;
                    cursor: pointer;
                    transition: all 0.2s ease;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    gap: 8px;
                }}
                
                .copy-btn:hover {{
                    background-color: var(--accent);
                    box-shadow: 0 4px 12px var(--accent-glow);
                }}
                
                .copy-btn:active {{
                    transform: scale(0.98);
                }}
                
                /* Toast notification */
                .toast {{
                    position: fixed;
                    bottom: 30px;
                    background-color: #4caf50;
                    color: #fff;
                    padding: 12px 24px;
                    border-radius: 30px;
                    font-weight: 600;
                    box-shadow: 0 8px 24px rgba(76, 175, 80, 0.4);
                    transform: translateY(100px);
                    opacity: 0;
                    transition: all 0.3s cubic-bezier(0.175, 0.885, 0.32, 1.275);
                    z-index: 1000;
                }}
                
                .toast.show {{
                    transform: translateY(0);
                    opacity: 1;
                }}
            </style>
        </head>
        <body>
            <header>
                <h1>Tamil Free Radio Premium Proxy 📻</h1>
                <p class="tagline">Providing dynamically authorized, clean, ad-free streaming URLs for every single station in the database.</p>
                
                <div class="instructions">
                    <h3>💡 How to Stream in VLC:</h3>
                    <ol>
                        <li>Click the <strong>"Copy VLC Link"</strong> button on any station card below.</li>
                        <li>Open <strong>VLC Media Player</strong> on your computer.</li>
                        <li>Press <strong>Ctrl + N</strong> (Open Network Stream), paste the link, and hit <strong>Play</strong>!</li>
                    </ol>
                </div>
                
                <div class="search-container">
                    <input type="text" class="search-bar" id="search" placeholder="Search 500+ stations by name, genre..." oninput="filterStations()">
                </div>
                
                <div class="filter-container">
                    <span class="chip active" onclick="setGenre('all', this)">All Stations</span>
                    <span class="chip" onclick="setGenre('popular', this)">⭐ Popular Only</span>
        """
        for g in sorted_genres:
            html += f'<span class="chip" onclick="setGenre(\'{g}\', this)">{g}</span>'
            
        html += f"""
                </div>
            </header>
            
            <div class="grid-container" id="grid">
                <!-- Cards injected by JS -->
            </div>
            
            <div class="toast" id="toast">Copied to Clipboard!</div>
            
            <script>
                const stations = {stations_json};
                let activeGenre = 'all';
                let searchText = '';
                
                function filterStations() {{
                    searchText = document.getElementById('search').value.toLowerCase().trim();
                    renderGrid();
                }}
                
                function setGenre(genre, element) {{
                    document.querySelectorAll('.chip').forEach(c => c.classList.remove('active'));
                    element.classList.add('active');
                    activeGenre = genre;
                    renderGrid();
                }}
                
                function copyToClipboard(text) {{
                    navigator.clipboard.writeText(text).then(() => {{
                        const toast = document.getElementById('toast');
                        toast.classList.add('show');
                        setTimeout(() => {{
                            toast.classList.remove('show');
                        }}, 2000);
                    }});
                }}
                
                function renderGrid() {{
                    const grid = document.getElementById('grid');
                    grid.innerHTML = '';
                    
                    const filtered = stations.filter(s => {{
                        const matchesSearch = s.name.toLowerCase().includes(searchText) || 
                                              s.subTitle.toLowerCase().includes(searchText) || 
                                              s.genre.some(g => g.toLowerCase().includes(searchText));
                        
                        let matchesGenre = false;
                        if (activeGenre === 'all') {{
                            matchesGenre = true;
                        }} else if (activeGenre === 'popular') {{
                            matchesGenre = s.popular;
                        }} else {{
                            matchesGenre = s.genre.includes(activeGenre);
                        }}
                        
                        return matchesSearch && matchesGenre;
                    }});
                    
                    if (filtered.length === 0) {{
                        grid.innerHTML = '<div style="grid-column: 1/-1; text-align: center; color: var(--text-sub); padding: 40px; font-size: 1.2em;">No stations found matching your search.</div>';
                        return;
                    }}
                    
                    filtered.forEach(s => {{
                        const card = document.createElement('div');
                        card.className = 'card';
                        
                        const titleEl = document.createElement('h3');
                        titleEl.className = 'card-title';
                        titleEl.textContent = s.name;
                        
                        if (s.popular) {{
                            const badge = document.createElement('span');
                            badge.className = 'popular-badge';
                            badge.textContent = '⭐ Popular';
                            titleEl.appendChild(badge);
                        }}
                        
                        const subEl = document.createElement('p');
                        subEl.className = 'card-subtitle';
                        subEl.textContent = s.subTitle || 'Live Radio Broadcast';
                        
                        const tagsEl = document.createElement('div');
                        tagsEl.className = 'card-tags';
                        s.genre.forEach(g => {{
                            const tag = document.createElement('span');
                            tag.className = 'tag';
                            tag.textContent = g;
                            tagsEl.appendChild(tag);
                        }});
                        
                        const btn = document.createElement('button');
                        btn.className = 'copy-btn';
                        btn.innerHTML = '📋 Copy VLC Link';
                        btn.onclick = () => copyToClipboard(s.playUrl);
                        
                        card.appendChild(titleEl);
                        card.appendChild(subEl);
                        card.appendChild(tagsEl);
                        card.appendChild(btn);
                        
                        grid.appendChild(card);
                    }});
                }}
                
                // Initial render
                renderGrid();
            </script>
        </body>
        </html>
        """
        self.wfile.write(html.encode("utf-8"))

    def handle_stream(self, station_key):
        # Open debug log file and clear it
        debug_log_path = "proxy_debug.txt"
        try:
            with open(debug_log_path, "w", encoding="utf-8") as lf:
                lf.write(f"=== Starting Dynamic Proxy Stream Handle for: {station_key} ===\n")
        except Exception:
            # Fallback to local Windows absolute path if relative folder is not writable
            debug_log_path = "c:/Users/Yuvandass/Downloads/southradios/proxy_debug.txt"
            try:
                with open(debug_log_path, "w", encoding="utf-8") as lf:
                    lf.write(f"=== Starting Dynamic Proxy Stream Handle for: {station_key} ===\n")
            except Exception:
                pass
            
        def log_debug(msg):
            try:
                # Strip non-ASCII emojis when printing to Windows terminal
                print(msg.encode('ascii', errors='ignore').decode('ascii'))
            except:
                pass
            try:
                with open(debug_log_path, "a", encoding="utf-8") as lf:
                    lf.write(msg + "\n")
            except:
                pass

        log_debug(f"[PROXY] Client requested station identifier: '{station_key}'")
        
        # 1. Lookup station in STATIONS_DB
        station = STATIONS_DB.get(station_key)
        if not station:
            log_debug(f"[PROXY] [ERROR] Station key '{station_key}' not found in loaded database!")
            self.send_error(404, f"Station key '{station_key}' not found")
            return
            
        station_name = station["name"]
        stream_url = station["streamUrl"]
        log_debug(f"[PROXY] Match found: '{station_name}' | DB Stream URL: {stream_url}")
        
        # 2. Bypass proxy with HTTP 302 redirect for direct non-SouthRadios streams
        if not should_proxy_station(station):
            log_debug(f"[PROXY] Bypass: Sending 302 Found redirect for direct stream URL: {stream_url}")
            self.send_response(302)
            self.send_header("Location", stream_url)
            self.end_headers()
            return
            
        # 3. Check if this is an apipermission/sentry gated stream
        if "apipermission.southradios.net/play/" in stream_url:
            # Extract sentry station_id from DB streamUrl
            sentry_station_id = stream_url.split("/play/")[-1].strip().lower()
            log_debug(f"[PROXY] Secured stream detected! Sentry station id: '{sentry_station_id}'")
            
            # Generate dynamic synchronized timestamps
            current_time_ms = int(time.time() * 1000)
            cb = f"{time.time():.5f}"
            session_id = f"{current_time_ms}.{random.randint(100000, 999999)}"
            
            query_string = (
                f"station={sentry_station_id}"
                "&companionAds=true"
                "&aw_0_awz.appVers=8.0.14%3A80000014"
                "&aw_0_1st.version=8.1.0%3Aandroid33"
                f"&aw_0_1st.ts={current_time_ms}"
                "&aw_0_req.permissions=CCCC1CCCCC1C00"
                "&calendar=0"
                "&aw_0_1st.playerId=Puradsifm%20_Android"
                f"&aw_0_1st.cb={cb}"
                f"&aw_0_1st.sessionid={session_id}"
                "&aw_0_req.appState=fg"
                "&sdkiad=1"
                "&aw_0_req.bundleId=com.southradios"
                "&aw_0_req.tapOpp=false"
                "&aw_0_awz.listenerid=00000000-0000-0000-0000-000000000000"
                "&aw_0_req.lmt=1"
                "&aw_0_1st.ifaType=fireOS"
                "&aw_0_req.wopp=0"
                "&aw_0_1st.ifa=00000000-0000-0000-0000-000000000000"
            )
            
            # Stage 1: Resolve redirects manually using Dalvik UA
            next_url = f"http://apipermission.southradios.net/play/{sentry_station_id}?{query_string}"
            dalvik_headers = {
                "User-Agent": "Dalvik/2.1.0 (Linux; U; Android 13; Subsystem for Android Build/33)"
            }
            
            redirect_count = 0
            direct_stream_url = None
            
            log_debug("[PROXY] Initiating Sentry authorization handshake...")
            while redirect_count < 5:
                try:
                    log_debug(f"[PROXY] Querying sentry hop URL: {next_url}")
                    r = requests.get(next_url, headers=dalvik_headers, allow_redirects=False, stream=True, timeout=5)
                    log_debug(f"[PROXY] Sentry hop returned status: {r.status_code}")
                    r.close() # Close immediately
                    
                    if r.status_code in (301, 302):
                        loc = r.headers.get("Location")
                        if not loc:
                            log_debug("[PROXY] Redirect status but no Location header!")
                            break
                        
                        log_debug(f"[PROXY] Redirected to: {loc}")
                        if "listenon.in" in loc:
                            direct_stream_url = loc
                            break
                        else:
                            next_url = loc
                            redirect_count += 1
                    else:
                        if "listenon.in" in next_url:
                            direct_stream_url = next_url
                        break
                except Exception as e:
                    log_debug(f"[PROXY] Redirect trace exception: {e}")
                    break
                    
            if not direct_stream_url:
                log_debug("[PROXY] [ERROR] Failed to dynamically authorize stream via sentry.")
                self.send_error(502, "Bad Gateway - Sentry authorization failed")
                return
                
            # Rewrite psrlive1 and psrlive2 to psrlive3 to bypass the ad-injection cluster blocks!
            if "psrlive1.listenon.in" in direct_stream_url:
                direct_stream_url = direct_stream_url.replace("psrlive1.listenon.in", "psrlive3.listenon.in")
                log_debug("[PROXY] Bypassing Ad-Injection Server: Rewrote psrlive1 -> psrlive3")
            elif "psrlive2.listenon.in" in direct_stream_url:
                direct_stream_url = direct_stream_url.replace("psrlive2.listenon.in", "psrlive3.listenon.in")
                log_debug("[PROXY] Bypassing Ad-Injection Server: Rewrote psrlive2 -> psrlive3")
                
            target_url = direct_stream_url
        else:
            # Direct non-secured stream URL
            log_debug(f"[PROXY] Direct non-secured stream detected. Directing to target stream.")
            target_url = stream_url
            
        # Stage 2: Connect and stream audio to client with clean okhttp UA
        okhttp_headers = {
            "User-Agent": "okhttp/4.9.1"
        }
        
        try:
            log_debug(f"[PROXY] Connecting to final stream URL:\n  {target_url}")
            remote_response = requests.get(target_url, headers=okhttp_headers, stream=True, timeout=10)
            
            if remote_response.status_code != 200:
                log_debug(f"[PROXY] [ERROR] Remote server returned status {remote_response.status_code}")
                self.send_error(remote_response.status_code, "Remote streaming error")
                remote_response.close()
                return
                
            remote_name = remote_response.headers.get("icy-name", station_name)
            remote_desc = remote_response.headers.get("icy-description", "")
            log_debug(f"[PROXY] Connected! Stream Name: {remote_name} | Description: {remote_desc}")
            
            # Send HTTP response headers to client
            self.send_response(200)
            
            for header_name in ["Content-Type", "icy-name", "icy-description", "icy-genre", "icy-br"]:
                val = remote_response.headers.get(header_name)
                if val:
                    self.send_header(header_name, val)
            
            self.send_header("Connection", "close")
            self.end_headers()
            
            log_debug("[PROXY] Proxying audio stream bytes to client... Enjoy the music!")
            bytes_forwarded = 0
            
            for chunk in remote_response.iter_content(chunk_size=4096):
                if chunk:
                    try:
                        self.wfile.write(chunk)
                        bytes_forwarded += len(chunk)
                    except (ConnectionResetError, ConnectionAbortedError, BrokenPipeError):
                        log_debug(f"[PROXY] Client disconnected. Stream closed. Forwarded {bytes_forwarded} bytes.")
                        break
            
            remote_response.close()
        except Exception as e:
            log_debug(f"[PROXY] [ERROR] Streaming exception: {e}")
            try:
                self.send_error(500, f"Streaming error: {e}")
            except:
                pass

class ThreadedHTTPServer(socketserver.ThreadingMixIn, http.server.HTTPServer):
    daemon_threads = True

def run():
    server_address = ('', PORT)
    httpd = ThreadedHTTPServer(server_address, RadioProxyHandler)
    
    print("\n" + "="*70)
    print(f"   TAMIL FREE RADIO UNIVERSAL PROXY SERVER RUNNING ON PORT {PORT}   ")
    print("="*70)
    print(f"\nLocal Interactive Dashboard Index: http://127.0.0.1:{PORT}/")
    print("\nLoad station dynamically using: http://127.0.0.1:8080/play/{station-id}")
    print("\nPress Ctrl+C to stop the proxy server.\n")
    
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping proxy server...")
        httpd.server_close()
        sys.exit(0)

if __name__ == "__main__":
    run()
