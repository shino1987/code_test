# Spiegazione delle Differenze - ICT Smart Money Bot

Questo documento spiega le differenze tra i vari parametri e concetti nel trading bot ICT.

## 1. Timeframe (TF) - Diversi Periodi Temporali

Il bot utilizza **3 timeframe diversi** per scopi differenti:

- **BIAS_TF = "30m"** (30 minuti)
  - Usato per determinare il **bias direzionale** generale del mercato
  - È il timeframe "più alto" per vedere la tendenza principale
  - Decide se cercare trade LONG o SHORT

- **ENTRY_TF = "5m"** (5 minuti)
  - Usato per trovare il **punto di ingresso preciso**
  - È il timeframe più basso per timing ottimale
  - Qui si cercano i segnali di conferma per entrare

- **SL_TF = "15m"** (15 minuti)
  - Usato per calcolare lo **Stop Loss strutturale**
  - È un timeframe intermedio per SL più robusti
  - Gli swing high/low su 15m sono più significativi che su 5m

**Perché timeframe diversi?**
- Timeframe alto (30m) → tendenza generale
- Timeframe basso (5m) → entrata precisa
- Timeframe medio (15m) → stop loss affidabile

---

## 2. LOOKBACK - Diversi Periodi di Analisi Storica

Il bot analizza diverse quantità di candele storiche per scopi diversi:

- **LOOKBACK_BIAS = 260**
  - Analizza 260 candele da 30m (~5 giorni)
  - Per identificare swing high/low sul bias

- **LOOKBACK_ENTRY = 320**
  - Analizza 320 candele da 5m (~1 giorno)
  - Per trovare pattern di entrata recenti

- **LOOKBACK_SL = 220**
  - Analizza 220 candele da 15m (~2 giorni)
  - Per calcolare swing strutturali per Stop Loss

- **BTC_LOOKBACK = 260**
  - Analizza 260 candele BTC da 15m
  - Per il filtro di conflitto generale BTC

- **BTC_REJ_LOOKBACK = 120**
  - Analizza 120 candele BTC da 15m (~30 ore)
  - Per contare i rifiuti recenti su zone BTC

- **BTC_ZONE_LOOKBACK = 384**
  - Analizza 384 candele BTC da 15m (~4 giorni)
  - Per identificare zone di rifiuto di lungo periodo

**Perché LOOKBACK diversi?**
Ogni timeframe richiede una diversa profondità storica per identificare pattern significativi.

---

## 3. SWING_LR - Fractal Left/Right per Diversi Scopi

Il parametro LR (Left/Right) determina quante candele a sinistra e destra devono essere controllate per identificare uno swing high/low:

- **SWING_LR_BIAS = 2**
  - Per swing sul timeframe BIAS (30m)
  - Cerca swing con 2 candele a sx e 2 a dx

- **SWING_LR_ENTRY = 2**
  - Per swing sul timeframe ENTRY (5m)
  - Identifica micro-swing per pattern di entrata

- **SWING_LR_SL = 2**
  - Per swing sul timeframe SL (15m)
  - Trova swing strutturali per calcolare stop loss

- **BTC_TREND_LR = 2**
  - Per identificare il trend di BTC su 15m
  - Indipendente dagli altri, usato solo per BTC

**Perché LR separati?**
Anche se tutti usano LR=2, sono separati perché operano su timeframe diversi. In futuro potrebbero essere configurati in modo diverso.

---

## 4. BTC CONFLICT FILTER vs BTC REJECTION ZONES

Questi sono **due filtri diversi** che controllano BTC ma con logiche diverse:

### BTC CONFLICT FILTER (Filtro di Conflitto)
```python
BTC_TF = "15m"
BTC_LOOKBACK = 260
BTC_NEAR_PCT = 0.0040        # 0.40%
BTC_REJ_MIN = 2              # almeno 2 rifiuti
BTC_REJ_LOOKBACK = 120       # ~30 ore
BTC_REJ_COOLDOWN = 4         # 4x15m = 1h
```

**Scopo**: Evitare trade quando il prezzo BTC è vicino a zone con rifiuti recenti
- Cerca Order Block (OB) su BTC nelle ultime 260 candele
- Controlla se ci sono stati almeno 2 rifiuti nelle ultime 120 candele
- Se BTC è entro 0.40% da tale zona → SKIP trade

### BTC REJECTION ZONES (Zone di Rifiuto)
```python
BTC_ZONE_TF = "15m"
BTC_ZONE_DAYS = 4
BTC_ZONE_LOOKBACK = 384      # 4 giorni
BTC_ZONE_CLUSTER_PCT = 0.0020    # 0.20%
BTC_ZONE_NEAR_PCT = 0.0040        # 0.40%
BTC_ZONE_MIN_REJ = 2              # minimo 2 rifiuti
BTC_ZONE_REJECT_WINDOW = 8        # 2 ore
BTC_ZONE_REJECT_MOVE_PCT = 0.0150 # 1.50%
BTC_ZONE_BREAK_PCT = 0.0010       # 0.10%
```

**Scopo**: Identificare zone di prezzo dove BTC è stato rifiutato più volte negli ultimi 4 giorni
- Analizza le ultime 384 candele (4 giorni) di BTC
- Trova cluster di swing high/low (entro 0.20%)
- Verifica che ci siano stati almeno 2 rifiuti in quella zona
- Se BTC si avvicina a questa zona (0.40%) → possibile conflitto

**Differenza Chiave**:
- **CONFLICT FILTER**: Cerca Order Block generici con rifiuti recenti (30 ore)
- **REJECTION ZONES**: Identifica zone di prezzo specifiche con rifiuti multipli in un periodo più lungo (4 giorni)
- Entrambi lavorano insieme per evitare trade quando BTC potrebbe influenzare negativamente

---

## 5. Percentuali (PCT) - Diversi Parametri di Prezzo

### Target Profit (TP)
- **TP_GROSS_PCT = 0.0120** (1.20%)
  - Take Profit iniziale lordo
  
- **TP_LADDER_PCTS = [0.0120]**
  - Lista di TP a gradini (per ora solo 1.20%)
  
- **TP_AFTER_LAST_STEP = 0.0025** (0.25%)
  - Incremento TP dopo l'ultimo gradino

### Stop Loss (SL)
- **MIN_STRUCT_SL_PCT = 0.0035** (0.35%)
  - Stop Loss strutturale minimo
  
- **SL_CAP_PCT = 0.0065** (0.65%)
  - CAP massimo per lo Stop Loss
  - Se SL strutturale supera -0.65%, viene forzato a -0.65%
  
- **SL_FIXED_PCT = 0.0100** (1.00%)
  - Stop Loss fisso quando non c'è struttura valida
  
- **STRUCT_SL_BUFFER_PCT = 0.00020** (0.02%)
  - Piccolo margine aggiunto oltre lo swing per SL

### BTC Filter
- **BTC_NEAR_PCT = 0.0040** (0.40%)
  - Distanza per considerare il prezzo "vicino" a una zona BTC
  
- **BTC_ZONE_CLUSTER_PCT = 0.0020** (0.20%)
  - Distanza per raggruppare swing in una "zona"
  
- **BTC_ZONE_NEAR_PCT = 0.0040** (0.40%)
  - Distanza per considerare BTC vicino a zona di rifiuto
  
- **BTC_ZONE_REJECT_MOVE_PCT = 0.0150** (1.50%)
  - Movimento minimo per considerarlo un "rifiuto"
  
- **BTC_ZONE_BREAK_PCT = 0.0010** (0.10%)
  - Rottura minima per considerare una zona "broken"

### Altri
- **SWEEP_BUFFER_PCT = 0.00025** (0.025%)
  - Margine per identificare sweep di liquidity
  
- **FVG_MIN_SIZE_PCT = 0.00010** (0.01%)
  - Dimensione minima Fair Value Gap
  
- **LOCK_RETRACE_PCT = 0.0030** (0.30%)
  - Tolleranza ritracciamento per profit lock
  
- **ROUND_TRIP_FEE_PCT = 0.0020** (0.20%)
  - Fee stimata per calcoli (non usata per ordini reali)

---

## 6. Flusso Logico del Bot

```
1. BIAS_TF (30m) → Determina direzione generale (LONG/SHORT)
   ↓
2. ENTRY_TF (5m) → Trova punto di ingresso preciso
   ↓
3. SL_TF (15m) → Calcola Stop Loss strutturale
   ↓
4. BTC FILTERS → Verifica che BTC non sia in conflitto
   ↓
5. OPEN TRADE → Con TP iniziale 1.20% e SL calcolato
   ↓
6. TP LADDER → TP progressivi con profit lock
```

---

## 7. Stati del Trade

Il bot passa attraverso questi stati:

1. **WAIT_SWEEP** → Aspetta sweep di liquidity
2. **WAIT_DISPLACEMENT** → Aspetta movimento impulsivo
3. **WAIT_RETRACE** → Aspetta ritracciamento in FVG/OB
4. **WAIT_CONFIRM** → Aspetta conferma per entrare
5. **OPEN** → Trade aperto

Ogni stato ha requisiti specifici basati sui timeframe e parametri sopra descritti.

---

## Riepilogo

**Le differenze principali sono**:

1. **Timeframe diversi** (30m, 5m, 15m) = scopi diversi (bias, entry, SL)
2. **LOOKBACK diversi** = profondità storica appropriata per ogni timeframe
3. **SWING_LR separati** = preparati per configurazioni future diverse
4. **Due filtri BTC** = protezione da conflitti sia a breve (30h) che a lungo termine (4 giorni)
5. **Percentuali diverse** = ogni parametro ha il suo scopo specifico (TP, SL, filtri, ecc.)

Ogni parametro è stato scelto per ottimizzare un aspetto specifico della strategia ICT Smart Money.
