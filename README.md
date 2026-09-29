# NEURAL-RMF

## Individualized EEG monitoring without training on seizure labels

**NEURAL-RMF is a research framework for individualized EEG monitoring.** It
creates a short reference from the current EEG session, then continuously
describes how later activity changes in relation to that reference.

It is not a conventional seizure classifier trained on a large population. It
does not need prior seizure labels to begin a session, and it does not estimate
the exact time at which a seizure will happen. Its research purpose is to
identify and record a trajectory of change that may provide an anticipatory
monitoring window for clinical investigation.

> **Research use only.** NEURAL-RMF is not a diagnostic device, an emergency
> warning service, or a substitute for clinical EEG review, medical judgement,
> or regulatory validation.

## The idea, in plain language

Think of the first usable minutes of a recording as learning the usual surface
of a pond. NEURAL-RMF does not ask, “does this look like a seizure from another
person?” It asks, “how different is this moment from the reference established
for this session?”

The framework observes that relationship over time. A sustained departure can
move through four research monitoring states:

| State | Plain-language meaning |
| --- | --- |
| **Green** | Activity is broadly compatible with this session’s reference. |
| **Yellow** | An early change from the reference is being observed. |
| **Orange** | The change has become sustained and is being monitored. |
| **Red** | A specific, persistent trajectory of change has consolidated and should be recorded for research review. |

Red is not produced by one unusually high value. It requires a temporal
sequence: sustained change, a sufficient individual peak, subsequent decline
or reorganization, increasing collective coherence, and persistence across
successive windows. This is why it is described as monitoring a trajectory,
not making a deterministic prediction.

## What NEURAL-RMF is — and is not

| Question | Answer |
| --- | --- |
| Is it an algorithm? | Yes. It is a dynamic signal-representation and monitoring algorithm. |
| Is it AI? | It is an AI-inspired, label-free representation framework; it is **not** a conventional supervised machine-learning classifier. |
| Does it need a training dataset? | No. It needs a brief, usable calibration from the session being monitored. |
| Does it use clinical labels to generate its states? | No. Labels are used only afterward to compare retrospective results. |
| Does it diagnose epilepsy or confirm a seizure? | No. Those conclusions require clinical EEG interpretation and appropriate validation. |
| Does it predict the exact time of a seizure? | No. It reports baseline-relative activity trajectories and potential anticipatory monitoring states. |

## How a session works

1. **Calibrate:** the first eight minutes establish a session-specific
   reference. This is repeated when a recording session changes or the device
   is removed.
2. **Monitor:** subsequent 30-second windows are compared with that reference.
3. **Describe the trajectory:** the system records the state, timing, and
   research metrics that led to it.
4. **Review retrospectively:** where public annotations exist, they can be
   overlaid after inference. They never generate the state.

## Why begin with four temporal nodes?

The first wearable hypothesis uses a compact bilateral temporal arrangement:
`F7`, `T7`, `F8`, and `T8` (or their equivalent derivations, depending on the
recording montage). Four nodes make a future headband simpler, lighter, and
more repeatable than a full clinical montage while retaining useful
retrospective monitoring coverage.

This is a **portability decision**, not a claim that four nodes replace 23
clinical EEG channels. Full multichannel EEG, video, clinical context, and
neurologist interpretation remain necessary for diagnosis and localization.
A six-node configuration remains a supported future option when it adds value
for a particular patient or recording protocol.

## What has been evaluated so far

The technical work used public, de-identified CHB-MIT and Siena scalp EEG
recordings. Each recording was treated as an independent session and received
its own eight-minute calibration. Labels were withheld while monitoring states
were generated.

The current retrospective report documents 80 session trajectories from 27
participants, including 69 annotated onsets outside calibration. It reports a
preceding generated red trajectory for 66 of those annotated onsets under its
specified protocol. The remaining cases require cautious interpretation:
short usable baseline, timing near calibration, or data-quality limitations do
not establish an absent physiological signal.

Some structured red trajectories do not coincide with an annotation in the
source dataset. They are **research candidates**, not automatically false
alarms and not confirmed subclinical seizures. Possible explanations include
transient physiology, artifacts, an interrupted transition, or subtle
epileptic activity. Resolving this requires synchronized video-EEG,
signal-quality assessment, symptom/context logs, and expert review.

For methods, protocol details, comparative benchmarks, channel-montage
results, definitions, and limitations, read the
[technical note](docs/TECHNICAL.md).

## Try it

- **Interactive MVP:** [open the bilingual monitoring demonstration](https://gusmal02.github.io/NEURAL-RMF/mvp/).
  It reproduces two public sessions, displays the calibration and monitoring
  trajectory, and exports JSON/CSV.
- **Colab example:** [run the two-case notebook](notebooks/NEURAL_RMF_Colab_Demo_EN.ipynb).
  It installs the released wheel, downloads only two public EDF recordings,
  performs the eight-minute per-session calibration, and generates figures and
  exports.
- **Technical preprint:** [Zenodo DOI](https://doi.org/10.5281/zenodo.22950874)
  · [PDF in this repository](preprint/NEURAL_RMF_preprint_EN.pdf).

## Public research distribution

The resonant-memory engine, encoding layer, and internal state logic are
distributed as compiled binary modules. This repository provides the public
research interface, reproducible examples, installation material, and
technical documentation without disclosing the protected internal engine
implementation.

See the [installation guide](docs/INSTALLATION.md),
[technical note](docs/TECHNICAL.md), and [license](LICENSE) before use.

## Collaboration

Clinical, signal-processing, wearable-EEG, and independent replication
collaborations are welcome. The next needed step is prospective and clinically
reviewed evaluation; the present results do not establish clinical efficacy or
safety for daily-life decisions.

**Gustavo Alfonso Maldonado Vallejo** · AI Engineer and Data Science

gustavo.a.maldonado.v@gmail.com

Copyright © 2026 Gustavo Alfonso Maldonado Vallejo. All rights reserved.
