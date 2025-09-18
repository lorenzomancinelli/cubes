import os
import json
import random
import re
from datetime import datetime, timezone
from flask import Flask, request, jsonify, render_template_string

app = Flask(__name__)

# ---- HTML + CSS + JS incorporati (frontend leggermente adattato per supportare player "locali") ----
html_content = """
<!doctype html>
<html lang="it">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>ROLLING CUBES - Multiplayer</title>
<style>
/* Stessi stili del tuo progetto originale (omessi qui per brevità) */
:root { --bg:#f5f6fa; --box:#fff; --text:#2d3436; --accent:#0984e3; }
* { box-sizing:border-box; }
body { margin:0; font-family:system-ui,Segoe UI,Roboto,Arial; background:var(--bg); color:var(--text); padding:18px; }
main { max-width:1000px; margin:0 auto; }
.topbar{display:flex;justify-content:space-between;gap:12px;align-items:center;margin-bottom:12px;flex-wrap:wrap}
.player-controls input{padding:6px 8px}
button{background:var(--accent);color:#fff;border:none;padding:8px 10px;border-radius:8px;cursor:pointer;font-weight:1000;margin-right:10px}
.timer-display{min-width:70px;font-weight:700;color:var(--accent);margin-left:6px;text-align:center}
.status{display:flex;gap:24px;align-items:flex-start;margin-bottom:12px}
.scoreboard{background:var(--box);padding:8px;border-radius:8px;box-shadow:0 8px 18px rgba(0,0,0,0.06);min-width:220px}
.scoreboard ul{list-style:none;padding:0;margin:6px 0}
.scoreboard li{padding:6px 8px;border-radius:6px;margin-bottom:6px;background:#fafafa;display:flex;justify-content:space-between;align-items:center}
#current-player{font-weight:800;color:var(--accent)}
.dice-pool{display:flex;flex-wrap:wrap;gap:10px;padding:12px;background:var(--box);border-radius:12px;box-shadow:0 6px 18px rgba(0,0,0,0.06)}
.die{width:60px;height:60px;border-radius:10px;display:flex;align-items:center;justify-content:center;font-size:26px;font-weight:700;cursor:pointer;box-shadow:0 6px 12px rgba(0,0,0,0.08);border:3px solid transparent}
.die.pari{background:#74b9ff;color:#2d3436;border-color:#0984e3}
.die.dispari{background:#fab1a0;color:#2d3436;border-color:#d63031}
.die.op{background:#55efc4;color:#2d3436;border-color:#00b894}
.die.uguale{background:#ffeaa7;color:#2d3436;border-color:#fdcb6e}
.slots{display:flex;flex-wrap:wrap;gap:8px;padding:12px;background:var(--box);border-radius:12px;box-shadow:0 6px 18px rgba(0,0,0,0.06)}
.slot{width:60px;height:60px;border-radius:10px;background:#dfe6e9;display:flex;align-items:center;justify-content:center;border:3px dashed #636e72}
.slot.filled{border-style:solid;border-color:var(--accent);background:#e6f3ff}
.feedback{margin-top:14px;min-height:26px;font-size:18px;font-weight:600;display:flex;align-items:center;justify-content:center}
.rules{margin-top:18px;padding:12px;background:var(--box);border-radius:10px}
</style>
</head>
<body>
<main>
<h1>ROLLING CUBES (Multiplayer)</h1>

<section class="topbar">
  <div class="player-controls">
    <input id="player-name" placeholder="Nome giocatore" />
    <button id="btn-add-player">Aggiungi / Entra</button>
    <button id="btn-reset">Azzera partita</button>
  </div>

  <div class="game-controls">
    <button id="btn-roll">Lancia dadi (inizio turno)</button>
    <button id="btn-verify">Verifica equazione (usa i TUOI slot)</button>
    <button id="btn-next">Passa turno</button>

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
  <div>Turno: <span id="current-player">—</span></div>
  <div class="scoreboard">
    <h3>Classifica</h3>
    <ul id="players-list"></ul>
  </div>
</section>

<section class="dice-area">
  <h2>Dadi (clicca per mettere nello slot; riclicca per rimuovere) — ognuno ha i propri slot locali</h2>
  <div id="dice-pool" class="dice-pool" aria-live="polite"></div>
</section>

<section class="slots-area">
  <h2>Slot (13) — i TUOI slot (non condivisi)</h2>
  <div id="slots" class="slots"></div>
</section>

<section class="feedback-area">
  <div id="feedback" class="feedback"></div>
</section>

<section class="rules">
  <h3>Istruzioni (Regole implementate)</h3>
  <ul>
    <li>Non è permesso l'uso di zeri iniziali nei numeri (es. 09).</li>
    <li>Non ammesso X = X identico</li>
    <li>1 Punto per ogni dado usato; </li>
    <li>+1 punto per ogni dado Moltiplicazione usato; (non vale se moltiplico * 1);</li>
    <li>+2 punti per ogni dado Divisione usato; (se divisore ≠ 1);</li>
    <li>Decine +2 punti , centinaia +3 punti, ... per ogni numero composto</li>
    <li>Bonus: 12 dadi +1, Bonus 13 dadi +2</li>
  </ul>
</section>
</main>

<script>
// --- Identificazione partita tramite game_id ---
let urlParams = new URLSearchParams(location.search);
let GAME_ID = urlParams.get('game_id') || 'game_' + Math.random().toString(36).substring(2, 8);
document.getElementById('game-id').textContent = GAME_ID;

// --- Player locale salvato in localStorage ---
let PLAYER = localStorage.getItem('rc_player') || '';
if(PLAYER) document.getElementById('player-name').value = PLAYER;

// --- Helpers fetch JSON (aggiungiamo player sempre ai param) ---
async function apiGet(url) {
  const sep = url.includes('?') ? '&' : '?';
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
const playersUl = document.getElementById('players-list');
const currentSpan = document.getElementById('current-player');
const feedbackDiv = document.getElementById('feedback');
const timerSel = document.getElementById('timer-select');
const timerDisp = document.getElementById('timer-display');

// --- Slot frontend (semplice render dei 13 slot personali) ---
function ensureSlots() {
  if(slotsDiv.children.length===13) return;
  slotsDiv.innerHTML='';
  for(let i=0;i<13;i++){
    const s=document.createElement('div');
    s.className='slot';
    s.dataset.index=i;
    s.addEventListener('click', async ()=>{
      // se c'è un dado selezionato (click sul dado) verrà piazzato qui
    });
    slotsDiv.appendChild(s);
  }
}
ensureSlots();

// --- Render stato ---
async function renderState(state){
  // giocatori e classifica
  playersUl.innerHTML='';
  (state.players||[]).forEach((p,i)=>{
    const li=document.createElement('li');
    const score = state.scores && state.scores[p]?state.scores[p]:0;
    const turnMark = (i === (state.current_index % (state.players.length||1))) ? ' ← turno':'');
    li.textContent=`${p}: ${score}${turnMark}`;
    playersUl.appendChild(li);
  });
  currentSpan.textContent = state.players && state.players.length ? state.players[state.current_index % state.players.length] : '—';

  // feedback
  if(state.winner){
    feedbackDiv.textContent=`🎉 ${state.winner} ha vinto la partita! 🎉`;
    feedbackDiv.style.color='green'; feedbackDiv.style.fontSize='24px'; feedbackDiv.style.fontWeight='bold';
  } else {
    feedbackDiv.textContent = state.last_feedback || '';
    feedbackDiv.style.color=''; feedbackDiv.style.fontSize=''; feedbackDiv.style.fontWeight='';
  }

  // timer: se server ha turn_started_at+timer
  if(state.turn_started_at){
    const started = Date.parse(state.turn_started_at);
    const now = Date.now();
    const dur = state.timer || parseInt(timerSel.value,10) || 0;
    const remaining = Math.max(0, Math.ceil((started + dur*1000 - now)/1000));
    timerDisp.textContent = remaining ? `${remaining}s` : '';
  } else {
    timerDisp.textContent = '';
  }

  // dadi/pool
  poolDiv.innerHTML='';

  // svuota i 13 slot (visualizzazione personale)
  [...slotsDiv.children].forEach(s=>{ s.innerHTML=''; s.classList.remove('filled'); });

  const mySlots = (state.personal_slots && state.personal_slots[PLAYER]) || [null]*13;

  (state.dice_pool||[]).forEach(d=>{
    const el = document.createElement('div');
    el.className='die '+d.type;
    el.textContent=d.value;
    el.dataset.id=d.id;
    el.addEventListener('click', async ()=>{
      if(state.winner) return;
      // toggle: se nel mio slot -> rimuovi, altrimenti inserisci nel primo libero
      const mySlotsLocal = (state.personal_slots && state.personal_slots[PLAYER]) || [null]*13;
      const index = mySlotsLocal.indexOf(d.id);
      if(index !== -1){
        await apiPost('/api/remove',{die_id:d.id});
      } else {
        await apiPost('/api/place',{die_id:d.id});
      }
      const st = await apiGet('/api/state');
      renderState(st);
    });

    // se il dado è presente nei miei slot, mettilo nella corrispondente UI
    const idx = mySlots.indexOf(d.id);
    if(idx !== -1){
      const s = slotsDiv.children[idx];
      if(s){ s.appendChild(el); s.classList.add('filled'); }
    } else {
      poolDiv.appendChild(el);
    }
  });
}

// --- Giocatori ---
document.getElementById('btn-add-player').addEventListener('click', async ()=>{
  const name=document.getElementById('player-name').value.trim();
  if(!name){alert('Inserisci un nome');return;}
  PLAYER = name;
  localStorage.setItem('rc_player', PLAYER);
  const st=await apiPost('/api/add_player',{name});
  renderState(st);
});

// --- Controlli gioco ---
document.getElementById('btn-roll').addEventListener('click', async ()=>{renderState(await apiPost('/api/roll'))});
document.getElementById('btn-verify').addEventListener('click', async ()=>{const res=await apiPost('/api/verify'); if(res.state) renderState(res.state)});
document.getElementById('btn-reset').addEventListener('click', async ()=>{renderState(await apiPost('/api/reset_game'))});

// --- Timer e cambio turno client-side (basato sullo stato server) ---
let tickHandle = null;
function startLocalTicker(){
  if(tickHandle) clearInterval(tickHandle);
  tickHandle = setInterval(async ()=>{
    const st = await apiGet('/api/state');
    renderState(st);
  },1000);
}
startLocalTicker();

// Bottone "Passa turno"
document.getElementById('btn-next').addEventListener('click', async ()=>{
  if(tickHandle) clearInterval(tickHandle);
  await apiPost('/api/next');
  const rolledState = await apiPost('/api/roll');
  renderState(rolledState);
  startLocalTicker();
});

// Polling 1s per aggiornamento stato (già avviato dal ticker), ma teniamo anche un fallback
setInterval(async ()=>{ const st = await apiGet('/api/state'); renderState(st); },3000);

// --- Iniziale ---
(async function init(){ renderState(await apiGet('/api/state')); })();
</script>
</body>
</html>
"""

# ---- Cartella dati partite ----
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data", "games")
os.makedirs(DATA_DIR, exist_ok=True)

# ---- Funzioni di utilità per stato per partita ----
def game_path(game_id: str) -> str:
    safe = re.sub(r'[^a-zA-Z0-9_\-]', '_', game_id or 'default')
    return os.path.join(DATA_DIR, f"{safe}.json")


def load_game(game_id: str) -> dict:
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


def default_game_state(game_id: str) -> dict:
    return {
        "game_id": game_id,
        "created_at": datetime.utcnow().replace(tzinfo=timezone.utc).isoformat(),
        "players": [],
        "scores": {},
        "current_index": 0,
        "timer": 60,
        "dice_pool": [],
        "slots": [None]*13,            # campo legacy (non più usato per il gameplay personale)
        "personal_slots": {},         # mappa player -> lista(13) dei die_id (o None)
        "turn_used_die_ids": [],
        "last_feedback": "Nuova partita",
        "turn_started_at": None,
        "winner": None
    }


def save_game(game_id: str, state: dict) -> None:
    path = game_path(game_id)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False, indent=2)

# ---- Dadi ----
def new_die_id():
    return f"d{random.randint(10**6, 10**7-1)}"


def roll_full_set() -> list:
    evens = [random.choice([0,2,4,6,8]) for _ in range(4)]
    odds = [random.choice([1,3,5,7,9]) for _ in range(4)]
    ops = [random.choice(['+','-','*','/']) for _ in range(4)]
    eq = ['=']
    dice_values = evens + odds + ops + eq
    random.shuffle(dice_values)
    dice = []
    for v in dice_values:
        if v == '=':
            tipo = 'uguale'
        elif v in ['+','-','*','/']:
            tipo = 'op'
        elif int(v) % 2 == 0:
            tipo = 'pari'
        else:
            tipo = 'dispari'
        dice.append({
            "id": new_die_id(),
            "type": tipo,
            "value": str(v),
        })
    return dice

# ---- Tokenizzazione, regole, punteggio (adattate per lavorare su slot passati) ----

def tokenize_by_slots_for_list(dice_pool: list, slots_list: list) -> list:
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


def invalid_rules(seq: list) -> str | None:
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


def safe_eval(expr: str):
    if not re.fullmatch(r'[0-9+\-*/. ]+', expr):
        raise ValueError("Espressione non valida")
    return eval(expr)


def compute_score(seq: list, used_ids: set, state: dict) -> int:
    punti = len(used_ids)
    for i, tok in enumerate(seq):
        if tok=='*':
            left = seq[i-1] if i-1>=0 else None
            right = seq[i+1] if i+1<len(seq) else None
            if left and right and left.isdigit() and right.isdigit():
                if left!='1' and right!='1':
                    punti +=1
        if tok=='/':
            left = seq[i-1] if i-1>=0 else None
            right = seq[i+1] if i+1<len(seq) else None
            if left and right and left.isdigit() and right.isdigit():
                if right!='1':
                    punti +=2
    for tok in seq:
        if tok.isdigit():
            for pos,_ in enumerate(reversed(tok), start=0):
                punti += pos
    if len(used_ids)==12: punti+=1
    if len(used_ids)==13: punti+=2
    return punti

# ---- Rotte principali ----
@app.route("/")
def home():
    return render_template_string(html_content)

# ------ ROTTE API ------

@app.get("/api/state")
def api_state():
    game_id = request.args.get("game_id", "default")
    player = request.args.get("player")
    state = load_game(game_id)

    # assicurati che tutti i players abbiano una lista di slot
    for p in state.get('players', []):
        if p not in state.get('personal_slots', {}):
            state.setdefault('personal_slots', {})[p] = [None]*13

    # se è richiesto un player, aggiungi la sua view personalizzata come my_slots
    view = dict(state)
    view['my_slots'] = state.get('personal_slots', {}).get(player, [None]*13) if player else [None]*13
    return jsonify(view)


@app.post("/api/roll")
def api_roll():
    game_id = request.args.get("game_id", "default")
    player = request.args.get("player")
    state = load_game(game_id)
    state["dice_pool"] = roll_full_set()

    # svuota tutti gli slot personali quando si rilanciano i dadi (comportamento scelto)
    state["personal_slots"] = {p: [None]*13 for p in state.get('players', [])}
    state["turn_used_die_ids"] = []
    state["last_feedback"] = "Dadi lanciati"

    # imposta inizio turno (sincronizza il timer del turno per tutti i client)
    state['turn_started_at'] = datetime.utcnow().replace(tzinfo=timezone.utc).isoformat()
    # manteniamo lo stato['timer'] come durata del turno
    save_game(game_id, state)
    return jsonify(state)


@app.post("/api/add_player")
def api_add_player():
    game_id = request.args.get("game_id", "default")
    name = (request.json or {}).get("name", "").strip()
    if not name:
        return jsonify({"error": "Nome richiesto"}), 400

    state = load_game(game_id)
    if name not in state["players"]:
        state["players"].append(name)
        state["scores"][name] = state["scores"].get(name, 0)
        state.setdefault('personal_slots', {})[name] = [None]*13
    save_game(game_id, state)
    return jsonify(state)


@app.post("/api/place")
def api_place():
    game_id = request.args.get("game_id", "default")
    player = request.args.get('player') or (request.json or {}).get('player')
    payload = request.get_json(silent=True) or {}
    die_id = payload.get("die_id")
    # target_slot è opzionale; se non passato piazzeremo al primo libero del player's slots
    target_slot = payload.get("slot")

    if not die_id:
        return jsonify({"error": "die_id richiesto"}), 400

    state = load_game(game_id)
    # ensure player exists
    if player and player not in state.get('players', []):
        return jsonify({"error": "Player non registrato"}), 400

    # validità dado
    valid_ids = {d["id"] for d in state.get("dice_pool", [])}
    if die_id not in valid_ids:
        return jsonify({"error": "Dado non trovato"}), 404

    # lavora sui slot personali
    if not player:
        return jsonify({"error": "player richiesto per operazioni sui slot personali"}), 400
    pslots = state.setdefault('personal_slots', {}).setdefault(player, [None]*13)

    # se il dado è già piazzato nei MY slot -> errore
    if die_id in pslots:
        return jsonify({"error": "Dado già piazzato nei tuoi slot", "state": state}), 400

    # scegli slot
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
    state['turn_used_die_ids'] = list({ref for p in state.get('personal_slots', {}) for ref in (state['personal_slots'][p] or []) if ref})
    save_game(game_id, state)
    return jsonify(state)


@app.post("/api/remove")
def api_remove():
    game_id = request.args.get("game_id", "default")
    player = request.args.get('player') or (request.json or {}).get('player')
    die_id = (request.json or {}).get("die_id")
    state = load_game(game_id)

    if not player:
        return jsonify({"error": "player richiesto per operazioni sui slot personali"}), 400

    pslots = state.setdefault('personal_slots', {}).setdefault(player, [None]*13)
    for i, ref in enumerate(pslots):
        if ref == die_id:
            pslots[i] = None
            break

    state['turn_used_die_ids'] = list({ref for p in state.get('personal_slots', {}) for ref in (state['personal_slots'][p] or []) if ref})
    save_game(game_id, state)
    return jsonify(state)


@app.post("/api/verify")
def api_verify():
    game_id = request.args.get("game_id", "default")
    player = request.args.get('player') or (request.json or {}).get('player')
    state = load_game(game_id)

    if state.get("winner"):
        return jsonify({"ok": False, "message": "Partita terminata", "state": state}), 200

    if not player:
        return jsonify({"ok": False, "message": "player richiesto per verificare la propria equazione", "state": state}), 400

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

    if state["players"]:
        cur_name = state["players"][state["current_index"] % len(state["players"]) ]
        # verifichiamo che il player che sta verificando sia effettivamente il giocatore corrente
        if player != cur_name:
            state["last_feedback"] = f"❌ Non è il tuo turno ({cur_name} sta giocando)"
            save_game(game_id, state)
            return jsonify({"ok": False, "message": "Non è il tuo turno", "state": state}), 200

        state["scores"][cur_name] = state["scores"].get(cur_name, 0) + points

        if state["scores"][cur_name] > 47:
            max_score = max(state["scores"].values())
            winners = [p for p, s in state["scores"].items() if s == max_score]
            winner_name = winners[0]
            state["winner"] = winner_name
            state["last_feedback"] = f"🎉 Complimenti {winner_name}, hai vinto con {max_score} punti!"
            save_game(game_id, state)
            return jsonify({"ok": True, "points": points, "winner": winner_name, "state": state})

    state["last_feedback"] = f"✅ Equazione corretta! +{points} punti"
    # rilancia dadi globalmente
    state["dice_pool"] = roll_full_set()
    # svuota tutti gli slot personali
    state["personal_slots"] = {p: [None]*13 for p in state.get('players', [])}
    state["turn_used_die_ids"] = []
    # passa al prossimo giocatore
    if state["players"]:
        state["current_index"] = (state["current_index"] + 1) % len(state["players"])
    # e aggiorna il timer di inizio turno
    state['turn_started_at'] = datetime.utcnow().replace(tzinfo=timezone.utc).isoformat()
    save_game(game_id, state)
    return jsonify({"ok": True, "points": points, "state": state})


@app.post("/api/next")
def api_next():
    game_id = request.args.get("game_id", "default")
    state = load_game(game_id)

    if state["players"]:
        state["current_index"] = (state["current_index"] + 1) % len(state["players"])

    # reset personale (passare turno non altera le slot personali degli altri? qui le azzeriamo per chiarezza)
    state["personal_slots"] = {p: [None]*13 for p in state.get('players', [])}
    state["turn_used_die_ids"] = []
    state["last_feedback"] = "Turno passato"
    state['turn_started_at'] = datetime.utcnow().replace(tzinfo=timezone.utc).isoformat()
    save_game(game_id, state)
    return jsonify(state)


@app.post("/api/reset_game")
def api_reset_game():
    game_id = request.args.get("game_id", "default")
    fresh = default_game_state(game_id)
    save_game(game_id, fresh)
    return jsonify(fresh)


# ---- Avvio server locale (per test) ----
if __name__ == "__main__":
    import logging
    log = logging.getLogger('werkzeug')
    log.setLevel(logging.ERROR)
    print("Avvia l'app in browser: http://127.0.0.1:8000/?game_id=room1")
    app.run(host="127.0.0.1", port=8000, debug=True)
