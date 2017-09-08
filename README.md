# Introduction
Generate CAN dbc file with OEM defined CAN matrix (*.xls). Class `CanDatabase` represents the CAN network and the architecture is similar to Vector Candb++.

# Manul
## Install
1. Put file path of 'candb.cmd' into system evironment variables.
2. Modify 'candb.py' file path in 'candb.cmd'.

## Command
Several command can be used in Command Line:
- `candb -h` show command help.
- `candb gen` generate dbc from excel.

### Usage
candb [-h] [-s SHEETNAME] [-t TEMPLATE] [-d] {gen} filename
- `gen` command is used to generate dbc from excel.
- `filename` the path of excle.
- `-s` specify a sheetname used in the excle workbook, optinal.
- `-t` specify a template to parse excel, optional. If not given, template is generated automatically.
- `-d` show more debug info.

### Example
```C
candb gen SAIC_XXXX.xls
```

## Import as module
Use method `import_excel` to load network from excel. Parameters are defined as below:<br>
* path:     Matrix file's path
* sheet:    Sheet name of matrix in the excel
* template: Template file which descripes matrix format

Use method `save` to write to file.<br> 
```python
database = CanDatabase()
database.import_excel("BAIC_IPC_Matrix_CAN_20161008.xls", "IPC", "b100k_gasoline")
database.save()
```
