# NEURAL-RMF — Research Edition

NEURAL-RMF is research software for patient-specific EEG state monitoring.
After an initial session calibration, it characterizes subsequent EEG windows
relative to that person's own baseline and reports interpretable monitoring
states. The research objective is to study evolving EEG activity and provide
an anticipatory monitoring window when a clinically meaningful state pattern
is observed.

NEURAL-RMF does **not** provide deterministic seizure prediction, diagnosis,
or medical advice. Its outputs are research observations that require clinical
validation, appropriate EEG review, and clinician oversight.

## Research distribution

The resonant-memory engine, encoding layer and internal state logic are
distributed as compiled binary modules. This repository deliberately contains
the public documentation and installation instructions, not the internal
engine source.

Binary releases support Windows and Linux on released Python versions. Linux
wheels can be installed in Google Colab when the notebook runtime matches a
released wheel.

Read the [installation guide](docs/INSTALLATION.md) and
[research-use license](LICENSE) before using the package.

## Intended use

- Research evaluation of four-channel EEG monitoring workflows.
- Per-session baseline calibration.
- Longitudinal recording of baseline-relative state changes.
- Reproducible technical analysis alongside clinical labels and review.

## Important limits

- A monitoring alert is not a diagnosis and must not be used as the sole basis
  for clinical or safety decisions.
- The software is not an emergency-warning device.
- Research outputs must be interpreted with clinical context, signal quality
  assessment, and, when available, synchronized clinical/video review.

## Author and collaboration

Developed by Gustavo Alfonso Maldonado Vallejo, AI Engineer and Data Science.
Research collaboration and independent clinical validation are welcome.

## Citable technical preprint

The current technical report, including its figures and retrospective analysis,
is publicly archived on Zenodo:

> Maldonado, Gustavo Alfonso. *NEURAL RMF: Individualized EEG Monitoring for
> Early Warnings of Epileptic Seizure Risk*. Zenodo.
> https://doi.org/10.5281/zenodo.22950874

The record is a citable technical preprint and is not peer-reviewed clinical
evidence. The corresponding manuscript PDF is available in this repository at
[preprint/NEURAL_RMF_preprint_EN.pdf](preprint/NEURAL_RMF_preprint_EN.pdf).
Future revisions should be released as new versions of the Zenodo record to
maintain an auditable version history.

Copyright © 2026 Gustavo Alfonso Maldonado Vallejo. All rights reserved.
