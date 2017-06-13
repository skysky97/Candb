# Candb
Generate CAN dbc file with OEM defined CAN matrix (*.xls). Class `CanDatabase` represents the CAN network and the architecture is similar to `Vector Candb++`.<br>
<br>
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
