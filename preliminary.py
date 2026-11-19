from requests import get
from pathlib import Path
from sys import argv
import re

root = Path(__file__).resolve().parent
OUTPUT_FOLDER = root / "Observations"
OUTPUT_FOLDER.mkdir(parents=True, exist_ok=True)

if len(argv) != 2:
    print(f"Unexpected number of arguments. Run python {argv[0]} \"[name of body]\"")
    exit(1)

# Get the body from the MPC
body_name = str(argv[1])
# TODO: Name recognition. "Ceres", while an unambiguous name, is not accepted by MPC.get_observations()
# Request observations for an object in ADES XML format
response = get("https://data.minorplanetcenter.net/api/get-obs", json={"desigs": [body_name], "output_format": ["XML"]})

# Function to sanitize an XML string
def sanitize(text):
    # Replace ampersands that aren't valid XML entity references
    sanitized, replacements = re.subn(
        r'&(?!amp;|lt;|gt;|quot;|apos;|#\d+;|#x[0-9a-fA-F]+;)',
        '&amp;',
        text,
    )
    return replacements > 0, sanitized

if response.ok:
    # Save the file to "{body_name}.xml"
    output_path = OUTPUT_FOLDER / f"{body_name.replace(' ', '_')}.xml"
    data = response.json()
    ades_xml = data[0]["XML"]
    changed, ades_xml = sanitize(ades_xml)
    if (changed):
        print("Warning: downloaded XML file has to be modified by regex")
    with open(output_path, "w", encoding="utf-8") as xml_file:
        xml_file.write(ades_xml)