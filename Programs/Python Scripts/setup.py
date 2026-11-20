from pathlib import Path
from urllib.request import Request, urlopen
import hashlib
import os
import tempfile

# If the folder does not exist, then I'd rather just crash
# More files are needed from Data than are downloaded here
# Thus, if you face issues with this script, you face them
# elsewhere. Just redownload the project if this does fail
DATA_DIR = Path(__file__).parent.parent.parent / "Data"

# Everything we want to download
# This will contain more in the future
RESOURCES = [
    {"filepath": DATA_DIR / "de440.bsp", "url": "https://ssd.jpl.nasa.gov/ftp/eph/planets/bsp/de440.bsp"}
]

CHUNK_SIZE = 1024 * 1024

for resource in RESOURCES:
    url = resource["url"]
    destination = Path(resource["filepath"])

    if destination.exists():
        print(f"{destination.name} already exists")
    
    else:
        temp_path = None

        with urlopen(Request(url), timeout=60) as response:
            expected_size = response.headers.get("Content-Length")
            
            with tempfile.NamedTemporaryFile(dir=destination.parent, delete=False) as temp:
                temp_path = Path(temp.name)
                digest = hashlib.sha256()

                while chunk := response.read(CHUNK_SIZE):
                    temp.write(chunk)
                    digest.update(chunk)

        # Once the file is downloaded, rename the temp file
        os.replace(temp_path, destination)

        if destination.exists():
            print(f"Downloaded {destination.name}")
        else:
            print(f"\033[91mError downloading {destination.name}\033[0m")