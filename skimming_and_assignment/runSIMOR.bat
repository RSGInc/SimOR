@ECHO OFF
@REM ECHO %startTime%%Time%

:: ~~~~~~~~
:: Settings
:: ~~~~~~~~~

SET ROOT_DIRECTORY=C:\Users\edna.aguilar\Documents\git_locals\SimOR
SET SKIM_DIR=%ROOT_DIRECTORY%\skimming_and_assignment
SET VISUM_DIR=D:\U-Expansion\Projects\Clients\Oregon\SimOR\skimming_and_assignment\visum
SET WALK_SKIM_DIR=%SKIM_DIR%\maz_maz_stop_skims

:: Define Python environments
SET PYTHON_SANDAG_ASIM=C:\Users\edna.aguilar\.conda\envs\asim_140\python.exe
SET PYTHON_VISUM=C:\Program Files\PTV Vision\PTV Visum 2026\Exe\Junction_Preview\Python\python.exe

:: ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
:: Skimming
:: ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

:: Motorized skimss
ECHO Running motorized skims.
CD %VISUM_DIR%
"%PYTHON_VISUM%" Visum_Runner.py skims visum_metro/SkimSequence_Metro.xml
IF %ERRORLEVEL% NEQ 0 GOTO MODEL_ERROR
ECHO Motorized skims complete.

:: Non-motorized skims 
ECHO Running non-motorized skim preprocessor.
CD %WALK_SKIM_DIR%
ECHO %WALK_SKIM_DIR%
%PYTHON_SANDAG_ASIM% 2zoneSkim_preprocessor.py 2zoneSkim_params.yaml

ECHO Running non-motorized skims.
%PYTHON_SANDAG_ASIM% 2zoneSkim.py 2zoneSkim_params.yaml
CD %SKIM_DIR%