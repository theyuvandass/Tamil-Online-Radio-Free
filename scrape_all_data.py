import requests
import json
import os

headers = {
    "X-Parse-Application-Id": "southRadios"
}

def fetch_all_from_class(classname):
    print(f"Fetching all records for class '{classname}'...")
    results = []
    limit = 1000
    skip = 0
    
    while True:
        url = f"http://app.puradsi.com/config/classes/{classname}"
        params = {
            "limit": limit,
            "skip": skip,
            "order": "priority"
        }
        
        try:
            response = requests.get(url, headers=headers, params=params)
            if response.status_code != 200:
                print(f"  [ERROR] Status {response.status_code} for {classname}: {response.text}")
                break
                
            data = response.json()
            batch = data.get("results", [])
            results.extend(batch)
            print(f"  Fetched {len(batch)} items (total: {len(results)})")
            
            if len(batch) < limit:
                break
                
            skip += limit
        except Exception as e:
            print(f"  [EXCEPTION] {e}")
            break
            
    return results

# Fetch everything!
stations = fetch_all_from_class("Station")
podcasts = fetch_all_from_class("podcast")
videos = fetch_all_from_class("Video")
configs = fetch_all_from_class("AppConfig")

print(f"\nSummary:")
print(f"  Stations: {len(stations)}")
print(f"  Podcasts: {len(podcasts)}")
print(f"  Videos: {len(videos)}")
print(f"  Configs: {len(configs)}")

# Save raw stations to all_stations.json
output_raw = {
    "results": stations
}

with open("all_stations.json", "w", encoding="utf-8") as f:
    json.dump(output_raw, f, indent=2, ensure_ascii=False)
print("Saved raw stations to all_stations.json")

# Save other raw files
with open("all_podcasts.json", "w", encoding="utf-8") as f:
    json.dump({"results": podcasts}, f, indent=2, ensure_ascii=False)
with open("all_videos.json", "w", encoding="utf-8") as f:
    json.dump({"results": videos}, f, indent=2, ensure_ascii=False)
with open("all_configs.json", "w", encoding="utf-8") as f:
    json.dump({"results": configs}, f, indent=2, ensure_ascii=False)
print("Saved raw podcasts, videos, and configs to all_*.json")

# Extract and clean streams
extracted_streams = []
unique_urls = set()

for idx, station in enumerate(stations, 1):
    name = station.get("name", "Unknown")
    genre = station.get("Genre", "Unknown")
    stream_url = station.get("streamUrl", "").strip()
    identifier = station.get("identifier", "None")
    priority = station.get("priority", 0)
    
    # Clean name
    name = name.replace("\n", " ").strip()
    
    if stream_url:
        unique_urls.add(stream_url)
        
    extracted_streams.append({
        "index": idx,
        "name": name,
        "genre": genre,
        "streamUrl": stream_url,
        "identifier": identifier,
        "priority": priority
    })

with open("extracted_streams.json", "w", encoding="utf-8") as f:
    json.dump(extracted_streams, f, indent=2, ensure_ascii=False)
print(f"Saved {len(extracted_streams)} extracted streams to extracted_streams.json (unique URLs: {len(unique_urls)})")

# Generate compiled_stations.md
md_lines = [
    "# Tamil Free Radio - Complete Live Station Listing",
    "",
    f"Successfully extracted **{len(stations)} stations** from the live database, containing **{len(unique_urls)} unique streaming URLs**.",
    "",
    "## Summary by Category",
    ""
]

# Group by category (Genre can be a list or a string)
category_counts = {}
for s in extracted_streams:
    genre = s["genre"]
    if isinstance(genre, list):
        genre_str = ", ".join(genre)
    else:
        genre_str = str(genre)
        
    category_counts[genre_str] = category_counts.get(genre_str, 0) + 1

# Sort categories by count descending
sorted_categories = sorted(category_counts.items(), key=lambda x: x[1], reverse=True)

md_lines.append("| Category | Count |")
md_lines.append("|---|---|")
for cat, count in sorted_categories:
    md_lines.append(f"| {cat} | {count} |")
md_lines.append("")

# Group stations by category for detailed listing
grouped_stations = {}
for s in extracted_streams:
    genre = s["genre"]
    if isinstance(genre, list):
        genre_str = ", ".join(genre)
    else:
        genre_str = str(genre)
        
    if genre_str not in grouped_stations:
        grouped_stations[genre_str] = []
    grouped_stations[genre_str].append(s)

for cat, _ in sorted_categories:
    cat_stations = grouped_stations[cat]
    md_lines.append(f"## {cat} ({len(cat_stations)} Stations)")
    md_lines.append("")
    md_lines.append("| # | Station Name | Streaming URL | Identifier | Priority |")
    md_lines.append("|---|---|---|---|---|")
    
    # Sort stations by priority descending, then by name
    cat_stations_sorted = sorted(cat_stations, key=lambda x: (-x["priority"], x["name"]))
    
    for i, s in enumerate(cat_stations_sorted, 1):
        name = s["name"]
        url = s["streamUrl"]
        ident = s["identifier"]
        prio = s["priority"]
        md_lines.append(f"| {i} | {name} | `{url}` | `{ident}` | {prio} |")
    md_lines.append("")

with open("compiled_stations.md", "w", encoding="utf-8") as f:
    f.write("\n".join(md_lines))
print("Saved markdown listing to compiled_stations.md")
