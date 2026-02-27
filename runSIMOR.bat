@ECHO OFF
ECHO %startTime%%Time%

::~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
:: Run ActivitySim and associated scripts
::~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

:: Settings 
SET PROJECT_DIRECTORY=%~dp0
ECHO PROJECT_DIRECTORY: %PROJECT_DIRECTORY%

SET SKIM_DIR=%PROJECT_DIRECTORY%\skimming_and_assignment
ECHO SKIM_DIR: %SKIM_DIR%

SET MODEL_DIR=%PROJECT_DIRECTORY%\resident
ECHO MODEL_DIR: %MODEL_DIR%

@REM SET VISUM_DIR=D:\U-Expansion\Projects\Clients\Oregon\SimOR\skimming_and_assignment\visum
@REM SET VISUM_DIR=%ROOT_DIRECTORY%\skimming_and_assignment\visum

:: User-defined python environments
SET PYTHON_SANDAG_ASIM=C:\Users\edna.aguilar\.conda\envs\asim_140\python.exe
SET PYTHON_VISUM=C:\Program Files\PTV Vision\PTV Visum 2026\Exe\Junction_Preview\Python\python.exe
SET PYTHON_ASIM=C:\Users\edna.aguilar\Documents\git_locals\activitysim\.venv\Scripts\python.exe

:: User-defined Visum version file (should be saved in skimming_and_assingment\Visum)
SET VISUM_VERSION_FILE=Metro_Model_v1_AllStreetsNetwork_MasterTransit_Visum26.ver
ECHO VISUM_VERSION_FILE: %VISUM_VERSION_FILE%

:: ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
:: Skimming
:: ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

:: Motorized skims
@REM ECHO Running motorized skims.
@REM ECHO %startTime%%Time%

@REM CD %SKIM_DIR%\visum
@REM "%PYTHON_VISUM%" Visum_Runner.py %VISUM_VERSION_FILE% skims visum_metro/SkimSequence_Metro.xml
@REM IF %ERRORLEVEL% NEQ 0 GOTO MODEL_ERROR
@REM ECHO Motorized skims complete.

:: Non-motorized skims 
ECHO Running non-motorized skims preprocessor.
ECHO %startTime%%Time%

CD %SKIM_DIR%\maz_maz_stop_skims
%PYTHON_SANDAG_ASIM% 2zoneSkim_preprocessor.py 2zoneSkim_params.yaml

ECHO Running non-motorized skims.
ECHO %startTime%%Time%
%PYTHON_SANDAG_ASIM% 2zoneSkim.py 2zoneSkim_params.yaml
CD %SKIM_DIR%

:: ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
:: Run ActivitySim
:: ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
@REM ECHO Running land use preprocessor.
@REM ECHO %startTime%%Time%
@REM CD /D %MODEL_DIR%
@REM %PYTHON_ASIM% preprocessor.py preprocessor_settings.yaml

