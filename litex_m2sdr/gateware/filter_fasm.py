#!/usr/bin/env python3
#
# This file is part of LiteX-M2SDR.
#
# Copyright (c) 2024-2026 Enjoy-Digital <enjoy-digital.fr>
# SPDX-License-Identifier: BSD-2-Clause

"""Filter FASM for openXC7 toolchain compatibility.

Handles mismatches between nextpnr-xilinx FASM output and prjxray database:
- Strips IBUFDS_GTE2 tile features (not in prjxray tilegrid).
- Renames PCIE_2_1 site to PCIE (nextpnr uses primitive name, prjxray uses short name).
- Strips PCIE features not found in segbits database.
"""

import os
import sys

def load_segbits_keys(db_root, tile_type):
    """Load known feature keys from a segbits database file."""
    keys = set()
    path = os.path.join(db_root, f"segbits_{tile_type.lower()}.db")
    if not os.path.exists(path):
        return keys
    with open(path) as f:
        for line in f:
            parts = line.split()
            if parts:
                keys.add(parts[0].split("[")[0])
    return keys

def filter_fasm(fasm_path, db_root):
    pcie_keys = load_segbits_keys(db_root, "pcie_bot")

    with open(fasm_path) as f:
        lines = f.readlines()

    with open(fasm_path, "w") as f:
        for line in lines:
            stripped = line.strip()

            # Strip IBUFDS_GTE2 pseudo-tile (not in prjxray tilegrid).
            if stripped.startswith("IBUFDS_GTE2_"):
                continue

            # Rename PCIE_2_1 -> PCIE and filter unknown features.
            if ".PCIE_2_1." in stripped:
                renamed = stripped.replace(".PCIE_2_1.", ".PCIE.")
                # Extract tile type and feature for database lookup.
                parts = renamed.split(".")
                tile_type = "_".join(parts[0].split("_")[:-1])  # PCIE_BOT_X67Y219 -> PCIE_BOT
                feature = ".".join(parts[1:]).split("[")[0].split(" ")[0]
                db_key = f"{tile_type}.{feature}"
                if db_key not in pcie_keys:
                    continue
                f.write(renamed + "\n")
            else:
                f.write(line)

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print(f"Usage: {sys.argv[0]} <fasm_file> <db_root>", file=sys.stderr)
        sys.exit(1)
    filter_fasm(sys.argv[1], sys.argv[2])
