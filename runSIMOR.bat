@ECHO OFF
SETLOCAL

::~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
:: Run ActivitySim and associated scripts
::~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

:: Settings 
SET "BASE_DIR=%~dp0"
SET "SKIM_DIR=%BASE_DIR%skimming_and_assignment"
SET "MODEL_DIR=%BASE_DIR%resident"

ECHO Base directory: %BASE_DIR%
ECHO Model directory: %MODEL_DIR%
ECHO Skimming directory: %SKIM_DIR%

:: Python environments built by setup_environment.bat
SET "EXT_DIR=%BASE_DIR%ext_dependencies"
SET "PYTHON_ASIM=%EXT_DIR%\activitysim\.venv\Scripts\python.exe"
SET "PYTHON_SANDAG_ASIM=%EXT_DIR%\sandag_parking\.venv\Scripts\python.exe"

:: Visum Python is a system install - edit this path to match your Visum version
SET "PYTHON_VISUM=C:\Program Files\PTV Vision\PTV Visum 2026\Exe\Junction_Preview\Python\python.exe"

:: User-defined Visum version file (should be saved in skimming_and_assingment\Visum)
SET "VISUM_VERSION_FILE=Metro_Model_v1_AllStreetsNetwork_MasterTransit_Visum26.ver"
SET "PROCEDURE_SEQ=%SKIM_DIR%\visum\config\visum_metro\SkimSequence_Metro.xml"

:: ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
:: Skimming
:: ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

:: Run motorized skims in Visum
ECHO.
ECHO Running motorized skims.
ECHO Visum version file: %VISUM_VERSION_FILE%
ECHO Procedure sequence: %PROCEDURE_SEQ%

CD /D "%SKIM_DIR%\visum"
"%PYTHON_VISUM%" Visum_Runner.py "%VISUM_VERSION_FILE%" "%PROCEDURE_SEQ%"
IF %ERRORLEVEL% NEQ 0 GOTO MODEL_ERROR
ECHO Motorized skims complete.

:: Run non-motorized skims in Python
ECHO.
ECHO Running non-motorized skim preprocessor.
CD /D "%SKIM_DIR%\maz_maz_stop_skims"
"%PYTHON_SANDAG_ASIM%" 2zoneSkim_preprocessor.py 2zoneSkim_params.yaml
IF %ERRORLEVEL% NEQ 0 GOTO MODEL_ERROR

ECHO .
ECHO Running non-motorized skims. 
"%PYTHON_SANDAG_ASIM%" 2zoneSkim.py 2zoneSkim_params.yaml
IF %ERRORLEVEL% NEQ 0 GOTO MODEL_ERROR
ECHO Non-motorized skims complete.

:: ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
:: Run ActivitySim
:: ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
ECHO.
ECHO Running land use preprocessor.
CD /D "%MODEL_DIR%"
"%PYTHON_ASIM%" preprocessor.py preprocessor_settings.yaml
IF %ERRORLEVEL% NEQ 0 GOTO MODEL_ERROR
ECHO Land use preprocessor complete.

ECHO.
ECHO All steps completed successfully.
ENDLOCAL
GOTO :EOF

:MODEL_ERROR
ECHO.
ECHO ERROR: A step failed. Check the output above for details.
ENDLOCAL
EXIT /B 1