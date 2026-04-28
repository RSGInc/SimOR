@ECHO OFF
SETLOCAL

::~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
:: Run ActivitySim and associated scripts
::~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

:: ---------------------------------------------------------------------------
:: Settings
:: ---------------------------------------------------------------------------
SET "BASE_DIR=%~dp0"
IF "%BASE_DIR:~-1%"=="\" SET "BASE_DIR=%BASE_DIR:~0,-1%"
SET "SKIM_DIR=%BASE_DIR%\skimming_and_assignment"
SET "MODEL_DIR=%BASE_DIR%\resident"

:: User-defined Visum version file and procedure sequence
SET "VISUM_VERSION_FILE=Metro_Model_v1_AllStreetsNetwork_MasterTransit_Visum26.ver"
SET "PROCEDURE_SEQ=%SKIM_DIR%\visum\config\visum_metro\SkimSequence_Metro.xml"

:: ---------------------------------------------------------------------------
:: Run environment setup (installs dependencies & exports Python paths)
:: ---------------------------------------------------------------------------
ECHO Running environment setup...
CALL "%BASE_DIR%\setup_environment.bat"
IF %ERRORLEVEL% NEQ 0 (
    ECHO Environment setup failed. Aborting.
    EXIT /B 1
)

ECHO.
ECHO Base directory: %BASE_DIR%
ECHO Model directory: %MODEL_DIR%
ECHO Skimming directory: %SKIM_DIR%
ECHO.
 
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
"%PYTHON_MAZ_SKIMMING%" 2zoneSkim_preprocessor.py 2zoneSkim_params.yaml
IF %ERRORLEVEL% NEQ 0 GOTO MODEL_ERROR

ECHO.
ECHO Running non-motorized skims. 
"%PYTHON_MAZ_SKIMMING%" 2zoneSkim.py 2zoneSkim_params.yaml
IF %ERRORLEVEL% NEQ 0 GOTO MODEL_ERROR
ECHO Non-motorized skims complete.

:: ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
:: Run ActivitySim -- full integration not yet implemented
:: ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
ECHO.
ECHO Running ActivitySim preprocessor.
CD /D "%MODEL_DIR%"
"%PYTHON_ACTIVITYSIM%" preprocessor.py preprocessor_settings.yaml
IF %ERRORLEVEL% NEQ 0 GOTO MODEL_ERROR
ECHO ActivitySim preprocessor complete.

ECHO.
ECHO Running ActivitySim (test cropped example)
"%PYTHON_ACTIVITYSIM%" resident\simulation.py -c resident\configs -d resident\model_data\metro\data_cropped -o outputs\cropped
IF %ERRORLEVEL% NEQ 0 GOTO MODEL_ERROR
ECHO ActivitySim complete.

ECHO.
ECHO All steps completed successfully.
ENDLOCAL
GOTO :EOF

:MODEL_ERROR
ECHO.
ECHO ERROR: A step failed. Check the output above for details.
ENDLOCAL
EXIT /B 1