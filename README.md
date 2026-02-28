# SimOR
Simulate Oregon (SimOR) - Oregon's Jointly Estimated ActivitySim Model
![image](SimOR.png)

## Running the model

### Setup

1. **Configure `setup_environment.bat`**

   Open `setup_environment.bat` and set the user-configurable variables at the top of the file:

   | Variable | Description | Default |
   |----------|-------------|---------|
   | `VISUM_PYTHON_DIR` | Folder containing your Visum 2026 Python interpreter | `C:\Program Files\PTV Vision\PTV Visum 2026\Exe\Junction_Preview\Python` |
   | `INSTALL_PARKING` | Clone and install sandag_parking (`Y` or `N`) | `Y` |

   You can run this script on its own to install all dependencies without running the model:
   ```
   setup_environment.bat
   ```
   It will install UV (if needed), clone and build the required repositories into `ext_dependencies/`, create the MAZ skimming Python environment from `ext_dependencies/maz_skimming/pyproject.toml`, and install the necessary Python packages into Visum's Python environment. On subsequent runs it detects existing installs and pulls the latest changes instead of re-cloning.

2. **Place the Visum version file**

   Copy your Visum network version file (`.ver`) into `skimming_and_assignment/visum/`.

3. **Update configuration files**

   Edit the following files to match your local data paths and project settings:

   | File | Purpose |
   |------|---------|
   | `skimming_and_assignment/maz_maz_stop_skims/2zoneSkim_params.yaml` | Non-motorized skim settings and file paths |
   | `resident/preprocessor_settings.yaml` | Land use preprocessor input/output paths and network settings |

4. **Set user-defined variables in `runSIMOR.bat`**

   Open `runSIMOR.bat` and update the following variables at the top of the file:

   | Variable | Description |
   |----------|-------------|
   | `VISUM_VERSION_FILE` | Filename of the Visum version file |
   | `PROCEDURE_SEQ` | Path to the Visum procedure sequence XML |

### Running the Pipeline

Run:
```
runSIMOR.bat
```

The script automatically calls `setup_environment.bat` to ensure all dependencies are installed and Python paths are set, then runs the following steps in sequence:

1. **Motorized skims** — Using Visum `Visum_Runner.py`. Automatically outputs required files to run non-motorized skims. 
2. **Non-motorized skim preprocessor** — Prepares walk network inputs via `2zoneSkim_preprocessor.py`.
3. **Non-motorized skims** — Computes MAZ-to-MAZ and MAZ-to-stop walk skims via `2zoneSkim.py`.
4. **Land use preprocessor** — Builds ActivitySim-ready land use table via `preprocessor.py`.
5. **Run ActivitySim** -- Runs ActivitySim -- (not yet implemented)