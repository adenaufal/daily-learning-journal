#!/usr/bin/env python3
"""Widya the Bookwyrm — a Tamagotchi that lives in this repo.

Each run is one "care event" (breakfast / study time / bedtime story).
The pet researches something new from free, keyless public APIs, gains
knowledge XP, evolves through stages, writes its own journal entry, and
refreshes its status card in the README.

Uses only the Python standard library. Every network call has a fallback,
so the pet never starves even when the internet is down.
"""

import json
import os
import random
import re
import ssl
import sys
import urllib.request
from datetime import datetime, timezone, timedelta

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STATE_FILE = os.path.join(REPO_ROOT, "pet", "state.json")
STREAK_FILE = os.path.join(REPO_ROOT, "data", "streak.json")
README_FILE = os.path.join(REPO_ROOT, "README.md")
QUOTES_FILE = os.path.join(REPO_ROOT, "quotes.txt")
JOURNAL_DIR = os.path.join(REPO_ROOT, "journal")

WIB = timezone(timedelta(hours=7))
USER_AGENT = "WidyaTheBookwyrm/1.0 (tamagotchi journal bot; github.com/adenaufal/daily-learning-journal)"

# ---------------------------------------------------------------- stages ----

STAGES = [
    # (min knowledge XP, key, label, emoji)
    (0,    "egg",       "Mysterious Egg",   "🥚"),
    (30,   "hatchling", "Hatchling",        "🐣"),
    (150,  "wyrmling",  "Wyrmling",         "🐛"),
    (400,  "scholar",   "Scholar Wyrm",     "📚"),
    (900,  "sage",      "Sage Wyrm",        "🧙"),
    (1800, "oracle",    "Oracle Wyrm",      "🐉"),
]

ART = {
    "egg": r"""
      ,--.
     / ?? \
    | ?  ? |
     \ ?? /
      `--'
   ..........
""",
    "hatchling": r"""
      ,--.
     / o  \_
    | ..    \
     \______/>
      w   w
""",
    "wyrmling": r"""
     __  __
    (o \/ o)
     \ ^^ /~~~,
      \__/____/
      /|  |\
""",
    "scholar": r"""
      _____
     / o o \  ___
    |   ^   |[Bk]
     \ \_/ / |__|
    ~~|===|~~
      /   \
""",
    "sage": r"""
       /\
      /--\____
     ( o_o    \~~*
      \ ~~ ____/
     ~~|===|~~
      _/   \_
""",
    "oracle": r"""
        /\___/\
       ( o . o )___
       /|  ~  |   \\~~~*
      ( |_____|___/
     ~~~|=====|~~~
       _/     \_
""",
}

MOODS = [
    # (min average stat, key, emoji, label)
    (80, "thriving", "🤩", "Thriving"),
    (60, "happy",    "😊", "Happy"),
    (40, "okay",     "😐", "Okay"),
    (20, "grumpy",   "😾", "Grumpy"),
    (0,  "hungry",   "🥺", "Hungry for knowledge"),
]

# ------------------------------------------------------------- fallbacks ----

FALLBACK_FACTS = [
    ("Offline archives", "Honey never spoils — archaeologists have eaten 3,000-year-old honey found in Egyptian tombs."),
    ("Offline archives", "Octopuses have three hearts, and two of them stop beating when the octopus swims."),
    ("Offline archives", "The word 'set' has more distinct definitions than almost any other word in English."),
    ("Offline archives", "A group of flamingos is called a 'flamboyance'."),
    ("Offline archives", "Bananas are berries, but strawberries are not."),
    ("Offline archives", "The Eiffel Tower grows about 15 cm taller in summer due to thermal expansion."),
    ("Offline archives", "Sharks existed before trees — by roughly 50 million years."),
    ("Offline archives", "There are more possible chess games than atoms in the observable universe."),
    ("Offline archives", "Wombats produce cube-shaped droppings."),
    ("Offline archives", "A day on Venus is longer than a year on Venus."),
]

# --------------------------------------------------------------- helpers ----


def http_get_json(url, timeout=12):
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT, "Accept": "application/json"})
    ctx = ssl.create_default_context()
    with urllib.request.urlopen(req, timeout=timeout, context=ctx) as resp:
        return json.loads(resp.read().decode("utf-8"))


def clean(text):
    return re.sub(r"\s+", " ", (text or "")).strip()


# ------------------------------------------------------- research sources ----


def fetch_wikipedia_random():
    data = http_get_json("https://en.wikipedia.org/api/rest_v1/page/random/summary")
    title = clean(data.get("title"))
    extract = clean(data.get("extract"))
    if not extract:
        raise ValueError("empty extract")
    if len(extract) > 500:
        extract = extract[:497].rsplit(" ", 1)[0] + "…"
    url = data.get("content_urls", {}).get("desktop", {}).get("page", "")
    body = f"**{title}** — {extract}"
    if url:
        body += f" ([source]({url}))"
    return ("📖 Wikipedia expedition", body)


def fetch_on_this_day(now):
    data = http_get_json(
        f"https://en.wikipedia.org/api/rest_v1/feed/onthisday/events/{now.month:02d}/{now.day:02d}"
    )
    events = data.get("events") or []
    if not events:
        raise ValueError("no events")
    ev = random.choice(events)
    year = ev.get("year", "?")
    text = clean(ev.get("text"))
    if not text:
        raise ValueError("empty event")
    return ("🗓️ On this day in history", f"In **{year}**: {text}")


def fetch_useless_fact():
    data = http_get_json("https://uselessfacts.jsph.pl/api/v2/facts/random?language=en")
    text = clean(data.get("text"))
    if not text:
        raise ValueError("empty fact")
    return ("🎲 Random fact snack", text)


def fetch_trivia():
    import html
    data = http_get_json("https://opentdb.com/api.php?amount=1&type=multiple")
    results = data.get("results") or []
    if not results:
        raise ValueError("no trivia")
    q = results[0]
    question = clean(html.unescape(q.get("question", "")))
    answer = clean(html.unescape(q.get("correct_answer", "")))
    category = clean(html.unescape(q.get("category", "Trivia")))
    if not question or not answer:
        raise ValueError("empty trivia")
    return (
        "🧩 Trivia challenge",
        f"*{category}:* {question}<br>"
        f"<details><summary>Reveal answer</summary><b>{answer}</b></details>",
    )


def fetch_zen_quote():
    data = http_get_json("https://zenquotes.io/api/random")
    if not isinstance(data, list) or not data:
        raise ValueError("no quote")
    text = clean(data[0].get("q"))
    author = clean(data[0].get("a")) or "Unknown"
    if not text:
        raise ValueError("empty quote")
    return ("💭 Wisdom nibble", f"“{text}” — {author}")


def fallback_fact():
    facts = list(FALLBACK_FACTS)
    try:
        with open(QUOTES_FILE, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    facts.append(("💭 Quote jar (offline)", line))
    except OSError:
        pass
    label, text = random.choice(facts)
    return (label, text)


def gather_research(now, count=2):
    """Fetch `count` research items, falling back to offline content."""
    sources = [
        fetch_wikipedia_random,
        lambda: fetch_on_this_day(now),
        fetch_useless_fact,
        fetch_trivia,
        fetch_zen_quote,
    ]
    random.shuffle(sources)
    items = []
    for source in sources:
        if len(items) >= count:
            break
        try:
            items.append(source())
        except Exception as exc:  # noqa: BLE001 — any source failure just means "try the next one"
            print(f"[research] source failed: {exc}", file=sys.stderr)
    while len(items) < count:
        items.append(fallback_fact())
    return items


# ----------------------------------------------------------------- state ----


def default_state():
    return {
        "name": "Widya",
        "species": "Bookwyrm",
        "born": "2026-08-07",
        "knowledge": 0,
        "hunger": 70,
        "happiness": 70,
        "energy": 90,
        "streak_days": 0,
        "last_care_date": None,
        "total_care_events": 0,
        "facts_learned": 0,
        "inherited_entries": 637,
    }


def load_state():
    try:
        with open(STATE_FILE, encoding="utf-8") as f:
            state = json.load(f)
        base = default_state()
        base.update(state)
        return base
    except (OSError, ValueError):
        return default_state()


def save_state(state):
    os.makedirs(os.path.dirname(STATE_FILE), exist_ok=True)
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(state, f, indent=2)
        f.write("\n")


def stage_for(knowledge):
    current = STAGES[0]
    for stage in STAGES:
        if knowledge >= stage[0]:
            current = stage
    return current


def next_stage_after(knowledge):
    for stage in STAGES:
        if stage[0] > knowledge:
            return stage
    return None


def mood_for(state):
    avg = (state["hunger"] + state["happiness"] + state["energy"]) / 3
    for threshold, key, emoji, label in MOODS:
        if avg >= threshold:
            return key, emoji, label
    return MOODS[-1][1:]


def stat_bar(value, width=10):
    filled = max(0, min(width, round(value / 100 * width)))
    return "█" * filled + "░" * (width - filled)


def care_event_for(now_wib):
    hour = now_wib.hour
    if hour < 11:
        return ("breakfast", "🍳 Breakfast Feeding", "Widya wakes up peckish and demands a fresh fact for breakfast.")
    if hour < 18:
        return ("study", "📚 Afternoon Study Session", "Widya curls up in the reading nook for some serious research.")
    return ("bedtime", "🌙 Bedtime Story", "Widya gets sleepy and asks for one more story before bed.")


# --------------------------------------------------------------- updates ----


def apply_care(state, now_wib, event_key, research_count):
    today = now_wib.strftime("%Y-%m-%d")

    # Streak: consecutive-day tracking based on first care event of the day.
    if state["last_care_date"] != today:
        if state["last_care_date"]:
            last = datetime.strptime(state["last_care_date"], "%Y-%m-%d").date()
            gap = (now_wib.date() - last).days
            if gap == 1:
                state["streak_days"] += 1
            elif gap > 1:
                # Missed days make the pet hungry and reset the streak.
                state["hunger"] = max(5, state["hunger"] - 15 * (gap - 1))
                state["happiness"] = max(5, state["happiness"] - 10 * (gap - 1))
                state["streak_days"] = 1
        else:
            state["streak_days"] = 1
        state["last_care_date"] = today

    # Natural decay between meals, then the care effect.
    state["hunger"] = max(0, state["hunger"] - random.randint(8, 14))
    state["energy"] = max(0, state["energy"] - random.randint(4, 9))

    gained = 0
    for _ in range(research_count):
        gained += random.randint(6, 12)
    bonus = 3 if state["streak_days"] >= 7 else 0
    gained += bonus

    state["knowledge"] += gained
    state["facts_learned"] += research_count
    state["hunger"] = min(100, state["hunger"] + 35)
    state["happiness"] = min(100, state["happiness"] + random.randint(8, 15))
    if event_key == "bedtime":
        state["energy"] = min(100, state["energy"] + 40)
    else:
        state["energy"] = min(100, state["energy"] + 10)
    state["total_care_events"] += 1
    return gained, bonus


# --------------------------------------------------------------- journal ----


def journal_entry(state, now_wib, event, research, gained, bonus, evolved, old_label, new_label):
    _, event_title, event_flavor = event
    _, _, stage_label, stage_emoji = stage_for(state["knowledge"])
    mood_key, mood_emoji, mood_label = mood_for(state)

    lines = []
    lines.append(f"### {event_title} — {now_wib.strftime('%H:%M')} WIB")
    lines.append("")
    lines.append(f"*{event_flavor}*")
    lines.append("")
    for label, body in research:
        lines.append(f"**{label}:**")
        lines.append(f"> {body}")
        lines.append("")
    reaction = random.choice([
        "Widya munched on these facts with great enthusiasm! 🍽️",
        "Widya's eyes sparkled — new knowledge acquired! ✨",
        "Widya scribbled this into a tiny notebook with a tiny pencil. ✏️",
        "Widya did a happy little wiggle after digesting that. 🪱",
        "Widya nodded sagely, pretending to have known this all along. 🤓",
    ])
    bonus_note = f" (+{bonus} streak bonus 🔥)" if bonus else ""
    lines.append(f"{reaction} **+{gained} knowledge XP**{bonus_note}")
    lines.append("")
    if evolved:
        lines.append(f"> 🎉 **EVOLUTION!** Widya evolved from *{old_label}* into *{new_label}*! {stage_emoji}")
        lines.append("")
    lines.append(
        f"`{stage_emoji} {stage_label} · Lv.{level_for(state['knowledge'])} · {mood_emoji} {mood_label}` "
        f"`Hunger {stat_bar(state['hunger'])}` "
        f"`Happy {stat_bar(state['happiness'])}` "
        f"`Energy {stat_bar(state['energy'])}`"
    )
    lines.append("")
    lines.append("---")
    lines.append("")
    return "\n".join(lines)


def level_for(knowledge):
    return knowledge // 50 + 1


def write_journal(state, now_wib, entry_text):
    os.makedirs(JOURNAL_DIR, exist_ok=True)
    path = os.path.join(JOURNAL_DIR, now_wib.strftime("%Y-%m") + ".md")
    month_header = f"# 🐉 Widya's Journal — {now_wib.strftime('%B %Y')}"
    day_header = f"## 📅 {now_wib.strftime('%A, %B %-d, %Y')}"

    if os.path.exists(path):
        with open(path, encoding="utf-8") as f:
            content = f.read()
    else:
        content = (
            f"{month_header}\n\n"
            f"The daily research diary of **{state['name']} the {state['species']}**, "
            "resident knowledge-pet of this repository. Every day Widya forages the "
            "internet's free APIs for facts, eats them, and writes about it here.\n\n"
            "---\n\n"
        )

    if day_header not in content:
        content += f"{day_header}\n\n"
    content += entry_text

    with open(path, "w", encoding="utf-8") as f:
        f.write(content)


# ---------------------------------------------------------------- readme ----

STATUS_START = "<!-- PET-STATUS:START -->"
STATUS_END = "<!-- PET-STATUS:END -->"


def render_status(state, now_wib):
    _, stage_key, stage_label, stage_emoji = stage_for(state["knowledge"])
    mood_key, mood_emoji, mood_label = mood_for(state)
    nxt = next_stage_after(state["knowledge"])
    if nxt:
        to_next = f"{nxt[0] - state['knowledge']} XP until **{nxt[2]}** {nxt[3]}"
    else:
        to_next = "Final form reached — Widya knows all. 🌌"

    lines = [
        STATUS_START,
        "```text",
        ART[stage_key].strip("\n"),
        "```",
        "",
        f"### {stage_emoji} {state['name']} the {state['species']} — {stage_label}, Lv.{level_for(state['knowledge'])}",
        "",
        f"**Mood:** {mood_emoji} {mood_label} &nbsp;·&nbsp; **Streak:** 🔥 {state['streak_days']} day(s) &nbsp;·&nbsp; **Facts eaten:** 🍽️ {state['facts_learned']}",
        "",
        "| Stat | Level |",
        "|------|-------|",
        f"| 🍖 Hunger | `{stat_bar(state['hunger'])}` {state['hunger']}/100 |",
        f"| 💖 Happiness | `{stat_bar(state['happiness'])}` {state['happiness']}/100 |",
        f"| ⚡ Energy | `{stat_bar(state['energy'])}` {state['energy']}/100 |",
        f"| 🧠 Knowledge | {state['knowledge']} XP — {to_next} |",
        "",
        f"*Last cared for: {now_wib.strftime('%A, %B %-d, %Y at %H:%M')} WIB*",
        STATUS_END,
    ]
    return "\n".join(lines)


def update_readme(state, now_wib):
    with open(README_FILE, encoding="utf-8") as f:
        content = f.read()
    block = render_status(state, now_wib)
    pattern = re.compile(re.escape(STATUS_START) + ".*?" + re.escape(STATUS_END), re.DOTALL)
    if pattern.search(content):
        content = pattern.sub(lambda _: block, content)
    else:
        content += "\n" + block + "\n"
    with open(README_FILE, "w", encoding="utf-8") as f:
        f.write(content)


def update_streak_file(state, now_wib):
    try:
        with open(STREAK_FILE, encoding="utf-8") as f:
            data = json.load(f)
    except (OSError, ValueError):
        data = {"total_entries": 0, "started_at": "2026-01-06"}
    data["total_entries"] = data.get("total_entries", 0) + 1
    data["last_updated"] = now_wib.strftime("%Y-%m-%d")
    data["tamagotchi_era"] = True
    os.makedirs(os.path.dirname(STREAK_FILE), exist_ok=True)
    with open(STREAK_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
        f.write("\n")


# ------------------------------------------------------------------ main ----


def main():
    now_wib = datetime.now(timezone.utc).astimezone(WIB)
    state = load_state()

    old_stage = stage_for(state["knowledge"])
    event = care_event_for(now_wib)
    research = gather_research(now_wib, count=2)
    gained, bonus = apply_care(state, now_wib, event[0], len(research))
    new_stage = stage_for(state["knowledge"])
    evolved = new_stage[1] != old_stage[1]

    entry = journal_entry(state, now_wib, event, research, gained, bonus, evolved, old_stage[2], new_stage[2])
    write_journal(state, now_wib, entry)
    update_readme(state, now_wib)
    update_streak_file(state, now_wib)
    save_state(state)

    print(f"Care event complete: {event[1]} | +{gained} XP | stage={new_stage[1]} | evolved={evolved}")


if __name__ == "__main__":
    main()
