import re
import time
from pathlib import Path

import requests

# Configuration
SVG_FILE = Path("new_readme.svg")
ASSETS_DIR = Path("assets")
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
TIMEOUT = 15  # seconds


def fetch_and_save(url: str, file_path: Path):
    """Fetches content from a URL and saves it to a file."""
    try:
        print(f"Fetching: {url}")
        headers = {"User-Agent": USER_AGENT}
        response = requests.get(url, timeout=TIMEOUT, headers=headers)

        # Raise an exception for bad status codes (4xx or 5xx)
        response.raise_for_status()

        # Ensure the parent directory exists
        file_path.parent.mkdir(parents=True, exist_ok=True)

        # Write the content to the file
        with open(file_path, "wb") as f:
            f.write(response.content)

        print(f"  -> Saved to: {file_path}")
        return True

    except requests.exceptions.RequestException as e:
        print(f"  -> Error fetching {url}: {e}")
    except IOError as e:
        print(f"  -> Error saving to {file_path}: {e}")
    except Exception as e:
        print(f"  -> An unexpected error occurred: {e}")

    return False


def main():
    """
    Parses the SVG file, finds asset URLs, and updates the local asset files.
    """
    if not SVG_FILE.is_file():
        print(f"Error: Source SVG file not found at '{SVG_FILE}'")
        return

    print(f"Processing '{SVG_FILE}' to update assets...")

    content = SVG_FILE.read_text()

    # Regex to find URL comments and their corresponding image hrefs
    # It captures the URL and the local path.
    pattern = re.compile(
        r'<!--\s*(?:href=")?(https?://.*?)"?\s*-->.*?href="(\./assets/.*?)"',  # TODO: remove href
        re.DOTALL | re.IGNORECASE,
    )

    matches = pattern.findall(content)

    if not matches:
        print("No asset URLs found in the SVG file.")
        return

    print(f"Found {len(matches)} assets to update.")
    success_count = 0

    for url, local_path_str in matches:
        # Clean up the URL if it has trailing characters
        url = url.strip()

        # The regex captures './assets/...' so we create a Path object from it.
        # Path() will handle the './' correctly.
        local_path = Path(local_path_str)

        if fetch_and_save(url, local_path):
            success_count += 1

        # Add a small delay to be polite to the servers
        time.sleep(1)

    print(
        f"\nUpdate complete. {success_count}/{len(matches)} assets updated successfully."
    )


if __name__ == "__main__":
    main()
