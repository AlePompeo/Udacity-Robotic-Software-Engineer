# Guida per rifare building e robot con gli editor di Gazebo

Coordinate in metri, sul piano del pavimento. Altezza muri 2.5 m, spessore 0.15 m (valori di default dell'editor).
Il mondo (`world/MyWorld.world`) include il building con posa `0 0 0`, quindi le coordinate qui sotto sono quelle del mondo.

Struttura: guscio ottagonale (muri `W1`–`W8`, con gli angoli smussati a 45°) e dentro una griglia 3×3 di stanze a muri ortogonali:
atrio al centro, sala sud (ingresso), sala nord, sala est, sala ovest e quattro stanze d'angolo.
Nessuna colonna: i muri si incontrano per sovrapposizione normale (l'editor li unisce da solo).

Immagine da ricalcare: `pianta_da_ricalcare.png` (1800 x 1400 px, **100 px per metro**, barra di scala di 10 m in basso a sinistra,
origine (0,0) al centro della croce rossa).

## 1. Building Editor

1. Avvia Gazebo con un mondo vuoto (`gazebo`), poi **Edit → Building Editor** (Ctrl+B).
2. (Facoltativo, comodo) **Import** nella palette a sinistra: scegli `pianta_da_ricalcare.png` e imposta la scala
   (100 px/m, oppure usa la barra dei 10 m). Poi ricalca cliccando sui vertici dei muri.
3. Per ogni muro fai doppio clic e nell'Inspector digita **Start / End** dalla tabella (precisione al centimetro), altezza 2.5, spessore 0.15.
4. **Livello A** (12 muri, consegna valida): guscio `W1`–`W8` e i 4 muri dell'atrio (`HSC`, `HNC`, `VWC`, `VEC`).
   **Livello B** (facoltativo, 8 muri): le stanze d'angolo e le sale laterali (`HSW`, `HSE`, `HNW`, `HNE`, `VWS`, `VWN`, `VES`, `VEN`).
   Aggiungi porte e finestre con la palette.
5. Colore e texture: strumenti *Color* e *Texture* della palette (clic sul muro). Mettine almeno uno (es. i muri dell'atrio terracotta, il guscio crema).
6. **File → Save As**: nome modello `Building`, cartella `Project1/model/` (crea `Building/model.sdf` e `model.config`). Poi **Exit Building Editor**.
7. Se il building appare spostato rispetto agli arredi, correggi la `<pose>` dell'include `building` in `world/MyWorld.world`.

### Muri Livello A (obbligatorio): 12 muri
| Muro | Start → End | Lungh. (m) | Aperture |
|---|---|---|---|
| W1 | (-5.5,-6) → (-1.5,-6); (1.5,-6) → (5.5,-6) | 11 | finestra 1.2 m in (-2.8,-6)<br>varco 3 m in (0,-6) (muro diviso in due)<br>finestra 1.2 m in (2.8,-6) |
| W2 | (5.5,-6) → (8,-3.5) | 3.54 | finestra 1.2 m in (6.75,-4.75) |
| W3 | (8,-3.5) → (8,3.5) | 7 | finestra 1.2 m in (8,-1.8)<br>finestra 1.2 m in (8,1.8) |
| W4 | (8,3.5) → (5.5,6) | 3.54 | finestra 1.2 m in (6.75,4.75) |
| W5 | (5.5,6) → (-5.5,6) | 11 | finestra 1.2 m in (2.5,6)<br>finestra 1.2 m in (0,6)<br>finestra 1.2 m in (-2.5,6) |
| W6 | (-5.5,6) → (-8,3.5) | 3.54 | finestra 1.2 m in (-6.75,4.75) |
| W7 | (-8,3.5) → (-8,-3.5) | 7 | finestra 1.2 m in (-8,1.8)<br>finestra 1.2 m in (-8,-1.8) |
| W8 | (-8,-3.5) → (-5.5,-6) | 3.54 | finestra 1.2 m in (-6.75,-4.75) |
| HSC | (-4,-3) → (4,-3) | 8 | porta 1.6 m in (0,-3) |
| HNC | (-4,3) → (4,3) | 8 | porta 1.6 m in (0,3) |
| VWC | (-4,-3) → (-4,3) | 6 | porta 1.6 m in (-4,0) |
| VEC | (4,-3) → (4,3) | 6 | porta 1.6 m in (4,0) |

### Muri Livello B (facoltativo): 8 muri
| Muro | Start → End | Lungh. (m) | Aperture |
|---|---|---|---|
| HSW | (-8,-3) → (-4,-3) | 4 | porta 1.4 m in (-6,-3) |
| HSE | (4,-3) → (8,-3) | 4 | porta 1.4 m in (6,-3) |
| HNW | (-8,3) → (-4,3) | 4 | porta 1.4 m in (-6,3) |
| HNE | (4,3) → (8,3) | 4 | porta 1.4 m in (6,3) |
| VWS | (-4,-6) → (-4,-3) | 3 | porta 1.4 m in (-4,-4.5) |
| VWN | (-4,3) → (-4,6) | 3 | porta 1.4 m in (-4,4.5) |
| VES | (4,-6) → (4,-3) | 3 | porta 1.4 m in (4,-4.5) |
| VEN | (4,3) → (4,6) | 3 | porta 1.4 m in (4,4.5) |

Totale nel disegno completo: 13 finestre e 12 porte (più il varco d'ingresso). Per la consegna ne bastano poche
(es. 4 finestre e le 4 porte dell'atrio). Finestra: larghezza 1.2, altezza 1.2, elevazione 0.9. Porta: altezza 2.0.

## 2. Model Editor (robot `Rover`)

Da zero (10 minuti), in **Edit → Model Editor** (Ctrl+M):

| Link | Forma | Dimensioni | Posa (x, y, z, roll, pitch, yaw) | Massa |
|---|---|---|---|---|
| `chassis` | box | 0.5 × 0.3 × 0.1 | 0, 0, 0.1, 0, 0, 0 | 5 |
| `wheel_left` | cilindro | raggio 0.1, lunghezza 0.05 | 0, 0.18, 0.1, 1.5707, 0, 0 | 0.5 |
| `wheel_right` | cilindro | raggio 0.1, lunghezza 0.05 | 0, -0.18, 0.1, 1.5707, 0, 0 | 0.5 |
| `caster_front` | sfera | raggio 0.05 | 0.2, 0, 0.05, 0, 0, 0 | 0.1 |
| `caster_back` | sfera | raggio 0.05 | -0.2, 0, 0.05, 0, 0, 0 | 0.1 |

Il copia-incolla della ruota è il modo più rapido per fare la seconda. Se riesci, imposta l'attrito delle sfere a 0
(Inspector del link → Collision → Surface, mu = mu2 = 0), così il robot non si impunta.

| Giunto | Tipo | Parent → Child | Asse |
|---|---|---|---|
| `left_wheel_joint` | revolute | `chassis` → `wheel_left` | Z, senza limiti |
| `right_wheel_joint` | revolute | `chassis` → `wheel_right` | Z, senza limiti |
| `caster_front_joint` | fixed | `chassis` → `caster_front` | — |
| `caster_back_joint` | fixed | `chassis` → `caster_back` | — |

Salva con **File → Save As** come `Rover` in `Project1/model/` (sostituisce il mio) ed esci. Il mondo usa `model://Rover`, non serve altro.
I rover nel mondo sono fermi (due istanze in stanze diverse): non c'è nessun plugin sul robot.

**Alternativa più veloce:** inserisci il `Rover` attuale, tasto destro → *Edit Model*, cambia qualcosa e Save As.

## 3. Dopo aver salvato
```bash
cd ~/Documenti/workspace_gazebo/Project1
rm -rf build                      # non va consegnata
micromamba activate ros_env
export GAZEBO_MODEL_PATH=$PWD/model
gz sdf -k model/Building/model.sdf && gz sdf -k model/Rover/model.sdf && gz sdf -k world/MyWorld.world
./run.sh                          # ricrea build/: eliminala di nuovo prima di consegnare
```
