import os
import json
import random
import re
from datetime import datetime
from flask import Flask, request, jsonify, render_template_string, send_from_directory

app = Flask(__name__)

# ---- HTML + CSS + JS incorporati ----
html_content = """
<!doctype html>
<html lang="it">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>ROLLING CUBES</title>
<style>
:root {
  --bg:#f5f6fa;
  --box:#fff;
  --text:#2d3436;
  --accent:#0984e3;
}
* { box-sizing:border-box; }
body {
  margin:0;
  font-family:system-ui,Segoe UI,Roboto,Arial;
  background:var(--bg);
  color:var(--text);
  padding:18px;
}
main { max-width:1000px; margin:0 auto; }
.topbar {
  display:flex;
  justify-content:space-between;
  gap:12px;
  align-items:center;
  margin-bottom:12px;
  flex-wrap:wrap;
}
.player-controls input { padding:6px 8px; }
button {
  background:var(--accent);
  color:#fff;
  border:none;
  padding:8px 10px;
  border-radius:8px;
  cursor:pointer;
  font-weight:1000;
  margin-right: 10px; /* spazio di 10px tra i bottoni */
}
button:active { transform:translateY(1px); }
.timer-display {
  min-width:70px;
  font-weight:700;
  color:var(--accent);
  margin-left:6px;
  text-align:center;
}
.status {
  display:flex;
  gap:24px;
  align-items:flex-start;
  margin-bottom:12px;
}
.scoreboard {
  background:var(--box);
  padding:8px;
  border-radius:8px;
  box-shadow:0 8px 18px rgba(0,0,0,0.06);
  min-width:220px;
}
.scoreboard ul {
  list-style:none;
  padding:0;
  margin:6px 0;
}
.scoreboard li {
  padding:6px 8px;
  border-radius:6px;
  margin-bottom:6px;
  background:#fafafa;
  display:flex;
  justify-content:space-between;
  align-items:center;
}
#current-player { font-weight:800; color:var(--accent); }
.dice-pool {
  display:flex;
  flex-wrap:wrap;
  gap:10px;
  padding:12px;
  background:var(--box);
  border-radius:12px;
  box-shadow:0 6px 18px rgba(0,0,0,0.06);
}
.die {
  width:60px;
  height:60px;
  border-radius:10px;
  display:flex;
  align-items:center;
  justify-content:center;
  font-size:26px;
  font-weight:700;
  cursor:pointer;
  box-shadow:0 6px 12px rgba(0,0,0,0.08);
  border:3px solid transparent;
}
.die.pari { background:#74b9ff; color:#2d3436; border-color:#0984e3; }
.die.dispari { background:#fab1a0; color:#2d3436; border-color:#d63031; }
.die.op { background:#55efc4; color:#2d3436; border-color:#00b894; }
.die.uguale { background:#ffeaa7; color:#2d3436; border-color:#fdcb6e; }
.slots {
  display:flex;
  flex-wrap:wrap;
  gap:8px;
  padding:12px;
  background:var(--box);
  border-radius:12px;
  box-shadow:0 6px 18px rgba(0,0,0,0.06);
}
.slot {
  width:60px;
  height:60px;
  border-radius:10px;
  background:#dfe6e9;
  display:flex;
  align-items:center;
  justify-content:center;
  border:3px dashed #636e72;
}
.slot.filled { border-style:solid; border-color:var(--accent); background:#e6f3ff; }
.feedback {
  margin-top:14px;
  min-height:26px;
  font-size:18px;
  font-weight:600;
  display:flex;
  align-items:center;
  justify-content:center;
}
.rules {
  margin-top:18px;
  padding:12px;
  background:var(--box);
  border-radius:10px;
}
</style>
</head>
<body>
<main>
<h1>ROLLING CUBES</h1>

<section class="topbar">
  <div class="player-controls">
    <input id="player-name" placeholder="Nome giocatore" />
    <button id="btn-add-player">Aggiungi</button>
    <button id="btn-reset">Azzera partita</button>

    </div> <!-- chiusura corretta player-controls -->

  <div class="game-controls">
    <button id="btn-roll">Lancia dadi</button>
    <button id="btn-verify">Verifica equazione</button>

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
  <h2>Dadi (clicca per mettere nello slot; riclicca per rimuovere)</h2>
  <div id="dice-pool" class="dice-pool" aria-live="polite"></div>
</section>

<section class="slots-area">
  <h2>Slot (13)</h2>
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

// --- Helpers fetch JSON ---
async function apiGet(url) {
  const r = await fetch(`${url}?game_id=${encodeURIComponent(GAME_ID)}`);
  return await r.json();
}
async function apiPost(url, payload={}) {
  const r = await fetch(`${url}?game_id=${encodeURIComponent(GAME_ID)}`, {
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

// --- Slot ---
function ensureSlots() {
  if(slotsDiv.children.length===13) return;
  slotsDiv.innerHTML='';
  for(let i=0;i<13;i++){
    const s=document.createElement('div');
    s.className='slot';
    s.dataset.index=i;
    slotsDiv.appendChild(s);
  }
}
ensureSlots();

// --- Render stato ---
async function renderState(state){
  // giocatori
  playersUl.innerHTML='';
  (state.players||[]).forEach((p,i)=>{
    const li=document.createElement('li');
    const score = state.scores && state.scores[p]?state.scores[p]:0;
    const turnMark = (i === (state.current_index % (state.players.length||1))) ? ' ← turno':'';
    li.textContent=`${p}: ${score}${turnMark}`;
    playersUl.appendChild(li);
  });
  currentSpan.textContent = state.players && state.players.length ? state.players[state.current_index % state.players.length] : '—';

  // feedback
  if(state.winner){
    feedbackDiv.textContent=`🎉 ${state.winner} ha vinto la partita! 🎉`;
    feedbackDiv.style.color='green';
    feedbackDiv.style.fontSize='24px';
    feedbackDiv.style.fontWeight='bold';
  } else {
    feedbackDiv.textContent = state.last_feedback || '';
    feedbackDiv.style.color='';
    feedbackDiv.style.fontSize='';
    feedbackDiv.style.fontWeight='';
  }

  // dadi/pool
  poolDiv.innerHTML='';
  [...slotsDiv.children].forEach(s=>s.innerHTML='');
  (state.dice_pool||[]).forEach(d=>{
    const el = document.createElement('div');
    el.className='die '+d.type;
    el.textContent=d.value;
    el.dataset.id=d.id;
    el.addEventListener('click', async ()=>{
      if(state.winner) return;
      const isInSlot = d.in_slot!==null && d.in_slot!==undefined;
      if(isInSlot){
        await apiPost('/api/remove',{die_id:d.id});
      } else {
        await apiPost('/api/place',{die_id:d.id});
      }
      const st = await apiGet('/api/state');
      renderState(st);
    });
    if(d.in_slot===null||d.in_slot===undefined){
      poolDiv.appendChild(el);
    } else {
      const s = slotsDiv.children[d.in_slot];
      if(s) s.appendChild(el);
    }
  });
}

// --- Giocatori ---
document.getElementById('btn-add-player').addEventListener('click', async ()=>{
  const name=document.getElementById('player-name').value.trim();
  if(!name){alert('Inserisci un nome');return;}
  const st=await apiPost('/api/add_player',{name});
  document.getElementById('player-name').value='';
  renderState(st);
});


// --- Controlli gioco ---
document.getElementById('btn-roll').addEventListener('click', async ()=>{renderState(await apiPost('/api/roll'))});
document.getElementById('btn-verify').addEventListener('click', async ()=>{const res=await apiPost('/api/verify'); if(res.state) renderState(res.state)});
document.getElementById('btn-reset').addEventListener('click', async ()=>{renderState(await apiPost('/api/reset_game'))});

// --- Timer e cambio turno ---
let gameRunning = false;
let remaining = parseInt(timerSel.value,10)||0;
let tickHandle = null;

async function startTurn() {
  const st = await apiGet('/api/state');
  if(!st.players || st.players.length===0) return;
  gameRunning = true;

  // --- Lancia dadi all'inizio turno ---
  const rolledState = await apiPost('/api/roll');
  renderState(rolledState);

  // Imposta timer
  remaining = parseInt(timerSel.value,10) || 0;
  timerDisp.textContent = remaining ? `${remaining}s` : '';

  if(tickHandle) clearInterval(tickHandle);
  if(remaining > 0){
    tickHandle = setInterval(async ()=>{
      remaining--;
      timerDisp.textContent = `${remaining}s`;
      if(remaining <= 0){
        clearInterval(tickHandle);
        await apiPost('/api/next');
        const rolledNextState = await apiPost('/api/roll');
        renderState(rolledNextState);
        startTurn();
      }
    },1000); // correzione da 10000 a 1000 ms
  }
}

document.addEventListener('DOMContentLoaded', () => {
    // Bottone "Inizia partita"
    const btnStart = document.createElement('button');
    btnStart.textContent = "Inizia partita";
    btnStart.addEventListener('click', startTurn);

    // Inserisci subito dopo "Aggiungi"
    const btnAdd = document.getElementById('btn-add-player');
    if(btnAdd && btnAdd.parentNode){
        btnAdd.insertAdjacentElement('afterend', btnStart);
    }
});


// Bottone "Passa turno"
document.getElementById('btn-next').addEventListener('click', async ()=>{
  if(tickHandle) clearInterval(tickHandle);
  await apiPost('/api/next');
  const rolledState = await apiPost('/api/roll');
  renderState(rolledState);
  remaining = parseInt(timerSel.value, 10) || 0;
  if(remaining>0) startTurn();
});

// Cambio timer manuale
timerSel.addEventListener('change', ()=>{
  remaining = parseInt(timerSel.value,10)||0;  // aggiorna solo il valore
  timerDisp.textContent = remaining ? `${remaining}s` : '';  // aggiorna la visualizzazione
  // non avviare il countdown automaticamente
});

// Polling 1s per aggiornamento stato
setInterval(async ()=>{
  const st = await apiGet('/api/state');
  renderState(st);
},1000);

// --- Iniziale ---
(async function init(){renderState(await apiGet('/api/state'))})();
</script>
<script>
let selectedShelf = null;
let selectedTrain = null;
let lastPlayer = 1;

function updateName(playerNum) {
    const input = document.getElementById(`name${playerNum}`);
    alert(`Nome Giocatore ${playerNum} aggiornato a: ${input.value}`);
}

function updateAvatar(playerNum) {
    const select = document.getElementById(`avatar${playerNum}`);
    const img = document.getElementById(`avatar_img${playerNum}`);
    img.src = "/static/" + select.value;
}

function render() {
    fetch("/state").then(r => r.json()).then(data => {
        if (data.current_player !== lastPlayer) {
            selectedShelf = null;
            selectedTrain = null;
            lastPlayer = data.current_player;
        }

        // aggiorna treno e shelves
        const trainContainer = document.getElementById("train");
        trainContainer.innerHTML = "";
        data.train.forEach((tile, idx) => {
            const tileDiv = document.createElement("div");
            tileDiv.className = "tile";
            ["left","right"].forEach(side=>{
                const sideDiv = document.createElement("div");
                sideDiv.className="side";
                sideDiv.innerText = tile[side];
                sideDiv.onclick = () => {
                    selectedTrain={trainIdx:idx, side};
                    render();
                    tryPlace();
                };
                if (selectedTrain && selectedTrain.trainIdx===idx && selectedTrain.side===side){
                    sideDiv.classList.add("selected");
                }
                tileDiv.appendChild(sideDiv);
            });
            trainContainer.appendChild(tileDiv);
        });

        ["p1_shelf","p2_shelf"].forEach(shelfId=>{
            const shelfDiv = document.getElementById(shelfId);
            const shelf = data[shelfId];
            shelfDiv.innerHTML = "";
            shelf.forEach((t,i)=>{
                if(!t) return;
                const tileDiv = document.createElement("div");
                tileDiv.className="tile";
                ["left","right"].forEach(side=>{
                    const sideDiv = document.createElement("div");
                    sideDiv.className="side";
                    sideDiv.innerText = t[side];
                    if ((shelfId==="p1_shelf" && data.current_player===1) || 
                        (shelfId==="p2_shelf" && data.current_player===2)){
                        sideDiv.onclick=()=>{
                            selectedShelf={shelfId,idx:i,side};
                            render();
                            tryPlace();
                        };
                    }
                    if (selectedShelf && selectedShelf.shelfId===shelfId && selectedShelf.idx===i && selectedShelf.side===side){
                        sideDiv.classList.add("selected");
                    }
                    tileDiv.appendChild(sideDiv);
                });
                shelfDiv.appendChild(tileDiv);
            });
        });

        document.getElementById("score1").innerText = data.scores["1"];
        document.getElementById("score2").innerText = data.scores["2"];
        document.getElementById("turn").innerText = "Tocca a: Giocatore " + data.current_player;
        document.getElementById("timer").innerText = "Timer: " + data.timer + "s";

        const winnerDiv = document.getElementById("success");
        if(data.winner){
            const playerName = data.winner===1?document.getElementById("name1").value:document.getElementById("name2").value;
            winnerDiv.innerHTML = `${playerName} ha vinto la partita! 🎉`;
            winnerDiv.style.animation = "flash 1s infinite";
        } else {
            winnerDiv.innerHTML = "";
            winnerDiv.style.animation="";
        }
    });
}

function tryPlace(){
    if(!selectedShelf || !selectedTrain) return;
    fetch("/place",{
        method:"POST",
        headers:{"Content-Type":"application/json"},
        body:JSON.stringify(selectedShelf && selectedTrain ? {
            shelfId:selectedShelf.shelfId,
            idx:selectedShelf.idx,
            shelfSide:selectedShelf.side,
            trainIdx:selectedTrain.trainIdx,
            trainSide:selectedTrain.side
        } : {})
    })
    .then(r=>r.json())
    .then(data=>{
        if(data.result==="success"){
            selectedShelf=null;
            selectedTrain=null;
        }
        render();
    });
}

document.getElementById("newGameBtn").onclick = ()=>{
    fetch("/reset",{method:"POST"})
    .then(r=>r.json())
    .then(()=>{
        selectedShelf=null;
        selectedTrain=null;
        lastPlayer=1;
        render();
    });
};

render();
setInterval(render,1000);
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
        # se il JSON è corrotto, restituisci uno stato base ma senza toccare i giocatori
        return {
            "game_id": game_id,
            "created_at": datetime.utcnow().isoformat(),
            "players": [],
            "scores": {},
            "current_index": 0,
            "timer": 60,
            "dice_pool": [],
            "slots": [None]*13,
            "turn_used_die_ids": [],
            "last_feedback": "Errore nel file di salvataggio, partita azzerata"
        }

def default_game_state(game_id: str) -> dict:
    return {
        "game_id": game_id,
        "created_at": datetime.utcnow().isoformat(),
        "players": [],
        "scores": {},
        "current_index": 0,
        "timer": 60,
        "dice_pool": [],
        "slots": [None]*13,
        "turn_used_die_ids": [],
        "last_feedback": "Nuova partita"
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
            "in_slot": None
        })
    return dice

# ---- Tokenizzazione, regole, punteggio ----
def tokenize_by_slots(state: dict) -> list:
    seq = []
    current_num = ""
    for dref in state["slots"]:
        if dref is None:
            if current_num != "":
                seq.append(current_num)
                current_num = ""
            continue
        die = next((d for d in state["dice_pool"] if d["id"] == dref), None)
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
    return jsonify(load_game(game_id))


@app.post("/api/roll")
def api_roll():
    game_id = request.args.get("game_id", "default")
    state = load_game(game_id)
    state["dice_pool"] = roll_full_set()
    state["slots"] = [None] * 13
    state["turn_used_die_ids"] = []
    state["last_feedback"] = "Dadi lanciati"
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
    save_game(game_id, state)
    return jsonify(state)


@app.post("/api/place")
def api_place():
    game_id = request.args.get("game_id", "default")
    payload = request.get_json(silent=True) or {}
    die_id = payload.get("die_id")
    target_slot = payload.get("slot")

    if not die_id:
        return jsonify({"error": "die_id richiesto"}), 400

    state = load_game(game_id)

    # ---- Sincronizzazione tra slots e dice_pool ----
    valid_ids = {d["id"] for d in state.get("dice_pool", [])}
    for i, ref in enumerate(state["slots"]):
        if ref is not None and ref not in valid_ids:
            state["slots"][i] = None

    for d in state["dice_pool"]:
        s = d.get("in_slot")
        if s is None:
            continue
        if not (isinstance(s, int) and 0 <= s < len(state["slots"]) and state["slots"][s] == d["id"]):
            d["in_slot"] = None

    # ---- Recupera il dado richiesto ----
    die = next((d for d in state["dice_pool"] if d["id"] == die_id), None)
    if not die:
        return jsonify({"error": "Dado non trovato"}), 404
    if die.get("in_slot") is not None:
        return jsonify({"error": "Dado già piazzato in uno slot", "state": state}), 400

    # ---- Determina slot di destinazione ----
    if target_slot is not None:
        try:
            idx = int(target_slot)
        except (TypeError, ValueError):
            return jsonify({"error": "slot deve essere un intero tra 0 e 12"}), 400
        if not (0 <= idx < len(state["slots"])):
            return jsonify({"error": "Indice slot fuori range"}), 400
        if state["slots"][idx] is not None:
            return jsonify({"error": "Slot già occupato"}), 400
    else:
        try:
            idx = state["slots"].index(None)
        except ValueError:
            return jsonify({"error": "Nessuno slot libero"}), 400

    # ---- Applica la mossa ----
    state["slots"][idx] = die_id
    die["in_slot"] = idx
    state["turn_used_die_ids"] = [ref for ref in state["slots"] if ref is not None]
    save_game(game_id, state)
    return jsonify(state)


@app.post("/api/remove")
def api_remove():
    game_id = request.args.get("game_id", "default")
    die_id = (request.json or {}).get("die_id")
    state = load_game(game_id)

    for i, ref in enumerate(state["slots"]):
        if ref == die_id:
            state["slots"][i] = None
            break

    die = next((d for d in state["dice_pool"] if d["id"] == die_id), None)
    if die:
        die["in_slot"] = None

    state["turn_used_die_ids"] = [x for x in state["slots"] if x]
    save_game(game_id, state)
    return jsonify(state)


@app.post("/api/verify")
def api_verify():
    game_id = request.args.get("game_id", "default")
    state = load_game(game_id)

    if state.get("winner"):
        return jsonify({"ok": False, "message": "Partita terminata", "state": state}), 200

    seq = tokenize_by_slots(state)
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

    used_ids = set([x for x in state["slots"] if x is not None])
    points = compute_score(seq, used_ids, state)

    if state["players"]:
        cur_name = state["players"][state["current_index"] % len(state["players"])]
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
    state["dice_pool"] = roll_full_set()
    state["slots"] = [None] * 13
    state["turn_used_die_ids"] = []
    if state["players"]:
        state["current_index"] = (state["current_index"] + 1) % len(state["players"])
        for d in state["dice_pool"]:
            d["in_slot"] = None
        state["turn_used_die_ids"] = []
    save_game(game_id, state)
    return jsonify({"ok": True, "points": points, "state": state})


@app.post("/api/next")
def api_next():
    game_id = request.args.get("game_id", "default")
    state = load_game(game_id)

    if state["players"]:
        state["current_index"] = (state["current_index"] + 1) % len(state["players"])

    state["slots"] = [None]*13
    for d in state["dice_pool"]:
        d["in_slot"] = None
    state["turn_used_die_ids"] = []
    state["last_feedback"] = "Turno passato"
    save_game(game_id, state)
    return jsonify(state)


@app.post("/api/reset_game")
def api_reset_game():
    game_id = request.args.get("game_id", "default")
    fresh = {
        "game_id": game_id,
        "created_at": datetime.utcnow().isoformat(),
        "players": [],
        "scores": {},
        "current_index": 0,
        "timer": 60,
        "dice_pool": [],
        "slots": [None]*13,
        "turn_used_die_ids": [],
        "last_feedback": "Partita azzerata"
    }
    save_game(game_id, fresh)
    return jsonify(fresh)


# ---- Avvio server ----
if __name__ == "__main__":
    import logging

    # Nasconde i log di ogni richiesta HTTP
    log = logging.getLogger('werkzeug')
    log.setLevel(logging.ERROR)

    # Stampa solo l’indirizzo di accesso
    print("Avvia l'app in browser: http://127.0.0.1:8000")

    # Avvio server
    app.run(host="127.0.0.1", port=8000, debug=True)
