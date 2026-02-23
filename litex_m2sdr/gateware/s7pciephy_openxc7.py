#
# This file is part of LiteX-M2SDR.
#
# Copyright (c) 2024-2026 Enjoy-Digital <enjoy-digital.fr>
# SPDX-License-Identifier: BSD-2-Clause

import os

from litepcie.phy.s7pciephy import S7PCIEPHY

# S7PCIEPHYOpenXC7 ---------------------------------------------------------------------------------

class S7PCIEPHYOpenXC7(S7PCIEPHY):
    """S7PCIEPHY variant for openXC7 (yosys+nextpnr) toolchain.

    Uses regymm/pcie_7x open-source PCIe endpoint instead of Vivado IP generation.
    Overrides add_sources() to provide pcie_7x Verilog files and add_gt_loc_constraints()
    as a no-op (nextpnr uses chipdb for placement). Raises NotImplementedError for
    use_external_qpll() since pcie_7x manages its own GTPE2_COMMON.
    """

    def __init__(self, platform, pads, *args, **kwargs):
        # pcie_7x only supports x1 lane.
        nlanes = len(pads.tx_p)
        if nlanes != 1:
            raise NotImplementedError(f"openXC7 PCIe only supports x1 (got x{nlanes}).")

        # PTM requires Vivado IP.
        if kwargs.get("with_ptm", False):
            raise NotImplementedError("PCIe PTM requires Vivado toolchain.")

        super().__init__(platform, pads, *args, **kwargs)

        # Add Verilog parameters for pcie_7x configuration.
        # These are passed through litepcie_pcie_s7.v -> pcie_7x.v.
        self.pcie_phy_params.update(
            p_BAR0                    = self.bar0_mask,
            p_CLASS_CODE              = 0x0D_10_00,  # Wireless/RF controller.
            p_CFG_DEV_ID              = 0x7021,       # 7020 + nlanes.
            p_CFG_VEND_ID             = 0x10EE,       # Xilinx vendor ID.
            p_LINK_CAP_MAX_LINK_SPEED = 2,            # Gen2 (5.0 GT/s).
            p_USER_CLK_FREQ           = 2,            # 125 MHz user clock.
        )

    def add_sources(self, platform, phy_path, phy_filename=None, user_config=None):
        pcie_7x_path = os.path.join(
            os.path.abspath(os.path.dirname(__file__)),
            "pcie_7x", "src",
        )
        platform.add_source(os.path.join(pcie_7x_path, "pcie_7x.v"))
        platform.add_source(os.path.join(pcie_7x_path, "pcie_block.v"))
        platform.add_source(os.path.join(pcie_7x_path, "pcie_brams.v"))
        platform.add_source(os.path.join(pcie_7x_path, "pcie_axi_tx.v"))
        platform.add_source(os.path.join(pcie_7x_path, "pcie_axi_rx.v"))
        platform.add_source(os.path.join(pcie_7x_path, "pcie_tx_thrtl_ctl.v"))
        platform.add_source(os.path.join(pcie_7x_path, "pipe_clock.v"))
        platform.add_source(os.path.join(pcie_7x_path, "pipe_wrapper.v"))
        platform.add_source(os.path.join(pcie_7x_path, "xilinx_pcie_mmcm.v"))
        platform.add_source(os.path.join(pcie_7x_path, "litepcie_pcie_s7.v"))

    def add_gt_loc_constraints(self, locs, gt_type=None, by_pipe_lane=True):
        # No-op: nextpnr uses chipdb for GT placement.
        pass

    def use_external_qpll(self, qpll_channel):
        raise NotImplementedError("openXC7 PCIe uses pcie_7x's internal GTPE2_COMMON.")
