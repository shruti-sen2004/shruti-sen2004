import base64
import mimetypes
import xml.etree.ElementTree as ET


def create_data_uri(file_path):
    """Encodes a file into a Base64 Data URI."""
    try:
        mime_type, _ = mimetypes.guess_type(file_path)
        if not mime_type:
            print(f"Warning: Could not determine MIME type for {file_path}. Skipping.")
            return None

        with open(file_path, "rb") as f:
            file_content = f.read()

        encoded_content = base64.b64encode(file_content).decode("utf-8")
        return f"data:{mime_type};base64,{encoded_content}"
    except FileNotFoundError:
        print(f"Warning: Asset file not found at '{file_path}'. Skipping.")
        return None
    except Exception as e:
        print(f"Error processing {file_path}: {e}")
        return None


def main():
    """
    Main function to process the SVG, embed assets, and write the output.
    """
    main_svg_path = "new_readme.svg"
    output_svg_path = "new_readme_embedded.svg"

    # Register namespaces to properly find and handle attributes like xlink:href
    namespaces = {
        "svg": "http://www.w3.org/2000/svg",
        "xlink": "http://www.w3.org/1999/xlink",
    }
    ET.register_namespace("", namespaces["svg"])
    ET.register_namespace("xlink", namespaces["xlink"])

    try:
        tree = ET.parse(main_svg_path)
        root = tree.getroot()
    except FileNotFoundError:
        print(f"Error: Main SVG file not found at '{main_svg_path}'")
        return
    except ET.ParseError as e:
        print(f"Error parsing SVG file: {e}")
        return

    # Find all <image> elements in the SVG
    images_to_process = root.findall(".//svg:image", namespaces)

    # Create a map of parent elements to their children to safely modify the tree
    parent_map = {c: p for p in root.iter() for c in p}

    for image_element in images_to_process:
        href_attr = f"{{{namespaces['xlink']}}}href"
        file_path = image_element.get(href_attr)

        if not file_path or not file_path.startswith("./assets/"):
            continue

        print(f"Processing: {file_path}")

        # --- Task 1: Handle PNG and GIF with Base64 ---
        if file_path.endswith(".png") or file_path.endswith(".gif"):
            data_uri = create_data_uri(file_path)
            if data_uri:
                image_element.set(href_attr, data_uri)
                print("  -> Embedded as Base64 Data URI.")

        # --- Task 2: Handle other SVGs by inlining content ---
        elif file_path.endswith(".svg"):
            parent_g_element = parent_map.get(image_element)
            if (
                parent_g_element is None
                or parent_g_element.tag != f"{{{namespaces['svg']}}}g"
            ):
                print(
                    f"  -> Warning: SVG asset '{file_path}' is not inside a <g> tag. Skipping."
                )
                continue

            try:
                # Read and parse the content of the asset SVG
                asset_tree = ET.parse(file_path)
                asset_root = asset_tree.getroot()

                # Remove namespace prefixes from the asset's tags for cleaner output
                for elem in asset_root.iter():
                    if "}" in elem.tag:
                        elem.tag = elem.tag.split("}", 1)[1]

                # Get positioning and dimensions from the original <image> tag
                x = image_element.get("x", "0")
                y = image_element.get("y", "0")
                width = image_element.get("width")
                height = image_element.get("height")

                # Apply a transform to the parent <g> tag to position the inlined content
                parent_g_element.set("transform", f"translate({x}, {y})")

                # Set width and height on the root of the asset SVG if they exist
                if width:
                    asset_root.set("width", width)
                if height:
                    asset_root.set("height", height)

                # Remove the original <image> tag
                parent_g_element.remove(image_element)

                # Insert the content (root element) of the asset SVG
                parent_g_element.append(asset_root)
                print(f"  -> Inlined content with transform: translate({x}, {y}).")

            except FileNotFoundError:
                print(f"  -> Warning: Asset file not found at '{file_path}'. Skipping.")
            except ET.ParseError as e:
                print(f"  -> Error parsing asset SVG '{file_path}': {e}. Skipping.")

    # Write the modified tree to a new file
    tree.write(output_svg_path, encoding="utf-8", xml_declaration=True)
    print(f"\nProcessing complete. Output saved to '{output_svg_path}'")


if __name__ == "__main__":
    main()

