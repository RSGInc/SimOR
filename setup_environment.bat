@ECHO OFF
SETLOCAL EnableDelayedExpansion

:: ============================================================================
:: SimOR Environment Setup Script
:: ============================================================================
:: This script sets up the computing environment for the SimOR project.
:: It installs UV (if needed), clones and builds ActivitySim, optionally
:: installs the sandag_parking repo, and configures Visum Python packages.
::
:: All cloned repos and virtual environments are placed in the
:: ext_dependencies subfolder within this SimOR repo.
:: ============================================================================

:: ---------------------------------------------------------------------------
:: User-configurable settings
:: ---------------------------------------------------------------------------
:: Set this to the folder containing Visum's bundled Python interpreter.
:: Example: C:\Program Files\PTV Vision\PTV Visum 2026\Exe\Python
SET "VISUM_PYTHON_DIR=C:\Program Files\PTV Vision\PTV Visum 2026\Exe\Python"

:: Set to Y to clone and install sandag_parking (oregon_metro branch), N to skip
:: (optional dependency, only needed if you want to regenerate parking cost data)
SET "INSTALL_PARKING=N"
:: ---------------------------------------------------------------------------


:: ---------------------------------------------------------------------------
:: Resolve the base directory (the root of this SimOR repo)
:: ---------------------------------------------------------------------------
SET "BASE_DIR=%~dp0"
:: Remove trailing backslash
IF "%BASE_DIR:~-1%"=="\" SET "BASE_DIR=%BASE_DIR:~0,-1%"

ECHO ============================================================
ECHO  SimOR Environment Setup
ECHO ============================================================
ECHO.
ECHO  Base directory: %BASE_DIR%
ECHO.

:: ---------------------------------------------------------------------------
:: Create ext_dependencies folder for cloned repos and environments
:: ---------------------------------------------------------------------------
SET "EXT_DIR=%BASE_DIR%\ext_dependencies"
IF NOT EXIST "%EXT_DIR%" (
    MKDIR "%EXT_DIR%"
    ECHO  Created ext_dependencies folder.
)


:: ============================================================================
:: STEP 1 – Ensure UV is installed
:: ============================================================================
ECHO [1/5] Checking for UV package manager...

where uv >nul 2>&1
IF %ERRORLEVEL% NEQ 0 (
    ECHO  UV not found. Installing UV...
    powershell -ExecutionPolicy Bypass -Command "irm https://astral.sh/uv/install.ps1 | iex"
    IF !ERRORLEVEL! NEQ 0 (
        ECHO  ERROR: Failed to install UV.
        GOTO :ERROR_EXIT
    )
    :: Refresh PATH so uv is available in this session
    FOR /F "tokens=*" %%A IN ('powershell -Command "[System.Environment]::GetEnvironmentVariable('Path','User')"') DO SET "PATH=%%A;%PATH%"
    where uv >nul 2>&1
    IF !ERRORLEVEL! NEQ 0 (
        ECHO  ERROR: UV installed but not found on PATH. Please restart your terminal and re-run this script.
        GOTO :ERROR_EXIT
    )
    ECHO  UV installed successfully.
) ELSE (
    ECHO  UV is already installed.
)
ECHO.

:: ============================================================================
:: STEP 1b – Ensure Git is available
:: ============================================================================
ECHO  Checking for Git...
where git >nul 2>&1
IF %ERRORLEVEL% NEQ 0 (
    ECHO  Git not found on PATH. Searching common install locations...
    SET "GIT_FOUND="
    FOR %%G IN (
        "%ProgramFiles%\Git\cmd"
        "%ProgramFiles(x86)%\Git\cmd"
        "%LOCALAPPDATA%\Programs\Git\cmd"
        "%ProgramFiles%\Git\bin"
    ) DO (
        IF EXIST "%%~G\git.exe" (
            SET "PATH=%%~G;!PATH!"
            SET "GIT_FOUND=1"
        )
    )
    IF NOT DEFINED GIT_FOUND (
        ECHO  ERROR: Git is not installed or not found.
        ECHO  Please install Git from https://git-scm.com/ and re-run this script.
        GOTO :ERROR_EXIT
    )
    ECHO  Found Git and added to PATH for this session.
) ELSE (
    ECHO  Git is available.
)
ECHO.

:: ============================================================================
:: STEP 2 – Clone / update ActivitySim and create its virtual environment
:: ============================================================================
ECHO [2/5] Setting up ActivitySim (SimOR_pnr branch)...

SET "ACTIVITYSIM_DIR=%EXT_DIR%\activitysim"

IF EXIST "%ACTIVITYSIM_DIR%\.git" (
    ECHO  ActivitySim repo already exists. Pulling latest changes...
    pushd "%ACTIVITYSIM_DIR%"
    git checkout SimOR_pnr
    git pull
    popd
) ELSE (
    ECHO  Cloning ActivitySim ^(SimOR_pnr branch^)...
    pushd "%EXT_DIR%"
    git clone --branch SimOR_pnr https://github.com/RSGInc/activitysim.git
    IF !ERRORLEVEL! NEQ 0 (
        ECHO  ERROR: Failed to clone ActivitySim.
        popd
        GOTO :ERROR_EXIT
    )
    popd
)

:: Build the environment using the uv lock file
ECHO  Installing ActivitySim dependencies via UV...
pushd "%ACTIVITYSIM_DIR%"
uv sync --frozen --link-mode copy
IF !ERRORLEVEL! NEQ 0 (
    ECHO  ERROR: uv sync failed for ActivitySim.
    popd
    GOTO :ERROR_EXIT
)
uv pip install -e . --no-deps --link-mode copy
popd

:: Resolve the absolute path to the venv Python
FOR /F "delims=" %%P IN ('powershell -Command "(Resolve-Path '%ACTIVITYSIM_DIR%\.venv\Scripts\python.exe').Path"') DO SET "PYTHON_ACTIVITYSIM=%%P"

IF NOT EXIST "%PYTHON_ACTIVITYSIM%" (
    ECHO  ERROR: Could not find Python at %ACTIVITYSIM_DIR%\.venv\Scripts\python.exe
    GOTO :ERROR_EXIT
)

ECHO  PYTHON_ACTIVITYSIM = %PYTHON_ACTIVITYSIM%
ECHO.

:: ============================================================================
:: STEP 3 – Visum Python packages
:: ============================================================================
ECHO [3/5] Setting up Visum Python packages...

IF NOT EXIST "%VISUM_PYTHON_DIR%\python.exe" (
    ECHO  WARNING: Visum Python not found at:
    ECHO    %VISUM_PYTHON_DIR%
    ECHO  Please edit VISUM_PYTHON_DIR in this script to point to your Visum 2026 Python folder.
    ECHO  Skipping Visum package installation.
) ELSE (
    ECHO  Installing tables, openmatrix, pyyaml into Visum Python...
    "%VISUM_PYTHON_DIR%\python.exe" -m pip install tables openmatrix pyyaml
    IF !ERRORLEVEL! NEQ 0 (
        ECHO  WARNING: Failed to install one or more Visum Python packages.
    ) ELSE (
        ECHO  Visum packages installed successfully.
    )
)
ECHO.

:: ============================================================================
:: STEP 4 – MAZ skimming Python environment
:: ============================================================================
ECHO [4/5] Setting up MAZ skimming Python environment...

SET "MAZ_SKIM_DIR=%EXT_DIR%\maz_skimming"

ECHO  Installing MAZ skimming dependencies via UV...
pushd "%MAZ_SKIM_DIR%"
uv sync --frozen --link-mode copy
IF !ERRORLEVEL! NEQ 0 (
    ECHO  ERROR: uv sync failed for MAZ skimming environment.
    popd
    GOTO :ERROR_EXIT
)
popd

:: Resolve the absolute path to the venv Python
FOR /F "delims=" %%P IN ('powershell -Command "(Resolve-Path '%MAZ_SKIM_DIR%\.venv\Scripts\python.exe').Path"') DO SET "PYTHON_MAZ_SKIMMING=%%P"

IF NOT EXIST "%PYTHON_MAZ_SKIMMING%" (
    ECHO  ERROR: Could not find Python at %MAZ_SKIM_DIR%\.venv\Scripts\python.exe
    GOTO :ERROR_EXIT
)

ECHO  PYTHON_MAZ_SKIMMING = %PYTHON_MAZ_SKIMMING%
ECHO.

:: ============================================================================
:: STEP 5 – (Optional) Clone / update sandag_parking
:: ============================================================================

IF /I "%INSTALL_PARKING%"=="Y" (
    ECHO  Setting up sandag_parking ^(oregon_metro branch^)...

    SET "PARKING_DIR=%EXT_DIR%\sandag_parking"

    IF EXIST "!PARKING_DIR!\.git" (
        ECHO  sandag_parking repo already exists. Pulling latest changes...
        pushd "!PARKING_DIR!"
        git checkout oregon_metro
        git pull
        popd
    ) ELSE (
        ECHO  Cloning sandag_parking ^(oregon_metro branch^)...
        pushd "%EXT_DIR%"
        git clone --branch oregon_metro https://github.com/RSGInc/sandag_parking.git
        IF !ERRORLEVEL! NEQ 0 (
            ECHO  ERROR: Failed to clone sandag_parking.
            popd
            GOTO :ERROR_EXIT
        )
        popd
    )

    :: Build the environment using the uv lock file
    ECHO  Installing sandag_parking dependencies via UV...
    pushd "!PARKING_DIR!"
    uv sync --frozen --link-mode copy
    IF !ERRORLEVEL! NEQ 0 (
        ECHO  ERROR: uv sync failed for sandag_parking.
        popd
        GOTO :ERROR_EXIT
    )
    popd

    :: Resolve the absolute path to the venv Python
    FOR /F "delims=" %%P IN ('powershell -Command "(Resolve-Path '!PARKING_DIR!\.venv\Scripts\python.exe').Path"') DO SET "PYTHON_PARKING=%%P"

    IF NOT EXIST "!PYTHON_PARKING!" (
        ECHO  ERROR: Could not find Python at !PARKING_DIR!\.venv\Scripts\python.exe
        GOTO :ERROR_EXIT
    )

    ECHO  PYTHON_PARKING = !PYTHON_PARKING!
) ELSE (
    :: Even if not cloning, set the variable if the repo already exists
    SET "PARKING_DIR=%EXT_DIR%\sandag_parking"
    IF EXIST "!PARKING_DIR!\.venv\Scripts\python.exe" (
        FOR /F "delims=" %%P IN ('powershell -Command "(Resolve-Path '!PARKING_DIR!\.venv\Scripts\python.exe').Path"') DO SET "PYTHON_PARKING=%%P"
        ECHO  Existing sandag_parking environment found.
        ECHO  PYTHON_PARKING = !PYTHON_PARKING!
    ) ELSE (
        SET "PYTHON_PARKING="
        ECHO  sandag_parking skipped.
    )
)
ECHO.

:: Set PYTHON_VISUM as the full path to the Visum Python executable
IF EXIST "%VISUM_PYTHON_DIR%\python.exe" (
    SET "PYTHON_VISUM=%VISUM_PYTHON_DIR%\python.exe"
) ELSE (
    SET "PYTHON_VISUM="
)

:: ============================================================================
:: Summary
:: ============================================================================
ECHO ============================================================
ECHO  Environment Setup Complete
ECHO ============================================================
ECHO.
ECHO  PYTHON_ACTIVITYSIM  = %PYTHON_ACTIVITYSIM%
ECHO  PYTHON_MAZ_SKIMMING = %PYTHON_MAZ_SKIMMING%
ECHO  PYTHON_VISUM        = %PYTHON_VISUM%
IF DEFINED PYTHON_PARKING (
    ECHO  PYTHON_PARKING     = !PYTHON_PARKING!
) ELSE (
    ECHO  PYTHON_PARKING     = ^(not set^)
)
ECHO.
ECHO ============================================================

:: ---------------------------------------------------------------------------
:: Export variables to the caller's scope (survives ENDLOCAL)
:: ---------------------------------------------------------------------------
ENDLOCAL & (
    SET "PYTHON_ACTIVITYSIM=%PYTHON_ACTIVITYSIM%"
    SET "PYTHON_MAZ_SKIMMING=%PYTHON_MAZ_SKIMMING%"
    SET "PYTHON_VISUM=%PYTHON_VISUM%"
    SET "PYTHON_PARKING=%PYTHON_PARKING%"
    SET "EXT_DIR=%EXT_DIR%"
    SET "BASE_DIR=%BASE_DIR%"
    SET "PATH=%PATH%"
)
GOTO :EOF

:ERROR_EXIT
ECHO.
ECHO ============================================================
ECHO  Setup failed. See errors above.
ECHO ============================================================
ENDLOCAL
EXIT /B 1
