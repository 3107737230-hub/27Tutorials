"""Execute each notebook in a clean Python kernel and validate the saved outputs."""
from pathlib import Path
import json
import os
import sys
import tempfile
from datetime import datetime, timezone
import cv2
import matplotlib
import numpy as np
import nbformat
from nbclient import NotebookClient
from jupyter_client.kernelspec import KernelSpecManager

ROOT = Path(__file__).resolve().parents[1]

def main():
    # Private kernel spec: use this interpreter without global kernel installation.
    records = []
    with tempfile.TemporaryDirectory(prefix="opencv-lab-kernel-") as tmp:
        tmp_path = Path(tmp)
        spec_dir = tmp_path / "kernels" / "lab-verify"
        spec_dir.mkdir(parents=True)
        (spec_dir / "kernel.json").write_text(json.dumps({
            "argv": [sys.executable, "-m", "ipykernel_launcher", "-f", "{connection_file}"],
            "display_name": "Lab verification", "language": "python"
        }), encoding="utf-8")
        old_jupyter_path = os.environ.get("JUPYTER_PATH")
        os.environ["JUPYTER_PATH"] = str(tmp_path)
        os.environ["MPLBACKEND"] = "module://matplotlib_inline.backend_inline"
        os.environ.setdefault("MPLCONFIGDIR", str(tmp_path / "matplotlib"))
        os.environ.setdefault("IPYTHONDIR", str(tmp_path / "ipython"))
        os.environ.setdefault("JUPYTER_RUNTIME_DIR", str(tmp_path / "runtime"))
        try:
            paths = sorted(ROOT.glob("lab[0-9][0-9]_*/lab[0-9][0-9].ipynb"))
            if len(paths) != 9:
                raise RuntimeError(f"Expected 9 notebooks, found {len(paths)}")
            manager = KernelSpecManager(kernel_dirs=[str(tmp_path / "kernels")])
            def execute(path, cwd, save):
                nb = nbformat.read(path, as_version=4)
                nbformat.validate(nb)
                client = NotebookClient(nb, timeout=180, kernel_name="lab-verify",
                                        resources={"metadata": {"path": str(cwd)}})
                # All kernel managers consult the isolated JUPYTER_PATH above.
                client.execute()
                errors = [o for c in nb.cells if c.cell_type == "code" for o in c.outputs if o.output_type == "error"]
                if errors:
                    raise RuntimeError(f"Unexpected errors in {path.name}")
                displays = sum(o.output_type in ("display_data", "execute_result") for c in nb.cells if c.cell_type == "code" for o in c.outputs)
                if displays == 0:
                    raise RuntimeError(f"No image/display outputs in {path.name}")
                if save:
                    # Preserve the portable user-facing kernel metadata.
                    nb.metadata.kernelspec = {"display_name": "Python 3 (lab .venv)", "language": "python", "name": "python3"}
                    nbformat.validate(nb)
                    nbformat.write(nb, path)
                return {"notebook": str(path.relative_to(ROOT)), "cwd": str(cwd.relative_to(ROOT)) or ".",
                        "code_cells": sum(c.cell_type == "code" for c in nb.cells), "display_outputs": displays, "status": "passed"}
            for path in paths:
                record = execute(path, path.parent, True)
                records.append(record)
                print(f"PASS {record['notebook']} ({record['code_cells']} code cells)", flush=True)
            records.append(execute(paths[2], ROOT, False))
            print("PASS lab03 from project root", flush=True)
        finally:
            if old_jupyter_path is None:
                os.environ.pop("JUPYTER_PATH", None)
            else:
                os.environ["JUPYTER_PATH"] = old_jupyter_path
    report = {
        "verified_at_utc": datetime.now(timezone.utc).isoformat(),
        "python": sys.version.split()[0], "opencv": cv2.__version__,
        "numpy": np.__version__, "matplotlib": matplotlib.__version__,
        "method": "nbclient; fresh interpreter kernel for every run; execution stops on first error",
        "checks": records,
    }
    (ROOT / "outputs" / "verification.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

if __name__ == "__main__":
    main()
