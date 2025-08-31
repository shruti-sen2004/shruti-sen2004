import base64
import re
import os
import mimetypes

def embed_assets_as_data_uri(match):
    """
    A replacer function for re.sub that converts a file path
    from a regex match into a Data URI.
    """
    # The first captured group is the full path (e.g., './assets/girl.gif')
    asset_path = match.group(1)
    
    # Remove './' if it exists to get a clean path
    clean_path = asset_path.lstrip('./')

    print(f"Processing asset: {clean_path}...")

    if not os.path.exists(clean_path):
        print(f"  -> Warning: File not found. Skipping.")
        return match.group(0) # Return the original string if file doesn't exist

    try:
        # Guess the MIME type of the file (e.g., 'image/png', 'image/gif')
        mime_type, _ = mimetypes.guess_type(clean_path)
        if not mime_type:
            print(f"  -> Warning: Could not determine MIME type for {clean_path}. Skipping.")
            return match.group(0)

        # Read the file in binary mode
        with open(clean_path, 'rb') as f:
            asset_content = f.read()

        # Encode the content in Base64
        encoded_asset = base64.b64encode(asset_content).decode('utf-8')

        # Create the full Data URI string
        data_uri = f"data:{mime_type};base64,{encoded_asset}"

        # Return the new xlink:href attribute to replace the old one
        return f'xlink:href="{data_uri}"'
    except Exception as e:
        print(f"  -> Error processing {clean_path}: {e}")
        return match.group(0) # Return original on error

# --- Main script ---
main_svg_path = 'new_readme.svg'
output_svg_path = 'new_readme_embedded.svg'

try:
    with open(main_svg_path, 'r', encoding='utf-8') as f:
        svg_content = f.read()
except FileNotFoundError:
    print(f"Error: Main SVG file not found at '{main_svg_path}'")
    exit()

# Regex to find all xlink:href attributes pointing to the local assets directory
# It captures the path inside the quotes.
pattern = re.compile(r'xlink:href="(\./assets/[^"]+)"')

# Use re.sub with our replacer function to perform all replacements
updated_svg_content = pattern.sub(embed_assets_as_data_uri, svg_content)

# Write the result to a new file
with open(output_svg_path, 'w', encoding='utf-8') as f:
    f.write(updated_svg_content)

print(f"\nSuccessfully embedded all local assets into '{output_svg_path}'")