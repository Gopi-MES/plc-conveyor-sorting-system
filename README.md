# PLC-Based Automated Conveyor Sorting System

Final-year B.E. project: a **PLC-controlled conveyor** that detects parts and sorts them automatically. An inductive proximity sensor classifies each part as metal or non-metal, and a pneumatic diverter pushes metal parts into Bin A while non-metal parts continue to Bin B.

This repo contains the control logic in **IEC 61131-3 Structured Text**, the matching **ladder diagram**, and a **Python scan-cycle simulator** so the logic can be tested without hardware.

```
  Infeed PE        Inductive Prox        Diverter PE + Solenoid
     │                  │                        │
 ════╪══════════════════╪════════════════════════╪═══════════════► Bin B (non-metal)
     ▼                  ▼                        ▼
  count part       metal? track it        metal part arrives → push ──► Bin A (metal)
```

## I/O map

| Address | Tag | Device |
|---|---|---|
| I0.0 | PB_Start | Start push button (NO) |
| I0.1 | PB_Stop | Stop push button (NC) |
| I0.2 | ES_Ok | Emergency stop (NC) |
| I0.3 | Guard_Closed | Guard door safety switch |
| I0.4 | PE_Entry | IR photo-eye at infeed |
| I0.5 | PX_Metal | Inductive proximity sensor |
| I0.6 | PE_Diverter | IR photo-eye at diverter |
| I0.7 | PB_Reset | Fault reset |
| Q0.0 | Q_Motor | Conveyor motor contactor |
| Q0.1 | Q_Diverter | Diverter solenoid valve |
| Q0.2 / Q0.3 | Q_LampRun / Q_LampFault | Stack light green / red |

## Control logic

1. **Start/stop seal-in** with E-stop, guard-door and fault interlocks
2. **Jam detection:** infeed photo-eye blocked for more than 3 s latches a fault and stops the motor
3. **Fault reset** is only accepted once the jam is cleared
4. **Counting and tracking:** rising-edge counters for total and metal parts, plus a pending-metal FIFO count
5. **Diverter:** a 200 ms pulse fires when a tracked metal part reaches the diverter eye
6. **E-stop** drops all outputs and clears tracking so nothing fires on restart

Files:

- `conveyor_sorting.st`: Structured Text program
- `ladder_logic.md`: the same logic as ladder rungs
- `plc_sim.py`: scan-cycle simulator (TON, TP and R_TRIG implemented in Python) plus a belt simulation
- `test_plc_sim.py`: interlock, jam/reset and sorting tests

## Run the simulation

```bash
python plc_sim.py
# Parts in: 12 | metal detected: 6 | Bin A (metal): 6 | Bin B (non-metal): 6

pip install pytest && pytest -q
```

## Tech

PLC programming · Ladder logic · IEC 61131-3 Structured Text · Sensors (IR photo-eye, inductive proximity) · Pneumatics · Safety interlocks · HMI status lamps · Python
