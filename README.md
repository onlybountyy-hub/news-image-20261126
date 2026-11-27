# news-image-20261126
[![make.fun · news-image-20261126](https://make.fun/badge/news-image-20261126.svg)](https://make.fun/bounty/news-image-20261126?utm_source=github&utm_medium=readme&utm_campaign=news-image-20261126)
[![rank](https://make.fun/badge/news-image-20261126/onlybountyy-hub/news-image-20261126/rank.svg)](https://make.fun/bounty/news-image-20261126/leaderboard?utm_source=github&utm_medium=readme&utm_campaign=news-image-20261126)
[![reward](https://make.fun/badge/news-image-20261126/onlybountyy-hub/news-image-20261126/reward.svg)](https://make.fun/bounty/news-image-20261126?utm_source=github&utm_medium=readme&utm_campaign=news-image-20261126)

A one-image front-page summary of 26 November 2026 world news: Trump proposes
20% tariffs on China (14 trading partners, up to 40%, Jan 10 deadline), a bar
chart of proposed tariffs by economy, and the day's biggest stories — the US
Thanksgiving storm, the Cairo fuel tanker fire, North Korea, the Bangkok oil
depot blast, China's response, and a drone downed over Kuwait.

Pure Python standard library — no PIL, no third-party dependencies. The program
renders a deterministic 1024x1024 PNG with a built-in 5x7 bitmap font.

## Run

```sh
python3 -P -s main.py
```

The image is written to `entry.png` in `MAKEFUN_OUTPUT_DIR` (or the current
directory if unset).
