from astropy import units as u
from astropy.coordinates import get_body_barycentric, solar_system_ephemeris
from astropy.time import Time
from erfa import ErfaWarning
from os import listdir
from pathlib import Path
import json
import numpy as np
import warnings

# Since we're working with historical data, we get 'dubious year' warnings
# UTC isn't defined for pre-1960 data, so to prevent the console from being flooded, we can simply ignore the warnings
warnings.filterwarnings("ignore", category=ErfaWarning, message=".*dubious year")

root = Path(__file__).resolve().parent
INPUT_FOLDER = root / "Observations"
INPUT_FOLDER.mkdir(parents=True, exist_ok=True)
OUTPUT_FOLDER = root / "Computed Observations"
OUTPUT_FOLDER.mkdir(parents=True, exist_ok=True)
OBSERVATORIES = root / "Data" / "Observatory Codes.txt"
# Earth an Sun data (among others) is pulled from here
DE440_KERNEL = root / "Data" / "de440.bsp"
if not DE440_KERNEL.exists():
    print("Needed kernel (de440.bsp) does not exist. Run setup_data.py")
    exit(0)

# Create a dict of all observatory codes
codes = {}
with OBSERVATORIES.open("r", encoding="utf-8") as f:
    lines = f.readlines()
    # Remove the title
    lines = lines[1:]
    for line in lines:
        # Extract information from the observatory table
        code = line[0:3]
        longitude = line[4:13]
        cos_phi = line[13:21]
        sin_phi = line[21:30]

        name = line[30:].rstrip("\r\n")
        # Convert everything to a float
        def parse_float(value):
            try:
                return float(value) if value else None
            except ValueError:
                return None
        # Assemble our dictionary
        codes[code] = {
            "longitude": parse_float(longitude),
            "cos_phi": parse_float(cos_phi),
            "sin_phi": parse_float(sin_phi),
            "name": name,
        }

# Return if the telescope has fixed coordinates
def is_fixed(code):
    details = codes[code]
    # Return if all entries are not None
    return all(details[key] is not None for key in ["longitude", "cos_phi", "sin_phi"])

# NOTE: Time is passed for when I start involving non-fixed telescopes
# TODO: Support known satellites
def get_geo_coord(code, time):
    observatory = codes[code]
    # Earth's equatorial radius, in meters
    EARTH_RADIUS = 6378137.0

    # TODO: If the code is a satellite of known observatory code, don't prematurely exit
    #       Use a different frame, e.g. ["HUBBLE", [x, y, z]] or ["ECI", [x, y, z]]
    if not is_fixed(code):
        print(f"Observatory {code} ({observatory['name']}) is not fixed.")
        exit()

    longitude = np.radians(observatory["longitude"])
    cos_phi = observatory["cos_phi"]
    sin_phi = observatory["sin_phi"]

    # ECEF coordinates
    x = EARTH_RADIUS * cos_phi * np.cos(longitude)
    y = EARTH_RADIUS * cos_phi * np.sin(longitude)
    z = EARTH_RADIUS * sin_phi

    return ["ECEF", [x, y, z]]

# Transform a given coordinate into heliocentric, equatorial coords
# TODO: Transform into ecliptic instead of equatorial coords (requires transforming direction vectors)
def transform(coordinates, times):
    if len(coordinates) != len(times):
        raise ValueError("Coordinates and times must have equal lengths.")

    # Validate frames
    for frame, position in coordinates:
        # TODO: Support non-ECEF frames, e.g. heliocentric
        if frame != "ECEF":
            print(f"Cannot transform frame {frame}. Expected ECEF.")
            exit(1)

    # Unpack everything into np arrays
    times = np.asarray(times, dtype=np.float64)
    ecef = np.asarray([position for frame, position in coordinates])

    # Get Earth's heliocentric position at all times
    astropy_times = Time(times, format="jd", scale="utc")

    # Get the Earth and Sun's positions at each time
    with solar_system_ephemeris.set(str(DE440_KERNEL)):
        earth = get_body_barycentric("earth", astropy_times)
        sun = get_body_barycentric("sun", astropy_times)

    # Barycentric -> heliocentric, in meters
    earth_helio = (earth - sun).xyz.to_value(u.m).T

    # It's simpler to just use a library than to calculate GMST manually
    # Don't feel like ensuring I've copied century^3 terms right
    gmst = astropy_times.sidereal_time("mean", "greenwich").radian

    # ECEF -> equatorial inertial
    x_eq = ecef[:, 0] * np.cos(gmst) - ecef[:, 1] * np.sin(gmst)
    y_eq = ecef[:, 0] * np.sin(gmst) + ecef[:, 1] * np.cos(gmst)
    z_eq = ecef[:, 2]

    observer_eq = np.column_stack((x_eq, y_eq, z_eq))

    # Earth-centered -> heliocentric equatorial
    return earth_helio + observer_eq


files = listdir(INPUT_FOLDER)
if len(files) == 0:
    print("No observation files are present. Run data_get.py")
    exit(0)

observations = {}
for file in files:
    # TODO: Figure out readable names. Either here or in data_get
    stem = Path(file).stem
    name = stem.replace("_", " ")
    print(f"Body: {name}")
    with (INPUT_FOLDER / file).open("r", encoding="utf-8") as f:
        data = json.load(f)

    # Prevent invalid datatypes
    if not isinstance(data, list) or not all(isinstance(entry, dict) for entry in data):
        print("Invalid format. Expected array of dicts")
        continue

    # Frame, position
    coordinates = []
    # Julian days
    times = []
    # RA, DEC
    angles = []
    # Info messages
    skipped = {}
    for observation in data:
        # Ensure all keys here exist
        required_keys = ["epoch", "RA", "DEC", "observatory"]
        if not all(key in observation for key in required_keys):
            print("Unexpected entry found:")
            print(observation)
            exit()
        # Ensure the code is recognized
        code = observation["observatory"]
        if code not in codes:
            message = f"Skipped {code} (no found name)"
            skipped[message] = skipped.get(message, 0) + 1
        # Ensure the telescope is fixed
        # TODO: Allow certain satellites
        elif not is_fixed(code):
            message = f"Skipped {code} ({codes[code]['name']}) - observatory w/ unknown position"
            skipped[message] = skipped.get(message, 0) + 1
        # Currently the only valid observation block
        else:
            epoch = observation["epoch"]
            coordinates.append(get_geo_coord(code, epoch))
            times.append(epoch)
            angles.append([observation["RA"], observation["DEC"]])

    # Print all notable messages
    for reason, count in skipped.items():
        count = f" (x{count})" if count != 1 else ""
        print(f"{reason}{count}")

    # Probably should use the skipped system, but it works here
    if not times:
        print("No usable observations")
        continue

    # TODO: Make this do *all* coordinates at once instead of one body's coordinates at a time
    positions = transform(coordinates, times)

    # observations[name] = [[time, ra, dec, x, y, z], ...]
    observations[name] = np.column_stack((np.asarray(times, dtype=np.float64), np.asarray(angles, dtype=np.float64), positions)).T

    # Save the observations as txts
    output_file = OUTPUT_FOLDER / f"{stem}.txt"
    np.savetxt(output_file, observations[name].T, fmt="%.17g", delimiter=" ")
    print(f"Saved {output_file.relative_to(root)}")