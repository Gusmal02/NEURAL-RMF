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

## Project overview

RMF means **Resonant Memory Field**: a dynamic representation framework in
which familiar patterns are incorporated as a collective state. A new input is
evaluated by its compatibility with that learned reference. In the EEG setting,
the reference is not a universal model of a healthy brain; it is the recent
baseline of the individual monitoring session.

NEURAL-RMF performs an eight-minute session calibration, then evaluates
sequential 30-second EEG windows. It tracks local and collective change,
temporal coherence, persistence, and the direction of change over time. The
output is an interpretable traffic light:

| State | Research interpretation |
| --- | --- |
| Green | Activity compatible with the individual session reference. |
| Yellow | Early deviation that warrants observation. |
| Orange | Sustained activity or loading under observation. |
| Red | A high-risk trajectory with sustained loading, sufficient peak change, subsequent decline or reorganization, rising collective coherence, and persistence. |

The red state is not triggered by a single high-novelty oscillation. It
requires a temporal sequence, which is why the project describes a monitored
risk transition rather than a binary classifier output or an exact seizure
clock.

## What makes the approach different

- **Individualized from the first session.** The initial reference is learned
  from the current recording; clinical seizure labels are not used during
  calibration or inference.
- **Trajectory-aware.** The system preserves the path from baseline through
  alert, event when available, and recovery rather than reducing activity to
  one threshold crossing.
- **Interpretable output.** CSV, JSON, timeline, and graph exports allow a
  clinician or researcher to inspect why an alert state emerged.
- **Compact monitoring hypothesis.** The proposed wearable configuration uses
  a bilateral temporal four-node arrangement centered on `F7`, `T7`, `F8`, and
  `T8`, rather than attempting to replicate a full diagnostic montage.

The four-node configuration was selected after internal technical comparisons
because it concentrated the signal used by this field calculation more
effectively than the evaluated six- and 23-channel configurations. This is not
a claim that four nodes replace clinical EEG: full multichannel EEG, video,
clinical context, and neurologist interpretation remain necessary for
diagnosis and localization.

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

## Retrospective technical evidence

The current preprint documents analysis of public, de-identified CHB-MIT and
Siena scalp EEG recordings. The evaluated cohort contained **80 session
trajectories from 27 unique patients**: 41 recordings from 14 CHB-MIT patients
and 39 recordings from 13 Siena patients. Each independent recording received
its own eight-minute calibration; labels were withheld while states were
generated.

| Retrospective result | Documented observation |
| --- | --- |
| Annotated onsets available after calibration | 69 |
| Annotated onsets with a preceding generated red trajectory | 66 of 69 |
| Remaining cases | Insufficient baseline availability or data-quality limitations; not conclusive evidence of absent signal |
| Unlabeled structured candidates retained for review | 99 |

In an internal comparison of 19 CHB-MIT runs, the four-node montage preceded
18 recorded onsets, compared with 16 using six channels and 14 using a
23-channel montage. Its internal CHB-MIT mean lead time was 67.2 minutes. The
corresponding internal Siena analysis reported 97% detection and a mean lead
time of 89.5 minutes. These lead times are not uniform: some trajectories are
gradual and emerge much earlier, while others are abrupt and provide a shorter
window.

These values are **retrospective technical observations**, not prospective
clinical-performance claims. They do not establish positive predictive value,
driving safety, clinical efficacy, or the performance of a medical device.

Some red trajectories do not coincide with an onset annotated in the source
dataset. They are neither automatically false alarms nor confirmed seizures.
Possible explanations include transient physiology, artifacts, aborted
transitions, or subtle/subclinical epileptic activity. Distinguishing those
possibilities requires synchronized video-EEG, signal-quality assessment,
symptom logs, and expert review.

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

Public data sources used for the retrospective analysis:

- [CHB-MIT Scalp EEG Database](https://physionet.org/content/chbmit/1.0.0/)
- [Siena Scalp EEG Database](https://physionet.org/content/siena-scalp-eeg/1.0.0/)

Copyright © 2026 Gustavo Alfonso Maldonado Vallejo. All rights reserved.
