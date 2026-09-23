# Installing the research package

NEURAL-RMF is released as platform-specific binary wheels. Download the asset
matching your operating system and Python version from GitHub Releases, then
install it with `pip`.

```bash
pip install /path/to/neural_rmf-<version>-cp<python>-<platform>.whl
```

For Google Colab, run this cell. It selects the matching Linux wheel for
Python 3.12 or 3.13:

```python
import subprocess
import sys

tag = f"cp{sys.version_info.major}{sys.version_info.minor}"
wheels = {
    "cp312": "https://github.com/Gusmal02/NEURAL-RMF/releases/download/v0.1.0/neural_rmf-0.1.0-cp312-cp312-manylinux2014_x86_64.manylinux_2_17_x86_64.manylinux_2_28_x86_64.whl",
    "cp313": "https://github.com/Gusmal02/NEURAL-RMF/releases/download/v0.1.0/neural_rmf-0.1.0-cp313-cp313-manylinux2014_x86_64.manylinux_2_17_x86_64.manylinux_2_28_x86_64.whl",
}
assert tag in wheels, f"No released Linux wheel for Python {sys.version}"
subprocess.check_call([sys.executable, "-m", "pip", "install", wheels[tag]])
```

Do not install from repository source: the research engine is supplied only as
a compiled component in the published wheels.

## Research-use limitation

NEURAL-RMF is research software. It is not a medical device, diagnostic tool,
or deterministic seizure-prediction system. Any use with patient data requires
appropriate consent, governance, clinical oversight, and independent
validation.
