(*
  PLC-Based Automated Conveyor Sorting System
  IEC 61131-3 Structured Text (equivalent to the ladder rungs in ladder_logic.md)

  Parts enter on a conveyor, pass an inductive proximity sensor (metal / non-metal)
  and an IR photo-eye at the diverter. Metal parts are pushed off by a pneumatic
  diverter into Bin A; non-metal parts continue to Bin B.
*)

PROGRAM ConveyorSorting
VAR_INPUT
    PB_Start      : BOOL;  (* I0.0  Start push button, NO          *)
    PB_Stop       : BOOL;  (* I0.1  Stop push button, NC (TRUE=OK) *)
    ES_Ok         : BOOL;  (* I0.2  Emergency stop, NC (TRUE=OK)   *)
    Guard_Closed  : BOOL;  (* I0.3  Guard door switch              *)
    PE_Entry      : BOOL;  (* I0.4  IR photo-eye at infeed         *)
    PX_Metal      : BOOL;  (* I0.5  Inductive proximity (metal)    *)
    PE_Diverter   : BOOL;  (* I0.6  IR photo-eye at diverter       *)
    PB_Reset      : BOOL;  (* I0.7  Fault reset push button        *)
END_VAR
VAR_OUTPUT
    Q_Motor       : BOOL;  (* Q0.0  Conveyor motor contactor *)
    Q_Diverter    : BOOL;  (* Q0.1  Diverter solenoid valve  *)
    Q_LampRun     : BOOL;  (* Q0.2  Green lamp               *)
    Q_LampFault   : BOOL;  (* Q0.3  Red lamp                 *)
END_VAR
VAR
    Run           : BOOL;
    Fault_Jam     : BOOL;
    Metal_Pending : INT := 0;    (* metal parts between sensor and diverter *)
    Count_Total   : INT := 0;
    Count_Metal   : INT := 0;
    Count_NonMetal: INT := 0;
    T_Jam         : TON;         (* entry photo-eye blocked too long *)
    T_Divert      : TP;          (* diverter pulse *)
    R_Entry       : R_TRIG;
    R_Metal       : R_TRIG;
    R_Diverter    : R_TRIG;
END_VAR

(* Rung 1: safety interlocks + start/stop seal-in *)
Run := (PB_Start OR Run) AND PB_Stop AND ES_Ok AND Guard_Closed AND NOT Fault_Jam;

(* Rung 2: jam detection - infeed photo-eye blocked > 3 s while running *)
T_Jam(IN := Run AND PE_Entry, PT := T#3S);
IF T_Jam.Q THEN
    Fault_Jam := TRUE;
END_IF;

(* Rung 3: fault reset only when the jam is cleared *)
IF PB_Reset AND NOT PE_Entry THEN
    Fault_Jam := FALSE;
END_IF;

(* Rung 4: count parts and track metal parts (FIFO count) *)
R_Entry(CLK := PE_Entry AND Run);
IF R_Entry.Q THEN
    Count_Total := Count_Total + 1;
END_IF;

R_Metal(CLK := PX_Metal AND Run);
IF R_Metal.Q THEN
    Metal_Pending := Metal_Pending + 1;
    Count_Metal := Count_Metal + 1;
END_IF;

(* Rung 5: fire diverter when a tracked metal part reaches the diverter eye *)
R_Diverter(CLK := PE_Diverter AND Run);
T_Divert(IN := R_Diverter.Q AND Metal_Pending > 0, PT := T#200MS);
IF R_Diverter.Q THEN
    IF Metal_Pending > 0 THEN
        Metal_Pending := Metal_Pending - 1;
    ELSE
        Count_NonMetal := Count_NonMetal + 1;
    END_IF;
END_IF;

(* Rung 6: outputs *)
Q_Motor     := Run;
Q_Diverter  := T_Divert.Q AND ES_Ok;
Q_LampRun   := Run;
Q_LampFault := Fault_Jam OR NOT ES_Ok;

(* E-stop clears tracking so no diverter fires on restart *)
IF NOT ES_Ok THEN
    Metal_Pending := 0;
END_IF;

END_PROGRAM
