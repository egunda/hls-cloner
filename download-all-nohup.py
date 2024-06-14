import os
import requests
import threading
from urllib.parse import urljoin, urlparse
import m3u8
import urllib3

# Disable SSL warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

NUM_THREADS = 20
PROGRESS_FILE = "progress.txt"

def log_progress(message):
    with open(PROGRESS_FILE, 'a') as progress_file:
        progress_file.write(message + '\n')
    print(message)

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
        log_progress(f"Error downloading {url}: {e}")
        return False

def process_playlist(base_url, playlist_url, headers, max_files_per_stream):
    try:
        playlist_full_url = urljoin(base_url, playlist_url)
        relative_path = os.path.relpath(urlparse(playlist_full_url).path, '/')
        local_playlist_path = os.path.join(relative_path)
        
        log_progress(f"Downloading playlist {playlist_full_url} to {local_playlist_path}")
        
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
                log_progress(f"{local_ts_path} already exists, skipping")
                continue
            
            log_progress(f"Downloading TS file from {ts_url} to {local_ts_path}")
            if download_file(ts_url, local_ts_path, headers):
                log_progress("TS file downloaded")
            else:
                log_progress(f"Error downloading TS file from {ts_url}")
    except Exception as e:
        log_progress(f"Error processing playlist {playlist_url}: {e}")

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
                log_progress(f"Processing variant playlist: {variant_url}")
                process_playlist(base_url, variant_url, headers, max_files_per_stream)
        else:
            log_progress(f"Processing master playlist: {m3u8_url}")
            process_playlist(base_url, m3u8_url, headers, max_files_per_stream)
    except Exception as e:
        log_progress(f"Error downloading TS files from {m3u8_url}: {e}")

def main():
    with open("input.txt", 'r') as infile:
        urls = infile.readlines()

    max_files_per_stream = None

    for url in urls:
        url = url.strip()
        domain = urlparse(url).netloc
        
        headers = {"Host": domain}
        
        local_manifest = os.path.relpath(urlparse(url).path, '/')
        
        if os.path.exists(local_manifest) and os.path.exists("all_playlists.txt"):
            log_progress(f"{local_manifest} already exists, skipping.")
        else:
            log_progress(f"Downloading master manifest from {url}")
            if download_file(url, local_manifest, headers):
                log_progress("Manifest downloaded, building list of playlists")
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
                log_progress("Error downloading manifest")
                continue
        
        log_progress("all_playlists.txt:")
        with open("all_playlists.txt", 'r') as file:
            playlists = file.readlines()
        
        threads = []
        
        for playlist in playlists:
            playlist = playlist.strip()
            thread = threading.Thread(target=download_ts_files, args=(urljoin(url, playlist), headers, max_files_per_stream))
            threads.append(thread)
            thread.start()
            
            if len(threads) >= NUM_THREADS:
                for t in threads:
                    t.join()
                threads = []
        
        for t in threads:
            t.join()
        
        os.remove("all_playlists.txt")

if __name__ == "__main__":
    main()
