# Introduction

This is my fourth version of a project I have (very creatively) named Tracking. The premise is simple:

> Given a set of observations of a celestial body, try to determine its orbital path.

My end goal is to be able to compute a fitted orbit for any body stored on the Minor Planet Center website.

# Execution

Running `python data_get.py "2026 ED138"` will generate a file containing observation data for 2026 ED138. The data for this body is relatively small (74 observations) and fairly simple to process (only two telescopes, and all contain RA/DEC data). Regardless, the program should run for any given body, as long as it has an unambiguous name according to MPC.

Note that names like `"Ceres"` will not work, use numbered designations if possible (in this case, `"1"`).