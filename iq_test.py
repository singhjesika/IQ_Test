from dotenv import load_dotenv
load_dotenv()
import json
import os
import sys
import time
import threading

from groq import Groq

# ── Colours ──────────────────────────────────────────────────────────────────
class C:
    RESET   = "\033[0m"
    BOLD    = "\033[1m"
    DIM     = "\033[2m"
    RED     = "\033[91m"
    GREEN   = "\033[92m"
    YELLOW  = "\033[93m"
    CYAN    = "\033[96m"
    BLUE    = "\033[94m"
    MAGENTA = "\033[95m"

def clr(text, *codes): return "".join(codes) + str(text) + C.RESET
def clear(): os.system("cls" if os.name == "nt" else "clear")

# ── Timer ─────────────────────────────────────────────────────────────────────
class CountdownTimer:
    def __init__(self, seconds):
        self.total   = seconds
        self.left    = seconds
        self._stop   = threading.Event()
        self._thread = threading.Thread(target=self._run, daemon=True)

    def _run(self):
        while self.left > 0 and not self._stop.is_set():
            ratio  = self.left / self.total
            filled = int(ratio * 20)
            bar    = "█" * filled + "░" * (20 - filled)
            colour = C.GREEN if ratio > .5 else (C.YELLOW if ratio > .25 else C.RED)
            sys.stdout.write(f"\r  {clr(bar, colour)}  {clr(f'{self.left:2d}s', colour, C.BOLD)}  ")
            sys.stdout.flush()
            time.sleep(1)
            self.left -= 1
        if not self._stop.is_set():
            sys.stdout.write(f"\r  {clr('Time is up!', C.RED, C.BOLD)}{' ' * 30}\n")
            sys.stdout.flush()

    def start(self):  self._thread.start()
    def stop(self):
        self._stop.set()
        self._thread.join()
        sys.stdout.write("\r" + " " * 55 + "\r")
        sys.stdout.flush()
    def expired(self): return self.left <= 0

# ── Constants ─────────────────────────────────────────────────────────────────
CATEGORIES = {
    "1": "Math & Numbers",
    "2": "Pattern Recognition",
    "3": "Verbal Reasoning",
    "4": "Logical Deduction",
}

DIFFICULTY_TIME  = {"Easy": 20, "Medium": 30, "Hard": 45}
DIFFICULTY_BONUS = {"Easy": 0,  "Medium": 5,  "Hard": 12}

# ── Groq question generator ───────────────────────────────────────────────────
def generate_questions(client, categories, difficulty, count):
    cat_str = ", ".join(categories)
    prompt  = f"""Generate exactly {count} IQ test questions as a JSON array.
Categories (distribute evenly): {cat_str}
Difficulty: {difficulty}

Rules:
- Each question must have 4 multiple-choice options labeled A, B, C, D
- Return ONLY valid JSON — no markdown, no explanation, no extra text at all
- Use this exact format for every object:
  {{"question":"...","options":{{"A":"...","B":"...","C":"...","D":"..."}},"answer":"A","category":"...","explanation":"1 sentence"}}
- Make questions genuinely challenging and varied
- No asterisks or markdown inside question text"""

    print(clr("\n  Groq is generating your questions", C.CYAN, C.BOLD), end="")
    for _ in range(3):
        time.sleep(0.3)
        print(clr(".", C.CYAN), end="", flush=True)

    response = client.chat.completions.create(
    model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.8,
        max_tokens=2500,
    )

    raw   = response.choices[0].message.content.strip()
    raw   = raw.replace("```json", "").replace("```", "").strip()
    start = raw.find("[")
    end   = raw.rfind("]") + 1
    if start == -1 or end == 0:
        raise ValueError("No JSON array found in response")
    questions = json.loads(raw[start:end])
    print(clr(f"  {len(questions)} questions ready!\n", C.GREEN, C.BOLD))
    return questions

# ── IQ Estimator ──────────────────────────────────────────────────────────────
def estimate_iq(results, difficulty):
    if not results:
        return 85
    correct     = sum(1 for r in results if r["correct"])
    total       = len(results)
    accuracy    = correct / total
    avg_time    = sum(r["time_taken"] for r in results) / total
    time_limit  = DIFFICULTY_TIME[difficulty]
    speed_bonus = max(0, (time_limit - avg_time) / time_limit) * 15
    diff_bonus  = DIFFICULTY_BONUS[difficulty]
    iq          = 70 + (accuracy * 65) + speed_bonus + diff_bonus
    return max(70, min(145, round(iq)))

def iq_label(iq):
    if iq >= 140: return clr("Genius",        C.MAGENTA, C.BOLD)
    if iq >= 130: return clr("Gifted",         C.CYAN,    C.BOLD)
    if iq >= 120: return clr("Superior",       C.BLUE,    C.BOLD)
    if iq >= 110: return clr("Above Average",  C.GREEN,   C.BOLD)
    if iq >= 90:  return clr("Average",        C.YELLOW,  C.BOLD)
    if iq >= 80:  return clr("Below Average",  C.RED)
    return             clr("Developing",       C.RED)

# ── UI helpers ────────────────────────────────────────────────────────────────
def banner():
    clear()
    print(clr("""
  ╔══════════════════════════════════════════╗
  ║   AI IQ TEST  ·  powered by Groq  ║
  ╚══════════════════════════════════════════╝""", C.CYAN, C.BOLD))

def divider(): print(clr("  " + "─" * 44, C.DIM))

def print_dashboard(results, difficulty):
    correct  = sum(1 for r in results if r["correct"])
    total    = len(results)
    iq       = estimate_iq(results, difficulty)
    avg_time = sum(r["time_taken"] for r in results) / total
    accuracy = correct / total * 100

    banner()
    print(clr("\n  RESULTS DASHBOARD\n", C.BOLD))
    divider()
    print(f"\n  {'Estimated IQ':<22} {clr(iq, C.CYAN, C.BOLD)}  {iq_label(iq)}")
    print(f"  {'Score':<22} {clr(f'{correct} / {total}', C.BOLD)}")
    print(f"  {'Accuracy':<22} {clr(f'{accuracy:.0f}%', C.BOLD)}")
    print(f"  {'Avg Response Time':<22} {clr(f'{avg_time:.1f}s', C.BOLD)}")
    print(f"  {'Difficulty':<22} {clr(difficulty, C.BOLD)}\n")
    divider()

    # category breakdown
    print(clr("\n  Category Breakdown\n", C.BOLD))
    cat_stats = {}
    for r in results:
        c = r["category"]
        cat_stats.setdefault(c, {"correct": 0, "total": 0})
        cat_stats[c]["total"] += 1
        if r["correct"]:
            cat_stats[c]["correct"] += 1

    for cat, s in cat_stats.items():
        pct    = s["correct"] / s["total"]
        filled = round(pct * 16)
        bar    = "█" * filled + "░" * (16 - filled)
        colour = C.GREEN if pct >= .7 else (C.YELLOW if pct >= .4 else C.RED)
        print(f"  {cat[:22]:<22} {clr(bar, colour)}  {s['correct']}/{s['total']}")

    divider()

    # wrong answer review
    wrong = [r for r in results if not r["correct"]]
    if wrong:
        print(clr(f"\n  {len(wrong)} incorrect — review below\n", C.RED, C.BOLD))
        for i, r in enumerate(wrong, 1):
            print(clr(f"  {i}. {r['question']}", C.BOLD))
            print(f"     Your answer  : {clr(r['user_answer'] or 'Timed out', C.RED)}")
            print(f"     Correct      : {clr(r['correct_answer'], C.GREEN)}")
            print(clr(f"     {r['explanation']}\n", C.DIM))
    else:
        print(clr("\n  Perfect score — all answers correct!\n", C.GREEN, C.BOLD))

# ══════════════════════════════════════════════════════════════════════════════
class IQTestApp:

    def __init__(self):
        api_key = os.environ.get("GROQ_API_KEY", "")
        if not api_key:
            print(clr("\n  GROQ_API_KEY not set.", C.RED, C.BOLD))
            print(clr("  Get a free key at: https://console.groq.com", C.DIM))
            print(clr("  Then run: export GROQ_API_KEY='your-key'\n", C.DIM))
            sys.exit(1)

        self.client       = Groq(api_key=api_key)
        self.score        = 0
        self.last_results = []
        self.difficulty   = "Medium"
        self.categories   = list(CATEGORIES.values())
        self.q_count      = 5

    # ── menu ──────────────────────────────────────────────────────────────────
    def display_menu(self):
        banner()
        cats_short = ", ".join(c.split()[0] for c in self.categories)
        print(clr(f"\n  Difficulty: {self.difficulty}  |  Questions: {self.q_count}  |  {cats_short}\n", C.DIM))
        print("  1.  Take Test")
        print("  2.  Show Last Score")
        print("  3.  Settings")
        print("  4.  Exit\n")
        divider()
        choice = input(clr("\n  Enter choice: ", C.CYAN)).strip()
        {
            "1": self.take_test,
            "2": self.show_score,
            "3": self.settings,
            "4": self.exit_app,
        }.get(choice, self.invalid)()

    def invalid(self):
        print(clr("\n  Invalid choice, try again.", C.YELLOW))
        time.sleep(1)

    # ── settings ──────────────────────────────────────────────────────────────
    def settings(self):
        banner()
        print(clr("\n  SETTINGS\n", C.BOLD))

        diffs = ["Easy", "Medium", "Hard"]
        print("  Difficulty:")
        for i, d in enumerate(diffs, 1):
            mark = clr("*", C.GREEN) if d == self.difficulty else " "
            print(f"    {mark} {i}. {d}")
        ch = input(clr("\n  Choose difficulty (1-3, Enter to skip): ", C.CYAN)).strip()
        if ch in ("1", "2", "3"):
            self.difficulty = diffs[int(ch) - 1]

        print(clr("\n  Categories:\n", C.BOLD))
        for k, v in CATEGORIES.items():
            mark = clr("*", C.GREEN) if v in self.categories else clr("o", C.DIM)
            print(f"    {mark} {k}. {v}")
        sel = input(clr("\n  Toggle categories by number (e.g. 1 3), Enter to skip: ", C.CYAN)).strip()
        if sel:
            for ch in sel.split():
                if ch in CATEGORIES:
                    cat = CATEGORIES[ch]
                    if cat in self.categories and len(self.categories) > 1:
                        self.categories.remove(cat)
                    elif cat not in self.categories:
                        self.categories.append(cat)

        counts = [5, 10, 15]
        print(clr("\n  Number of questions:\n", C.BOLD))
        for i, n in enumerate(counts, 1):
            mark = clr("*", C.GREEN) if n == self.q_count else " "
            print(f"    {mark} {i}. {n} questions")
        ch = input(clr("\n  Choose (1-3, Enter to skip): ", C.CYAN)).strip()
        if ch in ("1", "2", "3"):
            self.q_count = counts[int(ch) - 1]

        print(clr("\n  Settings saved!\n", C.GREEN, C.BOLD))
        time.sleep(1)

    # ── take test ─────────────────────────────────────────────────────────────
    def take_test(self):
        try:
            questions = generate_questions(
                self.client, self.categories, self.difficulty, self.q_count
            )
        except Exception as e:
            print(clr(f"\n  Could not generate questions: {e}\n", C.RED))
            input(clr("  Press Enter to return to menu...", C.DIM))
            return

        results    = []
        self.score = 0
        time_limit = DIFFICULTY_TIME[self.difficulty]
        cur_diff   = self.difficulty

        for idx, q in enumerate(questions, 1):
            clear()
            print(clr(f"\n  Q{idx}/{len(questions)}  ·  {q.get('category','')}  ·  {cur_diff}\n", C.DIM))
            divider()
            print(clr(f"\n  {q['question']}\n", C.BOLD))
            for letter, option in q["options"].items():
                print(f"    {clr(letter + '.', C.CYAN, C.BOLD)}  {option}")
            print()

            timer   = CountdownTimer(time_limit)
            timer.start()
            t_start = time.time()
            try:
                ans = input(clr("  Your answer (A/B/C/D): ", C.CYAN)).strip().upper()
            except EOFError:
                ans = ""
            t_taken = round(time.time() - t_start, 1)
            timer.stop()

            timed_out    = timer.expired() or not ans
            correct_key  = q["answer"].upper()
            correct_text = q["options"].get(correct_key, correct_key)
            user_text    = q["options"].get(ans) if ans else None
            is_correct   = (not timed_out) and (ans == correct_key)

            if timed_out:
                print(clr(f"\n  Time's up!  Correct was: {correct_key}. {correct_text}", C.RED, C.BOLD))
            elif is_correct:
                print(clr("  Correct!", C.GREEN, C.BOLD))
                self.score += 1
            else:
                print(clr(f"  Wrong.  Correct: {correct_key}. {correct_text}", C.RED))

            print(clr(f"  {q.get('explanation', '')}", C.DIM))

            results.append({
                "question"      : q["question"],
                "category"      : q.get("category", "General"),
                "correct"       : is_correct,
                "user_answer"   : user_text,
                "correct_answer": correct_text,
                "explanation"   : q.get("explanation", ""),
                "time_taken"    : t_taken,
            })

            # adaptive difficulty
            if len(results) >= 3:
                recent_acc = sum(1 for r in results[-3:] if r["correct"]) / 3
                if recent_acc == 1.0 and cur_diff == "Easy":
                    cur_diff = "Medium"; time_limit = 30
                    print(clr("  Difficulty up -> Medium!", C.YELLOW, C.BOLD))
                elif recent_acc == 1.0 and cur_diff == "Medium":
                    cur_diff = "Hard"; time_limit = 45
                    print(clr("  Difficulty up -> Hard!", C.RED, C.BOLD))
                elif recent_acc == 0.0 and cur_diff == "Hard":
                    cur_diff = "Medium"; time_limit = 30
                    print(clr("  Difficulty down -> Medium.", C.CYAN))
                elif recent_acc == 0.0 and cur_diff == "Medium":
                    cur_diff = "Easy"; time_limit = 20
                    print(clr("  Difficulty down -> Easy.", C.CYAN))

            time.sleep(1.8)

        self.last_results = results
        print_dashboard(results, self.difficulty)
        input(clr("\n  Press Enter to return to menu...", C.DIM))

    # ── show last score ───────────────────────────────────────────────────────
    def show_score(self):
        banner()
        if not self.last_results:
            print(clr("\n  No test taken yet.\n", C.YELLOW))
        else:
            total   = len(self.last_results)
            correct = sum(1 for r in self.last_results if r["correct"])
            iq      = estimate_iq(self.last_results, self.difficulty)
            print(f"\n  Last Score  : {clr(f'{correct} / {total}', C.BOLD)}")
            print(f"  IQ Estimate : {clr(iq, C.CYAN, C.BOLD)}  {iq_label(iq)}\n")
        input(clr("  Press Enter to return...", C.DIM))

    # ── exit ──────────────────────────────────────────────────────────────────
    def exit_app(self):
        print(clr("\n  Goodbye! Keep training your brain.\n", C.CYAN))
        raise SystemExit


# ── entry point ───────────────────────────────────────────────────────────────
if __name__ == "__main__":
    app = IQTestApp()
    while True:
        app.display_menu()





