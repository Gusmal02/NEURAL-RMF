# Anti-Ictal Forcing Module

## Overview

The anti-ictal forcing module (`anti_ictal_forcing` in `config.py`) is an **experimental**
closed-loop intervention that attempts to deflect a pre-ictal EEG trajectory back toward
the interictal baseline.

It is **disabled by default** and has been validated only in simulation.

---

## Clinical hypothesis

When the system enters the `FRONTERA` alert state, the EEG dynamics are on a trajectory
toward the ictal zone. The module applies an oscillatory perturbation to the internal
monitoring field, modeling the effect of an external stimulus (e.g., rhythmic auditory
entrainment) that could redirect the brain's state.

---

## Simulation results (H_AF2)

| Parameter | Value |
|-----------|-------|
| Validation dataset | CHB-MIT + Siena (simulated closed-loop) |
| Trigger state | `FRONTERA` |
| Amplitude A | 0.02 (sweet spot) |
| Novelty reduction | **72.7 %** (simulated) |
| Seizure suppression | Prevented in simulation |

The simulation models a closed loop:

```
EEG → encoder → field → FRONTERA alert
                         ↓
              oscillatory forcing applied
                         ↓
              next EEG window altered by stimulus
                         ↓
              field receives redirected signal
```

---

## Parameter sensitivity

| Amplitude A | Effect |
|-------------|--------|
| A = 0.01 | Too weak — minimal deflection |
| **A = 0.02** | **Sweet spot — 72.7 % novelty reduction** |
| A = 0.05 | Diminishing returns |
| A = 0.10 | Counterproductive — increases variance |

The optimal amplitude is **individual-specific**. Any clinical application would require
per-patient calibration.

---

## Domain validity

| Condition | Module behavior |
|-----------|-----------------|
| Alert onset > 25 min before seizure | Active — sufficient time for field calibration and stimulus delivery |
| Alert onset < 25 min | Inactive — insufficient calibration window |
| State = `CONOCIDO` | Inactive |
| State = `FRONTERA` | **Active** (trigger state) |
| State = `OPUESTO` | Inactive — intervention is too late |

The 25-minute minimum onset requirement is a hard architectural limit.
Below this threshold, the field has not completed calibration and the stimulus
cannot produce a meaningful correction.

---

## Configuration

```python
# config.py
anti_ictal_forcing: bool = False   # disabled by default
forcing_amplitude: float = 0.02   # A parameter (sweet spot)
```

To enable:

```python
anti_ictal_forcing = True
forcing_amplitude = 0.02
```

---

## Critical limitations

1. **Simulation only.** No clinical validation has been performed. All results are from
   a simulated closed-loop model, not from real EEG recordings with actual stimulation.

2. **Mapping to physical stimulus.** The forcing in the model acts on the internal
   field's ω-space. Translating this to a real physical stimulus (auditory frequency,
   amplitude, timing) requires a separate calibration protocol not yet developed.

3. **Sweet spot is individual.** The optimal amplitude A varies by patient. A fixed
   value of 0.02 is a simulation default, not a clinical recommendation.

4. **No effect in sleep or short-lead recordings.** The module was not tested on
   sleep EEG or recordings where seizure onset is < 25 minutes from start of monitoring.

5. **Not a treatment.** This module is a research prototype. It must not be used
   to replace or modify any patient's existing anti-epileptic medication or treatment plan.

---

## Literature basis

The oscillatory forcing mechanism is motivated by work on auditory-cortical entrainment
and closed-loop neuromodulation:

- Ngo H-VV et al. (2013). Auditory closed-loop stimulation of the sleep slow oscillation
  enhances memory. *Neuron*, 78(3), 545–553.
- Thut G et al. (2017). Guiding transcranial brain stimulation by EEG/MEG to interact with
  ongoing brain activity and associated functions. *Journal of Neuroscience*, 37(45), 10817–10830.

---

## Relation to detection pipeline

The anti-ictal module is downstream of the alert semaphore. Detection always runs;
forcing is optional and additive:

```
EEG → NEURAL-RMF detection (always on)
              ↓
        FRONTERA state?
              ↓ yes
   anti_ictal_forcing enabled?
              ↓ yes
   onset > 25 min?
              ↓ yes
   apply oscillatory forcing to field
```

The detection results (`results/results.json`) are unaffected by whether forcing
is enabled or disabled.
