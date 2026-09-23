# Installing the research package

NEURAL-RMF is released as platform-specific binary wheels. Download the asset
matching your operating system and Python version from GitHub Releases, then
install it with `pip`.

```bash
pip install /path/to/neural_rmf-<version>-cp<python>-<platform>.whl
```

For Google Colab, use a Linux wheel matching the active Python version. The
release-specific cell will be listed here after the first binary release is
published.

```python
import sys
print(sys.version)
```

Do not install from repository source: the research engine is supplied only as
a compiled component in the published wheels.

## Research-use limitation

NEURAL-RMF is research software. It is not a medical device, diagnostic tool,
or deterministic seizure-prediction system. Any use with patient data requires
appropriate consent, governance, clinical oversight, and independent
validation.
