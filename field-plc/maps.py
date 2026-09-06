"""Register maps for the two soft-PLCs.

Both speak Modbus/TCP (unit 1). The physics live in simmap; these PLCs serve
the protocol, run a golden control program, and - when the maintenance-mode
coil is set - expose this session's flag across an input-register block.
"""

# --- water treatment + distribution (container port 502) ---------------
WATER = dict(
    coil=dict(INTAKE=0, HIGHLIFT=1, CHLORINE=2, MAIN_VALVE=3, MAINT_MODE=8),
    hr=dict(HIGHLIFT_SP=0, CHLORINE_SP=1,
            TANK_LEVEL=10, MAIN_PRESSURE=11, CHLORINE_RESIDUAL=12, FLOW=13),
    di=dict(LOW_PRESSURE=0, LOW_TANK=1, LOW_CHLORINE=2),
    golden=dict(HIGHLIFT_SP=620, CHLORINE_SP=120),   # 62.0 psi, 1.20 ppm
    sp_clamp=dict(HIGHLIFT_SP=(400, 700), CHLORINE_SP=(60, 250)),
)

# --- power substation bus (container port 503) ------------------------
POWER = dict(
    coil=dict(BRK_MAIN=0, BRK_RES=1, BRK_DT=2, BRK_IND=3, BRK_ST=4,
              GEN_ENABLE=5, MAINT_MODE=8),
    hr=dict(GEN_SP=0, BUS_FREQ=10, BUS_VOLT=11, LOAD=12),
    golden=dict(GEN_SP=80),                           # 8.0 MW
    sp_clamp=dict(GEN_SP=(40, 120)),
)

FLAG_IR_BASE = 100     # input registers FLAG_IR_BASE .. +FLAG_IR_LEN hold the flag
FLAG_IR_LEN = 32       # 64 bytes, plenty for PKTR{...}


def pack_flag(text: str) -> list[int]:
    b = text.encode()[: FLAG_IR_LEN * 2]
    b = b + b"\x00" * (FLAG_IR_LEN * 2 - len(b))
    return [(b[i] << 8) | b[i + 1] for i in range(0, len(b), 2)]


def unpack_flag(regs: list[int]) -> str:
    raw = bytes(x for r in regs for x in ((r >> 8) & 0xFF, r & 0xFF))
    return raw.split(b"\x00", 1)[0].decode(errors="replace")
