@ECHO OFF
ECHO %startTime%%Time%

:: ~~~~~~~~
:: Settings
:: ~~~~~~~~~

SET ROOT_DIRECTORY=%1
SET SKIM_DIR=ROOT_DIRECTORY\skimming_and_assignment
SET VISUM_DIR=%SKIM_DIR%\visum
SET WALK_SKIM_DIR=%SKIM_DIR%\maz_maz_stop_skims

%PYTHON_SANDAG_ASIM%=C:\Users\edna.aguilar\AppData\Local\miniforge3\envs\asim_140\python.exe 
:: ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
:: Skimming
:: ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

:: Motorized skims
ECHO Running skims...
%PYTHON% Visum_Runner.py skims
IF %ERRORLEVEL% NEQ 0 GOTO MODEL_ERROR

:: NOn-motorized skims
ECHO Running non-motorizesd skim preprocessor.
CD %SKIM_DIR%
%PYTHON_SANDAG_ASIM% 2zoneSkim_preprocessor.py 2zoneSkim_params

ECHO Running non-motorized skims.
%PYTHON_SANDAG_ASIM% 2zoneSkim.py 2zoneSkim_params
