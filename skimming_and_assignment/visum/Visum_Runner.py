import os, shutil, sys, time, csv
sys.path.append(os.path.dirname(os.getwd()) + "\\applicationCode\\Puthon37\packages")
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
  print("load version file: " + os.getcwd() + "/" + fileName)
  Visum.LoadVersion(os.getcwd() + "/" + fileName)
  pathNo = [8,69,2,37,12]
  for i in range(0,len(pathNo)):
    Visum.SetPath(pathNo[i], os.getcwd())

def saveVersion(Visum, fileName):
  filePath = os.path.join(os.getcwd(), fileName)
  print("save version file: " + filePath)
  Visum.SaveVersion(filePath)

def closeVisum(Visum):
  print("close Visum")
  Visum = 0

def loadProcedure(Visum,parFileName,execute=True):
  print("run procedure file: " + parFileName)
  Visum.Procedures.Open(parFileName)
  if execute:
    Visum.Procedures.Execute()
    
if __name__ == "__main__":
    runmode = sys.argv[1].tolower()
    inputVersionFile = "Metro_Model_v1_AllStreetsNetwork_MasterTransit_Visum26.ver"
    
    print("start " + runmode + "run: " + time.time())
    
    if runmode == 'skims':
        try:
            Visum = startVisum()
            loadVersion(Visum, inputVersionFile)
            loadProcedure(Visum, "config/SkimSequence_Metro.xml")
        except Exception as e:
            print(runmode + "Failed")
            print(e)
            sys.exit(1)