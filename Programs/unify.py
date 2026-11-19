from astropy import units as u
from astropy.coordinates import EarthLocation, solar_system_ephemeris, get_body_barycentric
from astropy.time import Time
from datetime import datetime, timezone
from erfa import ErfaWarning
from os import listdir
from pathlib import Path
import numpy as np
import warnings
import xml.etree.ElementTree as ET

# We use data from 1801. Ephemeris data for the Earth does not go that far back, so it's a dubious year (a year we guessed the data for)
# Given I'm using a decent amount of this data, I'd rather not see the warning
warnings.filterwarnings('ignore', message='.*dubious year.*', category=ErfaWarning)

# Needed filepaths
root = Path(__file__).resolve().parent.parent
INPUT_FOLDER  = root / "Downloaded Observations"
OUTPUT_FOLDER = root / "Unified Observations"
OBSERVATORIES = root / "Data" / "Observatory Codes.txt"
DE440_KERNEL  = root / "Data" / "de440.bsp"
# Ensure needed folders / files exist
# (Note: non-checked folders come with the project)
OUTPUT_FOLDER.mkdir(parents=True, exist_ok=True)
INPUT_FOLDER.mkdir(parents=True, exist_ok=True)
if not DE440_KERNEL.exists():
    print("Needed kernel (de440.bsp) does not exist. Run setup.py")
    exit()
solar_system_ephemeris.set(str(DE440_KERNEL))

# Create a dict of all observatory codes
codes = {}
with OBSERVATORIES.open("r", encoding="utf-8") as f:
    lines = f.readlines()
    # Remove the title
    lines = lines[1:]
    for line in lines:
        # Extract information from the observatory table
        code = line[0:3]
        allowed = line[3] != "X"
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
            "allowed": allowed
        }

files = listdir(INPUT_FOLDER)
if len(files) == 0:
    print("No observation files are present. Run ingest.py")
    exit(0)
files = [INPUT_FOLDER / file for file in files]

# Filter observations so we know what to expect
# TODO: Break up this giant if statement nightmare
all_observations = {}
for file in files:
    messages = {}
    stem = Path(file).stem
    name = stem.replace("_", " ")
    print(f"Processing data for \x1b[93m{name}\x1b[0m")
    observations_xml_tree = ET.parse(file)
    observations_xml_root = observations_xml_tree.getroot()
    observations = []
    for observation_xml in observations_xml_root:
        tag = observation_xml.tag
        if tag == "optical":
            observation = {}
            invalid_entry = False
            for observation_xml_property in observation_xml:
                if len(observation_xml_property) > 0:
                    msg = f"Property {observation_xml_property.tag} has a child"
                    messages[msg] = messages.get(msg, 0) + 1
                    invalid_entry = True
                    break
                observation[observation_xml_property.tag] = observation_xml_property.text
            if invalid_entry:
                continue
            # Allow implied frames
            # Ensure needed properties exist
            req_props = ["stn", "obsTime", "ra", "dec"]
            if all([req_prop in observation for req_prop in req_props]):
                code = observation["stn"]
                if len(code) == 3:
                    # Ensure the telescope is recognized
                    if code in codes:
                        if codes[code]["allowed"]:
                            # Check if the telescope is fixed and known
                            static_properties = ["longitude", "cos_phi", "sin_phi"]
                            if all([codes[code][prop] is not None for prop in static_properties]):
                                
                                observation["Format"] = "Geodetic Station with Code"
                                observations.append(observation)

                            else:
                                # TODO: Support satellites
                                # TODO: Use given coords when not fixed
                                msg = f"Non-stationary station {code} ({codes[code]["name"]})"
                                messages[msg] = messages.get(msg, 0) + 1

                        else:
                            msg = f"Disallowed station {code} ({codes[code]["name"]})"
                            messages[msg] = messages.get(msg, 0) + 1

                    else:
                        msg = f"Unrecognized station code: {code}"
                        messages[msg] = messages.get(msg, 0) + 1

                else:
                    # TODO: Support 4-letter codes
                    msg = f"Non-3 letter station code ({code}) not supported"
                    messages[msg] = messages.get(msg, 0) + 1

            # A needed property did not exist
            else:
                missing = [req_prop for req_prop in req_props if req_prop not in observation]
                msg = f"Missing required properties: {', '.join(missing)}"
                messages[msg] = messages.get(msg, 0) + 1

        elif tag == "occultation":
            # TODO: Support occultation
            msg = f"Unsupported observation type: {tag}"
            messages[msg] = messages.get(msg, 0) + 1
        
        # I don't recognize the tag
        else:
            msg = f"Unrecognized observation type: {tag}"
            messages[msg] = messages.get(msg, 0) + 1
    # Print all messages
    for msg, cnt in messages.items():
        cnt = f" (x{cnt})" if cnt > 1 else ""
        print(f" {msg}{cnt}")
    all_observations[name] = observations

# We want to convert all observations into barycentric ecliptic values
# Entries not belonging to the array are filled with None (e.g. radar measurements will have a None for their RA)
# TODO: Get/use the following fields:
#       precRA, precDec, precTime, rmsRA, rmsDec, rmsTime, rmsCorr
bodies, times, ras, decs, stns, formats = [], [], [], [], [], []
for name, observations in all_observations.items():
    for observation in observations:
        bodies.append(name)
        times.append(observation["obsTime"])
        ras.append(observation["ra"])
        decs.append(observation["dec"])
        stns.append(observation["stn"])
        formats.append(observation["Format"])

# Convert ras and decs to floats
for i in range(len(ras)):
    if not ras[i] is None:
        try:
            ras[i] = float(ras[i])
        except:
            print(f"RA value ({ras[i]}) could not be parsed")
for i in range(len(decs)):
    if not decs[i] is None:
        try:
            decs[i] = float(decs[i])
        except:
            print(f"DEC value ({decs[i]}) could not be parsed")
# Convert times to UNIX seconds
epoch = datetime(1970, 1, 1, tzinfo=timezone.utc)
converted_times = []
for i in range(len(times)):
    time = times[i]
    if not isinstance(time, str):
        print(f"Invalid observation time: {time}")
        exit(0)

    # UTC/Z offsets are accepted, but an offset or Z is required because a
    # timezone is otherwise an assumption not present in the input.
    iso_time = time[:-1] + "+00:00" if time.endswith("Z") else time
    try:
        parsed_time = datetime.fromisoformat(iso_time)
    except ValueError:
        print(f"Invalid observation time: {time}")
        exit(0)
    if parsed_time.tzinfo is None:
        print(f"Observation time has no timezone: {time}")
        exit(0)
    times[i] = (parsed_time.astimezone(timezone.utc) - epoch).total_seconds()

# Now convert everything into the unified format
# Each entry will be an array of strings
# Later they will be printed to a file, joined with newlines
output = {body: [] for body in set(bodies)}

def ECEF(code):
    radius = 6378137.0
    if code not in codes:
        print(f"Unexpected code: {code}")
        exit()
    observatory = codes[code]
    if observatory is None or observatory.get("longitude") is None:
        print(f"Station code '{code}' has missing or None longitude data.")
        exit()
    longitude = np.radians(observatory["longitude"])
    cos_phi = observatory["cos_phi"]
    sin_phi = observatory["sin_phi"]
    x = radius * cos_phi * np.cos(longitude)
    y = radius * cos_phi * np.sin(longitude)
    z = radius * sin_phi
    return [x, y, z]
# Return (positions, directions) in barycentric ecliptic coords
# TODO: Use a time-variable epsilon value
# TODO: Get rid of get_gcrs_posvel, use a local file to compute this instead
def ecliptic(stns, ras, decs, times):
    EPS = np.radians(84381.448 / 3600)
    R_ECL = np.array([[1, 0, 0], [0,  np.cos(EPS), np.sin(EPS)], [0, -np.sin(EPS), np.cos(EPS)]])
    t = Time(times, format="unix", scale="utc")
    stns = np.asarray(stns)
    earth = get_body_barycentric("earth", t).xyz.to(u.m).value.T
    geo = np.empty_like(earth)
    for code in np.unique(stns):
        # [stn == code for stn in stns]
        m = (stns == code)
        loc = EarthLocation.from_geocentric(*ECEF(code), unit=u.m)
        pos, _ = loc.get_gcrs_posvel(t[m])
        geo[m] = pos.xyz.to(u.m).value.T
    ra, dec = np.radians(np.asarray(ras, float)), np.radians(np.asarray(decs, float))
    d = np.stack([np.cos(dec) * np.cos(ra), np.cos(dec) * np.sin(ra), np.sin(dec)], -1)
    return (earth + geo) @ R_ECL.T, d @ R_ECL.T

# Perform the transformation to ecliptic for all well-known, fixed, geodetic stations
# Then append them to output
GSWC = np.where(np.array(formats) == "Geodetic Station with Code")[0]
GSWC_times = [times[i] for i in GSWC]
GSWC_ras   = [ras[i] for i in GSWC]
GSWC_decs  = [decs[i] for i in GSWC]
GSWC_stns  = [stns[i] for i in GSWC]
GSWC_bodies  = [bodies[i] for i in GSWC]
GSWC_positions, GSWC_directions = ecliptic(GSWC_stns, GSWC_ras, GSWC_decs, GSWC_times)
for i in range(len(GSWC)):
    name, time, obs_x, obs_y, obs_z, dir_x, dir_y, dir_z = GSWC_bodies[i], GSWC_times[i], *GSWC_positions[i], *GSWC_directions[i]
    output[name].append(f"GSWC {time:.17f} {obs_x:.17f} {obs_y:.17f} {obs_z:.17f} {dir_x:.17f} {dir_y:.17f} {dir_z:.17f}")

for name, out_str in output.items():
    out_str = "\n".join(out_str)
    out_path = OUTPUT_FOLDER / f"{name.replace(" ", "_")}.txt"
    out_path.write_text(out_str, encoding="utf-8")