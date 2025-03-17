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
    output_file = 'all_playlists_simple.txt'

    # Clear the output file if it exists
    open(output_file, 'w').close()

    with open(input_file, 'r') as infile:
        urls = [line.strip() for line in infile if line.strip()]
    with open(output_file, 'a') as outfile:
        outfile.write("TsvHttpData-1.0\n")  # Static first line

    for master_url in urls:
        log_progress(f'Processing master playlist: {master_url}')
        try:
            response = requests.get(master_url, verify=False)
            response.raise_for_status()
            master_playlist = m3u8.loads(response.text)
        except Exception as e:
            log_progress(f"Error fetching master playlist {master_url}: {e}")
            continue

        if master_playlist.is_variant:
            for playlist in master_playlist.playlists:
                variant_uri = playlist.uri
                variant_url = urljoin(master_url, variant_uri)
                log_progress(f'Found variant playlist: {variant_url}')

                # Write the variant .m3u8 URL to the output file
                with open(output_file, 'a') as outfile:
                    outfile.write(f'{variant_url}\n')

                # Fetch and parse the variant playlist
                try:
                    variant_response = requests.get(variant_url, verify=False)
                    variant_response.raise_for_status()
                    variant_playlist = m3u8.loads(variant_response.text)
                except Exception as e:
                    log_progress(f"Error fetching variant playlist {variant_url}: {e}")
                    continue

                # Extract and write all .ts segment URLs
                for segment in variant_playlist.segments:
                    ts_url = urljoin(variant_url, segment.uri)
                    with open(output_file, 'a') as outfile:
                        outfile.write(f'{ts_url}\n')
        else:
            # Non-variant playlist (single playlist with .ts segments)
            log_progress(f'Processing single playlist: {master_url}')
            for segment in master_playlist.segments:
                ts_url = urljoin(master_url, segment.uri)
                with open(output_file, 'a') as outfile:
                    outfile.write(f'{ts_url}\n')

    log_progress("Playlist generation complete. Check 'all_playlists_simple.txt' for the URLs.")

if __name__ == "__main__":
    create_playlist_file()

