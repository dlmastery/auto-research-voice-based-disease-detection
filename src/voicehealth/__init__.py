"""voicehealth — frozen-embedding benchmark harness for the voice-health claim audit.

Modules
-------
`embed`      frozen SSL / foundation-model embedding extraction, content-hash cached
`features`   the classical eGeMAPS baseline that SOTA papers claim to beat
`benchmark`  speaker-disjoint GroupKFold harness + confound baseline + margins

Design rules inherited from CLAUDE.md:
  R1  every number is written to an artifact file with its config hash
  R2  the agent never states a metric it did not read out of an artifact
  R6  statistical power is COMPUTED per family, never assumed
  §4.3 speaker-disjoint splits, confound baselines, calibration -- always
"""

__all__ = ["embed", "features", "benchmark"]
__version__ = "0.1.0"
