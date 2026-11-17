# Introduction

This is my fourth version of a project I have (very creatively) named Tracking. The premise is simple:

> Given a set of observations of a celestial body, try to determine its orbital path.

My end goal is to be able to compute a fitted orbit for any body stored on the Minor Planet Center website.

# Execution

If you have not run the program before, run `setup_data.py` to download needed files. Currently, this downloads ephemeris data used for tracking the Earth and Sun.

To process an observation, run `data_get.py ID` to download observation data for `ID`. See note below. Once you have your target observations downloaded, run `data_parse.py` to process them into a more useable format. Note that `data_parse.py` processes all downloaded observation JSONs at once.