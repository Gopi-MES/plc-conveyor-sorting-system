from plc_sim import ConveyorPLC, Inputs, demo


def start(plc):
    i = Inputs(pb_start=True)
    plc.scan(i)
    i.pb_start = False
    return i


def test_seal_in_and_stop():
    plc = ConveyorPLC()
    i = start(plc)
    assert plc.scan(i).motor            # sealed in after releasing Start
    i.pb_stop = False
    assert not plc.scan(i).motor


def test_estop_and_guard_interlocks():
    plc = ConveyorPLC()
    i = start(plc)
    i.es_ok = False
    o = plc.scan(i)
    assert not o.motor and o.lamp_fault
    plc2 = ConveyorPLC()
    i2 = Inputs(pb_start=True, guard_closed=False)
    assert not plc2.scan(i2).motor


def test_jam_fault_and_reset():
    plc = ConveyorPLC()
    i = start(plc)
    i.pe_entry = True
    for _ in range(310):                # > 3 s at 10 ms scans
        plc.scan(i)
    assert plc.fault_jam and not plc.out.motor
    i.pb_reset = True
    plc.scan(i)
    assert plc.fault_jam                # can't reset while still blocked
    i.pe_entry = False
    plc.scan(i)
    assert not plc.fault_jam


def test_sorting_matches_detection():
    plc, bin_a, bin_b = demo(parts=20)
    assert bin_a == plc.count_metal
    assert bin_a + bin_b == plc.count_total == 20
