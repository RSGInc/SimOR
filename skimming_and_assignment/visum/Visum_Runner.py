import os, shutil, sys, time, csv
sys.path.append("C:/Program Files/PTV Vision/PTV Visum 2026/Exe/Python/Lib/site-packages")
import win32com.client as com
import VisumPy.helpers
import VisumPy.csvHelpers
import traceback
import pandas as pd
sys.path.append("scripts") # check
import warnings
import tables

warnings.simplefilter('ignore', tables.NaturalNameWarning)

# Define functions
def startVisum():
    print("Start Visum")
    Visum = VisumPy.helpers.CreateVisum(26)
    pathNo = [8,69,2,37,12]
    for i in range(0,len(pathNo)):
        Visum.SetPath(pathNo[i], os.getcwd())
    return(Visum)

def loadVersion(Visum, fileName):
  print("Load version file: " + os.getcwd() + "/" + fileName)
  Visum.LoadVersion(os.getcwd() + "/" + fileName)
  pathNo = [8,69,2,37,12]
  for i in range(0,len(pathNo)):
    Visum.SetPath(pathNo[i], os.getcwd())

def saveVersion(Visum, fileName):
  filePath = os.path.join(os.getcwd(), fileName)
  print("Save version file: " + filePath)
  Visum.SaveVersion(filePath)

def closeVisum(Visum):
  print("Close Visum")
  Visum = 0

def loadProcedure(Visum,parFileName,execute=True):
  print("Run procedure file: " + parFileName)
  Visum.Procedures.Open(parFileName)
  if execute:
    Visum.Procedures.Execute()
    
if __name__ == "__main__":
    runmode = sys.argv[1]
    procedure = sys.argv[2]
    inputVersionFile = f"Metro_Model_v1_AllStreetsNetwork_MasterTransit_Visum26.ver"
    
    print(f"start {runmode} run: {time.time()}")
    
    if runmode == 'skims':
        try:
            Visum = startVisum()
            loadVersion(Visum, inputVersionFile)
            print("Loaded Visum")
            loadProcedure(Visum, os.path.join("config", procedure))
            closeVisum(Visum)
            sys.exit(0)
        except Exception as e:
            print(runmode + "Failed")
            print(e)
            sys.exit(1)