import os
import requests
from urllib.parse import urljoin, urlparse
import m3u8
import urllib3

# Disable SSL warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def log_progress(message):
    with open("progress.txt", 'a') as progress_file:
        progress_file.write(message + '\n')
    print(message)

def create_playlist_file():
    input_file = 'input.txt'
    output_file = 'all_playlists_highest.txt'

    # Clear the output file if it exists
    open(output_file, 'w').close()

    with open(input_file, 'r') as infile:
        urls = [line.strip() for line in infile if line.strip()]
    
    with open(output_file, 'a') as outfile:
        outfile.write("TsvHttpData-1.0\n")  # Static first line

    priority_profiles = ['720', '688', '480', '360', '240']  # Highest to lowest preference

    for master_url in urls:
        log_progress(f'Processing master playlist: {master_url}')
        try:
            response = requests.get(master_url, verify=False)
            response.raise_for_status()
            master_playlist = m3u8.loads(response.text)
        except Exception as e:
            log_progress(f"Error fetching master playlist {master_url}: {e}")
            continue

        # Extract base URL for key file
        parsed_url = urlparse(master_url)
        base_path = '/'.join(parsed_url.path.split('/')[:-1])  # Extract base path from URL
        key_file_url = urljoin(f'{parsed_url.scheme}://{parsed_url.netloc}{base_path}/', 'hls/enc.key')
        
        selected_variant_url = None
        ts_urls = []

        if master_playlist.is_variant:
            for profile in priority_profiles:
                for playlist in master_playlist.playlists:
                    variant_uri = playlist.uri
                    if profile in variant_uri:
                        selected_variant_url = urljoin(master_url, variant_uri)
                        log_progress(f'Selected variant profile: {profile}, URL: {selected_variant_url}')
                        break
                if selected_variant_url:
                    break

            if selected_variant_url:
                try:
                    variant_response = requests.get(selected_variant_url, verify=False)
                    variant_response.raise_for_status()
                    variant_playlist = m3u8.loads(variant_response.text)
                except Exception as e:
                    log_progress(f"Error fetching variant playlist {selected_variant_url}: {e}")
                    continue

                # Extract all .ts segment URLs
                for segment in variant_playlist.segments:
                    ts_url = urljoin(selected_variant_url, segment.uri)
                    ts_urls.append(ts_url)
        else:
            # Non-variant playlist (single playlist with .ts segments)
            log_progress(f'Processing single playlist: {master_url}')
            for segment in master_playlist.segments:
                ts_url = urljoin(master_url, segment.uri)
                ts_urls.append(ts_url)

        # Write to the output file in proper order
        with open(output_file, 'a') as outfile:
            if selected_variant_url:
                outfile.write(f'{selected_variant_url}\n')
            for url in ts_urls:
                outfile.write(f'{url}\n')
            if ts_urls:  # Ensure key file is written only if there's relevant data
                outfile.write(f'{key_file_url}\n')
    
    log_progress("Playlist generation complete. Check 'all_playlists_highest.txt' for the URLs.")

if __name__ == "__main__":
    create_playlist_file()
