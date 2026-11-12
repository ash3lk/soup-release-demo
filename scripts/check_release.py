import argparse
from email.parser import BytesHeaderParser
from pathlib import Path
from zipfile import ZipFile

parser = argparse.ArgumentParser()
parser.add_argument("wheel_dir", type=Path)
parser.add_argument("tag")
args = parser.parse_args()

wheels = list(args.wheel_dir.glob("*.whl"))
if len(wheels) != 1:
    raise SystemExit(f"Expected exactly one wheel, found {len(wheels)}")

with ZipFile(wheels[0]) as wheel:
    metadata = [
        name for name in wheel.namelist() if name.endswith(".dist-info/METADATA")
    ]
    if len(metadata) != 1:
        raise SystemExit("Expected exactly one METADATA file in wheel")
    version = BytesHeaderParser().parsebytes(wheel.read(metadata[0])).get("Version")

if not version:
    raise SystemExit("Version is missing from wheel metadata")

expected_tag = f"v{version}"
if args.tag != expected_tag:
    raise SystemExit(f"Tag mismatch: got {args.tag}, wheel expects {expected_tag}")

print(f"Tag {args.tag} matches wheel version {version}")
