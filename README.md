# SimOR
Simulate Oregon (SimOR) - Oregon's Jointly Estimated ActivitySim Model
![image](SimOR.png)

## Currently in development
To run the prototype mini example, download and install the correct fork of Activitysim from [here](https://github.com/RSGInc/activitysim/tree/SimOR_pnr) and follow the launch commands in the .vscode/launch.json file.  This version of ActivitySim contains the necessary park-and-ride changes to run the SimOR model.

## Skimming and ActivitySim Preprocessing

The `ims_allstreets` branch contains the motorized and non-motorized skimming pipelines and the ActivitySim land use preprocessor. Follow the steps below to run the full workflow.

### Setup

1. **Check out the branch**
   ```
   git checkout ims_allstreets
   ```

2. **Configure and run the environment setup script**

   Open `setup_environment.bat` and set `VISUM_PYTHON_DIR` to the folder containing your Visum installation's Python interpreter. Then run:
   ```
   setup_environment.bat
   ```
   This script will install UV (if needed), clone and build the required ActivitySim (`SimOR_pnr` branch) and `sandag_parking` (`oregon_metro` branch) repositories into `ext_dependencies/`, and install the necessary Python packages into Visum's Python environment.

3. **Place the Visum version file**

   Copy your Visum network version file (`.ver`) into `skimming_and_assignment/visum/`.

4. **Update configuration files**

   Edit the following files to match your local data paths and project settings:

   | File | Purpose |
   |------|---------|
   | `skimming_and_assignment/maz_maz_stop_skims/2zoneSkim_params.yaml` | Non-motorized skim settings and file paths |
   | `resident/preprocessor_settings.yaml` | Land use preprocessor input/output paths and network settings |

5. **Set user-defined variables in `runSIMOR.bat`**

   Open `runSIMOR.bat` and update the following variables at the top of the file:

   | Variable | Description |
   |----------|-------------|
   | `PYTHON_VISUM` | Full path to Visum's `python.exe` |
   | `VISUM_VERSION_FILE` | Filename the Visum version file |

### Running the Pipeline

Run:
```
runSIMOR.bat
```

The script runs the following steps in sequence:

1. **Motorized skims** — Using Visum `Visum_Runner.py`. Automatically outputs required files to run non-motorized skims. 
2. **Non-motorized skim preprocessor** — Prepares walk network inputs via `2zoneSkim_preprocessor.py`.
3. **Non-motorized skims** — Computes MAZ-to-MAZ and MAZ-to-stop walk skims via `2zoneSkim.py`.
4. **Land use preprocessor** — Builds ActivitySim-ready land use table via `preprocessor.py`.