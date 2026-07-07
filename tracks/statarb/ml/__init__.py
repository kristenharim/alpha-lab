"""Signal-quality meta-model: given a residual signal AT ENTRY, predict whether it mean-reverts.

The residual model generates signals; this scores them. Leakage-safe by construction — see
dataset.py's ENTRY_FEATURES / EXIT_ONLY partition. Prototype on backward (survivor-biased) data;
graduates to the forward paper book's clean labels.
"""
