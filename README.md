# Introduction

This is my fourth version of a project I have (very creatively) named Tracking. The premise is simple:

> Given a set of observations of a celestial body, try to determine its orbital path.

My end goal is to be able to compute a fitted orbit for any body stored on the Minor Planet Center website.

# Execution

If you have not run the program before, run `setup.py` to download needed files. Currently, this downloads ephemeris data used for tracking the Earth and Sun.

To get observation data for an object, run `ingest.py ID` to download observation data for `ID`. See note below. Once you have your target observations downloaded, run `unify.py` to process them into format future code will work with. Note that `unify.py` processes *all* downloaded observation data in one go, not per ID like `ingest.py`.

Note: `ID` must be a numeric ID. Names, like Ceres, are unsupported. If you want to download observations for a body, Google "[Body] MPC ID". Also note that not every body gets a *number*. For example, 2026 ED₁₃₈'s ID is `2026 ED138`. I aim to improve this in the future, especially as I want to download datafrom multiple sources that may use a different name for a minor body.