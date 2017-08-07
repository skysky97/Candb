@echo off
rem = """ Do any custom setup like setting environment variables etc if required here ...
c:\python27\python -x "%~f0" %1 %2 %3 %4 %5 %6 %7 %8 %9
goto endofPython """

import os
import sys
import subprocess as sp


#bc = os.path.join(os.getcwd(), 'candb.py')
bc = '''G:\\SampleCode\\PyCharm\\template\\candb.py'''
sp.call([bc] + sys.argv[1:], shell=True)

rem = """
:endofPython """