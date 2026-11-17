from astroquery.mpc import MPC
from pathlib import Path
from sys import argv

root = Path(__file__).resolve().parent
OUTPUT_FOLDER = root / "Observations"
OUTPUT_FOLDER.mkdir(parents=True, exist_ok=True)

if len(argv) != 2:
    print(f"Unexpected number of arguments. Run python {argv[0]} \"[name of body]\"")
    exit(1)

# Get the body from the MPC
body_name = str(argv[1])
# TODO: Name recognition. "Ceres", while an unambiguous name, is not accepted by MPC.get_observations()
observations = MPC.get_observations(body_name)
# Save the file to "{body_name}.json"
output_path = OUTPUT_FOLDER / f"{body_name.replace(' ', '_')}.json"
observations.to_pandas().to_json(output_path, orient="records", indent=2)