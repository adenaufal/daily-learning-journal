# 🐉 Widya the Bookwyrm — A Tamagotchi Learning Journal

This repository is home to **Widya**, a virtual Bookwyrm who survives on a strict
diet of *facts*. Three times a day, GitHub Actions wakes Widya up so it can forage
the internet's free APIs for new knowledge, eat it, level up, and write about the
experience in its own journal.

<!-- PET-STATUS:START -->
```text
      ,--.
     / o  \_
    | ..    \
     \______/>
      w   w
```

### 🐣 Widya the Bookwyrm — Hatchling, Lv.1

**Mood:** 🤩 Thriving &nbsp;·&nbsp; **Streak:** 🔥 1 day(s) &nbsp;·&nbsp; **Facts eaten:** 🍽️ 4

| Stat | Level |
|------|-------|
| 🍖 Hunger | `██████████` 100/100 |
| 💖 Happiness | `█████████░` 93/100 |
| ⚡ Energy | `██████████` 100/100 |
| 🧠 Knowledge | 39 XP — 111 XP until **Wyrmling** 🐛 |

*Last cared for: Friday, August 7, 2026 at 22:09 WIB*
<!-- PET-STATUS:END -->

## 🎮 How it works

Every day Widya gets three care events, fully automated:

| Time (WIB) | Event | What happens |
|------------|-------|--------------|
| 08:00 | 🍳 Breakfast Feeding | Widya eats a fresh fact for breakfast |
| 14:30 | 📚 Afternoon Study | Serious research in the reading nook |
| 21:15 | 🌙 Bedtime Story | One more story before sleep (restores energy) |

At each event Widya:

1. **Researches** 2 items from free, keyless public APIs — Wikipedia random
   articles, Wikipedia "On this day", Useless Facts, Open Trivia DB, and
   ZenQuotes (with offline fallbacks so it never starves)
2. **Gains knowledge XP** and updates its hunger / happiness / energy stats
3. **Writes a journal entry** in [`journal/`](journal/) about what it learned
4. **Updates its status card** above

## 🧬 Evolution stages

| XP | Stage |
|----|-------|
| 0 | 🥚 Mysterious Egg |
| 30 | 🐣 Hatchling |
| 150 | 🐛 Wyrmling |
| 400 | 📚 Scholar Wyrm |
| 900 | 🧙 Sage Wyrm |
| 1800 | 🐉 Oracle Wyrm (final form) |

Keeping a daily streak going earns bonus XP. Missing days makes Widya hungry
and sad, and resets the streak. Be kind to Widya.

## 📁 Structure

```
├── journal/            # Widya's daily research diary (YYYY-MM.md)
├── pet/state.json      # Widya's current stats and stage
├── scripts/
│   └── tamagotchi.py   # The pet's brain (stdlib-only Python)
├── archive/            # The original 2026 learning journal, preserved forever
├── data/streak.json    # Long-running entry counter
└── quotes.txt          # Emergency offline food supply
```

## 🗄️ The archive

Before Widya hatched, this repo was a plain daily learning journal
(637 entries, Jan–Aug 2026). Those entries live untouched in
[`archive/`](archive/) — lore says Widya absorbed them all while still in its egg.

## 🤝 Manual care

You can feed Widya manually anytime: run the **Feed Widya the Bookwyrm**
workflow from the Actions tab, or run `python3 scripts/tamagotchi.py` locally.

---

*"Learning never exhausts the mind."* — Leonardo da Vinci *(it does, however, exhaust Widya, hence the bedtime stories)*
