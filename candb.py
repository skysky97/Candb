
"""\
This module provides CAN database(*dbc) and matrix(*xls) operation functions.


"""
import re
import xlrd
import sys
import traceback
import os

reload(sys)
sys.setdefaultencoding('utf-8')

# enable or disable debug info display, this switch is controlled by -d option.
debug_enable = False

# symbol definition of DBC format file
new_symbols = [
    'NS_DESC_', 'CM_', 'BA_DEF_', 'BA_', 'VAL_', 'CAT_DEF_', 'CAT_',
    'FILTER', 'BA_DEF_DEF_', 'EV_DATA_', 'ENVVAR_DATA_', 'SGTYPE_',
    'SGTYPE_VAL_', 'BA_DEF_SGTYPE_', 'BA_SGTYPE_', 'SIG_TYPE_REF_',
    'VAL_TABLE_', 'SIG_GROUP_', 'SIG_VALTYPE_', 'SIGTYPE_VALTYPE_',
    'BO_TX_BU_', 'BA_DEF_REL_', 'BA_REL_', 'BA_DEF_DEF_REL_',
    'BU_SG_REL_', 'BU_EV_REL_', 'BU_BO_REL_', 'SG_MUL_VAL_'
]


# pre-defined attribution definitions
#  object type    name                      value type          min     max     default   value range
attr_defs_init = [
    ["Message", "DiagRequest", "Enumeration", "", "", "No", ["No", "Yes"]],
    ["Message", "DiagResponse", "Enumeration", "", "", "No", ["No", "Yes"]],
    ["Message", "DiagState", "Enumeration", "", "", "No", ["No", "Yes"]],
    ["Message", "GenMsgCycleTime", "Integer", 0, 0, 0, []],
    ["Message", "GenMsgCycleTimeActive", "Integer", 0, 0, 0, []],
    ["Message", "GenMsgCycleTimeFast", "Integer", 0, 0, 0, []],
    ["Message", "GenMsgDelayTime", "Integer", 0, 0, 0, []],
    ["Message", "GenMsgILSupport", "Enumeration", "", "", "No", ["No", "Yes"]],
    ["Message", "GenMsgNrOfRepetition", "Integer", 0, 0, 0, []],
    ["Message", "GenMsgSendType", "Enumeration", "", "", "cycle", ["cycle", "NoSendType", "IfActive"]],
    ["Message", "GenMsgStartDelayTime", "Integer", 0, 65535, 0, []],
    ["Message", "NmMessage", "Enumeration", "", "", "No", ["No", "Yes"]],
    ["Network", "BusType", "String", "", "", "CAN", []],
    ["Network", "Manufacturer", "String", "", "", "", []],
    ["Network", "NmBaseAddress", "Hex", 0x0, 0x7FF, 0x400, []],
    ["Network", "NmMessageCount", "Integer", 0, 255, 128, []],
    ["Network", "NmType", "String", "", "", "", []],
    ["Network", "DBName", "String", "", "", "", []],
    ["Node", "DiagStationAddress", "Hex", 0x0, 0xFF, 0x0, []],
    ["Node", "ILUsed", "Enumeration", "", "", "No", ["No", "Yes"]],
    ["Node", "NmCAN", "Integer", 0, 2, 0, []],
    ["Node", "NmNode", "Enumeration", "", "", "Not", ["Not", "Yes"]],
    ["Node", "NmStationAddress", "Hex", 0x0, 0xFF, 0x0, []],
    ["Node", "NodeLayerModules", "String", "", "", "CANoeILNVector.dll", []],
    ["Signal", "GenSigInactiveValue", "Integer", 0, 0, 0, []],
    ["Signal", "GenSigSendType", "Enumeration", "", "", "cycle",
    ["cycle", "OnChange", "OnWrite", "IfActive", "OnChangeWithRepetition", "OnWriteWithRepetition",  "IfActiveWithRepetition"]],
    ["Signal", "GenSigStartValue", "Integer", 0, 0, 0, []],
    ["Signal", "GenSigTimeoutValue", "Integer", 0, 1000000000, 0, []],
]

# matrix template dict
# Matrix parser use this dict to parse can network information from excel. The
# 'key's are used in this module and the 'ValueTable' are used to match excel
# column header. 'ValueTable' may include multi string.
matrix_template_map = {
    "msg_name_col":         ["MsgName"],
    "msg_type_col":         ["MsgType"],
    "msg_id_col":           ["MsgID"],
    "msg_send_type_col":    ["MsgSendType"],
    "msg_cycle_col":        ["MsgCycleTime"],
    "msg_len_col":          ["MsgLength"],
    "sig_name_col":         ["SignalName"],
    "sig_comment_col":      ["SignalDescription"],
    "sig_byte_order_col":   ["ByteOrder"],
    "sig_start_bit_col":    ["StartBit"],
    "sig_len_col":          ["BitLength"],
    "sig_value_type_col":   ["DateType"],
    "sig_factor_col":       ["Resolution"],
    "sig_offset_col":       ["Offset"],
    "sig_min_phys_col":     ["SignalMin.Value(phys)"],
    "sig_max_phys_col":     ["SignalMax.Value(phys)"],
    "sig_init_val_col":     ["InitialValue(Hex)"],
    "sig_unit_col":         ["Unit"],
    "sig_val_col":          ["SignalValueDescription"],
}

# excel workbook sheets with name in this list are ignored
matrix_sheet_ignore = ["Cover", "History", "Legend", "ECU Version", ]

matrix_nodes = ["IPC","ICM"]

NODE_NAME_MAX = 8


class MatrixTemplate(object):
    def __init__(self):
        self.msg_name_col = 0
        self.msg_type_col = 0
        self.msg_id_col = 0
        self.msg_send_type_col = 0
        self.msg_cycle_col = 0
        self.msg_len_col = 0
        self.sig_name_col = 0
        self.sig_comment_col = 0
        self.sig_byte_order_col = 0
        self.sig_start_bit_col = 0
        self.sig_len_col = 0
        self.sig_value_type_col = 0
        self.sig_factor_col = 0
        self.sig_offset_col = 0
        self.sig_min_phys_col = 0
        self.sig_max_phys_col = 0
        self.sig_init_val_col = 0
        self.sig_unit_col = 0
        self.sig_val_col = 0
        self.nodes = {}

        self.start_row = 0  # start row number of valid data

    def members(self):
        return sorted(vars(self).items(), key=lambda item:item[1])

    def __str__(self):
        s = []
        for key, var in self.members():
            if type(var) == int:
                s.append("  %s : %d (%s)" % (key, var, get_xls_col(var)))
        return '\n'.join(s)


def get_xls_col(val):
    """
    get_xls_col(col) --> string
    
    Convert int column number to excel column symbol like A, B, AB .etc
    """
    if type(val) == type(0):
        if val <= 25:
            s = chr(val+0x41)
        elif val <100:
            s = chr(val/26-1+0x41)+chr(val%26+0x41)
        else:
            raise ValueError("column number too large: ", str(val))
        return s
    else:
        raise TypeError("column number only support int: ", str(val))


def get_list_item(list_object):
    """
    get_list_item(list_object) --> object(string)

    Show object list to terminal and get selection object from ternimal.
    """
    list_index = 0
    for item in list_object:
        print "   %2d %s" %(list_index, item)
        list_index += 1
    while True:
        user_input = raw_input()
        if user_input.isdigit():
            select_index = int(user_input)
            if select_index < len(list_object):
                return list_object[select_index]
            else:
                print "input over range"
        else:
            print "input invalid"


def parse_sheetname(workbook):
    """
    Get sheet name of can matrix in the xls workbook. 
    Only informations in this sheet are used.

    """
    sheets = []
    for sheetname in workbook.sheet_names():
        if sheetname == "Matrix":
            return sheetname
        if sheetname not in matrix_sheet_ignore:
            sheets.append(sheetname)
    if len(sheets)==1:
        return sheets[0]
    elif len(sheets)>=2:
        print "Select one sheet blow:"
        # print "  ","  ".join(sheets)
        # return raw_input()
        return get_list_item(sheets)
    else:
        print "Select one sheet blow:"
        # print "  ","  ".join(workbook.sheet_names())
        # return raw_input()
        return get_list_item(workbook.sheet_names())


def parse_template(sheet):
    """
    parse_template(sheet) -> MatrixTemplate
    
    Parse column headers of xls sheet and the result of column numbers is 
    returned as MatrixTemplate object
    """
    # find table header row
    header_row_num = 0xFFFF
    for row_num in range(0, sheet.nrows):
        if sheet.row_values(row_num)[0].find("Msg Name") != -1:
            #print "table header row number: %d" % row_num
            header_row_num = row_num
    if header_row_num == 0xFFFF:
        raise ValueError("Can't find \"Msg Name\" in this sheet")
    # get header info
    template = MatrixTemplate()
    for col_num in range(0, sheet.ncols):
        value = sheet.row_values(header_row_num)[col_num]
        if value is not None:
            value = value.replace(" ","")
            for col_name in matrix_template_map.keys():
                for col_header in matrix_template_map[col_name]:
                    if col_header in value and getattr(template,col_name)==0:
                        setattr(template, col_name, col_num)
                        break
    template.start_row = header_row_num + 1
    # get ECU nodes
    node_start_col = template.sig_val_col
    for col in range(node_start_col, sheet.ncols):
        value = sheet.row_values(header_row_num)[col]
        if value is not None:
            value = value.replace(" ","")
            if len(value) <= NODE_NAME_MAX:
                template.nodes[value] = col
    # print "detected nodes: ", template.nodes
    return template


def parse_sig_vals(val_str):
    """
    parse_sig_vals(val_str) -> {valuetable}

    Get signal key:value pairs from string. Returns None if failed.
    """
    vals = {}
    if val_str is not None and val_str != '':
        token = re.split('[\;\:\\n]+', val_str.strip())
        if len(token) >= 2:
            if len(token) % 2 == 0:
                for i in range(0, len(token), 2):
                    try:
                        val = getint(token[i])
                        desc = token[i + 1]  # .replace('.', ' ').replace('\"',' ')
                        vals[desc] = val
                    except ValueError:
                        # print "waring: ignored signal value definition: " ,token[i], token[i+1]
                        raise
                return vals
            else:
                # print "waring: ignored signal value description: ", val_str
                raise ValueError()
        else:
            raise ValueError(val_str)
    else:
        return None


def getint(str, default=None):
    """
    getint(str) -> int
    
    Convert string to int number. If default is given, default value is returned 
    while str is None.
    """
    if str == '':
        if default==None:
            raise ValueError("None type object is unexpected")
        else:
            return default
    else:
        try:
            val = int(str)
            return val
        except (ValueError, TypeError):
            try:
                val = int(str, 16)
                return val
            except:
                raise


class CanNetwork(object):
    def __init__(self):
        self.nodes = []
        self.messages = []
        self.name = 'CAN'
        self.val_tables = []
        self.version = ''
        self.new_symbols = new_symbols
        self.attr_defs = []
        self._init_attr_defs()
        self._filename = ''

    def _init_attr_defs(self):
        for attr_def in attr_defs_init:
            self.attr_defs.append(CanAttribution(attr_def[1], attr_def[0], attr_def[2], attr_def[3], attr_def[4],
                                                 attr_def[5], attr_def[6]))

    def __str__(self):
        # ! version
        lines = ['VERSION ' + r'""']
        lines.append('\n\n\n')

        # ! new_symbols
        lines.append('NS_ :\n')
        for symbol in self.new_symbols:
            lines.append('        ' + symbol + '\n')
        lines.append('\n')

        # ! bit_timming
        lines.append("BS_:\n")
        lines.append('\n')

        # ! nodes
        line = ["BU_:"]
        for node in self.nodes:
            line.append(node)
        lines.append(' '.join(line) + '\n\n\n')

        # ! messages
        for msg in self.messages:
            lines.append(str(msg) + '\n\n')
        lines.append('\n\n')

        # ! comments
        lines.append('''CM_ " "''' + ";" + "\n")
        for msg in self.messages:
            # <message comment are ignored> # todo
            for sig in msg.signals:
                comment = sig.comment
                if comment != "":
                    line = ["CM_", "SG_", str(msg.msg_id), sig.name, "\"" + comment + "\"" + ";"]
                    lines.append(" ".join(line) + '\n')

        # ! attribution defines
        for attr_def in self.attr_defs:
            line = ["BA_DEF_"]
            obj_type = attr_def.object_type
            if (obj_type == "Node"):
                line.append("BU_")
            elif (obj_type == "Message"):
                line.append("BO_")
            elif (obj_type == "Signal"):
                line.append("SG_")
            ##elif (obj_type == "Network")
            line.append(" \"" + attr_def.name + "\"")
            val_type = attr_def.value_type
            if (val_type == "Enumeration"):
                line.append("ENUM")
                val_range = []
                for val in attr_def.values:
                    val_range.append("\"" + val + "\"")
                line.append(",".join(val_range) + ";")
            elif (val_type == "String"):
                line.append("STRING" + " " + ";")
            elif (val_type == "Hex"):
                line.append("HEX")
                line.append(str(attr_def.min))
                line.append(str(attr_def.max) + ";")
            elif (val_type == "Integer"):
                line.append("INT")
                line.append(str(attr_def.min))
                line.append(str(attr_def.max) + ";")
            lines.append(" ".join(line) + '\n')

        # ! attribution default values
        for attr_def in self.attr_defs:
            line = ["BA_DEF_DEF_"]
            line.append(" \"" + attr_def.name + "\"")
            val_type = attr_def.value_type
            if (val_type == "Enumeration"):
                line.append("\"" + attr_def.default + "\"" + ";")
            elif (val_type == "String"):
                line.append("\"" + attr_def.default + "\"" + ";")
            elif (val_type == "Hex"):
                line.append(str(attr_def.default) + ";")
            elif (val_type == "Integer"):
                line.append(str(attr_def.default) + ";")
            lines.append(" ".join(line) + '\n')

        # ! attribution value of object
        # build-in value "DBName"
        line = ["BA_"]
        line.append('''"DBName"''')
        line.append(self.name + ";")
        lines.append(" ".join(line) + '\n')
        # ! message attribution values
        for msg in self.messages:
            for attr_def in self.attr_defs:
                if (msg.attrs.has_key(attr_def.name)):
                    if (msg.attrs[attr_def.name] != attr_def.default):
                        line = ["BA_"]
                        line.append("\"" + attr_def.name + "\"")
                        line.append("BO_")
                        line.append(str(msg.msg_id))
                        if (attr_def.value_type == "Enumeration"):
                            # write enum index instead of enum value
                            line.append(str(attr_def.values.index(str(msg.attrs[attr_def.name]))) + ";")
                        else:
                            line.append(str(msg.attrs[attr_def.name]) + ";")
                        lines.append(" ".join(line) + '\n')
        # ! signal attribution values
        for msg in self.messages:
            for sig in msg.signals:
                if sig.init_val is not None and sig.init_val is not 0:
                    line = ["BA_"]
                    line.append('''"GenSigStartValue"''')
                    line.append("SG_")
                    line.append(str(msg.msg_id))
                    line.append(sig.name)
                    line.append(str(sig.init_val))
                    line.append(';')
                    lines.append(' '.join(line) + '\n')
        # ! Value table define
        for msg in self.messages:
            for sig in msg.signals:
                if sig.values is not None and len(sig.values) >= 1:
                    line = ['VAL_']
                    line.append(str(msg.msg_id))
                    line.append(sig.name)
                    for key in sig.values:
                        line.append(str(sig.values[key]))
                        line.append('"'+ key +'"')
                    line.append(';')
                    lines.append(' '.join(line) + '\n')
        return ''.join(lines)

    def sort(self):
        messages = self.messages
        # sort by msg_id, id is treated as string, NOT numbers, to keep the same with candb++
        messages.sort(key=lambda msg: str(msg.msg_id))
        for msg in messages:
            signals = msg.signals
            signals.sort(key=lambda sig: sig.start_bit)

    def load(self, path):
        dbc = open(path, 'r')

        for line in dbc:
            line_trimmed = line.strip()
            line_split = re.split('[\s\(\)\[\]\|\,\:\@]+', line_trimmed)
            if len(line_split) > 0:
                if line_split[0] == 'BO_':
                    msg = CanMessage()
                    msg.msg_id = int(line_split[1])
                    msg.name   = line_split[2]
                    msg.dlc    = int(line_split[3])
                    msg.sender = line_split[4]
                    self.messages.append(msg)
                elif line_split[0] == 'SG_':
                    sig = CanSignal()
                    sig.name        = line_split[1]
                    sig.start_bit   = int(line_split[2])
                    sig.sig_len     = int(line_split[3])
                    sig.byte_order  = line_split[4][:1]
                    sig.value_type  = line_split[4][1:]
                    sig.factor      = line_split[5]
                    sig.offset      = line_split[6]
                    sig.min         = line_split[7]
                    sig.max         = line_split[8]
                    sig.unit        = line_split[9][1:-1]  # remove quotation makes
                    sig.receivers   = line_split[10:]  # receiver is a list
                    msg.signals.append(sig)

    def save(self, path=None):
        if (path == None):
            file = open(self._filename + ".dbc", "w")
        else:
            file = open(path, 'w')
        # file.write(unicode.encode(str(self), "utf-8"))
        file.write(str(self))

    def import_excel(self, path, sheetname=None, template=None):
        # Open file
        book = xlrd.open_workbook(path)
        # open sheet
        if sheetname is not None:
            print "use specified sheet: ", sheetname
            sheet = book.sheet_by_name(sheetname)
        else:
            sheetname = parse_sheetname(book)
            print "select sheet: ", sheetname
            sheet = book.sheet_by_name(sheetname)

        # import template
        if template is not None:
            print 'use specified template: ', template
            import_string = "import templates." + template + " as template"
            exec import_string
        else:
            print "parse template"
            template = parse_template(sheet)
            if debug_enable:
                print template
        # ! load network information
        filename = os.path.basename(path).split(".")
        self._filename = ".".join(filename[:-1])
        self.name = ".".join(filename[:-1]).replace(" ", "_").replace('.', '_').replace('-', '_')  # use filename as default DBName

        # ! load nodes information
        self.nodes = template.nodes.keys()

        # ! load messages
        messages = self.messages
        nrows = sheet.nrows
        for row in range(template.start_row, nrows):
            row_values = sheet.row_values(row)
            msg_name = row_values[template.msg_name_col]
            if (msg_name != ''):
                # This row defines a message!
                message = CanMessage()
                signals = message.signals
                message.name = msg_name.replace(' ', '')
                # message.type = row_values[template.msg_type_col] # todo: should set candb attribution instead
                message.msg_id = getint(row_values[template.msg_id_col])
                message.dlc = getint(row_values[template.msg_len_col])
                send_type = row_values[template.msg_send_type_col].upper().strip()
                if (send_type == "CYCLE") or (send_type == "CE"):  # todo: CE is treated as cycle
                    try:
                        msg_cycle = getint(row_values[template.msg_cycle_col])
                    except ValueError:
                        print "warning: message %s\'s cycle time \"%s\" is invalid, auto set to \'0\'" % (message.name, row_values[template.msg_cycle_col])
                        msg_cycle = 0
                    message.set_attr("GenMsgCycleTime", msg_cycle)
                    message.set_attr("GenMsgSendType", "cycle")
                else:
                    message.set_attr("GenMsgSendType", "NoSendType")

                # message sender
                message.sender = None
                for nodename in template.nodes:
                    nodecol = template.nodes[nodename]
                    sender = row_values[nodecol].strip().upper()
                    if sender == "S":
                        message.sender = nodename
                        break
                if message.sender is None:
                    message.sender = 'Vector__XXX'
                messages.append(message)
            else:
                sig_name = row_values[template.sig_name_col]
                if (sig_name != ''):
                    # This row defines a signal!
                    signal = CanSignal()
                    signal.name = sig_name.replace(' ', '')
                    signal.start_bit = getint(row_values[template.sig_start_bit_col])
                    signal.sig_len = getint(row_values[template.sig_len_col])
                    if (row_values[template.sig_byte_order_col].upper() == "MOTOROLA_LSB"):  # todo
                        signal.byte_order = '1'
                    else:
                        signal.byte_order = '0'
                    if (row_values[template.sig_value_type_col].upper() == "UNSIGNED"):
                        signal.value_type = '+'
                    else:
                        signal.value_type = '-'
                    signal.factor = row_values[template.sig_factor_col]
                    signal.offset = row_values[template.sig_offset_col]
                    signal.min = row_values[template.sig_min_phys_col]
                    signal.max = row_values[template.sig_max_phys_col]
                    signal.unit = row_values[template.sig_unit_col]
                    signal.init_val = getint((row_values[template.sig_init_val_col]), 0)
                    try:
                        signal.values = parse_sig_vals(row_values[template.sig_val_col])
                    except ValueError:
                        if debug_enable:
                            print "warning: signal %s\'s value table is ignored" % signal.name
                        else:
                            pass
                    signal.comment = row_values[template.sig_comment_col].replace("\"", "\'").replace("\r", '\n') # todo
                    # get signal receivers
                    signal.receivers = []
                    for nodename in template.nodes:
                        nodecol = template.nodes[nodename]
                        receiver = row_values[nodecol].strip().upper()
                        if receiver == "R":
                            signal.receivers.append(nodename)
                        elif receiver == "S":
                            if message.sender == 'Vector__XXX':
                                message.sender = nodename
                                print "warning: message %s\'s sender is set to \"%s\" via signal" %(message.name, nodename)
                            else:
                                print "warning: message %s\'s sender is conflict to signal \"%s\"" %(message.name, nodename)
                        else:
                            pass
                    if len(signal.receivers) == 0:
                        signal.receivers.append('Vector__XXX')
                    signals.append(signal)
        self.sort();


class CanMessage(object):
    def __init__(self, name='', msg_id=0, dlc=8, sender='Vector__XXX'):
        ''' 
        name: message name
        id: message id (11bit or 29 bit)
        dlc: message data length
        sender: message send node
        '''
        self.name = name
        self.msg_id = msg_id
        self.send_type = ''
        self.dlc = dlc
        self.sender = sender
        self.signals = []
        self.attrs = {}

    def __str__(self):
        para = []
        line = ["BO_", str(self.msg_id), self.name + ":", str(self.dlc), self.sender]
        para.append(" ".join(line))
        for sig in self.signals:
            para.append(str(sig))
        return '\n '.join(para)

    def set_attr(self, name, value):
        self.attrs[name] = value


class CanSignal(object):
    def __init__(self, name='', start_bit=0, sig_len=1, init_val=0):
        self.name = name
        self.start_bit = start_bit
        self.sig_len = sig_len
        self.init_val = init_val
        self.byte_order = '0'
        self.value_type = '+'
        self.factor = 1
        self.offset = 0
        self.min = 0
        self.max = 1
        self.unit = ''
        self.values = {}
        self.receivers = []
        self.comment = ''

    def __str__(self):
        line = ["SG_", self.name, ":",
                str(self.start_bit) + "|" + str(self.sig_len) + "@" + self.byte_order + self.value_type,
                "(" + str(self.factor) + "," + str(self.offset) + ")", "[" + str(self.min) + "|" + str(self.max) + "]",
                "\"" + self.unit + "\"", ','.join(self.receivers)]
        return " ".join(line)


class CanAttribution(object):
    def __init__(self, name, object_type, value_type, min, max, default, values=None):
        self.name = name
        self.object_type = object_type
        self.value_type = value_type
        self.min = min
        self.max = max
        self.default = default
        self.values = values

    def __str__(self):
        pass


def parse_args():
    """
    Parse command line commands.
    """
    import argparse
    parse = argparse.ArgumentParser()
    parse.add_argument("-d","--debug",help="show debug info",action="store_true", dest="debug_switch", default=False)
    subparser = parse.add_subparsers(title="subcommands")
    
    parse_gen = subparser.add_parser("gen", help="Generate dbc from excle file")
    parse_gen.add_argument("filename", help="The xls file to generate dbc")
    parse_gen.add_argument("-s","--sheetname",help="set sheet name of xls",default=None)
    parse_gen.add_argument("-t","--template",help="Choose a template",default=None)
    parse_gen.set_defaults(func=cmd_gen)
    
    parse_sort = subparser.add_parser("sort", help="Sort dbc message and signals")
    parse_sort.add_argument("filename", help="Dbc filename")
    parse_sort.add_argument("-o","--output", help="Specify output file path", default=None)
    parse_sort.set_defaults(func=cmd_sort)
    
    parse_cmp = subparser.add_parser("cmp", help="Compare difference bettween two dbc files")
    parse_cmp.add_argument("filename1", help="The base file to be compared with")
    parse_cmp.add_argument("filename2", help="The new file to be compared")
    parse_cmp.set_defaults(func=cmd_cmp)
    
    args = parse.parse_args()
    args.func(args)


def cmd_gen(args):
    try:
        can = CanNetwork()
        can.import_excel(args.filename, args.sheetname, args.template)
        can.save()
    except IOError,e:
        print e
    except xlrd.biffh.XLRDError,e:
        print e
        
        
def cmd_sort(args):
    can = CanNetwork()
    can.load(args.filename)
    can.sort()
    if args.output is None:
        can.save("sorted.dbc")
    else:
        can.save(savepath)


def cmd_cmp(args):
    print "Compare function is comming soon!"


if __name__ == '__main__':
    parse_args()


