import base64
import mimetypes
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Dict, Optional


def create_data_uri(file_path: Path) -> Optional[str]:
    """Encodes a file into a Base64 Data URI."""
    if not file_path.is_file():
        print(f"Warning: Asset file not found at '{file_path}'. Skipping.")
        return None

    mime_type, _ = mimetypes.guess_type(file_path)
    if not mime_type:
        print(f"Warning: Could not determine MIME type for {file_path}. Skipping.")
        return None

    try:
        with open(file_path, "rb") as f:
            file_content = f.read()
        encoded_content = base64.b64encode(file_content).decode("utf-8")
        return f"data:{mime_type};base64,{encoded_content}"
    except Exception as e:
        print(f"Error processing {file_path}: {e}")
        return None


def embed_base64_image(image_element: ET.Element, file_path: Path):
    """Embeds a PNG or GIF as a Base64 Data URI."""
    data_uri = create_data_uri(file_path)
    if data_uri:
        image_element.set("href", data_uri)
        print("  -> Embedded as Base64 Data URI.")


def inline_svg_asset(
    image_element: ET.Element,
    file_path: Path,
    parent_map: Dict[ET.Element, ET.Element],
    svg_ns: str,
):
    """Inlines an SVG asset into the main SVG."""
    parent_g_element = parent_map.get(image_element)
    if parent_g_element is None or parent_g_element.tag != f"{{{svg_ns}}}g":
        print(
            f"  -> Warning: SVG asset '{file_path}' is not inside a <g> tag. Skipping."
        )
        return

    try:
        asset_tree = ET.parse(file_path)
        asset_root = asset_tree.getroot()

        for elem in asset_root.iter():
            if "}" in elem.tag:
                elem.tag = elem.tag.split("}", 1)[1]

        x = image_element.get("x", "0")
        y = image_element.get("y", "0")
        width = image_element.get("width")
        height = image_element.get("height")

        parent_g_element.set("transform", f"translate({x}, {y})")
        if width:
            asset_root.set("width", width)
        if height:
            asset_root.set("height", height)

        parent_g_element.remove(image_element)
        parent_g_element.append(asset_root)
        print(f"  -> Inlined content with transform: translate({x}, {y}).")

    except FileNotFoundError:
        print(f"  -> Warning: Asset file not found at '{file_path}'. Skipping.")
    except ET.ParseError as e:
        print(f"  -> Error parsing asset SVG '{file_path}': {e}. Skipping.")


def main():
    """
    Main function to process the SVG, embed assets, and write the output.
    """
    main_svg_path = Path("new_readme.svg")
    output_svg_path = Path("new_readme_embedded.svg")
    assets_dir = Path("./assets")

    svg_ns = "http://www.w3.org/2000/svg"
    ET.register_namespace("", svg_ns)

    try:
        tree = ET.parse(main_svg_path)
        root = tree.getroot()
    except FileNotFoundError:
        print(f"Error: Main SVG file not found at '{main_svg_path}'")
        return
    except ET.ParseError as e:
        print(f"Error parsing SVG file: {e}")
        return

    parent_map = {c: p for p in root.iter() for c in p}

    for image_element in root.findall(f".//{{{svg_ns}}}image"):
        href = image_element.get("href")
        if not href:
            continue

        file_path = Path(href)
        if assets_dir not in file_path.parents:
            continue

        print(f"Processing: {file_path}")

        if file_path.suffix in (".png", ".gif"):
            embed_base64_image(image_element, file_path)
        elif file_path.suffix == ".svg":
            inline_svg_asset(image_element, file_path, parent_map, svg_ns)

    tree.write(output_svg_path, encoding="utf-8", xml_declaration=True)
    print(f"\nProcessing complete. Output saved to '{output_svg_path}'")


if __name__ == "__main__":
    main()
