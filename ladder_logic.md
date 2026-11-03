# Ladder Logic

The same logic as `conveyor_sorting.st`, written as ladder rungs.

```
Rung 1: Start / Stop seal-in with interlocks
   I0.0 Start      I0.1 Stop   I0.2 E-Stop  I0.3 Guard   M_Fault
 ──┤ ├───┬────────┤ ├────────┤ ├────────┤ ├────────┤/├──────────( M_Run )──
         │
   M_Run │
 ──┤ ├───┘

Rung 2: Jam detection timer
   M_Run     I0.4 Entry PE
 ──┤ ├───────┤ ├──────────────────────[ TON T_Jam  PT=3s ]──

Rung 3: Latch jam fault
   T_Jam.DN
 ──┤ ├───────────────────────────────────────────────(S M_Fault )──

Rung 4: Reset fault (only when infeed is clear)
   I0.7 Reset   I0.4 Entry PE
 ──┤ ├──────────┤/├──────────────────────────────────(R M_Fault )──

Rung 5: Part counter
   M_Run     I0.4 Entry PE
 ──┤ ├───────┤P├────────────────────────[ ADD Count_Total +1 ]──

Rung 6: Metal detected -> track it
   M_Run     I0.5 Prox
 ──┤ ├───────┤P├────────────────────────[ ADD Metal_Pending +1 ]──
                                        [ ADD Count_Metal  +1 ]──

Rung 7: Diverter pulse when a tracked metal part arrives
   M_Run     I0.6 Div PE   Metal_Pending>0
 ──┤ ├───────┤P├───────────[ > ]────────[ TP T_Div PT=200ms ]──
                                        [ SUB Metal_Pending -1 ]──

Rung 8: Outputs
   M_Run                                              ( Q0.0 Motor )──
   T_Div.Q      I0.2 E-Stop                           ( Q0.1 Diverter )──
   M_Run                                              ( Q0.2 Green lamp )──
   M_Fault ──┬──                                      ( Q0.3 Red lamp )──
   I0.2 /    ┘
```

`┤ ├` = normally open contact, `┤/├` = normally closed contact, `┤P├` = rising edge
