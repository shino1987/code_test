# 🚀 ICT Strategy Quick Reference

## Pipeline Overview

```
BIAS (M15) → SWEEP (M15) → DISPLACEMENT (M15) → RETRACE (M15) → CONFIRM (M5) → ENTRY
```

## Step-by-Step Checklist

### ✅ STEP 1: BIAS (M15)
- [ ] Swing highs/lows identificati
- [ ] Liquidità chiara (external high/low)
- [ ] No compressione (range > ATR × 1.2)
- [ ] Output: UP, DOWN, o NONE

### ✅ STEP 2: SWEEP (M15)
- [ ] Wick oltre pool (> ATR × 0.10)
- [ ] Close reclaim (> pool + ATR × 0.02)
- [ ] Wick dominance (≥ 1.2× body)
- [ ] Direzione coerente con BIAS
- [ ] Output: direction, pool, extreme

### ✅ STEP 3: DISPLACEMENT (M15)
- [ ] BOS: close > swing_high + ATR × 0.02 (o sotto per DOWN)
- [ ] Impulse: range ≥ ATR × 0.80
- [ ] Body dominance: body ≥ range × 0.55
- [ ] FVG detection (opzionale per Grade A)
- [ ] Output: dir, bos_level, fvg, grade

### ✅ STEP 4: RETRACE (M15)
- [ ] Zona definita (FVG o 50-79% range)
- [ ] Hit detection (wick tocca zona)
- [ ] No timeout (< 8 bars)
- [ ] No invalidation (close non oltre range ± ATR × 0.05)
- [ ] Depth 0.50-0.79 per Grade A
- [ ] Output: zone, depth, grade

### ✅ STEP 5: CONFIRM (M5)
- [ ] Context gate (prezzo vicino zona ± ATR_M5 × 0.25)
- [ ] Micro BOS M5: close > swing_high_m5 + ATR_M5 × 0.02
- [ ] Impulse M5: range ≥ ATR_M5 × 0.60
- [ ] Body: body ≥ range × 0.50
- [ ] No timeout (< 12 bars M5)
- [ ] Mini FVG opzionale per Grade A
- [ ] Output: dir, micro_bos_level, grade

### 🎯 ENTRY
- [ ] Tutti i 5 step completati
- [ ] Direzioni tutte coerenti (UP o DOWN)
- [ ] Grades idealmente A o B per tutti gli step

## Configuration Values

```python
# BIAS
SWING_LEFT_RIGHT = 2
ATR_PERIOD = 14
COMPRESSION_THRESHOLD = 1.2

# SWEEP
SWEEP_MIN_DIST_MULT = 0.10
SWEEP_RECLAIM_MULT = 0.02
SWEEP_WICK_RATIO = 1.2

# DISPLACEMENT
DISPLACEMENT_BOS_BUFFER = 0.02
DISPLACEMENT_IMPULSE_MULT = 0.80
DISPLACEMENT_BODY_RATIO = 0.55

# RETRACE
MAX_RETRACE_BARS = 8
RETRACE_INVALIDATION_MULT = 0.05
RETRACE_ZONE_MIN = 0.50
RETRACE_ZONE_MAX = 0.79

# CONFIRMATION
MAX_CONFIRM_BARS = 12
CONFIRM_ZONE_BUFFER = 0.25
CONFIRM_BOS_BUFFER = 0.02
CONFIRM_IMPULSE_MULT = 0.60
CONFIRM_BODY_RATIO = 0.50
```

## Grading System

| Grade | Criteria | Quality |
|-------|----------|---------|
| **A** | Setup + FVG coerente | Massima |
| **B** | Setup senza FVG | Buona |
| **NONE** | Setup non valido | - |

## Timeframes

| Timeframe | Usage | Analysis |
|-----------|-------|----------|
| **M15 (HTF)** | Setup principale | BIAS, SWEEP, DISPLACEMENT, RETRACE |
| **M5 (LTF)** | Confirmation | Micro BOS, Mini FVG |

## Status Codes

| Status | Meaning | Action |
|--------|---------|--------|
| **CONFIRMED** | Setup valido | Procedi |
| **HIT** | Zona toccata | Procedi |
| **WAIT** | In attesa | Monitora |
| **EXPIRED** | Timeout | Reset |
| **INVALIDATED** | Rotto | Reset |

## Entry Requirements

**LONG Entry:**
```
BIAS = UP
+ SWEEP detected
+ DISPLACEMENT UP (Grade A/B)
+ RETRACE HIT (Grade A/B)
+ CONFIRM UP (Grade A/B)
= LONG SIGNAL 🎯
```

**SHORT Entry:**
```
BIAS = DOWN
+ SWEEP detected
+ DISPLACEMENT DOWN (Grade A/B)
+ RETRACE HIT (Grade A/B)
+ CONFIRM DOWN (Grade A/B)
= SHORT SIGNAL 🎯
```

## Common Scenarios

### ✅ Perfect Setup (All Grade A)
```
✅ BIAS: UP
✅ SWEEP: Detected
✅ DISPLACEMENT: Grade A (with FVG)
✅ RETRACE: Grade A (depth 0.65)
✅ CONFIRMATION: Grade A (with mini FVG)
→ VERY HIGH PROBABILITY SETUP
```

### ✅ Good Setup (Mixed Grades)
```
✅ BIAS: UP
✅ SWEEP: Detected
✅ DISPLACEMENT: Grade B (no FVG)
✅ RETRACE: Grade A (depth 0.70)
✅ CONFIRMATION: Grade B (no mini FVG)
→ GOOD PROBABILITY SETUP
```

### ❌ Invalid Setup (Missing Components)
```
✅ BIAS: UP
✅ SWEEP: Detected
❌ DISPLACEMENT: NONE
→ NO ENTRY (incomplete setup)
```

### ❌ Invalid Setup (Timeout)
```
✅ BIAS: UP
✅ SWEEP: Detected
✅ DISPLACEMENT: Grade A
⏱️ RETRACE: EXPIRED (> 8 bars)
→ NO ENTRY (setup too old)
```

## Troubleshooting

### No Entry Signals?
1. Check BIAS is not NONE
2. Verify all 5 steps are aligned
3. Ensure directions are coherent
4. Check timeouts haven't expired
5. Verify price is in context (near zones)

### Too Many False Signals?
1. Require Grade A on all steps
2. Increase ATR multipliers
3. Add stricter body dominance
4. Reduce timeout windows

### Missing Good Setups?
1. Reduce ATR multipliers
2. Allow Grade B setups
3. Increase timeout windows
4. Relax body dominance

## Performance Tips

1. **Wait for complete setup** - Don't enter prematurely
2. **Respect grades** - Grade A setups have higher probability
3. **Monitor timeouts** - Fresh setups are better
4. **Check context** - Confirmation must be near retrace zone
5. **Validate direction** - All steps must align

## Quick Diagnostics

```bash
# Check if bot is running
ps aux | grep paper_trading_bot

# View real-time logs
tail -f paper_trades.csv

# Check syntax
python3 -m py_compile paper_trading_bot.py

# Run test
python3 -c "import paper_trading_bot; print('OK')"
```

---

**Remember:** Entry ONLY when ALL 5 steps are complete and aligned! 🎯
