import os
import requests
from urllib.parse import urlparse
from pathlib import Path

def download_image(url, folder):
    """Download an image from URL and save it to the specified folder."""
    if not url:
        return None
    
    # Create folder if it doesn't exist
    os.makedirs(folder, exist_ok=True)
    
    # Get filename from URL
    parsed_url = urlparse(url)
    filename = os.path.basename(parsed_url.path)
    
    # Full path for saving
    save_path = os.path.join(folder, filename)
    
    # Download image
    response = requests.get(url, stream=True)
    if response.status_code == 200:
        with open(save_path, 'wb') as f:
            for chunk in response.iter_content(1024):
                f.write(chunk)
        print(f"Downloaded: {url} -> {save_path}")
        # Return relative path from media folder
        return os.path.join(os.path.basename(folder), filename)
    else:
        print(f"Failed to download: {url}")
        return None

# URLs à télécharger
images = {
    'avatars': [
        'https://images.pexels.com/photos/774909/pexels-photo-774909.jpeg',
        'https://images.pexels.com/photos/220453/pexels-photo-220453.jpeg'
    ],
    'posts': [
        'https://images.pexels.com/photos/11035471/pexels-photo-11035471.jpeg',
        'https://images.pexels.com/photos/1181671/pexels-photo-1181671.jpeg'
    ],
    'podcast_covers': [
        'https://images.pexels.com/photos/1181671/pexels-photo-1181671.jpeg',
        'https://images.pexels.com/photos/546819/pexels-photo-546819.jpeg'
    ],
    'video_thumbnails': [
        'https://images.pexels.com/photos/3861972/pexels-photo-3861972.jpeg',
        'https://images.pexels.com/photos/4164418/pexels-photo-4164418.jpeg'
    ]
}

def main():
    # Set media root folder
    media_root = Path('media')
    
    # Download all images
    for folder, urls in images.items():
        folder_path = media_root / folder
        for url in urls:
            download_image(url, folder_path)

if __name__ == "__main__":
    main()