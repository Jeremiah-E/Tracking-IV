from astroquery.mpc import MPC
from sys import argv
from pathlib import Path

if len(argv) != 2:
    print(f"Unexpected number of arguments. Run python {argv[0]} \"[name of body]\"")
    exit(1)

# Get the body from the MPC
body_name = str(argv[1])
# TODO: Name recognition. "Ceres", while an unambiguous name, is not accepted by MPC.get_observations()
observations = MPC.get_observations(body_name)
# Save the file to "{body_name}.json"
root = Path(__file__).resolve().parent
output_path = root / "Observations" / f"{body_name.replace(' ', '_')}.json"
observations.to_pandas().to_json(output_path, orient="records", indent=2)