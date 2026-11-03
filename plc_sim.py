"""Scan-cycle simulator for the conveyor sorting PLC program.

Mirrors conveyor_sorting.st so the logic can be tested without hardware:
each call to scan() = one PLC scan (read inputs -> execute logic -> write outputs).
Run `python plc_sim.py` for a console demo of the conveyor moving parts.
"""
import random
from dataclasses import dataclass, field


class RTrig:
    def __init__(self):
        self.prev = False

    def __call__(self, clk):
        q = clk and not self.prev
        self.prev = clk
        return q


class TON:
    """On-delay timer."""
    def __init__(self, pt_ms):
        self.pt, self.et, self.q = pt_ms, 0, False

    def __call__(self, inp, dt_ms):
        self.et = min(self.et + dt_ms, self.pt) if inp else 0
        self.q = inp and self.et >= self.pt
        return self.q


class TP:
    """Pulse timer."""
    def __init__(self, pt_ms):
        self.pt, self.et, self.q = pt_ms, 0, False

    def __call__(self, trig, dt_ms):
        if trig and not self.q:
            self.q, self.et = True, 0
        elif self.q:
            self.et += dt_ms
            if self.et >= self.pt:
                self.q = False
        return self.q


@dataclass
class Inputs:
    pb_start: bool = False
    pb_stop: bool = True        # NC
    es_ok: bool = True          # NC
    guard_closed: bool = True
    pe_entry: bool = False
    px_metal: bool = False
    pe_diverter: bool = False
    pb_reset: bool = False


@dataclass
class Outputs:
    motor: bool = False
    diverter: bool = False
    lamp_run: bool = False
    lamp_fault: bool = False


@dataclass
class ConveyorPLC:
    scan_ms: int = 10
    run: bool = False
    fault_jam: bool = False
    metal_pending: int = 0
    count_total: int = 0
    count_metal: int = 0
    count_nonmetal: int = 0
    out: Outputs = field(default_factory=Outputs)

    def __post_init__(self):
        self.t_jam, self.t_div = TON(3000), TP(200)
        self.r_entry, self.r_metal, self.r_div = RTrig(), RTrig(), RTrig()

    def scan(self, i: Inputs) -> Outputs:
        # Rung 1
        self.run = (i.pb_start or self.run) and i.pb_stop and i.es_ok and i.guard_closed and not self.fault_jam
        # Rung 2-3
        if self.t_jam(self.run and i.pe_entry, self.scan_ms):
            self.fault_jam = True
        if i.pb_reset and not i.pe_entry:
            self.fault_jam = False
        # Rung 4
        if self.r_entry(i.pe_entry and self.run):
            self.count_total += 1
        if self.r_metal(i.px_metal and self.run):
            self.metal_pending += 1
            self.count_metal += 1
        # Rung 5
        div_edge = self.r_div(i.pe_diverter and self.run)
        self.t_div(div_edge and self.metal_pending > 0, self.scan_ms)
        if div_edge:
            if self.metal_pending > 0:
                self.metal_pending -= 1
            else:
                self.count_nonmetal += 1
        # Rung 6
        self.out = Outputs(motor=self.run, diverter=self.t_div.q and i.es_ok,
                           lamp_run=self.run, lamp_fault=self.fault_jam or not i.es_ok)
        if not i.es_ok:
            self.metal_pending = 0
        return self.out


def demo(parts=12, seed=3):
    """Simulate parts travelling down the belt: entry(0) -> prox(20) -> diverter(40)."""
    rng = random.Random(seed)
    plc, i = ConveyorPLC(), Inputs()
    i.pb_start = True; plc.scan(i); i.pb_start = False
    belt = []                      # [position, is_metal]
    bin_a = bin_b = 0
    for t in range(parts * 30 + 60):
        if t % 30 == 0 and t // 30 < parts:
            belt.append([0, rng.random() < 0.4])
        i.pe_entry = any(p[0] in (0, 1, 2) for p in belt)
        i.px_metal = any(p[0] == 20 and p[1] for p in belt)
        i.pe_diverter = any(p[0] == 40 for p in belt)
        o = plc.scan(i)
        for p in belt:
            if p[0] == 40 and o.diverter:
                p[0] = -1; bin_a += 1
        if o.motor:
            for p in belt:
                if p[0] >= 0:
                    p[0] += 1
        for p in belt:
            if p[0] > 60:
                p[0] = -1; bin_b += 1
        belt = [p for p in belt if p[0] >= 0]
    print(f"Parts in: {plc.count_total} | metal detected: {plc.count_metal} | "
          f"Bin A (metal): {bin_a} | Bin B (non-metal): {bin_b}")
    return plc, bin_a, bin_b


if __name__ == "__main__":
    demo()
