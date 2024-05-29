import os
import requests
import m3u8
from concurrent.futures import ThreadPoolExecutor, as_completed
from urllib.parse import urljoin, urlparse

def download_segment(url, save_path):
    try:
        r = requests.get(url, stream=True)
        if r.status_code == 200:
            with open(save_path, 'wb') as f:
                for chunk in r.iter_content(chunk_size=1024):
                    if chunk:
                        f.write(chunk)
            print(f"Downloaded: {save_path}")
        else:
            print(f"Failed to download: {url}")
    except Exception as e:
        print(f"Error downloading {url}: {e}")

def download_playlist(playlist_url, save_dir, num_threads):
    # Create save directory if it doesn't exist
    if not os.path.exists(save_dir):
        os.makedirs(save_dir)
    
    # Download master playlist
    master_playlist_content = requests.get(playlist_url).text
    master_playlist_path = os.path.join(save_dir, 'master.m3u8')
    with open(master_playlist_path, 'w') as f:
        f.write(master_playlist_content)
    
    master_playlist = m3u8.loads(master_playlist_content)

    def download_child_playlist(playlist, save_dir):
        child_playlist_url = urljoin(playlist_url, playlist.uri)
        child_playlist_content = requests.get(child_playlist_url).text
        child_playlist_path = os.path.join(save_dir, os.path.basename(playlist.uri))
        with open(child_playlist_path, 'w') as f:
            f.write(child_playlist_content)
        return m3u8.loads(child_playlist_content), os.path.dirname(child_playlist_path)

    # Download child playlists and their segments
    with ThreadPoolExecutor(max_workers=num_threads) as executor:
        future_to_playlist = {executor.submit(download_child_playlist, playlist, save_dir): playlist for playlist in master_playlist.playlists}
        for future in as_completed(future_to_playlist):
            child_playlist, child_dir = future.result()
            segment_urls = [urljoin(playlist_url, segment.uri) for segment in child_playlist.segments]
            save_paths = [os.path.join(child_dir, os.path.basename(urlparse(segment_url).path)) for segment_url in segment_urls]
            
            # Download all segments
            with ThreadPoolExecutor(max_workers=num_threads) as segment_executor:
                segment_futures = [segment_executor.submit(download_segment, url, path) for url, path in zip(segment_urls, save_paths)]
                for _ in as_completed(segment_futures):
                    pass

def main():
    import argparse
    parser = argparse.ArgumentParser(description='Download HLS multi-bitrate video with multiple threads.')
    
    # Ask user for inputs
    playlist_url = input("Enter the HLS URL: ").strip()
    if not playlist_url:
        print("HLS URL is required.")
        return

    threads_input = input("Enter the number of threads (default is 5): ").strip()
    num_threads = int(threads_input) if threads_input.isdigit() else 5

    save_dir = 'hls_download'

    download_playlist(playlist_url, save_dir, num_threads)
    print('Download complete.')

if __name__ == "__main__":
    main()
