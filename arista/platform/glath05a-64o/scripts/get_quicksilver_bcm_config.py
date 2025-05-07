#!/bin/env python3
# Copyright (c) 2025 Arista Networks, Inc.  All rights reserved.
# Arista Networks, Inc. Confidential and Proprietary.
 
import pandas as pd

def generate_list_of_pairs(n: int) -> list[list[int]]:
    result = []
    for i in range(1, n + 1):
        result.append([i, i])
    return result


def main():
    static_df   = pd.read_csv("quicksilver_static_mapping.csv")
    port_map_df = pd.read_csv("quicksilver_port_profile_mapping.csv")

    lanes = (
        static_df[ static_df["A_CHIP_TYPE"] == "NPU" ]
        .drop_duplicates(subset=["A_CORE_ID", "A_CORE_LANE"])
        .sort_values(["A_CORE_ID", "A_CORE_LANE"])
        .reset_index(drop=True)
    )

    lanes["PC_PM_ID"] = lanes['A_CORE_ID'] + 1
    lanes["CORE_INDEX"] = 0

    def build_lane_map(coreGroup, col):
        # For lanes 7 to 0, take the physical lane and encode as a single hex digit
        sortedGroup = coreGroup.sort_values('A_CORE_LANE', ascending=False)
        return "0x" + "".join(
            f"{(val-sortedGroup['A_CORE_ID'][val]*8):X}"
            for val in sortedGroup[col]
        )

    pm_entries = []
    # Process lane mapping and polarity flips for PC_PM_CORE section
    for pm_id, grp in lanes.groupby("PC_PM_ID"):
        if pm_id > 64: continue
        rx_map = build_lane_map(grp, "A_PHYSICAL_RX_LANE")
        tx_map = build_lane_map(grp, "A_PHYSICAL_TX_LANE")

        # Build polarity bitmasks based on physical lane positions
        rx_bits = 0
        tx_bits = 0

        for _, row in grp.iterrows():
            thisLane = int(row["A_CORE_LANE"])
            if str(row["A_RX_POLARITY_SWAP"]).strip().upper() == "Y":
                rx_bits |= (1 << thisLane)
            if str(row["A_TX_POLARITY_SWAP"]).strip().upper() == "Y":
                tx_bits |= (1 << thisLane)

        pm_entries.append({
            "PC_PM_ID":              pm_id,
            "CORE_INDEX":            0,
            "RX_LANE_MAP":           rx_map,
            "RX_LANE_MAP_AUTO":      0,
            "TX_LANE_MAP":           tx_map,
            "TX_LANE_MAP_AUTO":      0,
            "RX_POLARITY_FLIP":      f"0x{rx_bits:02X}",
            "RX_POLARITY_FLIP_AUTO": 0,
            "TX_POLARITY_FLIP":      f"0x{tx_bits:02X}",
            "TX_POLARITY_FLIP_AUTO": 0,
        })

    # Prepare PC_PORT_PHYS_MAP in the exact CSV order
    lane_to_phys = {}
    for _, r in lanes.iterrows():
        pm  = int(r["PC_PM_ID"])
        lane = int(r["A_CORE_LANE"])
        # physical port index within the chip:
        lane_to_phys[(r["A_CORE_ID"], lane)] = (pm - 1) * 8 + (lane + 1)


    phys_map = {}
    for _, port in port_map_df.iterrows():
        port_id = int(port["Global_PortID"])
        parts = port["Port_Name"].split("/")  # e.g. "eth1/2/1"
        if len(parts) != 3:
            continue

        z_chip = int(parts[1]) - 0
        z_lane = int(parts[2]) - 1

        # Find matching static row
        match = static_df[
            (static_df["A_CORE_ID"] == z_chip) &
            (static_df["Z_CORE_LANE"] == z_lane)
        ]
        if len(match) != 1:
            continue

        a_core = int(match["A_CORE_ID"].iloc[0])
        a_lane = int(match["A_CORE_LANE"].iloc[0])
        # one-based physical port ID
        phys_id = a_core * 8 + a_lane + 1

        print(f"{match['A_CORE_ID']}      a_core: {a_core}")
        print(f"port_id ({port_id}): phys_id ({phys_id})  ({a_core} + {a_lane})   zchip({z_chip})  z_lane({z_lane})")

        phys_map[port_id] = phys_id


    # Write out the YAML exactly as you provided
    out = "generated_quicksilver_config.yaml"
    with open(out, "w") as f:
        f.write("---\n")
        f.write("device:\n")
        f.write("  0:\n")
        f.write("    PC_PM_CORE:\n")
        for e in pm_entries:
            f.write("      ?\n")
            f.write(f"       PC_PM_ID: {e['PC_PM_ID']}\n")
            f.write(f"       CORE_INDEX: {e['CORE_INDEX']}\n")
            f.write("      :\n")
            f.write(f"       RX_LANE_MAP_AUTO: {e['RX_LANE_MAP_AUTO']}\n")
            f.write(f"       TX_LANE_MAP_AUTO: {e['TX_LANE_MAP_AUTO']}\n")
            f.write(f"       RX_POLARITY_FLIP_AUTO: {e['RX_POLARITY_FLIP_AUTO']}\n")
            f.write(f"       TX_POLARITY_FLIP_AUTO: {e['TX_POLARITY_FLIP_AUTO']}\n")
            f.write(f"       RX_LANE_MAP: {e['RX_LANE_MAP']}\n")
            f.write(f"       TX_LANE_MAP: {e['TX_LANE_MAP']}\n")
            f.write(f"       RX_POLARITY_FLIP: {e['RX_POLARITY_FLIP']}\n")
            f.write(f"       TX_POLARITY_FLIP: {e['TX_POLARITY_FLIP']}\n")
            
        f.write("...\n")
        f.write("---\n")
        f.write("device:\n")
        f.write("  0:\n")
        f.write("    PC_PORT_PHYS_MAP:\n")
        for port_id, phys_id in sorted(phys_map.items()):
            f.write("      ?\n")
            f.write(f"       PORT_ID: {port_id}\n")
            f.write("      :\n")
            f.write(f"       PC_PHYS_PORT_ID: {phys_id}\n")


        f.write("...\n")
        f.write("---\n")
        f.write("device:\n")
        f.write("  0:\n")
        f.write("    PC_PORT:\n")
        f.write("      ?\n")
        f.write(f"       PORT_ID: {generate_list_of_pairs(512)}\n")
        f.write("      :\n")
        f.write("        ENABLE: 0\n")
        f.write("        SPEED: 100000\n")
        f.write("        NUM_LANES: 1\n")
        f.write("        FEC_MODE: PC_FEC_RS544_2XN\n")
        f.write("        MAX_FRAME_SIZE: 9416\n")



        f.write("...\n")
        f.write("---\n")
        f.write("device:\n")
        f.write("  0:\n")
        f.write("    PORT_CONFIG:\n")
        f.write("      PORT_SYSTEM_PROFILE_OPERMODE_PIPEUNIQUE: 1\n")


        f.write("...\n")
        f.write("---\n")
        f.write("bcm_device:\n")
        f.write("  0:\n")
        f.write("    global:\n")
        f.write("      l3_alpm_template: 1\n")
        f.write("      l3_alpm_hit_mode: 1\n")
        f.write("      ipv6_lpm_128b_enable: 1\n")
        f.write("      pktio_driver_type: 1\n")
        f.write("      qos_map_multi_get_mode: 1\n")
        f.write("      rx_cosq_mapping_management_mode: 0\n")
        f.write("      l3_iif_reservation_skip: 0\n")
        f.write("      pcie_host_intf_timeout_purge_enable: 0\n")
        f.write("      macro_flow_hash_shuffle_random_seed: 34345645\n")
        f.write("      bcm_linkscan_interval: 25000\n")
        f.write("      sai_common_hash_crc: 0x1\n")
        f.write("      sai_disable_srcmacqedstmac_ctrl: 0x1\n")
        f.write("      sai_acl_qset_optimization: 0x1\n")
        f.write("      sai_optimized_mmu: 0x1\n")
        f.write("      sai_pkt_rx_custom_cfg: 1\n")
        f.write("      sai_pkt_rx_pkt_size: 16512\n")
        f.write("      sai_pkt_rx_cfg_ppc: 16\n")
        f.write("      sai_async_fdb_nbr_enable: 0x1\n")
        f.write("      sai_pfc_defaults_disable: 0x1\n")
        f.write("      sai_ifp_enable_on_cpu_tx: 0x1\n")
        f.write("      sai_vfp_smac_drop_filter_disable: 1\n")
        f.write("      sai_macro_flow_based_hash: 1\n")
        f.write("      sai_mmu_qgroups_default: 1\n")
        f.write("      sai_dis_ctr_incr_on_port_ln_dn: 0\n")
        f.write("      custom_feature_mesh_topology_sync_mode: 1\n")
        f.write("      sai_ecmp_group_members_increment: 1\n")
        f.write("      sai_field_group_auto_prioritize: 1\n")
        f.write("      bcm_tunnel_term_compatible_mode: 1\n")
        f.write("      sai_l2_cpu_fdb_event_suppress: 1\n")
        f.write("      sai_port_phy_time_sync_en: 1\n")
        f.write("      sai_stats_support_mask: 0x2\n")
        f.write("      sai_disable_internal_port_serdes: 1\n")
        f.write("      global_flexctr_ing_action_num_reserved: 20\n")
        f.write("      global_flexctr_ing_pool_num_reserved: 8\n")
        f.write("      global_flexctr_ing_op_profile_num_reserved: 20\n")
        f.write("      global_flexctr_ing_group_num_reserved: 2\n")
        f.write("      global_flexctr_egr_action_num_reserved: 8\n")
        f.write("      global_flexctr_egr_pool_num_reserved: 5\n")
        f.write("      global_flexctr_egr_op_profile_num_reserved: 10\n")
        f.write("      global_flexctr_egr_group_num_reserved: 1\n")
        f.write("      sai_uncached_port_stats: 0x1\n")
        f.write("      ecmp_dlb_port_speeds: 1\n")
        f.write("      l3_ecmp_member_secondary_mem_size: 4096\n")

        f.write("...\n")
        f.write("---\n")
        f.write("device:\n")
        f.write("  0:\n")
        f.write("    TM_THD_CONFIG:\n")
        f.write("      THRESHOLD_MODE: LOSSY\n")

        f.write("...\n")
        f.write("---\n")
        f.write("device:\n")
        f.write("  0:\n")
        f.write("    PORT:\n")
        f.write("      ?\n")
        f.write(f"       PORT_ID: {generate_list_of_pairs(512)}\n")
        f.write("      :\n")
        f.write(f"       MTU: 9416\n")
        f.write(f"       MTU_CHECK: 1\n")

        f.write("...\n")
        f.write("---\n")
        f.write("device:\n")
        f.write("  0:\n")
        f.write("    DEVICE_CONFIG:\n")
        f.write("      AUTOLOAD_BOARD_SETTINGS: 0\n")
        f.write("      CORE_CLK_FREQ: CLK_1125MHZ\n")
        f.write("      PP_CLK_FREQ: CLK_675MHZ\n")

        f.write("...\n")
        f.write("---\n")
        f.write("device:\n")
        f.write("  0:\n")
        f.write("    FP_CONFIG:\n")
        f.write("      FP_ING_OPERMODE: GLOBAL_PIPE_AWARE\n")

        f.write("...\n")
        f.write("---\n")
        f.write("device:\n")
        f.write("  0:\n")
        f.write("    CTR_EFLEX_CONFIG:\n")
        f.write("      CTR_ING_EFLEX_OPERMODE_PIPEUNIQUE: 1\n")
        f.write("      CTR_ING_EFLEX_OPERMODE_PIPE_INSTANCE_UNIQUE: 1\n")
        f.write("      CTR_EGR_EFLEX_OPERMODE_PIPEUNIQUE: 1\n")
        f.write("      CTR_EGR_EFLEX_OPERMODE_PIPE_INSTANCE_UNIQUE: 1\n")
        f.write("...\n")

if __name__ == "__main__":
    main()
