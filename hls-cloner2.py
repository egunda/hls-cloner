import os
import requests
import threading
from urllib.parse import urljoin, urlparse
import m3u8
import urllib3

# Disable SSL warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

DEFAULT_THREADS = 5

def download_file(url, local_path, headers=None):
    try:
        response = requests.get(url, headers=headers, stream=True, verify=False)
        response.raise_for_status()
        os.makedirs(os.path.dirname(local_path), exist_ok=True)
        with open(local_path, 'wb') as file:
            for chunk in response.iter_content(chunk_size=8192):
                file.write(chunk)
        return True
    except Exception as e:
        print(f"Error downloading {url}: {e}")
        return False

def process_playlist(base_url, playlist_url, headers, max_files_per_stream):
    try:
        playlist_full_url = urljoin(base_url, playlist_url)
        relative_path = os.path.relpath(urlparse(playlist_full_url).path, '/')
        local_playlist_path = os.path.join(relative_path)
        
        print(f"Downloading playlist {playlist_full_url} to {local_playlist_path}")
        
        if not download_file(playlist_full_url, local_playlist_path, headers):
            return
        
        with open(local_playlist_path, 'r') as file:
            playlist_content = file.read()
        
        playlist = m3u8.loads(playlist_content)
        
        ts_files = [seg.uri for seg in playlist.segments]
        
        if isinstance(max_files_per_stream, int):
            ts_files = ts_files[:max_files_per_stream]
        
        for ts_file in ts_files:
            ts_url = urljoin(playlist_full_url, ts_file)
            ts_relative_path = os.path.relpath(urlparse(ts_url).path, '/')
            local_ts_path = os.path.join(ts_relative_path)
            
            if os.path.exists(local_ts_path):
                print(f"{local_ts_path} already exists, skipping")
                continue
            
            print(f"Downloading TS file from {ts_url} to {local_ts_path}")
            if download_file(ts_url, local_ts_path, headers):
                print("TS file downloaded")
            else:
                print(f"Error downloading TS file from {ts_url}")
    except Exception as e:
        print(f"Error processing playlist {playlist_url}: {e}")

def download_ts_files(m3u8_url, headers=None, max_files_per_stream=None):
    try:
        response = requests.get(m3u8_url, headers=headers, verify=False)
        response.raise_for_status()
        
        relative_path = os.path.relpath(urlparse(m3u8_url).path, '/')
        local_manifest_path = os.path.join(relative_path)
        
        os.makedirs(os.path.dirname(local_manifest_path), exist_ok=True)
        
        with open(local_manifest_path, 'wb') as file:
            file.write(response.content)
        
        master_playlist = m3u8.loads(response.text)
        
        base_url = os.path.dirname(m3u8_url)
        
        if master_playlist.is_variant:
            for variant in master_playlist.playlists:
                variant_url = variant.uri
                print(f"Processing variant playlist: {variant_url}")
                process_playlist(base_url, variant_url, headers, max_files_per_stream)
        else:
            print(f"Processing master playlist: {m3u8_url}")
            process_playlist(base_url, m3u8_url, headers, max_files_per_stream)
    except Exception as e:
        print(f"Error downloading TS files from {m3u8_url}: {e}")

def main():
    url = input("Enter the URL of the M3U8 playlist: ").strip()
    domain = urlparse(url).netloc
    
    headers = {"Host": domain}
    
    local_manifest = os.path.relpath(urlparse(url).path, '/')
    
    if os.path.exists(local_manifest) and os.path.exists("all_playlists.txt"):
        print(f"{local_manifest} already exists, skipping.")
    else:
        print(f"Downloading master manifest from {url}")
        if download_file(url, local_manifest, headers):
            print("Manifest downloaded, building list of playlists")
            with open(local_manifest, 'r') as file:
                lines = file.readlines()
            
            playlists = []
            for i, line in enumerate(lines):
                if "#EXT-X-STREAM-INF:" in line or "#EXT-X-MEDIA" in line:
                    if i + 1 < len(lines):
                        next_line = lines[i + 1].strip()
                        if next_line.endswith(".m3u8"):
                            playlists.append(next_line)
            
            with open("all_playlists.txt", 'w') as file:
                file.write('\n'.join(playlists))
        else:
            print("Error downloading manifest")
            return
    
    print("all_playlists.txt:")
    with open("all_playlists.txt", 'r') as file:
        playlists = file.readlines()
    
    num_threads = int(input(f"Enter number of threads (default {DEFAULT_THREADS}): ") or DEFAULT_THREADS)
    
    max_files_input = input("How many chunks do you want to download? (Enter a number or 'All' for all chunks): ").strip()
    if max_files_input.lower() == 'all' or max_files_input == '':
        max_files_per_stream = None
    else:
        max_files_per_stream = int(max_files_input)
    
    threads = []
    
    for playlist in playlists:
        playlist = playlist.strip()
        thread = threading.Thread(target=download_ts_files, args=(urljoin(url, playlist), headers, max_files_per_stream))
        threads.append(thread)
        thread.start()
        
        if len(threads) >= num_threads:
            for t in threads:
                t.join()
            threads = []
    
    for t in threads:
        t.join()
    
    os.remove("all_playlists.txt")

if __name__ == "__main__":
    main()
