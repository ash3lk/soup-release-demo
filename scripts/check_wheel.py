import os
import subprocess
import sys
import tempfile
import venv
from pathlib import Path


wheel_dir = Path(sys.argv[1]).resolve()
wheels = list(wheel_dir.glob("*.whl"))
if len(wheels) != 1:
    raise SystemExit(f"Expected one wheel in {wheel_dir}, found {len(wheels)}")

tests_dir = Path("tests").resolve()

with tempfile.TemporaryDirectory() as temp_dir:
    venv_dir = Path(temp_dir) / "venv"
    venv.create(venv_dir, with_pip=True)

    bin_dir = venv_dir / ("Scripts" if os.name == "nt" else "bin")
    python = bin_dir / ("python.exe" if os.name == "nt" else "python")

    env = os.environ.copy()
    env.pop("PYTHONPATH", None)
    env.pop("PYTHONHOME", None)
    env["PATH"] = str(bin_dir) + os.pathsep + env.get("PATH", "")

    subprocess.run(
        [str(python), "-m", "pip", "install", "--no-cache-dir", str(wheels[0])],
        cwd=temp_dir,
        env=env,
        check=True,
    )
    subprocess.run(
        [str(python), "-m", "unittest", "discover", "-s", str(tests_dir)],
        cwd=temp_dir,
        env=env,
        check=True,
    )
