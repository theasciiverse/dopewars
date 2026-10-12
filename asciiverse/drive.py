"""drive.py SESSION SECONDS: play single-player dopewars in a tmux pane.

A simple trader: buys the drug that is cheapest compared with its usual
price (dopewars' own default price ranges), sells when the price has risen
well above what it paid, jets somewhere else, runs from the cops and turns
down every other offer. After SECONDS it quits and declines another game.

Recorded asciiverse/dopewars.cast: asciinema rec runs ./dopewars -t -n (single
player, curses client) inside a 100x30 tmux session while this script reads
the pane and sends the keys."""
import random, re, subprocess, sys, time

S, secs = sys.argv[1], float(sys.argv[2])
USUAL = {"Acid": 2700, "Cocaine": 22000, "Hashish": 880, "Heroin": 9250, "Ludes": 35,
         "MDA": 2950, "Opium": 895, "PCP": 1750, "Peyote": 460, "Shrooms": 965,
         "Speed": 170, "Weed": 600}
PAUSE = 0.7      # leave each screen up long enough to read in the recording

def key(*k): subprocess.run(["tmux", "send-keys", "-t", S, *k])
def screen():
    return subprocess.run(["tmux", "capture-pane", "-p", "-t", S], capture_output=True, text=True).stdout

def prices(text):
    return {m[1]: (m[0], int(m[2].replace(",", "")))
            for m in re.findall(r"([A-Z])\. (\w+)\s+\$([\d,]+)", text)}

held = {}        # drug name -> price paid
plan = None      # what the next buy/sell prompt is for
t0, quitting = time.time(), False
time.sleep(1.5); key("Space"); time.sleep(PAUSE); key("M", "a", "x", "Enter"); time.sleep(PAUSE)
while time.time() - t0 < secs + 25:
    s = screen()
    last = [l for l in s.splitlines() if l.strip()][-1] if s.strip() else ""
    if "Play again?" in last:
        key("n"); break
    if "want to quit" in last:
        key("y")
    elif "Press any key" in last:
        key("Space")
    elif "Do you run" in last or "R>un" in last:
        key("r")
    elif "Would you like" in last or "[Yes/No]" in last:
        key("n")
    elif "or L>eave?" in last:
        key("l")
    elif "How many do you sell?" in last:
        m = re.search(r"You have (\d+)", s)
        key(*str(m[1] if m else 999), "Enter"); held.pop(plan, None)
    elif "How many do you buy?" in last:
        m = re.search(r"afford ([\d,]+), and can carry ([\d,]+)", s)
        n = min(int(m[1].replace(",", "")), int(m[2].replace(",", ""))) if m else 0
        key(*str(n), "Enter")
    elif "What do you wish to sell?" in last or "What do you wish to buy?" in last:
        key(prices(s)[plan][0].lower())
    elif "Where to, dude" in last:
        here = s.splitlines()[0].split()[1] if s.strip() else ""
        opts = re.findall(r"(\d)\. (\w[\w ]*?)(?=\s{2,}|$)", s)
        pick = [o for o in opts if not here or not o[1].startswith(here)] or opts
        key(random.choice(pick)[0] if pick else "1")
    elif "Will you B>uy" in last or "J>et" in last:
        p = prices(s)
        if not quitting and time.time() - t0 >= secs:
            quitting = True; key("q")
        elif ", S>ell" in last and (sell := [d for d, paid in held.items()
                                             if d in p and p[d][1] >= paid * 1.25]):
            plan = sell[0]; key("s")
        elif "B>uy" in last and not held and p:
            plan = min(p, key=lambda d: p[d][1] / USUAL.get(d, p[d][1]))
            held[plan] = p[plan][1]; key("b")
        else:
            key("j")
    time.sleep(PAUSE)
print("held at the end:", held, file=sys.stderr)
