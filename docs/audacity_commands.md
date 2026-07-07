# Audacity mod-script-pipe Commands

> Auto-generated reference from Audacity Help output. Re-run `python scratch/list_commands.py` to refresh.

**Generated:** 2026-07-07 16:46:47 UTC  
**Source:** `scratch/list_commands.py`  
**Discovery query:** `GetInfo: Type=Commands Format=Brief`  
**Total commands:** 64  
**Successful lookups:** 64  
**Failed lookups:** 0

## Overview

This document merges Brief-format command discovery with per-command `Help` queries. Each command section includes Brief metadata and the full JSON schema returned by Audacity.

## Command Index

| Command | Name | Description |
| --- | --- | --- |
| `Amplify` | Amplify | Increases or decreases the volume of the audio you have selected |
| `AutoDuck` | Auto Duck | Reduces (ducks) the volume of one or more tracks whenever the volume of a specified "control" track reaches a particular level |
| `BassAndTreble` | Bass and Treble | Simple tone control effect |
| `ChangePitch` | Change Pitch | Changes the pitch of a track without changing its tempo |
| `ChangeSpeedAndPitch` | Change Speed and Pitch | Changes the speed of a track, also changing its pitch |
| `ChangeTempo` | Change Tempo | Changes the tempo of a selection without changing its pitch |
| `Chirp` | Chirp | Generates an ascending or descending tone of one of four types |
| `ClassicFilters` | Classic Filters | Performs IIR filtering that emulates analog filters |
| `ClickRemoval` | Click Removal | Click Removal is designed to remove clicks on audio tracks |
| `Compressor` | Compressor | Reduces "dynamic range", or differences between loud and quiet parts. |
| `DtmfTones` | DTMF Tones | Generates dual-tone multi-frequency (DTMF) tones like those produced by the keypad on telephones |
| `Distortion` | Distortion | Waveshaping distortion effect |
| `Echo` | Echo | Repeats the selected audio again and again |
| `FadeIn` | Fade In | Applies a linear fade-in to the selected audio |
| `FadeOut` | Fade Out | Applies a linear fade-out to the selected audio |
| `FilterCurve` | Filter Curve EQ | Adjusts the volume levels of particular frequencies |
| `FindClipping` | Find Clipping | Creates labels where clipping is detected |
| `GraphicEq` | Graphic EQ | Adjusts the volume levels of particular frequencies |
| `Invert` | Invert | Flips the audio samples upside-down, reversing their polarity |
| `LegacyCompressor` | Legacy Compressor | Compresses the dynamic range of audio |
| `Limiter` | Limiter | Augments loudness while minimizing distortion. |
| `LoudnessNormalization` | Loudness Normalization | Sets the loudness of one or more tracks |
| `NoiseReduction` | Noise Reduction | Removes background noise such as fans, tape noise, or hums |
| `Noise` | Noise | Generates one of three different types of noise |
| `Normalize` | Normalize | Sets the peak amplitude of one or more tracks |
| `Paulstretch` | Paulstretch | Paulstretch is only for an extreme time-stretch or "stasis" effect |
| `Phaser` | Phaser | Combines phase-shifted signals with the original signal |
| `Repair` | Repair | Sets the peak amplitude of a one or more tracks |
| `Repeat` | Repeat | Repeats the selection the specified number of times |
| `Reverb` | Reverb | Adds ambience or a "hall effect" |
| `Reverse` | Reverse | Reverses the selected audio |
| `Silence` | Silence | Creates audio of zero amplitude |
| `SlidingStretch` | Sliding Stretch | Allows continuous changes to the tempo and/or pitch |
| `StereoToMono` | Stereo To Mono | Converts stereo tracks to mono |
| `Tone` | Tone | Generates a constant frequency tone of one of four types |
| `TruncateSilence` | Truncate Silence | Automatically reduces the length of passages where the volume is below a specified level |
| `Wahwah` | Wahwah | Rapid tone quality variations, like that guitar sound so popular in the 1970's |
| `ClearLog` | Clear Log | Clears the log contents. |
| `Comment` | Comment | For comments in a macro. |
| `CompareAudio` | Compare Audio | Compares a range on two tracks. |
| `Drag` | Drag | Drags mouse from one place to another. |
| `Export2` | Export2 | Exports to a file. |
| `GetInfo` | Get Info | Gets information in JSON format. |
| `GetPreference` | Get Preference | Gets the value of a single preference. |
| `Help` | Help | Gives help on a command. |
| `Import2` | Import2 | Imports from a file. |
| `Message` | Message | Echos a message. |
| `OpenProject2` | Open Project2 | Opens a project. |
| `SaveCopy` | Save Copy | Saves a copy of current project. |
| `SaveLog` | Save Log | Saves the log contents. |
| `SaveProject2` | Save Project2 | Saves a project. |
| `SelectFrequencies` | Select Frequencies | Selects a frequency range. |
| `SelectTime` | Select Time | Selects a time range. |
| `SelectTracks` | Select Tracks | Selects a range of tracks. |
| `Select` | Select | Selects Audio. |
| `SetClip` | Set Clip | Sets various values for a clip. |
| `SetEnvelope` | Set Envelope | Sets an envelope point position. |
| `SetLabel` | Set Label | Sets various values for a label. |
| `SetPreference` | Set Preference | Sets the value of a single preference. |
| `SetProject` | Set Project | Sets various values for a project. |
| `SetTrackAudio` | Set Track Audio | Sets various values for a track. |
| `SetTrackStatus` | Set Track Status | Sets various values for a track. |
| `SetTrackVisuals` | Set Track Visuals | Sets various values for a track. |
| `SetTrack` | Set Track | Sets various values for a track. |

## Commands

### Amplify

**Name:** Amplify  
**Manual URL:** Amplify  
**Description:** Increases or decreases the volume of the audio you have selected

**JSON Schema:**

```json
{
  "id": "Amplify",
  "name": "Amplify",
  "params": [
    {
      "default": 0.9,
      "key": "Ratio",
      "type": "double"
    },
    {
      "default": "False",
      "key": "AllowClipping",
      "type": "bool"
    }
  ],
  "tip": "Increases or decreases the volume of the audio you have selected",
  "url": "Amplify"
}
```

### AutoDuck

**Name:** Auto Duck  
**Manual URL:** Auto_Duck  
**Description:** Reduces (ducks) the volume of one or more tracks whenever the volume of a specified "control" track reaches a particular level

**JSON Schema:**

```json
{
  "id": "AutoDuck",
  "name": "Auto Duck",
  "params": [
    {
      "default": -12,
      "key": "DuckAmountDb",
      "type": "double"
    },
    {
      "default": 0,
      "key": "InnerFadeDownLen",
      "type": "double"
    },
    {
      "default": 0,
      "key": "InnerFadeUpLen",
      "type": "double"
    },
    {
      "default": 0.5,
      "key": "OuterFadeDownLen",
      "type": "double"
    },
    {
      "default": 0.5,
      "key": "OuterFadeUpLen",
      "type": "double"
    },
    {
      "default": -30,
      "key": "ThresholdDb",
      "type": "double"
    },
    {
      "default": 1,
      "key": "MaximumPause",
      "type": "double"
    }
  ],
  "tip": "Reduces (ducks) the volume of one or more tracks whenever the volume of a specified \"control\" track reaches a particular level",
  "url": "Auto_Duck"
}
```

### BassAndTreble

**Name:** Bass and Treble  
**Manual URL:** Bass_and_Treble  
**Description:** Simple tone control effect

**JSON Schema:**

```json
{
  "id": "BassAndTreble",
  "name": "Bass and Treble",
  "params": [
    {
      "default": 0,
      "key": "Bass",
      "type": "double"
    },
    {
      "default": 0,
      "key": "Treble",
      "type": "double"
    },
    {
      "default": 0,
      "key": "Gain",
      "type": "double"
    },
    {
      "default": "False",
      "key": "Link Sliders",
      "type": "bool"
    }
  ],
  "tip": "Simple tone control effect",
  "url": "Bass_and_Treble"
}
```

### ChangePitch

**Name:** Change Pitch  
**Manual URL:** Change_Pitch  
**Description:** Changes the pitch of a track without changing its tempo

**JSON Schema:**

```json
{
  "id": "ChangePitch",
  "name": "Change Pitch",
  "params": [
    {
      "default": 0,
      "key": "Percentage",
      "type": "double"
    },
    {
      "default": "False",
      "key": "SBSMS",
      "type": "bool"
    }
  ],
  "tip": "Changes the pitch of a track without changing its tempo",
  "url": "Change_Pitch"
}
```

### ChangeSpeedAndPitch

**Name:** Change Speed and Pitch  
**Manual URL:** Change_Speed  
**Description:** Changes the speed of a track, also changing its pitch

**JSON Schema:**

```json
{
  "id": "ChangeSpeedAndPitch",
  "name": "Change Speed and Pitch",
  "params": [
    {
      "default": 0,
      "key": "Percentage",
      "type": "double"
    }
  ],
  "tip": "Changes the speed of a track, also changing its pitch",
  "url": "Change_Speed"
}
```

### ChangeTempo

**Name:** Change Tempo  
**Manual URL:** Change_Tempo  
**Description:** Changes the tempo of a selection without changing its pitch

**JSON Schema:**

```json
{
  "id": "ChangeTempo",
  "name": "Change Tempo",
  "params": [
    {
      "default": 0,
      "key": "Percentage",
      "type": "double"
    },
    {
      "default": "False",
      "key": "SBSMS",
      "type": "bool"
    }
  ],
  "tip": "Changes the tempo of a selection without changing its pitch",
  "url": "Change_Tempo"
}
```

### Chirp

**Name:** Chirp  
**Manual URL:** Chirp  
**Description:** Generates an ascending or descending tone of one of four types

**JSON Schema:**

```json
{
  "id": "Chirp",
  "name": "Chirp",
  "params": [
    {
      "default": 440,
      "key": "StartFreq",
      "type": "double"
    },
    {
      "default": 1320,
      "key": "EndFreq",
      "type": "double"
    },
    {
      "default": 0.8,
      "key": "StartAmp",
      "type": "double"
    },
    {
      "default": 0.1,
      "key": "EndAmp",
      "type": "double"
    },
    {
      "default": "Sine",
      "enum": [
        "Sine",
        "Square",
        "Sawtooth",
        "Square, no alias",
        "Triangle"
      ],
      "key": "Waveform",
      "type": "enum"
    },
    {
      "default": "Linear",
      "enum": [
        "Linear",
        "Logarithmic"
      ],
      "key": "Interpolation",
      "type": "enum"
    }
  ],
  "tip": "Generates an ascending or descending tone of one of four types",
  "url": "Chirp"
}
```

### ClassicFilters

**Name:** Classic Filters  
**Manual URL:** Classic_Filters  
**Description:** Performs IIR filtering that emulates analog filters

**JSON Schema:**

```json
{
  "id": "ClassicFilters",
  "name": "Classic Filters",
  "params": [
    {
      "default": "Butterworth",
      "enum": [
        "Butterworth",
        "Chebyshev Type I",
        "Chebyshev Type II"
      ],
      "key": "FilterType",
      "type": "enum"
    },
    {
      "default": "Lowpass",
      "enum": [
        "Lowpass",
        "Highpass"
      ],
      "key": "FilterSubtype",
      "type": "enum"
    },
    {
      "default": 1,
      "key": "Order",
      "type": "int"
    },
    {
      "default": 1000,
      "key": "Cutoff",
      "type": "float"
    },
    {
      "default": 1,
      "key": "PassbandRipple",
      "type": "float"
    },
    {
      "default": 30,
      "key": "StopbandRipple",
      "type": "float"
    }
  ],
  "tip": "Performs IIR filtering that emulates analog filters",
  "url": "Classic_Filters"
}
```

### ClickRemoval

**Name:** Click Removal  
**Manual URL:** Click_Removal  
**Description:** Click Removal is designed to remove clicks on audio tracks

**JSON Schema:**

```json
{
  "id": "ClickRemoval",
  "name": "Click Removal",
  "params": [
    {
      "default": 200,
      "key": "Threshold",
      "type": "int"
    },
    {
      "default": 20,
      "key": "Width",
      "type": "int"
    }
  ],
  "tip": "Click Removal is designed to remove clicks on audio tracks",
  "url": "Click_Removal"
}
```

### Compressor

**Name:** Compressor  
**Manual URL:**   
**Description:** Reduces "dynamic range", or differences between loud and quiet parts.

**JSON Schema:**

```json
{
  "id": "Compressor",
  "name": "Compressor",
  "params": [
    {
      "default": -10,
      "key": "thresholdDb",
      "type": "double"
    },
    {
      "default": 0,
      "key": "makeupGainDb",
      "type": "double"
    },
    {
      "default": 5,
      "key": "kneeWidthDb",
      "type": "double"
    },
    {
      "default": 10,
      "key": "compressionRatio",
      "type": "double"
    },
    {
      "default": 1,
      "key": "lookaheadMs",
      "type": "double"
    },
    {
      "default": 30,
      "key": "attackMs",
      "type": "double"
    },
    {
      "default": 150,
      "key": "releaseMs",
      "type": "double"
    },
    {
      "default": 0,
      "key": "showInput",
      "type": "double"
    },
    {
      "default": 1,
      "key": "showOutput",
      "type": "double"
    },
    {
      "default": 1,
      "key": "showActual",
      "type": "double"
    },
    {
      "default": 0,
      "key": "showTarget",
      "type": "double"
    }
  ],
  "tip": "Reduces \"dynamic range\", or differences between loud and quiet parts.",
  "url": ""
}
```

### DtmfTones

**Name:** DTMF Tones  
**Manual URL:** DTMF_Tones  
**Description:** Generates dual-tone multi-frequency (DTMF) tones like those produced by the keypad on telephones

**JSON Schema:**

```json
{
  "id": "DtmfTones",
  "name": "DTMF Tones",
  "params": [
    {
      "default": "audacity",
      "key": "Sequence",
      "type": "string"
    },
    {
      "default": 55,
      "key": "Duty Cycle",
      "type": "double"
    },
    {
      "default": 0.8,
      "key": "Amplitude",
      "type": "double"
    }
  ],
  "tip": "Generates dual-tone multi-frequency (DTMF) tones like those produced by the keypad on telephones",
  "url": "DTMF_Tones"
}
```

### Distortion

**Name:** Distortion  
**Manual URL:** Distortion  
**Description:** Waveshaping distortion effect

**JSON Schema:**

```json
{
  "id": "Distortion",
  "name": "Distortion",
  "params": [
    {
      "default": "Hard Clipping",
      "enum": [
        "Hard Clipping",
        "Soft Clipping",
        "Soft Overdrive",
        "Medium Overdrive",
        "Hard Overdrive",
        "Cubic Curve (odd harmonics)",
        "Even Harmonics",
        "Expand and Compress",
        "Leveller",
        "Rectifier Distortion",
        "Hard Limiter 1413"
      ],
      "key": "Type",
      "type": "enum"
    },
    {
      "default": "False",
      "key": "DC Block",
      "type": "bool"
    },
    {
      "default": -6,
      "key": "Threshold dB",
      "type": "double"
    },
    {
      "default": -70,
      "key": "Noise Floor",
      "type": "double"
    },
    {
      "default": 50,
      "key": "Parameter 1",
      "type": "double"
    },
    {
      "default": 50,
      "key": "Parameter 2",
      "type": "double"
    },
    {
      "default": 1,
      "key": "Repeats",
      "type": "int"
    }
  ],
  "tip": "Waveshaping distortion effect",
  "url": "Distortion"
}
```

### Echo

**Name:** Echo  
**Manual URL:** Echo  
**Description:** Repeats the selected audio again and again

**JSON Schema:**

```json
{
  "id": "Echo",
  "name": "Echo",
  "params": [
    {
      "default": 1,
      "key": "Delay",
      "type": "double"
    },
    {
      "default": 0.5,
      "key": "Decay",
      "type": "double"
    }
  ],
  "tip": "Repeats the selected audio again and again",
  "url": "Echo"
}
```

### FadeIn

**Name:** Fade In  
**Manual URL:**   
**Description:** Applies a linear fade-in to the selected audio

**JSON Schema:**

```json
{
  "id": "FadeIn",
  "name": "Fade In",
  "params": [],
  "tip": "Applies a linear fade-in to the selected audio",
  "url": ""
}
```

### FadeOut

**Name:** Fade Out  
**Manual URL:**   
**Description:** Applies a linear fade-out to the selected audio

**JSON Schema:**

```json
{
  "id": "FadeOut",
  "name": "Fade Out",
  "params": [],
  "tip": "Applies a linear fade-out to the selected audio",
  "url": ""
}
```

### FilterCurve

**Name:** Filter Curve EQ  
**Manual URL:** Filter_Curve_EQ  
**Description:** Adjusts the volume levels of particular frequencies

**JSON Schema:**

```json
{
  "id": "FilterCurve",
  "name": "Filter Curve EQ",
  "params": [
    {
      "default": 8191,
      "key": "FilterLength",
      "type": "size_t"
    },
    {
      "default": "False",
      "key": "InterpolateLin",
      "type": "bool"
    },
    {
      "default": "B-spline",
      "enum": [
        "B-spline",
        "Cosine",
        "Cubic"
      ],
      "key": "InterpolationMethod",
      "type": "enum"
    }
  ],
  "tip": "Adjusts the volume levels of particular frequencies",
  "url": "Filter_Curve_EQ"
}
```

### FindClipping

**Name:** Find Clipping  
**Manual URL:** Find_Clipping  
**Description:** Creates labels where clipping is detected

**JSON Schema:**

```json
{
  "id": "FindClipping",
  "name": "Find Clipping",
  "params": [
    {
      "default": 3,
      "key": "Duty Cycle Start",
      "type": "int"
    },
    {
      "default": 3,
      "key": "Duty Cycle End",
      "type": "int"
    }
  ],
  "tip": "Creates labels where clipping is detected",
  "url": "Find_Clipping"
}
```

### GraphicEq

**Name:** Graphic EQ  
**Manual URL:** Graphic_EQ  
**Description:** Adjusts the volume levels of particular frequencies

**JSON Schema:**

```json
{
  "id": "GraphicEq",
  "name": "Graphic EQ",
  "params": [
    {
      "default": 8191,
      "key": "FilterLength",
      "type": "size_t"
    },
    {
      "default": "False",
      "key": "InterpolateLin",
      "type": "bool"
    },
    {
      "default": "B-spline",
      "enum": [
        "B-spline",
        "Cosine",
        "Cubic"
      ],
      "key": "InterpolationMethod",
      "type": "enum"
    }
  ],
  "tip": "Adjusts the volume levels of particular frequencies",
  "url": "Graphic_EQ"
}
```

### Invert

**Name:** Invert  
**Manual URL:**   
**Description:** Flips the audio samples upside-down, reversing their polarity

**JSON Schema:**

```json
{
  "id": "Invert",
  "name": "Invert",
  "params": [],
  "tip": "Flips the audio samples upside-down, reversing their polarity",
  "url": ""
}
```

### LegacyCompressor

**Name:** Legacy Compressor  
**Manual URL:** Compressor  
**Description:** Compresses the dynamic range of audio

**JSON Schema:**

```json
{
  "id": "LegacyCompressor",
  "name": "Legacy Compressor",
  "params": [
    {
      "default": -12,
      "key": "Threshold",
      "type": "double"
    },
    {
      "default": -40,
      "key": "NoiseFloor",
      "type": "double"
    },
    {
      "default": 2,
      "key": "Ratio",
      "type": "double"
    },
    {
      "default": 0.2,
      "key": "AttackTime",
      "type": "double"
    },
    {
      "default": 1,
      "key": "ReleaseTime",
      "type": "double"
    },
    {
      "default": "True",
      "key": "Normalize",
      "type": "bool"
    },
    {
      "default": "False",
      "key": "UsePeak",
      "type": "bool"
    }
  ],
  "tip": "Compresses the dynamic range of audio",
  "url": "Compressor"
}
```

### Limiter

**Name:** Limiter  
**Manual URL:**   
**Description:** Augments loudness while minimizing distortion.

**JSON Schema:**

```json
{
  "id": "Limiter",
  "name": "Limiter",
  "params": [
    {
      "default": -5,
      "key": "thresholdDb",
      "type": "double"
    },
    {
      "default": -1,
      "key": "makeupTargetDb",
      "type": "double"
    },
    {
      "default": 2,
      "key": "kneeWidthDb",
      "type": "double"
    },
    {
      "default": 1,
      "key": "lookaheadMs",
      "type": "double"
    },
    {
      "default": 20,
      "key": "releaseMs",
      "type": "double"
    },
    {
      "default": 0,
      "key": "showInput",
      "type": "double"
    },
    {
      "default": 1,
      "key": "showOutput",
      "type": "double"
    },
    {
      "default": 1,
      "key": "showActual",
      "type": "double"
    },
    {
      "default": 0,
      "key": "showTarget",
      "type": "double"
    }
  ],
  "tip": "Augments loudness while minimizing distortion.",
  "url": ""
}
```

### LoudnessNormalization

**Name:** Loudness Normalization  
**Manual URL:** Loudness_Normalization  
**Description:** Sets the loudness of one or more tracks

**JSON Schema:**

```json
{
  "id": "LoudnessNormalization",
  "name": "Loudness Normalization",
  "params": [
    {
      "default": "False",
      "key": "StereoIndependent",
      "type": "bool"
    },
    {
      "default": -23,
      "key": "LUFSLevel",
      "type": "double"
    },
    {
      "default": -20,
      "key": "RMSLevel",
      "type": "double"
    },
    {
      "default": "True",
      "key": "DualMono",
      "type": "bool"
    },
    {
      "default": 0,
      "key": "NormalizeTo",
      "type": "int"
    }
  ],
  "tip": "Sets the loudness of one or more tracks",
  "url": "Loudness_Normalization"
}
```

### NoiseReduction

**Name:** Noise Reduction  
**Manual URL:**   
**Description:** Removes background noise such as fans, tape noise, or hums

**JSON Schema:**

```json
{
  "id": "NoiseReduction",
  "name": "Noise Reduction",
  "params": [],
  "tip": "Removes background noise such as fans, tape noise, or hums",
  "url": ""
}
```

### Noise

**Name:** Noise  
**Manual URL:** Noise  
**Description:** Generates one of three different types of noise

**JSON Schema:**

```json
{
  "id": "Noise",
  "name": "Noise",
  "params": [
    {
      "default": "White",
      "enum": [
        "White",
        "Pink",
        "Brownian"
      ],
      "key": "Type",
      "type": "enum"
    },
    {
      "default": 0.8,
      "key": "Amplitude",
      "type": "double"
    }
  ],
  "tip": "Generates one of three different types of noise",
  "url": "Noise"
}
```

### Normalize

**Name:** Normalize  
**Manual URL:** Normalize  
**Description:** Sets the peak amplitude of one or more tracks

**JSON Schema:**

```json
{
  "id": "Normalize",
  "name": "Normalize",
  "params": [
    {
      "default": -1,
      "key": "PeakLevel",
      "type": "double"
    },
    {
      "default": "True",
      "key": "ApplyVolume",
      "type": "bool"
    },
    {
      "default": "True",
      "key": "RemoveDcOffset",
      "type": "bool"
    },
    {
      "default": "False",
      "key": "StereoIndependent",
      "type": "bool"
    }
  ],
  "tip": "Sets the peak amplitude of one or more tracks",
  "url": "Normalize"
}
```

### Paulstretch

**Name:** Paulstretch  
**Manual URL:** Paulstretch  
**Description:** Paulstretch is only for an extreme time-stretch or "stasis" effect

**JSON Schema:**

```json
{
  "id": "Paulstretch",
  "name": "Paulstretch",
  "params": [
    {
      "default": 10,
      "key": "Stretch Factor",
      "type": "float"
    },
    {
      "default": 0.25,
      "key": "Time Resolution",
      "type": "float"
    }
  ],
  "tip": "Paulstretch is only for an extreme time-stretch or \"stasis\" effect",
  "url": "Paulstretch"
}
```

### Phaser

**Name:** Phaser  
**Manual URL:** Phaser  
**Description:** Combines phase-shifted signals with the original signal

**JSON Schema:**

```json
{
  "id": "Phaser",
  "name": "Phaser",
  "params": [
    {
      "default": 2,
      "key": "Stages",
      "type": "int"
    },
    {
      "default": 128,
      "key": "DryWet",
      "type": "int"
    },
    {
      "default": 0.4,
      "key": "Freq",
      "type": "double"
    },
    {
      "default": 0,
      "key": "Phase",
      "type": "double"
    },
    {
      "default": 100,
      "key": "Depth",
      "type": "int"
    },
    {
      "default": 0,
      "key": "Feedback",
      "type": "int"
    },
    {
      "default": -6,
      "key": "Gain",
      "type": "double"
    }
  ],
  "tip": "Combines phase-shifted signals with the original signal",
  "url": "Phaser"
}
```

### Repair

**Name:** Repair  
**Manual URL:**   
**Description:** Sets the peak amplitude of a one or more tracks

**JSON Schema:**

```json
{
  "id": "Repair",
  "name": "Repair",
  "params": [],
  "tip": "Sets the peak amplitude of a one or more tracks",
  "url": ""
}
```

### Repeat

**Name:** Repeat  
**Manual URL:** Repeat  
**Description:** Repeats the selection the specified number of times

**JSON Schema:**

```json
{
  "id": "Repeat",
  "name": "Repeat",
  "params": [
    {
      "default": 1,
      "key": "Count",
      "type": "int"
    }
  ],
  "tip": "Repeats the selection the specified number of times",
  "url": "Repeat"
}
```

### Reverb

**Name:** Reverb  
**Manual URL:** Reverb  
**Description:** Adds ambience or a "hall effect"

**JSON Schema:**

```json
{
  "id": "Reverb",
  "name": "Reverb",
  "params": [
    {
      "default": 75,
      "key": "RoomSize",
      "type": "double"
    },
    {
      "default": 10,
      "key": "Delay",
      "type": "double"
    },
    {
      "default": 50,
      "key": "Reverberance",
      "type": "double"
    },
    {
      "default": 50,
      "key": "HfDamping",
      "type": "double"
    },
    {
      "default": 100,
      "key": "ToneLow",
      "type": "double"
    },
    {
      "default": 100,
      "key": "ToneHigh",
      "type": "double"
    },
    {
      "default": -1,
      "key": "WetGain",
      "type": "double"
    },
    {
      "default": -1,
      "key": "DryGain",
      "type": "double"
    },
    {
      "default": 100,
      "key": "StereoWidth",
      "type": "double"
    },
    {
      "default": "False",
      "key": "WetOnly",
      "type": "bool"
    }
  ],
  "tip": "Adds ambience or a \"hall effect\"",
  "url": "Reverb"
}
```

### Reverse

**Name:** Reverse  
**Manual URL:**   
**Description:** Reverses the selected audio

**JSON Schema:**

```json
{
  "id": "Reverse",
  "name": "Reverse",
  "params": [],
  "tip": "Reverses the selected audio",
  "url": ""
}
```

### Silence

**Name:** Silence  
**Manual URL:** Silence  
**Description:** Creates audio of zero amplitude

**JSON Schema:**

```json
{
  "id": "Silence",
  "name": "Silence",
  "params": [],
  "tip": "Creates audio of zero amplitude",
  "url": "Silence"
}
```

### SlidingStretch

**Name:** Sliding Stretch  
**Manual URL:** Sliding_Stretch  
**Description:** Allows continuous changes to the tempo and/or pitch

**JSON Schema:**

```json
{
  "id": "SlidingStretch",
  "name": "Sliding Stretch",
  "params": [
    {
      "default": 0,
      "key": "RatePercentChangeStart",
      "type": "double"
    },
    {
      "default": 0,
      "key": "RatePercentChangeEnd",
      "type": "double"
    },
    {
      "default": 0,
      "key": "PitchHalfStepsStart",
      "type": "double"
    },
    {
      "default": 0,
      "key": "PitchHalfStepsEnd",
      "type": "double"
    },
    {
      "default": 0,
      "key": "PitchPercentChangeStart",
      "type": "double"
    },
    {
      "default": 0,
      "key": "PitchPercentChangeEnd",
      "type": "double"
    }
  ],
  "tip": "Allows continuous changes to the tempo and/or pitch",
  "url": "Sliding_Stretch"
}
```

### StereoToMono

**Name:** Stereo To Mono  
**Manual URL:**   
**Description:** Converts stereo tracks to mono

**JSON Schema:**

```json
{
  "id": "StereoToMono",
  "name": "Stereo To Mono",
  "params": [],
  "tip": "Converts stereo tracks to mono",
  "url": ""
}
```

### Tone

**Name:** Tone  
**Manual URL:** Tone  
**Description:** Generates a constant frequency tone of one of four types

**JSON Schema:**

```json
{
  "id": "Tone",
  "name": "Tone",
  "params": [
    {
      "default": 440,
      "key": "Frequency",
      "type": "double"
    },
    {
      "default": 0.8,
      "key": "Amplitude",
      "type": "double"
    },
    {
      "default": "Sine",
      "enum": [
        "Sine",
        "Square",
        "Sawtooth",
        "Square, no alias",
        "Triangle"
      ],
      "key": "Waveform",
      "type": "enum"
    },
    {
      "default": "Linear",
      "enum": [
        "Linear",
        "Logarithmic"
      ],
      "key": "Interpolation",
      "type": "enum"
    }
  ],
  "tip": "Generates a constant frequency tone of one of four types",
  "url": "Tone"
}
```

### TruncateSilence

**Name:** Truncate Silence  
**Manual URL:** Truncate_Silence  
**Description:** Automatically reduces the length of passages where the volume is below a specified level

**JSON Schema:**

```json
{
  "id": "TruncateSilence",
  "name": "Truncate Silence",
  "params": [
    {
      "default": -20,
      "key": "Threshold",
      "type": "double"
    },
    {
      "default": "Truncate Detected Silence",
      "enum": [
        "Truncate Detected Silence",
        "Compress Excess Silence"
      ],
      "key": "Action",
      "type": "enum"
    },
    {
      "default": 0.5,
      "key": "Minimum",
      "type": "double"
    },
    {
      "default": 0.5,
      "key": "Truncate",
      "type": "double"
    },
    {
      "default": 50,
      "key": "Compress",
      "type": "double"
    },
    {
      "default": "False",
      "key": "Independent",
      "type": "bool"
    }
  ],
  "tip": "Automatically reduces the length of passages where the volume is below a specified level",
  "url": "Truncate_Silence"
}
```

### Wahwah

**Name:** Wahwah  
**Manual URL:** Wahwah  
**Description:** Rapid tone quality variations, like that guitar sound so popular in the 1970's

**JSON Schema:**

```json
{
  "id": "Wahwah",
  "name": "Wahwah",
  "params": [
    {
      "default": 1.5,
      "key": "Freq",
      "type": "double"
    },
    {
      "default": 0,
      "key": "Phase",
      "type": "double"
    },
    {
      "default": 70,
      "key": "Depth",
      "type": "int"
    },
    {
      "default": 2.5,
      "key": "Resonance",
      "type": "double"
    },
    {
      "default": 30,
      "key": "Offset",
      "type": "int"
    },
    {
      "default": -6,
      "key": "Gain",
      "type": "double"
    }
  ],
  "tip": "Rapid tone quality variations, like that guitar sound so popular in the 1970's",
  "url": "Wahwah"
}
```

### ClearLog

**Name:** Clear Log  
**Manual URL:** Extra_Menu:_Scriptables_II#Clear_log  
**Description:** Clears the log contents.

**JSON Schema:**

```json
{
  "id": "ClearLog",
  "name": "Clear Log",
  "params": [],
  "tip": "Clears the log contents.",
  "url": "Extra_Menu:_Scriptables_II#Clear_log"
}
```

### Comment

**Name:** Comment  
**Manual URL:** Extra_Menu:_Scriptables_II#comment  
**Description:** For comments in a macro.

**JSON Schema:**

```json
{
  "id": "Comment",
  "name": "Comment",
  "params": [
    {
      "default": "",
      "key": "_",
      "type": "string"
    }
  ],
  "tip": "For comments in a macro.",
  "url": "Extra_Menu:_Scriptables_II#comment"
}
```

### CompareAudio

**Name:** Compare Audio  
**Manual URL:** Extra_Menu:_Scriptables_II#compare_Audio  
**Description:** Compares a range on two tracks.

**JSON Schema:**

```json
{
  "id": "CompareAudio",
  "name": "Compare Audio",
  "params": [
    {
      "default": 0,
      "key": "Threshold",
      "type": "float"
    }
  ],
  "tip": "Compares a range on two tracks.",
  "url": "Extra_Menu:_Scriptables_II#compare_Audio"
}
```

### Drag

**Name:** Drag  
**Manual URL:** Extra_Menu:_Scriptables_II#move_mouse  
**Description:** Drags mouse from one place to another.

**JSON Schema:**

```json
{
  "id": "Drag",
  "name": "Drag",
  "params": [
    {
      "default": "unchanged",
      "key": "Id",
      "type": "int"
    },
    {
      "default": "unchanged",
      "key": "Window",
      "type": "string"
    },
    {
      "default": "unchanged",
      "key": "FromX",
      "type": "double"
    },
    {
      "default": "unchanged",
      "key": "FromY",
      "type": "double"
    },
    {
      "default": "unchanged",
      "key": "ToX",
      "type": "double"
    },
    {
      "default": "unchanged",
      "key": "ToY",
      "type": "double"
    },
    {
      "default": "unchanged",
      "enum": [
        "Panel",
        "App",
        "Track0",
        "Track1"
      ],
      "key": "RelativeTo",
      "type": "enum"
    }
  ],
  "tip": "Drags mouse from one place to another.",
  "url": "Extra_Menu:_Scriptables_II#move_mouse"
}
```

### Export2

**Name:** Export2  
**Manual URL:** Extra_Menu:_Scriptables_II#export  
**Description:** Exports to a file.

**JSON Schema:**

```json
{
  "id": "Export2",
  "name": "Export2",
  "params": [
    {
      "default": "/home/jaypee/exported.wav",
      "key": "Filename",
      "type": "string"
    },
    {
      "default": 1,
      "key": "NumChannels",
      "type": "int"
    }
  ],
  "tip": "Exports to a file.",
  "url": "Extra_Menu:_Scriptables_II#export"
}
```

### GetInfo

**Name:** Get Info  
**Manual URL:** Extra_Menu:_Scriptables_II#get_info  
**Description:** Gets information in JSON format.

**JSON Schema:**

```json
{
  "id": "GetInfo",
  "name": "Get Info",
  "params": [
    {
      "default": "Commands",
      "enum": [
        "Commands",
        "Menus",
        "Preferences",
        "Tracks",
        "Clips",
        "Envelopes",
        "Labels",
        "Boxes",
        "Selection"
      ],
      "key": "Type",
      "type": "enum"
    },
    {
      "default": "JSON",
      "enum": [
        "JSON",
        "LISP",
        "Brief"
      ],
      "key": "Format",
      "type": "enum"
    }
  ],
  "tip": "Gets information in JSON format.",
  "url": "Extra_Menu:_Scriptables_II#get_info"
}
```

### GetPreference

**Name:** Get Preference  
**Manual URL:** Extra_Menu:_Scriptables_I#get_preference  
**Description:** Gets the value of a single preference.

**JSON Schema:**

```json
{
  "id": "GetPreference",
  "name": "Get Preference",
  "params": [
    {
      "default": "",
      "key": "Name",
      "type": "string"
    }
  ],
  "tip": "Gets the value of a single preference.",
  "url": "Extra_Menu:_Scriptables_I#get_preference"
}
```

### Help

**Name:** Help  
**Manual URL:** Extra_Menu:_Scriptables_II#help  
**Description:** Gives help on a command.

**JSON Schema:**

```json
{
  "id": "Help",
  "name": "Help",
  "params": [
    {
      "default": "Help",
      "key": "Command",
      "type": "string"
    },
    {
      "default": "JSON",
      "enum": [
        "JSON",
        "LISP",
        "Brief"
      ],
      "key": "Format",
      "type": "enum"
    }
  ],
  "tip": "Gives help on a command.",
  "url": "Extra_Menu:_Scriptables_II#help"
}
```

### Import2

**Name:** Import2  
**Manual URL:** Extra_Menu:_Scriptables_II#import  
**Description:** Imports from a file.

**JSON Schema:**

```json
{
  "id": "Import2",
  "name": "Import2",
  "params": [
    {
      "default": "",
      "key": "Filename",
      "type": "string"
    }
  ],
  "tip": "Imports from a file.",
  "url": "Extra_Menu:_Scriptables_II#import"
}
```

### Message

**Name:** Message  
**Manual URL:** Extra_Menu:_Scriptables_II#message  
**Description:** Echos a message.

**JSON Schema:**

```json
{
  "id": "Message",
  "name": "Message",
  "params": [
    {
      "default": "Some message",
      "key": "Text",
      "type": "string"
    }
  ],
  "tip": "Echos a message.",
  "url": "Extra_Menu:_Scriptables_II#message"
}
```

### OpenProject2

**Name:** Open Project2  
**Manual URL:** Extra_Menu:_Scriptables_II#open_project  
**Description:** Opens a project.

**JSON Schema:**

```json
{
  "id": "OpenProject2",
  "name": "Open Project2",
  "params": [
    {
      "default": "test.aup3",
      "key": "Filename",
      "type": "string"
    },
    {
      "default": "unchanged",
      "key": "AddToHistory",
      "type": "bool"
    }
  ],
  "tip": "Opens a project.",
  "url": "Extra_Menu:_Scriptables_II#open_project"
}
```

### SaveCopy

**Name:** Save Copy  
**Manual URL:** Extra_Menu:_Scriptables_II#save_copy  
**Description:** Saves a copy of current project.

**JSON Schema:**

```json
{
  "id": "SaveCopy",
  "name": "Save Copy",
  "params": [
    {
      "default": "name.aup3",
      "key": "Filename",
      "type": "string"
    }
  ],
  "tip": "Saves a copy of current project.",
  "url": "Extra_Menu:_Scriptables_II#save_copy"
}
```

### SaveLog

**Name:** Save Log  
**Manual URL:** Extra_Menu:_Scriptables_II#save_log  
**Description:** Saves the log contents.

**JSON Schema:**

```json
{
  "id": "SaveLog",
  "name": "Save Log",
  "params": [
    {
      "default": "log.txt",
      "key": "Filename",
      "type": "string"
    }
  ],
  "tip": "Saves the log contents.",
  "url": "Extra_Menu:_Scriptables_II#save_log"
}
```

### SaveProject2

**Name:** Save Project2  
**Manual URL:** Extra_Menu:_Scriptables_II#save_project  
**Description:** Saves a project.

**JSON Schema:**

```json
{
  "id": "SaveProject2",
  "name": "Save Project2",
  "params": [
    {
      "default": "name.aup3",
      "key": "Filename",
      "type": "string"
    },
    {
      "default": "False",
      "key": "AddToHistory",
      "type": "bool"
    }
  ],
  "tip": "Saves a project.",
  "url": "Extra_Menu:_Scriptables_II#save_project"
}
```

### SelectFrequencies

**Name:** Select Frequencies  
**Manual URL:** Extra_Menu:_Scriptables_I#select_frequencies  
**Description:** Selects a frequency range.

**JSON Schema:**

```json
{
  "id": "SelectFrequencies",
  "name": "Select Frequencies",
  "params": [
    {
      "default": "unchanged",
      "key": "High",
      "type": "double"
    },
    {
      "default": "unchanged",
      "key": "Low",
      "type": "double"
    }
  ],
  "tip": "Selects a frequency range.",
  "url": "Extra_Menu:_Scriptables_I#select_frequencies"
}
```

### SelectTime

**Name:** Select Time  
**Manual URL:** Extra_Menu:_Scriptables_I#select_time  
**Description:** Selects a time range.

**JSON Schema:**

```json
{
  "id": "SelectTime",
  "name": "Select Time",
  "params": [
    {
      "default": "unchanged",
      "key": "Start",
      "type": "double"
    },
    {
      "default": "unchanged",
      "key": "End",
      "type": "double"
    },
    {
      "default": "unchanged",
      "enum": [
        "ProjectStart",
        "Project",
        "ProjectEnd",
        "SelectionStart",
        "Selection",
        "SelectionEnd"
      ],
      "key": "RelativeTo",
      "type": "enum"
    }
  ],
  "tip": "Selects a time range.",
  "url": "Extra_Menu:_Scriptables_I#select_time"
}
```

### SelectTracks

**Name:** Select Tracks  
**Manual URL:** Extra_Menu:_Scriptables_I#select_tracks  
**Description:** Selects a range of tracks.

**JSON Schema:**

```json
{
  "id": "SelectTracks",
  "name": "Select Tracks",
  "params": [
    {
      "default": "unchanged",
      "key": "Track",
      "type": "double"
    },
    {
      "default": "unchanged",
      "key": "TrackCount",
      "type": "double"
    },
    {
      "default": "unchanged",
      "enum": [
        "Set",
        "Add",
        "Remove"
      ],
      "key": "Mode",
      "type": "enum"
    }
  ],
  "tip": "Selects a range of tracks.",
  "url": "Extra_Menu:_Scriptables_I#select_tracks"
}
```

### Select

**Name:** Select  
**Manual URL:** Extra_Menu:_Scriptables_II#select  
**Description:** Selects Audio.

**JSON Schema:**

```json
{
  "id": "Select",
  "name": "Select",
  "params": [
    {
      "default": "unchanged",
      "key": "Start",
      "type": "double"
    },
    {
      "default": "unchanged",
      "key": "End",
      "type": "double"
    },
    {
      "default": "unchanged",
      "enum": [
        "ProjectStart",
        "Project",
        "ProjectEnd",
        "SelectionStart",
        "Selection",
        "SelectionEnd"
      ],
      "key": "RelativeTo",
      "type": "enum"
    },
    {
      "default": "unchanged",
      "key": "High",
      "type": "double"
    },
    {
      "default": "unchanged",
      "key": "Low",
      "type": "double"
    },
    {
      "default": "unchanged",
      "key": "Track",
      "type": "double"
    },
    {
      "default": "unchanged",
      "key": "TrackCount",
      "type": "double"
    },
    {
      "default": "unchanged",
      "enum": [
        "Set",
        "Add",
        "Remove"
      ],
      "key": "Mode",
      "type": "enum"
    }
  ],
  "tip": "Selects Audio.",
  "url": "Extra_Menu:_Scriptables_II#select"
}
```

### SetClip

**Name:** Set Clip  
**Manual URL:** Extra_Menu:_Scriptables_I#set_clip  
**Description:** Sets various values for a clip.

**JSON Schema:**

```json
{
  "id": "SetClip",
  "name": "Set Clip",
  "params": [
    {
      "default": "unchanged",
      "key": "At",
      "type": "double"
    },
    {
      "default": "unchanged",
      "enum": [
        "Color0",
        "Color1",
        "Color2",
        "Color3"
      ],
      "key": "Color",
      "type": "enum"
    },
    {
      "default": "unchanged",
      "key": "Start",
      "type": "double"
    }
  ],
  "tip": "Sets various values for a clip.",
  "url": "Extra_Menu:_Scriptables_I#set_clip"
}
```

### SetEnvelope

**Name:** Set Envelope  
**Manual URL:** Extra_Menu:_Scriptables_I#set_envelope  
**Description:** Sets an envelope point position.

**JSON Schema:**

```json
{
  "id": "SetEnvelope",
  "name": "Set Envelope",
  "params": [
    {
      "default": "unchanged",
      "key": "Time",
      "type": "double"
    },
    {
      "default": "unchanged",
      "key": "Value",
      "type": "double"
    },
    {
      "default": "unchanged",
      "key": "Delete",
      "type": "bool"
    }
  ],
  "tip": "Sets an envelope point position.",
  "url": "Extra_Menu:_Scriptables_I#set_envelope"
}
```

### SetLabel

**Name:** Set Label  
**Manual URL:** Extra_Menu:_Scriptables_I#set_label  
**Description:** Sets various values for a label.

**JSON Schema:**

```json
{
  "id": "SetLabel",
  "name": "Set Label",
  "params": [
    {
      "default": 0,
      "key": "Label",
      "type": "int"
    },
    {
      "default": "unchanged",
      "key": "Text",
      "type": "string"
    },
    {
      "default": "unchanged",
      "key": "Start",
      "type": "double"
    },
    {
      "default": "unchanged",
      "key": "End",
      "type": "double"
    },
    {
      "default": "unchanged",
      "key": "Selected",
      "type": "bool"
    }
  ],
  "tip": "Sets various values for a label.",
  "url": "Extra_Menu:_Scriptables_I#set_label"
}
```

### SetPreference

**Name:** Set Preference  
**Manual URL:** Extra_Menu:_Scriptables_I#set_preference  
**Description:** Sets the value of a single preference.

**JSON Schema:**

```json
{
  "id": "SetPreference",
  "name": "Set Preference",
  "params": [
    {
      "default": "",
      "key": "Name",
      "type": "string"
    },
    {
      "default": "",
      "key": "Value",
      "type": "string"
    },
    {
      "default": "False",
      "key": "Reload",
      "type": "bool"
    }
  ],
  "tip": "Sets the value of a single preference.",
  "url": "Extra_Menu:_Scriptables_I#set_preference"
}
```

### SetProject

**Name:** Set Project  
**Manual URL:** Extra_Menu:_Scriptables_I#set_project  
**Description:** Sets various values for a project.

**JSON Schema:**

```json
{
  "id": "SetProject",
  "name": "Set Project",
  "params": [
    {
      "default": "unchanged",
      "key": "Name",
      "type": "string"
    },
    {
      "default": "unchanged",
      "key": "Rate",
      "type": "double"
    },
    {
      "default": "unchanged",
      "key": "X",
      "type": "int"
    },
    {
      "default": "unchanged",
      "key": "Y",
      "type": "int"
    },
    {
      "default": "unchanged",
      "key": "Width",
      "type": "int"
    },
    {
      "default": "unchanged",
      "key": "Height",
      "type": "int"
    }
  ],
  "tip": "Sets various values for a project.",
  "url": "Extra_Menu:_Scriptables_I#set_project"
}
```

### SetTrackAudio

**Name:** Set Track Audio  
**Manual URL:** Extra_Menu:_Scriptables_I#set_track_audio  
**Description:** Sets various values for a track.

**JSON Schema:**

```json
{
  "id": "SetTrackAudio",
  "name": "Set Track Audio",
  "params": [
    {
      "default": "unchanged",
      "key": "Mute",
      "type": "bool"
    },
    {
      "default": "unchanged",
      "key": "Solo",
      "type": "bool"
    },
    {
      "default": "unchanged",
      "key": "Volume",
      "type": "double"
    },
    {
      "default": "unchanged",
      "key": "Pan",
      "type": "double"
    }
  ],
  "tip": "Sets various values for a track.",
  "url": "Extra_Menu:_Scriptables_I#set_track_audio"
}
```

### SetTrackStatus

**Name:** Set Track Status  
**Manual URL:** Extra_Menu:_Scriptables_I#set_track_status  
**Description:** Sets various values for a track.

**JSON Schema:**

```json
{
  "id": "SetTrackStatus",
  "name": "Set Track Status",
  "params": [
    {
      "default": "unchanged",
      "key": "Name",
      "type": "string"
    },
    {
      "default": "unchanged",
      "key": "Selected",
      "type": "bool"
    },
    {
      "default": "unchanged",
      "key": "Focused",
      "type": "bool"
    }
  ],
  "tip": "Sets various values for a track.",
  "url": "Extra_Menu:_Scriptables_I#set_track_status"
}
```

### SetTrackVisuals

**Name:** Set Track Visuals  
**Manual URL:** Extra_Menu:_Scriptables_I#set_track_visuals  
**Description:** Sets various values for a track.

**JSON Schema:**

```json
{
  "id": "SetTrackVisuals",
  "name": "Set Track Visuals",
  "params": [
    {
      "default": "unchanged",
      "key": "Height",
      "type": "int"
    },
    {
      "default": "unchanged",
      "enum": [
        "Waveform",
        "Spectrogram",
        "Multiview"
      ],
      "key": "Display",
      "type": "enum"
    },
    {
      "default": "unchanged",
      "enum": [
        "Linear",
        "dB",
        "LinearDB"
      ],
      "key": "Scale",
      "type": "enum"
    },
    {
      "default": "unchanged",
      "enum": [
        "Color0",
        "Color1",
        "Color2",
        "Color3"
      ],
      "key": "Color",
      "type": "enum"
    },
    {
      "default": "unchanged",
      "enum": [
        "Reset",
        "Times2",
        "HalfWave"
      ],
      "key": "VZoom",
      "type": "enum"
    },
    {
      "default": "unchanged",
      "key": "VZoomHigh",
      "type": "double"
    },
    {
      "default": "unchanged",
      "key": "VZoomLow",
      "type": "double"
    },
    {
      "default": "unchanged",
      "key": "SpecPrefs",
      "type": "bool"
    },
    {
      "default": "unchanged",
      "key": "SpectralSel",
      "type": "bool"
    },
    {
      "default": "unchanged",
      "enum": [
        "SpecColorNew",
        "SpecColorTheme",
        "SpecGrayscale",
        "SpecInvGrayscale"
      ],
      "key": "SpecColor",
      "type": "enum"
    }
  ],
  "tip": "Sets various values for a track.",
  "url": "Extra_Menu:_Scriptables_I#set_track_visuals"
}
```

### SetTrack

**Name:** Set Track  
**Manual URL:** Extra_Menu:_Scriptables_II#set_track  
**Description:** Sets various values for a track.

**JSON Schema:**

```json
{
  "id": "SetTrack",
  "name": "Set Track",
  "params": [
    {
      "default": "unchanged",
      "key": "Name",
      "type": "string"
    },
    {
      "default": "unchanged",
      "key": "Selected",
      "type": "bool"
    },
    {
      "default": "unchanged",
      "key": "Focused",
      "type": "bool"
    },
    {
      "default": "unchanged",
      "key": "Mute",
      "type": "bool"
    },
    {
      "default": "unchanged",
      "key": "Solo",
      "type": "bool"
    },
    {
      "default": "unchanged",
      "key": "Volume",
      "type": "double"
    },
    {
      "default": "unchanged",
      "key": "Pan",
      "type": "double"
    },
    {
      "default": "unchanged",
      "key": "Height",
      "type": "int"
    },
    {
      "default": "unchanged",
      "enum": [
        "Waveform",
        "Spectrogram",
        "Multiview"
      ],
      "key": "Display",
      "type": "enum"
    },
    {
      "default": "unchanged",
      "enum": [
        "Linear",
        "dB",
        "LinearDB"
      ],
      "key": "Scale",
      "type": "enum"
    },
    {
      "default": "unchanged",
      "enum": [
        "Color0",
        "Color1",
        "Color2",
        "Color3"
      ],
      "key": "Color",
      "type": "enum"
    },
    {
      "default": "unchanged",
      "enum": [
        "Reset",
        "Times2",
        "HalfWave"
      ],
      "key": "VZoom",
      "type": "enum"
    },
    {
      "default": "unchanged",
      "key": "VZoomHigh",
      "type": "double"
    },
    {
      "default": "unchanged",
      "key": "VZoomLow",
      "type": "double"
    },
    {
      "default": "unchanged",
      "key": "SpecPrefs",
      "type": "bool"
    },
    {
      "default": "unchanged",
      "key": "SpectralSel",
      "type": "bool"
    },
    {
      "default": "unchanged",
      "enum": [
        "SpecColorNew",
        "SpecColorTheme",
        "SpecGrayscale",
        "SpecInvGrayscale"
      ],
      "key": "SpecColor",
      "type": "enum"
    }
  ],
  "tip": "Sets various values for a track.",
  "url": "Extra_Menu:_Scriptables_II#set_track"
}
```
