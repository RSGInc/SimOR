import os, sys, time
_visum_site_packages = os.path.normpath(
    os.path.join(os.path.dirname(sys.executable), "..", "..", "Python", "Lib", "site-packages")
)
sys.path.append(_visum_site_packages)
import VisumPy.helpers
import pandas as pd 
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
    inputVersionFile = sys.argv[1]
    procedure = sys.argv[2]
        
    print(f"start {procedure} run: {time.time()}")

    try:
      Visum = startVisum()
      loadVersion(Visum, inputVersionFile)
      print("Loaded Visum")
      loadProcedure(Visum, os.path.join("config", procedure))
      closeVisum(Visum)
      sys.exit(0)
    except Exception as e:
      print(procedure + "Failed")
      print(e)
      sys.exit(1)