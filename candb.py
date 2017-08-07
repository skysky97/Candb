import re
import xlrd
import string

import sys

reload(sys)
sys.setdefaultencoding('utf-8')

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

def open_dbc(path):
    network = CanNetwork()
    network.load(path)
    return network


def import_excel(path, sheet, template):
    network = CanNetwork()
    network.import_excel(path, sheet, template)
    return network


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
                if sig.values is not None:
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
            file = open(self.name + ".dbc", "w")
        else:
            file = open(path, 'w')
        # file.write(unicode.encode(str(self), "utf-8"))
        file.write(str(self))

    def import_excel(self, path, sheet, template):
        # Open file
        book = xlrd.open_workbook(path)
        sheet = book.sheet_by_name(sheet)
        nrows = sheet.nrows
        # import template
        import_string = "import templates." + template + " as template"
        exec import_string

        # ! load network information
        filename = path.split(".")
        self.name = ".".join(filename[:-1]).replace(" ", "_").replace('.', '_').replace('-', '_')  # use filename as default DBName

        # ! load nodes information
        self.nodes.append(template.node_name)  # todo: only record current node yet

        # ! load messages
        messages = self.messages;
        for row in range(template.start_row, nrows):
            row_values = sheet.row_values(row)
            msg_name = row_values[template.msg_name_col]
            if (msg_name != ''):
                # This row defines a message!
                message = CanMessage()
                signals = message.signals
                message.name = msg_name.replace(' ', '')
                # message.type = row_values[template.msg_type_col] # todo: should set candb attribution instead
                message.msg_id = int(row_values[template.msg_id_col][2:], 16)
                send_type = row_values[template.msg_send_type_col].upper().strip()
                if (send_type == "CYCLE") or (send_type == "CE"):  # todo: CE is treated as cycle
                    message.set_attr("GenMsgCycleTime", int(row_values[template.msg_cycle_col]))
                    message.set_attr("GenMsgSendType", "cycle")
                else:
                    message.set_attr("GenMsgSendType", "NoSendType")
                message.dlc = int(row_values[template.msg_len_col])
                # message sender
                sender = row_values[template.node_col].strip().upper()
                if (sender == "S"):
                    message.sender = template.node_name
                else:
                    message.sender = 'Vector__XXX'
                messages.append(message)
            else:
                sig_name = row_values[template.sig_name_col]
                if (sig_name != ''):
                    # This row defines a signal!
                    signal = CanSignal()
                    signal.name = sig_name.replace(' ', '')
                    signal.start_bit = int(row_values[template.sig_start_bit_col])
                    signal.sig_len = int(row_values[template.sig_len_col])
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
                    signal.init_val = _int((row_values[template.sig_init_val_col]))
                    signal.values = _parse_sig_val(row_values[template.sig_val_col])
                    signal.comment = row_values[template.sig_comment_col].replace("\"", "\'")  # todo
                    receiver = row_values[template.node_col].strip().upper()
                    if (receiver == "R"):
                        signal.receivers.append(template.node_name)
                    elif (receiver == "S"):
                        signal.receivers.append('Vector__XXX')
                        message.sender = template.node_name  # todo: maybe a warning?
                    else:
                        signal.receivers.append('Vector__XXX')
                    signals.append(signal)
        self.sort();


def _int(val_str):
    if val_str is not None:
        try:
            val = int(val_str, 16)
            return val
        except (ValueError, TypeError):
            try:
                val = int(val_str)
                return val
            except ValueError:
                return None
    return None


def _parse_sig_val(val_str):
    vals={}
    if val_str is not None:
        token = re.split('[\;\:\\n\-]+', val_str.strip())
        if len(token) >= 2:
            if len(token) % 2 == 0:
                for i in range(0, len(token), 2):
                    val = _int(token[i])
                    if val is None:
                        print "waring: ignored signal value: " + val_str
                    vals[token[i + 1]] = val
                return vals
            else:
                print "waring: ignored signal value: " + val_str
        else:
            return None
    else:
        return None

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


if __name__ == '__main__':
    print "\n====Candb tool====:"
    print '''For generate dbc file from excel, use command:\n    candb [path] [sheet] [template]'''
    print 'Supported template:\n    b100k_gasoline | b100k_hybird | c51e\n'

    import sys, getopt

    # opts, args = getopt.getopt(sys.argv[1:], 'h', ['help'])
    try:
        database = CanNetwork()
        # database.import_excel("BAIC_IPC_Matrix_CAN_20161008.xls", "IPC", "b100k_gasoline")
        database.import_excel(sys.argv[1], sys.argv[2], sys.argv[3])
        database.save()
        print "Success\n"
    except IndexError:
        print "Error: Invalid parameter\n"

