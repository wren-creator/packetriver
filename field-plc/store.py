"""Shared Modbus datastores for the water and power soft-PLCs.

Two independent slave contexts (unit 1 each), one per plant, each guarded by
its own lock. run.py serves them and runs the scan loop; hmi.py reads them for
the operator screen.
"""
import threading

from pymodbus.datastore import (
    ModbusSequentialDataBlock,
    ModbusServerContext,
    ModbusSlaveContext,
)


def _ctx():
    slave = ModbusSlaveContext(
        di=ModbusSequentialDataBlock(0, [0] * 64),
        co=ModbusSequentialDataBlock(0, [0] * 64),
        hr=ModbusSequentialDataBlock(0, [0] * 64),
        ir=ModbusSequentialDataBlock(0, [0] * 160),
        zero_mode=True,
    )
    return ModbusServerContext(slaves={1: slave}, single=False), threading.Lock()


WCTX, WLOCK = _ctx()
PCTX, PLOCK = _ctx()


def rd(ctx, lock, fc, addr, count=1):
    with lock:
        return ctx[1].getValues(fc, addr, count=count)


def wr(ctx, lock, fc, addr, values):
    with lock:
        ctx[1].setValues(fc, addr, values)
