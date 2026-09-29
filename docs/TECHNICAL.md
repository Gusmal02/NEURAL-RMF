# NEURAL-RMF technical note

This document is the technical companion to the repository README. It explains
the public monitoring workflow and reported retrospective evidence without
disclosing the protected implementation of the resonant-memory engine.

## 1. Technical definition

NEURAL-RMF is a **label-free, individualized EEG representation and monitoring
framework**. Its monitoring workflow has three public properties:

1. a short reference is established from the current session;
2. subsequent EEG windows are expressed relative to that session reference;
3. a temporal state machine converts a sustained sequence of baseline-relative
   changes into interpretable monitoring states.

It is not a supervised seizure classifier. There is no population training
phase, no seizure-label fitting step, and no label supplied while a session is
being calibrated or monitored. “Learning” in this context means constructing
the reference representation from the current usable baseline; it does not
mean training a classifier on a catalogue of prior patients.

The protected engine is distributed as compiled research software. The public
materials provide its inputs, outputs, calibration protocol, state semantics,
examples, and reproducible EDF workflow.

## 2. Session protocol

| Component | Public protocol |
| --- | --- |
| Calibration | 8 minutes of usable signal from the current recording |
| Analysis window | 30 seconds |
| Unit of analysis | Independent recording/session |
| Labels during inference | Withheld |
| Labels after inference | Retrospective overlay only |
| Primary portable montage | Four bilateral temporal contacts or equivalent derivations |
| Outputs | State timeline, CSV, JSON, figures, and research metrics |

Independent recordings are not treated as one continuous session merely
because they belong to the same person. A new session requires a new
calibration, just as a wearable monitor would need to calibrate after being
removed or restarted.

## 3. Public monitoring variables

The interactive MVP and exported files expose derived research variables. They
are aids to inspection, not clinical scores or probabilities.

| Variable | Interpretation |
| --- | --- |
| `Novelty Max` | Largest localized difference from the session reference among the selected inputs. |
| Collective novelty | Field-level difference from the reference across the selected inputs. |
| P80 baseline threshold | Individual threshold derived from the calibration distribution. |
| `r_field` | A collective temporal-coherence descriptor used to evaluate trajectory structure. |
| State | Green, yellow, orange, or red summary of the trajectory; not a diagnosis. |

## 4. State logic

The traffic-light presentation is deliberately more restrictive than a single
threshold crossing.

| State | Technical interpretation |
| --- | --- |
| Green | Relative compatibility with the calibrated reference. |
| Yellow | Early baseline-relative deviation. |
| Orange | Sustained loading or change under observation. |
| Red | A completed primary trajectory: sustained orange episode, sufficient individual peak, decline/reorganization from that peak, rising collective coherence, and persistence across consecutive windows. |

The primary red state is therefore not “high novelty = seizure.” The trajectory
is intended to distinguish a temporally organized transition from an isolated
fluctuation. A secondary abrupt-candidate signal may be logged in research
exports, but it is not presented as a user-facing red alert in the MVP because
its specificity requires further study.

## 5. Retrospective datasets and reported evidence

The work used public, de-identified CHB-MIT Scalp EEG and Siena Scalp EEG
recordings. The report snapshot includes 80 session trajectories from 27
participants: 41 CHB-MIT recordings from 14 participants and 39 Siena
recordings from 13 participants.

There were 69 clinically annotated onsets outside the calibration period. The
technical preprint reports a preceding generated primary red trajectory for 66
of 69 under its stated analysis snapshot. The three remaining events occurred
in sessions affected by a short available post-calibration interval, onset
close to calibration, or data-quality/recording constraints. They should not
be converted into a clinical sensitivity estimate.

### Label-blind temporal order

For every evaluated recording, the intended order is:

```text
EDF signal → calibration → state generation → saved outputs → annotation overlay
```

This order prevents an annotation from causing an alert. It does not make the
study prospective: source labels were still available afterward for
retrospective comparison.

## 6. Internal comparative benchmarks

These comparisons answer narrow technical questions under matched local
protocols. They are **not** head-to-head comparisons with published clinical
devices or external commercial algorithms, because cohorts, preprocessing,
montages, event definitions, and evaluation windows differ.

### 6.1 Trajectory logic versus simpler local baselines

One 69-event retrospective benchmark compared RMF trajectory monitoring with
two label-free local alternatives:

| Method | Annotated events with prior alert | Alert burden |
| --- | ---: | ---: |
| Simple P80 persistence threshold | 69 / 69 | 36.72 alert min/hour |
| Robust statistical feature anomaly | 58 / 69 | 19.33 alert min/hour |
| RMF primary trajectory | 65 / 69 | 17.29 alert min/hour |

The result is a trade-off, not proof of clinical superiority: the simple P80
rule covered more annotated events but produced approximately twice the alert
time. The primary trajectory reduced alert burden while retaining high
retrospective coverage. This benchmark count differs from the 66/69 report
snapshot because it used a separately frozen comparison run and inclusion
filters; results from distinct analysis snapshots should not be pooled.

### 6.2 Compact montage comparison

The four-node configuration was evaluated as a portable design constraint, not
as a replacement for full clinical EEG.

| Cohort / matched protocol | Four temporal | Six frontotemporal | Full 23-channel evaluation |
| --- | ---: | ---: | ---: |
| CHB-MIT: events with preceding primary trajectory | 31 / 34 (91.2%) | 33 / 34 (97.1%) | 34 / 34 (100%) |
| Siena: events with preceding primary trajectory | 34 / 35 (97.1%) | 32 / 35 (91.4%) | Not completed cohort-wide |

The cohorts use different recording representations, so this is not evidence
that one montage wins universally. It shows why the portable four-node design
should be treated as a practical starting point and evaluated per patient and
per acquisition protocol. A complete Siena full-montage comparison remains a
future streaming/chunked-processing task because long EDFs require substantial
memory.

## 7. Interpretation of unannotated trajectories

A generated red trajectory with no coincident source annotation is an
**unannotated research candidate**. It may represent artifact, transient
physiology, an interrupted transition, a subtle/subclinical epileptic event,
or another non-epileptic change. The present datasets do not contain enough
clinical context to decide among these explanations reliably.

The proposed next study therefore requires synchronized video-EEG, signal
quality and electrode-contact records, symptoms/context logs, medication
information when ethically available, and blinded clinical review.

## 8. What the evidence does and does not support

### Supported technical observations

- Per-session label-free calibration and subsequent state generation are
  reproducible with public EDF examples.
- The framework produces interpretable trajectories and preserves exports for
  later review.
- The primary trajectory rule reduced alert burden relative to a simple local
  threshold in one frozen retrospective benchmark.
- A four-node temporal arrangement is viable for research into a compact
  wearable-monitoring workflow.

### Not established

- Prospective seizure prediction or an exact seizure clock.
- Diagnosis, seizure confirmation, or positive predictive value.
- Safety for driving, work, or independent treatment decisions.
- Clinical efficacy, regulatory suitability, or superiority to multichannel
  EEG systems.
- Clinical meaning of unannotated candidate trajectories.

## 9. Reproducibility resources

- [Interactive bilingual MVP](https://gusmal02.github.io/NEURAL-RMF/mvp/)
- [Two-case English Colab demo](../notebooks/NEURAL_RMF_Colab_Demo_EN.ipynb)
- [Technical preprint on Zenodo](https://doi.org/10.5281/zenodo.22950874)
- [Preprint PDF](../preprint/NEURAL_RMF_preprint_EN.pdf)
- [CHB-MIT Scalp EEG Database](https://physionet.org/content/chbmit/1.0.0/)
- [Siena Scalp EEG Database](https://physionet.org/content/siena-scalp-eeg/1.0.0/)

## 10. Citation

> Maldonado, Gustavo Alfonso. *NEURAL RMF: Individualized EEG Monitoring for
> Early Warnings of Epileptic Seizure Risk*. Zenodo.
> https://doi.org/10.5281/zenodo.22950874
