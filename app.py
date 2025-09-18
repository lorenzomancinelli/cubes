import os
import json
import random
import re
from datetime import datetime, timezone
from flask import Flask, request, jsonify, render_template_string

app = Flask(__name__)

# ---- HTML + CSS + JS (multiplayer simultaneo) ----
html_content = """
<!doctype html>
<html lang="it">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>ROLLING CUBES</title>
<style>
.topbar {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.row-buttons {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
  align-items: center;
}
#btn-new-game {
  background: var(--accent);
  color: #fff;
}

.row-settings {
  display: flex;
  flex-wrap: wrap;
  gap: 20px;
  align-items: center;
  font-size: 20px;
  font-weight: 700;
}
.verify-big {
  display:block;
  margin:16px auto;
  padding:16px 24px;
  font-size:20px;
  font-weight:700;
  border-radius:12px;
}
.player-controls label,
.player-controls button {
  margin-left: 8px;
}
.timer-display {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 120px;
  height: 60px;
  background: var(--accent);
  color: #ffffff !important;
  font-size: 28px;
  font-weight: 900;
  border-radius: 12px;
  margin-left: 10px;
}
.topbar button {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  padding: 10px 20px;
  font-size: 18px;
  font-weight: 600;
  border-radius: 14px;
  background: var(--accent);
  color: #fff;
  cursor: pointer;
  margin: 10px;
}
#player-name {
  font-size: 20px;
  padding: 14px 20px;
  border-radius: 10px;
  border: 2px solid #ccc;
  width: 190px;   /* aumenta la larghezza */
  margin-right: 10px;
}
:root { --bg:#f5f6fa; --box:#fff; --text:#2d3436; --accent:#0984e3; }
* { box-sizing:border-box; }
body { margin:0; font-family:system-ui,Segoe UI,Roboto,Arial; background:var(--bg); color:var(--text); padding:18px; }
main { max-width:1200px; margin:0 auto; }
.topbar { display:flex; justify-content:space-between; gap:12px; align-items:center; margin-bottom:12px; flex-wrap:wrap; }
.player-controls input { padding:6px 8px; }
button { background:var(--accent); color:#fff; border:none; padding:8px 10px; border-radius:8px; cursor:pointer; font-weight:1000; margin-right:10px; }
button:active { transform:translateY(1px); }
.timer-display { min-width:70px; font-weight:700; color:var(--accent); margin-left:6px; text-align:center; }
.status { margin-bottom:12px; }
.scoreboard { background:var(--box); padding:8px; border-radius:8px; box-shadow:0 8px 18px rgba(0,0,0,0.06); }
.scoreboard-grid { display:grid; grid-template-columns: repeat(6, 1fr); gap:6px; }
.scoreboard .player { padding:6px 8px; border-radius:6px; background:#fafafa; display:flex; justify-content:space-between; align-items:center; }
.dice-pool { display:flex; flex-wrap:wrap; gap:10px; padding:12px; background:var(--box); border-radius:12px; box-shadow:0 6px 18px rgba(0,0,0,0.06); }
.die { width:60px; height:60px; border-radius:10px; display:flex; align-items:center; justify-content:center; font-size:26px; font-weight:700; cursor:pointer; box-shadow:0 6px 12px rgba(0,0,0,0.08); border:3px solid transparent; }
.die.pari { background:#74b9ff; color:#2d3436; border-color:#0984e3; }
.die.dispari { background:#fab1a0; color:#2d3436; border-color:#d63031; }
.die.op { background:#55efc4; color:#2d3436; border-color:#00b894; }
.die.uguale { background:#ffeaa7; color:#2d3436; border-color:#fdcb6e; }
.slots { display:flex; flex-wrap:wrap; gap:8px; padding:12px; background:var(--box); border-radius:12px; box-shadow:0 6px 18px rgba(0,0,0,0.06); }
.slot { width:60px; height:60px; border-radius:10px; background:#dfe6e9; display:flex; align-items:center; justify-content:center; border:3px dashed #636e72; }
.slot.filled { border-style:solid; border-color:var(--accent); background:#e6f3ff; }
.feedback { margin-top:14px; min-height:26px; font-size:18px; font-weight:600; display:flex; align-items:center; justify-content:center; }
.rules{margin-top:18px;padding:12px;background:var(--box);border-radius:10px}
</style>
</head>
<body>
<main>
  <h1>ROLLING CUBES (Multiplayer simultaneo)</h1>
<section class="topbar">
  <!-- Prima riga -->
  <div class="row-buttons">
    <input id="player-name" placeholder="Nome giocatore" />
    <button id="btn-add-player">Aggiungi / Entra</button>
    <button id="btn-reset">Azzera partita</button>
    <button id="btn-roll">Lancia dadi</button>
    <button id="btn-new-game">Crea nuova partita</button>
  </div>

  <!-- Seconda riga -->
  <div class="row-settings">
    <label>Punti per la Vittoria:
      <select id="victory-select">
        <option value="30">30</option>
        <option value="40">40</option>
        <option value="50" selected>50</option>
        <option value="60">60</option>
      </select>
    </label>

    <label>Timer:
      <select id="timer-select">
        <option value="0">Off</option>
        <option value="30">30s</option>
        <option value="60" selected>60s</option>
        <option value="120">120s</option>
      </select>
    </label>

    <div id="timer-display" class="timer-display"></div>
  </div>
</section>


  <section class="status">
    <div>Partita: <b id="game-id"></b></div>
    <div class="scoreboard">
      <h3>Classifica</h3>
      <div id="players-list" class="scoreboard-grid"></div>
    </div>
  </section>

  <section class="dice-area">
    <h2>Dadi (clicca per spostare nei tuoi slot / rimuovere)</h2>
    <div id="dice-pool" class="dice-pool" aria-live="polite"></div>
  </section>

  <section class="slots-area">
    <h2>I tuoi Slot (13)</h2>
    <div id="slots" class="slots"></div>
    <button id="btn-verify" class="verify-big">Verifica equazione</button>
  </section>

  <section class="feedback-area">
    <div id="feedback" class="feedback"></div>
  </section>

  <section class="rules">
    <h3>Regole implementate</h3>
    <ul>
      <li>Un solo tentativo di verifica per giocatore per round.</li>
      <li>Reroll automatico allo scadere del timer globale.</li>
      <li>1 punto per ogni dado usato; +1 per '*' (se non moltiplica per 1); +2 per '/' (se divisore ≠ 1).</li>
      <li>Decine +2, centinaia +3, ... per numero composto.</li>
      <li>Bonus: 12 dadi +1, 13 dadi +2.</li>
    </ul>
  </section>
</main>

<script>
// --- GAME ID in URL (autocreazione) ---
let urlParams = new URLSearchParams(location.search);
let GAME_ID = urlParams.get('game_id');
if (!GAME_ID) {
  GAME_ID = 'game_' + Math.random().toString(36).substring(2, 8);
  window.location = location.pathname + '?game_id=' + GAME_ID;
}
document.getElementById('game-id').textContent = GAME_ID;

// --- Player locale ---
let PLAYER = localStorage.getItem('rc_player') || '';
if (PLAYER) document.getElementById('player-name').value = PLAYER;

// --- Helpers fetch ---
async function apiGet(url) {
  const playerPart = PLAYER ? `&player=${encodeURIComponent(PLAYER)}` : '';
  const r = await fetch(`${url}?game_id=${encodeURIComponent(GAME_ID)}${playerPart}`);
  return await r.json();
}
async function apiPost(url, payload={}) {
  const playerPart = PLAYER ? `&player=${encodeURIComponent(PLAYER)}` : '';
  const r = await fetch(`${url}?game_id=${encodeURIComponent(GAME_ID)}${playerPart}`, {
    method:'POST',
    headers:{'Content-Type':'application/json'},
    body: JSON.stringify(payload)
  });
  return await r.json();
}

// --- DOM refs ---
const poolDiv = document.getElementById('dice-pool');
const slotsDiv = document.getElementById('slots');
const playersGrid = document.getElementById('players-list');
const feedbackDiv = document.getElementById('feedback');
const timerSel = document.getElementById('timer-select');
const timerDisp = document.getElementById('timer-display');
const victorySel = document.getElementById('victory-select');

// --- Slot personali (13) ---
function ensureSlots() {
  if (slotsDiv.children.length === 13) return;
  slotsDiv.innerHTML = '';
  for (let i = 0; i < 13; i++) {
    const s = document.createElement('div');
    s.className = 'slot';
    slotsDiv.appendChild(s);
  }
}
ensureSlots();

// --- Render stato ---
async function renderState(state) {
  // aggiorna dropdown (server authoritative)
  if (state && typeof state.victory_score === 'number') {
    victorySel.value = String(state.victory_score);
  }
  if (state && typeof state.timer === 'number') {
    timerSel.value = String(state.timer);
  }

  // classifica: ordinata lato server; mostrata in griglia 6 colonne
  playersGrid.innerHTML = '';
  (state.players || []).forEach(p => {
    const tile = document.createElement('div');
    tile.className = 'player';
    tile.textContent = `${p}: ${state.scores && state.scores[p] ? state.scores[p] : 0}`;
    playersGrid.appendChild(tile);
  });

  // feedback / winner
  if (state.winner) {
    feedbackDiv.textContent = `🎉 ${state.winner} ha vinto! 🎉`;
    feedbackDiv.style.color = 'green';
    feedbackDiv.style.fontSize = '24px';
  } else {
    feedbackDiv.textContent = state.last_feedback || '';
    feedbackDiv.style.color = '';
    feedbackDiv.style.fontSize = '';
  }

  // timer globale di round (visuale)
  if (state.round_started_at && state.timer) {
    const started = Date.parse(state.round_started_at);
    const now = Date.now();
    const remaining = Math.max(0, Math.ceil((started + state.timer * 1000 - now) / 1000));
    timerDisp.textContent = remaining ? `${remaining}s` : '';
  } else {
    timerDisp.textContent = '';
  }

  // pool + i miei slot
  poolDiv.innerHTML = '';
  [...slotsDiv.children].forEach(s => { s.innerHTML = ''; s.classList.remove('filled'); });

  const mySlots = (state.personal_slots && PLAYER ? state.personal_slots[PLAYER] : null) || Array(13).fill(null);

  (state.dice_pool || []).forEach(d => {
    const el = document.createElement('div');
    el.className = 'die ' + d.type;
    el.textContent = d.value;
    el.dataset.id = d.id;
    el.addEventListener('click', async () => {
      if (state.winner) return;
      const current = (state.personal_slots && state.personal_slots[PLAYER]) || Array(13).fill(null);
      const idx = current.indexOf(d.id);
      if (idx !== -1) {
        await apiPost('/api/remove', { die_id: d.id });
      } else {
        await apiPost('/api/place', { die_id: d.id });
      }
      const st = await apiGet('/api/state');
      renderState(st);
    });
    const idx = mySlots.indexOf(d.id);
    if (idx !== -1) {
      const s = slotsDiv.children[idx];
      if (s) { s.appendChild(el); s.classList.add('filled'); }
    } else {
      poolDiv.appendChild(el);
    }
  });
}

// --- Eventi UI ---
document.getElementById('btn-new-game').addEventListener('click', () => {
  const newGameId = 'game_' + Math.random().toString(36).substring(2, 8);
  window.location = location.pathname + '?game_id=' + newGameId;
});

document.getElementById('btn-add-player').addEventListener('click', async () => {
  const name = document.getElementById('player-name').value.trim();
  if (!name) { alert('Inserisci un nome'); return; }
  PLAYER = name; localStorage.setItem('rc_player', PLAYER);
  const st = await apiPost('/api/add_player', { name });
  renderState(st);
});
document.getElementById('btn-roll').addEventListener('click', async () => {
  renderState(await apiPost('/api/roll'));
});
document.getElementById('btn-verify').addEventListener('click', async () => {
  const res = await apiPost('/api/verify');
  if (res.state) renderState(res.state);
});
document.getElementById('btn-reset').addEventListener('click', async () => {
  renderState(await apiPost('/api/reset_game'));
});

// imposta punteggio vittoria
victorySel.addEventListener('change', async () => {
  await apiPost('/api/set_victory', { victory: victorySel.value });
  const st = await apiGet('/api/state'); renderState(st);
});

// imposta timer globale (server-side)
timerSel.addEventListener('change', async () => {
  await apiPost('/api/set_timer', { seconds: parseInt(timerSel.value, 10) || 0 });
  const st = await apiGet('/api/state'); renderState(st);
});

// polling stato
setInterval(async () => { const st = await apiGet('/api/state'); renderState(st); }, 1000);

// init
(async function init(){ renderState(await apiGet('/api/state')); })();
</script>
</body>
</html>
"""

# ---- Cartella dati partite ----
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data", "games")
os.makedirs(DATA_DIR, exist_ok=True)

def game_path(game_id):
    safe = re.sub(r'[^a-zA-Z0-9_\-]', '_', game_id or 'default')
    return os.path.join(DATA_DIR, f"{safe}.json")

# ---- Stato di default (senza turni a rotazione) ----
def default_game_state(game_id):
    return {
        "game_id": game_id,
        "created_at": datetime.utcnow().replace(tzinfo=timezone.utc).isoformat(),
        "players": [],
        "scores": {},
        "dice_pool": [],              # set di dadi condiviso
        "personal_slots": {},         # player -> lista(13) di die_id o None
        "timer": 60,                  # durata round globale
        "round_started_at": None,     # inizio round corrente
        "last_feedback": "Nuova partita",
        "winner": None,
        "slots_by_player": {},        # alias/back-compat (non usato direttamente)
        "already_verified": [],       # giocatori che hanno già verificato nel round
        "victory_score": 50           # soglia di vittoria (30/40/50/60)
    }

# ---- I/O su file ----
def load_game(game_id):
    path = game_path(game_id)
    if not os.path.exists(path):
        return default_game_state(game_id)
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = f.read().strip()
            if not data:
                return default_game_state(game_id)
            return json.loads(data)
    except (json.JSONDecodeError, IOError):
        return default_game_state(game_id)

def save_game(game_id, state):
    path = game_path(game_id)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False, indent=2)

# ---- Dadi ----
def new_die_id():
    return f"d{random.randint(10**6, 10**7-1)}"

def roll_full_set():
    evens = [random.choice([0,2,4,6,8]) for _ in range(4)]
    odds  = [random.choice([1,3,5,7,9]) for _ in range(4)]
    ops   = [random.choice(['+','-','*','/']) for _ in range(4)]
    eq    = ['=']
    dice_values = evens + odds + ops + eq
    random.shuffle(dice_values)
    dice = []
    for v in dice_values:
        if v == '=': tipo = 'uguale'
        elif v in ['+','-','*','/']: tipo = 'op'
        elif int(v) % 2 == 0: tipo = 'pari'
        else: tipo = 'dispari'
        dice.append({"id": new_die_id(), "type": tipo, "value": str(v)})
    return dice

# ---- Parsing & punteggio ----
def tokenize_by_slots_for_list(dice_pool, slots_list):
    seq = []
    current_num = ""
    for dref in slots_list:
        if dref is None:
            if current_num != "":
                seq.append(current_num)
                current_num = ""
            continue
        die = next((d for d in dice_pool if d["id"] == dref), None)
        if not die:
            if current_num != "":
                seq.append(current_num)
                current_num = ""
            continue
        val = die["value"]
        if val.isdigit():
            current_num += val
        else:
            if current_num != "":
                seq.append(current_num)
                current_num = ""
            seq.append(val)
    if current_num != "":
        seq.append(current_num)
    return seq

def invalid_rules(seq):
    if '=' not in seq:
        return "Manca il segno di uguale"
    for tok in seq:
        if tok.isdigit() and len(tok) > 1 and tok[0] == '0':
            return "Numero con zero iniziale non consentito"
    try:
        eq_idx = seq.index('=')
        left = "".join(seq[:eq_idx])
        right = "".join(seq[eq_idx+1:])
        if re.fullmatch(r'\d+', left) and re.fullmatch(r'\d+', right) and left == right:
            return "Uguaglianza banale (X = X) non consentita"
    except Exception:
        pass
    for i, tok in enumerate(seq):
        if tok in ['*', '/'] and i+1 < len(seq):
            right = seq[i+1]
            if right.isdigit() and int(right) == 0:
                return "Non puoi moltiplicare/dividere per 0"
    return None

def safe_eval(expr):
    if not re.fullmatch(r'[0-9+\-*/. ]+', expr):
        raise ValueError("Espressione non valida")
    return eval(expr)

def compute_score(seq, used_ids, state):
    punti = len(used_ids)
    for i, tok in enumerate(seq):
        if tok == '*':
            left = seq[i-1] if i-1>=0 else None
            right = seq[i+1] if i+1<len(seq) else None
            if left and right and left.isdigit() and right.isdigit():
                if left!='1' and right!='1':
                    punti += 1
        if tok == '/':
            left = seq[i-1] if i-1>=0 else None
            right = seq[i+1] if i+1<len(seq) else None
            if left and right and left.isdigit() and right.isdigit():
                if right!='1':
                    punti += 2
    for tok in seq:
        if tok.isdigit():
            for pos, _ in enumerate(reversed(tok), start=0):
                punti += pos
    if len(used_ids) == 12: punti += 1
    if len(used_ids) == 13: punti += 2
    return punti

# ---- ROUTES ----
@app.route("/")
def home():
    return render_template_string(html_content)

@app.get("/api/state")
def api_state():
    game_id = request.args.get("game_id", "default")
    player = request.args.get("player")
    state = load_game(game_id)

    # Forza reroll se timer scaduto
    if state.get("round_started_at") and state.get("timer"):
        try:
            started = datetime.fromisoformat(state["round_started_at"])
        except Exception:
            started = None
        if started is not None:
            now_utc = datetime.utcnow().replace(tzinfo=timezone.utc)
            elapsed = (now_utc - started).total_seconds()
            if elapsed >= state["timer"]:
                state["dice_pool"] = roll_full_set()
                for p in state.get('players', []):
                    state.setdefault('personal_slots', {})[p] = [None]*13
                state['round_started_at'] = now_utc.isoformat()
                state['already_verified'] = []
                state['last_feedback'] = "⏰ Tempo scaduto! Nuovi dadi generati."
                save_game(game_id, state)

    # ordina i giocatori per punteggio (top first)
    state['players'] = sorted(state.get('players', []), key=lambda p: state['scores'].get(p, 0), reverse=True)

    # garantisci 13 slot per ciascun player
    for p in state.get('players', []):
        state.setdefault('personal_slots', {}).setdefault(p, [None]*13)

    view = dict(state)
    view['my_slots'] = state.get('personal_slots', {}).get(player, [None]*13) if player else [None]*13
    return jsonify(view)

@app.post("/api/add_player")
def api_add_player():
    game_id = request.args.get("game_id", "default")
    name = (request.json or {}).get("name", "").strip()
    if not name:
        return jsonify({"error": "Nome richiesto"}), 400

    state = load_game(game_id)
    if name not in state.get("players", []):
        state.setdefault("players", []).append(name)
        state.setdefault("scores", {})[name] = state.get("scores", {}).get(name, 0)
        state.setdefault('personal_slots', {})[name] = [None]*13
        state.setdefault('slots_by_player', {})[name] = [None]*13  # back-compat
        save_game(game_id, state)
    return jsonify(state)

@app.post("/api/roll")
def api_roll():
    game_id = request.args.get("game_id", "default")
    state = load_game(game_id)
    state["dice_pool"] = roll_full_set()
    for p in state.get('players', []):
        state.setdefault('personal_slots', {})[p] = [None]*13
    state['round_started_at'] = datetime.utcnow().replace(tzinfo=timezone.utc).isoformat()
    state['already_verified'] = []
    state['last_feedback'] = "Nuovi dadi generati"
    save_game(game_id, state)
    return jsonify(state)

@app.post("/api/place")
def api_place():
    game_id = request.args.get("game_id", "default")
    player = request.args.get('player') or (request.json or {}).get('player')
    payload = request.get_json(silent=True) or {}
    die_id = payload.get("die_id")
    target_slot = payload.get("slot")

    if not die_id:
        return jsonify({"error": "die_id richiesto"}), 400

    state = load_game(game_id)
    if not player:
        return jsonify({"error": "player richiesto"}), 400
    if player not in state.get('players', []):
        return jsonify({"error": "Player non registrato"}), 400

    valid_ids = {d["id"] for d in state.get("dice_pool", [])}
    if die_id not in valid_ids:
        return jsonify({"error": "Dado non trovato"}), 404

    pslots = state.setdefault('personal_slots', {}).setdefault(player, [None]*13)
    if die_id in pslots:
        return jsonify({"error": "Dado già piazzato nei tuoi slot", "state": state}), 400

    if target_slot is not None:
        try:
            idx = int(target_slot)
        except (TypeError, ValueError):
            return jsonify({"error": "slot deve essere un intero tra 0 e 12"}), 400
        if not (0 <= idx < len(pslots)):
            return jsonify({"error": "Indice slot fuori range"}), 400
        if pslots[idx] is not None:
            return jsonify({"error": "Slot già occupato"}), 400
    else:
        try:
            idx = pslots.index(None)
        except ValueError:
            return jsonify({"error": "Nessuno slot libero nei tuoi slot"}), 400

    pslots[idx] = die_id
    save_game(game_id, state)
    return jsonify(state)

@app.post("/api/remove")
def api_remove():
    game_id = request.args.get("game_id", "default")
    player = request.args.get('player') or (request.json or {}).get('player')
    die_id = (request.json or {}).get("die_id")

    state = load_game(game_id)
    if not player:
        return jsonify({"error": "player richiesto"}), 400

    pslots = state.setdefault('personal_slots', {}).setdefault(player, [None]*13)
    for i, ref in enumerate(pslots):
        if ref == die_id:
            pslots[i] = None
            break

    save_game(game_id, state)
    return jsonify(state)

@app.post("/api/verify")
def api_verify():
    game_id = request.args.get("game_id", "default")
    player = request.args.get('player') or (request.json or {}).get('player')
    state = load_game(game_id)

    if not player:
        return jsonify({"ok": False, "message": "player richiesto", "state": state}), 400

    # un solo tentativo per round
    if player in state.get('already_verified', []):
        return jsonify({"ok": False, "message": "Hai già verificato in questo round", "state": state}), 200

    pslots = state.get('personal_slots', {}).get(player, [None]*13)
    seq = tokenize_by_slots_for_list(state.get('dice_pool', []), pslots)
    msg = invalid_rules(seq)
    if msg:
        state["last_feedback"] = f"❌ {msg}"
        save_game(game_id, state)
        return jsonify({"ok": False, "message": msg, "state": state}), 200

    try:
        eq_idx = seq.index('=')
    except ValueError:
        state["last_feedback"] = "❌ Manca '='"
        save_game(game_id, state)
        return jsonify({"ok": False, "message": "Manca '='", "state": state}), 200

    lhs_tokens = seq[:eq_idx]
    rhs_tokens = seq[eq_idx+1:]
    if not lhs_tokens or not rhs_tokens:
        state["last_feedback"] = "❌ LHS o RHS vuoto"
        save_game(game_id, state)
        return jsonify({"ok": False, "message": "LHS o RHS vuoto", "state": state}), 200

    try:
        lhs_val = safe_eval("".join(lhs_tokens))
        rhs_val = safe_eval("".join(rhs_tokens))
    except Exception as e:
        state["last_feedback"] = f"❌ Espressione non valida ({e})"
        save_game(game_id, state)
        return jsonify({"ok": False, "message": f"Espressione non valida: {e}", "state": state}), 200

    if abs(lhs_val - rhs_val) > 1e-9:
        state["last_feedback"] = "❌ Equazione errata"
        save_game(game_id, state)
        return jsonify({"ok": False, "message": "Equazione errata", "state": state}), 200

    used_ids = set([x for x in pslots if x is not None])
    points = compute_score(seq, used_ids, state)

    state.setdefault('scores', {})[player] = state.get('scores', {}).get(player, 0) + points
    state.setdefault('personal_slots', {})[player] = [None]*13
    state.setdefault('already_verified', []).append(player)

    # vittoria
    if state['scores'][player] >= state.get('victory_score', 50):
        state['winner'] = player
        state['last_feedback'] = f"🎉 {player} ha vinto raggiungendo {state['scores'][player]} punti!"
    else:
        state['last_feedback'] = f"✅ {player}: +{points} punti"

    save_game(game_id, state)
    return jsonify({"ok": True, "points": points, "state": state})

@app.post("/api/set_victory")
def api_set_victory():
    game_id = request.args.get("game_id", "default")
    state = load_game(game_id)
    value = (request.json or {}).get("victory")
    try:
        val = int(value)
        if val in [30, 40, 50, 60]:
            state['victory_score'] = val
            save_game(game_id, state)
            return jsonify(state)
    except Exception:
        pass
    return jsonify({"error": "Valore non valido"}), 400

@app.post("/api/set_timer")
def api_set_timer():
    game_id = request.args.get("game_id", "default")
    state = load_game(game_id)
    seconds = (request.json or {}).get("seconds", 60)
    try:
        sec = int(seconds)
        if sec >= 0 and sec <= 3600:
            state['timer'] = sec
            # se non c'è round in corso, parte da ora; se c'è, manteniamo start e si aggiorna al prossimo reroll
            if state.get('round_started_at') is None and sec > 0:
                state['round_started_at'] = datetime.utcnow().replace(tzinfo=timezone.utc).isoformat()
            save_game(game_id, state)
            return jsonify(state)
    except Exception:
        pass
    return jsonify({"error": "Timer non valido"}), 400

@app.post("/api/reset_game")
def api_reset_game():
    game_id = request.args.get("game_id", "default")
    fresh = default_game_state(game_id)
    save_game(game_id, fresh)
    return jsonify(fresh)

# ---- Avvio locale ----
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
