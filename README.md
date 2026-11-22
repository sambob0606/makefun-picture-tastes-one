# Pancake Stack — The Picture That Tastes of One

A single Python program that paints a warm breakfast scene — a tall stack of
golden pancakes on a white plate, glossy maple syrup dripping down the sides,
a melting pat of butter, blueberries, halved strawberries, a dusting of
powdered sugar, and thin steam curling up into a golden morning glow — and
writes it out as a 1024×1024 PNG.

Everything is drawn from scratch in pure Python standard library: the picture
lives in a 2048×2048 RGB buffer, is downsampled 2×2 for smooth edges, and the
PNG file itself is encoded by hand with `zlib` and `struct`. No image
libraries, no assets, no network, no fonts — just code and a fixed random
seed, so the output is fully deterministic.

## Run it

```sh
python3 main.py
```

The picture is written to `entry.png` inside the directory given by
`MAKEFUN_OUTPUT_DIR` (or `/output` if that variable is not set).

[![make.fun · the-picture-that-tastes-of-one-20261122-2047](https://make.fun/badge/the-picture-that-tastes-of-one-20261122-2047.svg)](https://make.fun/bounty/the-picture-that-tastes-of-one-20261122-2047?utm_source=github&utm_medium=readme&utm_campaign=the-picture-that-tastes-of-one-20261122-2047)
[![rank](https://make.fun/badge/the-picture-that-tastes-of-one-20261122-2047/sambob0606/makefun-picture-tastes-one/rank.svg)](https://make.fun/bounty/the-picture-that-tastes-of-one-20261122-2047/leaderboard?utm_source=github&utm_medium=readme&utm_campaign=the-picture-that-tastes-of-one-20261122-2047)
[![reward](https://make.fun/badge/the-picture-that-tastes-of-one-20261122-2047/sambob0606/makefun-picture-tastes-one/reward.svg)](https://make.fun/bounty/the-picture-that-tastes-of-one-20261122-2047?utm_source=github&utm_medium=readme&utm_campaign=the-picture-that-tastes-of-one-20261122-2047)

Bounty page: https://make.fun/c/the-picture-that-tastes-of-one-20261122-2047
