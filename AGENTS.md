## AIFRED VST:
# Architecture Callibration, Integration, and Analysis Algorythms and Telemetry
===================================================================================


# Core Principles
----------------------


 # aifred_engine implements recognized measurement algorithms. 
 
    DSP profiles configure those algorithms. BufferHunter observes their output over time. aifred_filter interprets the observation. The LLM never defines or modifies a measurement.

    Professional analyzers already use this general model. FabFilter exposes analyzer resolution, range, release speed and display tilt; Pro-Q 4 maps its Low/Medium/High/Maximum analyzer resolutions to 1024/2048/4096/8192-point analysis. Voxengo SPAN exposes FFT block size, overlap, visual slope, smoothing, secondary/maximum spectra, RMS, true peak, EBU R128, K-System and correlation metering. iZotope exposes real-time/averaged spectrum behavior, peak hold, multiple spectral representations and correlation/stereo metering.

First: { 
    the real algorithm library inside aifred_engine
   
    These should be shared implementations. A profile does not get its own hand-written version of RMS, FFT, LUFS, etc. It selects configuration parameters for these modules.


    Engine module	

    Algorithm / basis	

    What AIFRED should implement
};


Sample Peak	max(abs(sample)), converted to dBFS	Per-channel + overall max; clip/sample-over detection from unrounded value

RMS	Root-mean-square over a defined integration window	Configurable window; explicitly document the window used by each profile

True Peak	ITU-R BS.1770 Annex 2	Proper interpolation/oversampling; at 48 kHz the ITU 

example uses 4× to 192 kHz; report dBTP

Momentary LUFS	ITU/EBU K-weighted loudness	400 ms

Short-Term LUFS	ITU/EBU K-weighted loudness	3 s

Integrated LUFS	BS.1770 gated programme loudness	K weighting, mean-square, channel 

weighting, 400 ms blocks/75% overlap, absolute + relative gates

LRA	EBU Tech 3342	Statistical loudness distribution with gating/percentiles

Spectrum	FFT/STFT	Configurable 1024/2048/4096/8192 FFT, overlap, averaging/release, peak hold

30-band telemetry	Band-energy extraction from FFT	Derive the 30 AIFRED bands from the full FFT; do not replace the high-resolution FFT

Crest	Peak-to-average relationship	Explicitly define which peak and RMS window are 
paired; don't ambiguously change definitions per mode

Correlation	Normalized L/R correlation	Continuous -1...+1, rolling window

Stereo balance	L/R energy comparison	Publish actual energy/balance, not a vague “good/bad” 
judgment

M/S energy	Mid/Side transform + level/energy measurement	
Better authoritative basis for width than an unexplained proprietary-looking percentage

Vectorscope source	L/R or M/S sample pairs	Visualization data only; no new “quality” metric
ITU-R BS.1770-5 is the current in-force recommendation for programme loudness and true peak. 

The loudness algorithm uses K weighting, mean-square channel measurements and channel-weighted summation; gated integrated loudness uses 400 ms blocks with 75% overlap, an absolute gate around −70 LKFS and a relative gate 10 dB below the preliminary loudness. EBU Mode defines Momentary as 400 ms, Short-term as 3 s, and Integrated as start-to-stop/programme measurement.

For true peak, don't ever go back to simple linear interpolation and call it dBTP. ITU's guidance specifically describes oversampled waveform reconstruction; its 48 kHz example uses 4× interpolation to 192 kHz, with proportionally less oversampling at higher source rates.

LRA should also remain a real standardized measure, not an AIFRED dynamics score. EBU Tech 3342 bases LRA on the statistical distribution of 3-second loudness measurements with gating and percentile-based spread, specifically so isolated short loud events or quiet tails don't dominate the result.

And crest factor can remain useful, but it needs a documented definition. iZotope correctly notes that in practical mastering use, “crest factor” generally compares some peak measure against an average measure over a corresponding interval; different peak/average choices produce different meanings. So AIFRED should name the definition instead of silently changing it.

## The AIFRED DSP profiles to build
-----------------------------------

    These are workflow profiles, not proprietary-plugin clones.

1. TRACKING_FAST
Purpose: live recording, arrangement work, low CPU, very responsive meters.
FFT              1024
window            Hann
overlap           50%
spectrum release  fast
spectrum hold     short
sample peak       ON
RMS               short/fast window
Momentary LUFS    ON
Short LUFS        ON
Integrated LUFS   optional/not primary
True Peak         ON
Correlation       fast rolling
M/S energy        ON
LRA               OFF until sufficient material

    FabFilter specifically uses 1024 points for its Low analyzer resolution and notes that lower resolution updates faster while higher resolution improves low-frequency precision. That's exactly the tradeoff this profile exploits.

## BufferHunter policy: short observation, maybe roughly 5–10 seconds.
{

    1. The LLM gets: {

    profile = TRACKING_FAST
    observation = short
    confidence in long-term tonal/loudness conclusions = limited
    };
    
So it doesn't make mastering pronouncements based on somebody tracking a vocal for six seconds.

    2. MIX_BALANCED — default AIFRED mode

Purpose: general mixing. This should probably be the flagship default.
    FFT              2048 or 4096
    window            Hann
    overlap           75%
    spectrum release  medium
    peak hold         ON
    sample peak       ON
    RMS               medium integration
    Momentary LUFS    ON
    Short LUFS        ON
    Integrated LUFS   ON
    True Peak         ON
    Crest             ON
    Correlation       ON
    L/R balance       ON
    M/S energy        ON
    30-band telemetry ON


FabFilter's documented Medium and High analyzer modes are 2048 and 4096 points. SPAN similarly exposes block size, overlap and smoothing as normal professional analyzer configuration rather than pretending one FFT configuration is always correct.

#BufferHunter policy: 
----------------------

    Roughly 10–20 seconds before strong tonal/dynamics judgments, continuously updating thereafter.

This is where the thing we figured out matters:

DSP: {
    ST-LUFS -10.43
         -10.88
         -11.12
         -10.51
    ...

    BufferHunter:
        typical -11
        observed -10 → -12
};

#The DSP remains precise. The LLM sees the musical observation.

3. SPECTRUM_SURGICAL

 Purpose: {
    "EQ work", 
    "resonance hunting",    
    "detailed low-frequency inspection", 
    "omparing tiny tonal changes"
};

config: {
    FFT       =       8192
    window    =       Hann initially
    overlap   =        75%
    spectrum release = slow/medium
    peak spectrum   =  ON
    average spectrum = ON
    spectrum range  =  wide
    sample peak   =    ON
    other meters   =   still available
};

    #30-band telemetry derived from same FFT
    #FabFilter's Maximum analyzer resolution is 8192 points, and its docs specifically #recommend High/Maximum resolution for better low-frequency peak/collision detection. It #also exposes 60/90/120 dB display ranges, release speed, and a 4.5 dB/oct display tilt #around 1 kHz.
# Very important: {
Tilt is presentation, not measurement authority.
    We keep:  
    rawSpectrumDb
    and separately:
    displaySpectrumDb
};
    A 4.5 dB/oct visual slope must never reach BufferHunter pretending the highs literally became louder.
    And we do not claim this is “FabFilter DSP.” It's an 8192-point FFT analyzer using publicly established analysis techniques and a similar professional high-resolution workflow.

BufferHunter policy: tonal observations can use a longer averaged spectrum, but level/loudness metrics still come from their proper algorithms.
4. MASTERING_PRECISION
Purpose: final stereo mix/master evaluation.
This is the big one.
FFT                 4096–8192
average spectrum    slow
peak/average traces ON
sample peak          ON
BS.1770 true peak    REQUIRED
Momentary LUFS       REQUIRED
Short-Term LUFS      REQUIRED
Integrated LUFS      REQUIRED
LRA                  REQUIRED
RMS                  ON
Crest                ON
Correlation          ON
L/R balance          ON
M/S energy           ON
30-band telemetry    ON
This uses the real ITU/EBU loudness suite rather than inventing a “mastering loudness” formula. Waves WLM similarly exposes momentary, short- and long-term loudness plus true peak and standards-oriented metering; the exact product internals are proprietary, but the standards themselves are public.
BufferHunter policy: longer observation — something like 20–30 seconds for mix-state advice, plus whole-session Integrated/LRA measurements accumulating independently.
That's important:
BufferHunter 30-second observation
≠
Integrated LUFS
Integrated LUFS keeps its proper programme measurement.
BufferHunter merely says:
during this observed section:
short-term loudness usually -10 → -12
typical -11
while aifred_engine may simultaneously report:
Integrated = -11.8 LUFS
LRA = 5.1 LU
TP = -0.8 dBTP
No bastardized averaging.
5. REFERENCE_LONG_TERM
Purpose: Reference Mode and tonal matching without the reference display jumping everywhere.
This should run the same legitimate measurement stack as MASTERING_PRECISION, but its spectrum observation policy is much slower.
iZotope explicitly documents slowing spectrum averaging to around 10 seconds when comparing source and reference so tonal differences are easier to see, and its reference workflow overlays the stored/reference spectrum with the current source spectrum.
FFT                  4096–8192
spectrum average     long
reference peak trace optional
BS.1770 suite        ON
True Peak            ON
RMS / Crest          ON
Correlation / M/S    ON
30-band telemetry    ON
BufferHunter policy: 30–60 seconds or a user-captured section.
This is where ReferenceProfiles eventually generate distributions:
selected references:

LUFS median
LUFS percentile band

crest median/range

correlation distribution

30-band spectrum median/envelope

true-peak distribution
Then aifred_filter can legitimately classify:
CURRENT
typical ST-LUFS -11
range -10 → -12

REFERENCE
normal range -9 → -13

STATUS
inside reference distribution
instead of:
target = -10.5
current = -10.3
ERROR!!!! 😂
6. STEREO_PHASE_DIAGNOSTIC
Purpose: stereo image, mono compatibility, phase relationships.
Correlation         continuous normalized L/R correlation
Correlation trace   ON
L/R energy balance  ON
M/S energy          ON
vectorscope data    ON
spectrum            2048 or 4096
optional M/S spectra
iZotope's documented correlation meter uses exactly the familiar +1 / 0 / -1 interpretation: +1 for strongly identical/in-phase channels, −1 for opposite phase, with its correlation trace preserving history. Its Imager also uses Polar and Lissajous views plus stereo balance.
I'd stop pretending “Width = 27%” is itself some universal standard unless we explicitly define it.
Better engine output:
correlation = +0.73
mid_energy_db = ...
side_energy_db = ...
side_to_mid_ratio = ...
left_right_balance = ...
Then AIFRED's GUI can still offer a friendly:
WIDTH 27%
but the definition has to be documented and the LLM can reason from the real primitives.
BufferHunter policy: track typical correlation, minimum correlation, time spent below zero, M/S range, and persistent channel imbalance.
That gives the LLM much better information than one instantaneous +0.734192.
7. LOUDNESS_COMPLIANCE
Purpose: broadcast/delivery/QC, not artistic genre advice.
This profile should actually have subprofiles:
EBU_R128
ATSC_A85
CUSTOM_DELIVERY
EBU R128 is based on BS.1770 and uses -23 LUFS as its programme target in EBU workflows, with defined Momentary/Short/Integrated behavior. ATSC A/85 is its own delivery practice; current A/85 documentation remains standards-driven rather than genre-driven.
This mode should be brutally boring:
BS.1770 loudness
BS.1770 true peak
EBU/ATSC target
tolerance
pass/fail / margin
No:
“Your song would sound better with more shimmer.”
😂
That's not what compliance metering is for.
The filter knows:
interpretation_policy = COMPLIANCE
and the LLM knows exactly what it is being asked to assess.
Optional later: K-System
SPAN supports K-System metering, and Bob Katz defines K-20, K-14, and K-12 as monitoring/meter scales for progressively more compressed program contexts: K-20 for wide-dynamic-range material, K-14 for much home/music production, and K-12 for broadcast-style work.
I'd make this a meter calibration/display family, not a replacement for BS.1770:
K20
K14
K12
Useful eventually, but not necessary for BufferHunter v1.
The 30-band question
And here's where I think we can finally get this completely straight.
Your intended centers are:
20
30
40
50
60
70
80
90
100
150
200
250
350
450
600
750
850
1000
1500
2000
3000
4000
6000
8000
10000
12000
14000
16000
18000
20000 Hz
850 Hz is the 30th.
But I'm not going to pretend that exact frequency set is an ITU/EBU/FabFilter standard. It isn't.
That's okay.
The measurement algorithm can still be completely legitimate:
high-resolution FFT/STFT
        ↓
power spectrum
        ↓
frequency regions centered on AIFRED's 30 telemetry frequencies
        ↓
integrate/average power within each region
        ↓
convert band energy to dB
Those 30 values are an AIFRED telemetry representation of real FFT energy, not a replacement FFT and not a made-up psychoacoustic quality algorithm.
That was the mistake in the failed Codex pass.
Keep:
1025/2049/4097 raw FFT bins
depending on FFT size.
Derive:
30-band intelligence vector
from them.
Professional tools do similar reductions in legitimate forms: iZotope exposes linear, 1/3-octave, critical-band and full-octave spectrum representations, while retaining underlying FFT-based analysis.
How I would actually structure aifred_engine
Something along these lines conceptually:
aifred_engine/
│
├── analysis/
│   ├── SamplePeakAnalyzer
│   ├── TruePeakAnalyzer
│   ├── RmsAnalyzer
│   ├── LoudnessAnalyzer
│   ├── LoudnessRangeAnalyzer
│   ├── SpectrumAnalyzer
│   ├── CorrelationAnalyzer
│   ├── StereoEnergyAnalyzer
│   └── CrestAnalyzer
│
├── spectrum/
│   ├── FFT
│   ├── Window
│   ├── Averaging
│   ├── PeakHold
│   └── Aifred30BandExtractor
│
├── profiles/
│   ├── tracking_fast
│   ├── mix_balanced
│   ├── spectrum_surgical
│   ├── mastering_precision
│   ├── reference_long_term
│   ├── stereo_phase
│   └── loudness_compliance
│
└── EngineSnapshot
One algorithm implementation. Many configurations.
Not:
MasteringRMS.cpp
MixRMS.cpp
ReferenceRMS.cpp
SpanLikeRMS.cpp
OzoneRMS.cpp
GodHelpUsFinalRMS2.cpp
😂
A profile should be mostly data/configuration:
DspProfile {
    id;
    version;

    fftSize;
    overlap;
    spectrumWindow;
    spectrumRelease;
    spectrumAverage;
    spectrumTiltDisplay;

    rmsWindow;

    enableMomentary;
    enableShortTerm;
    enableIntegrated;
    enableLra;
    enableTruePeak;

    correlationWindow;
    stereoEnergyWindow;
}
And every EngineSnapshot carries:
profile_id
profile_version
sample_rate
sequence
sample_clock
validity
measurement definitions
Then profile switching connects cleanly to BufferHunter
This is the really important part for the eventual LLM.
USER
selects MASTERING_PRECISION
       ↓
aifred_engine
loads mastering DSP configuration
       ↓
EngineSnapshot
profile_id = mastering_precision.v1
       ↓
BufferHunter
CLOSES old observation epoch
starts new observation epoch
       ↓
aifred_filter
loads matching mastering interpretation policy
       ↓
LLM
receives mastering-semantic context
Never:
10 seconds measured in MIX mode
+
10 seconds measured in MASTERING mode
=
one 20 second average
Different DSP configurations cannot share one observation epoch.
And there are things that absolutely do not belong in aifred_engine
This research actually makes that line clearer.
Things like:
TONAL BALANCE = GOOD
PUNCH = 74%
HARSHNESS = 22
LOW END CONTROL = GREAT
YOUR MIX SHOULD BE -9 LUFS
are not fundamental DSP measurement standards.
If we want them, they belong downstream:
real DSP measurements
       ↓
BufferHunter
       ↓
aifred_filter
       ↓
semantic interpretation
Same with genre targets.
aifred_engine should never know:
“Trap masters should be -9 LUFS.”
It knows:
Integrated LUFS = -10.7
True Peak = -0.8
LRA = 4.2
Crest = 8.1

Reference/genre data tells the filter what's normal.
That's how we stop corrupting measurement with product opinion.
The first implementation set I'd actually build
I wouldn't implement all seven profiles at once.

For the first BufferHunter rewrite, I'd use:
MIX_BALANCED
SPECTRUM_SURGICAL
MASTERING_PRECISION
STEREO_PHASE_DIAGNOSTIC
Those four prove the architecture.
Then add:
REFERENCE_LONG_TERM
LOUDNESS_COMPLIANCE
TRACKING_FAST
once switching/reset semantics and validation are rock solid.
And every algorithm gets tested independently against something external. ITU/EBU provide official test material for loudness/true-peak compliance; then we can manually run identical audio through AIFRED, Waves WLM, SPAN, Pro-Q/Ozone/FL as appropriate and compare behavior rather than blindly trusting our own tests. EBU explicitly provides loudness test signals for meter compliance.

This is the technical profile block I'd put inside the eventual architecture prompt. It gives Codex the real algorithms and profile intent without telling it exactly which classes to write or handing it canned implementation pseudocode.
And the core rule at the top of that prompt should be one sentence:
Every DSP measurement must trace to a documented signal-processing algorithm or recognized metering standard; AIFRED-specific interpretation begins only after aifred_engine, in BufferHunter/aifred_filter.

# ChatGPT Desktop Work Pre-refactor_Task: September 3, 2026

```
simplified prompt outline:

 go through and clean both repos without removing any current configuration....its focus should be all of the docuemtation..there are so many readme's throughout both repos theres a lot of documentation that basically blurs all together and descibe states from multiple build states...some has been updated some has been left becoause those still applied or didn't effect whatever implementation that was being done...so it basically needs to extract the current state minimize documentation and rewrite what it needs to...in the AIFRED_Offical repo only, needs to add documentation that literally puts what you just said into a "repo contruction guide for codex...baszically it needs to produce a clean workspace with identifiable current state for all aspects of the AIFRED repo...then it creates the scaffolding for the new dsp build ...so we can cleanly tell codex to bridge the beta and flagship to the same backend and dsp engine without using any old aifred_engine code...also clean up hardcoded file paths and produce globally platform compatible scripts or simple folder scaffolding for win macOS linux and linux needs to be arch deb ubuntu compatible...like serious organization so the beta and flagship are cleanly separated but compatible to run in the same daw session together ... create scaffolding for production and distribution so theres clear installation, uninstallation, updated separation then once the scaffolding and the new documentation will give codex a clear job...build aifred_engine, bufferHunter, aifred_filter, then route the current beta and the current 4.0 build to them then add the different modes and configuration settings to the gui ...once we get the analyzer done...we start scaffolding the LLM we start actually configuring the aifred_filter with the map-forgelike-tooling-for-audio-analysis-and-daw-intelligence-system-routing that to the LLM model file, and configure AIFRED's general personality by explaining its purpose..Im going to include soul.md heartbeat.md skills.md memories.md etc so user can literally customize their interactions with the model. 

 ```