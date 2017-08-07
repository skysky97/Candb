# excel info
file_name = 'BAIC_C51E_BCAN_ICM_CAN_V0.52.xls'
sheet_name = 'Matrix'
network_name = 'BCAN'

# byte order
byte_order_options = ["INTEL", "MOTOROLA_MSB", "MOTOROLA_LSB"]
byte_order = "MOTOROLA_MSB"

# matrix table row header info
msg_name_col = 0
msg_type_col = 1
msg_id_col = 2
msg_send_type_col = 3
msg_cycle_col = 4
msg_len_col = 5

sig_name_col = 6
sig_comment_col = 7
sig_byte_order_col = 8
sig_start_bit_col = 10
sig_len_col = 12
sig_value_type_col = 13
sig_factor_col = 14
sig_offset_col = 15
sig_min_phys_col = 16
sig_max_phys_col = 17
sig_unit_col = 23
sig_val_col = 24

node_name = "ICM" # name of ECU defined in excel
node_col = 28 # ECU name column number

# others
start_row = 2 # start row number of valid data
