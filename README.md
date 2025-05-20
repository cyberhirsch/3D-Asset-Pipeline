# 3D-Asset_Pipeline

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

This project provides a suite of Python scripts to automate a 3D asset processing pipeline. It takes raw OBJ files, processes them in Blender (scaling, decimation, UV unwrapping, high/low poly export), and then textures them in Adobe Substance 3D Painter (project creation, smart material application, baking, texture export).

The entire workflow is configured via a central `config.json` file and can be orchestrated using the provided Python scripts or the sample Windows batch file.

## Features

*   **Batch Processing:** Process multiple assets automatically.
*   **Blender Automation (`process_assets.py` & `blender_decimate_unwrap.py`):**
    *   Copies original OBJ files to a working directory.
    *   Scales models.
    *   Applies existing model scale if specified.
    *   Exports a scaled, pre-decimation version as `_high.obj`.
    *   Saves a `.blend` file of the scaled model.
    *   Decimates the mesh to create a low-poly version.
    *   Optionally fills holes in the mesh.
    *   Performs Smart UV Project with configurable parameters.
    *   Exports the decimated, unwrapped mesh as `_low.obj`.
*   **Substance Painter Automation (`painter_automate.py` & `lib_remote.py`):**
    *   Scans for `_low.obj` files processed by Blender.
    *   For each asset:
        *   Creates a new Substance Painter project using the `_low.obj`.
        *   Renames the default texture set (e.g., to `M_AssetName`).
        *   Applies a specified Smart Material.
        *   Bakes mesh maps using the corresponding `_high.obj` (Normal, AO, Curvature, etc.).
        *   Saves the Substance Painter project (`.spp`).
        *   Exports textures using the "glTF PBR Metal Roughness" preset.
*   **Configuration Driven:** All paths, Blender parameters, and Painter settings are managed in `config.json`.
*   **Optional Windows Batch File:** For a more streamlined execution of both stages on Windows.

## Prerequisites

1.  **Python 3.x:** Ensure Python is installed and in your system's PATH.
2.  **Blender:** Tested with Blender 4.x. The scripts use Blender's Python API.
3.  **Adobe Substance 3D Painter:** The version should be compatible with the Python API used in `painter_automate.py` (scripts seem to target a relatively modern API).
    *   **Crucially for manual Painter launch:** If you are *not* using the provided batch file (which launches Painter automatically), Substance Painter must be launched with remote scripting enabled. You can do this by creating a shortcut or running it from the command line with the `--enable-remote-scripting` flag.
      For example (Windows): `"C:\Program Files\Adobe\Adobe Substance 3D Painter\Adobe Substance 3D painter.exe" --enable-remote-scripting`

## Setup

1.  **Clone the Repository or Download Files:**
    Get all the files (`process_assets.py`, `blender_decimate_unwrap.py`, `painter_automate.py`, `lib_remote.py`, `config.json`, and optionally the batch file below) into a single directory.

2.  **Configure `config.json`:**
    This is the most important step. Open `config.json` and edit the paths and parameters to match your system and desired workflow.

    ```json
    {
      "comment": "this is the config.json file for the python files",
      "global_paths": {
        "input_base_folder": "E:\\Path\\To\\Your\\Raw\\OBJs", // Folder containing subfolders for each asset
        "processed_objs_folder": "E:\\Path\\To\\Output\\Blender\\Meshes", // Where .blend, _high.obj, _low.obj go
        "painter_output_base_folder": "E:\\Path\\To\\Output\\Painter\\TexturesAndProjects" // Where .spp and textures go
      },
      "blender_settings": {
        "executable_path_windows": "C:\\Program Files\\Blender Foundation\\Blender 4.3\\blender.exe",
        "executable_path_macos": "/Applications/Blender.app/Contents/MacOS/Blender",
        "executable_path_linux": "blender", // Or full path if not in PATH
        "script_params": {
          "decimate_ratio": 0.1,
          "sp_angle_degrees": 20.0,
          "sp_island_margin": 0.000,
          "sp_area_weight": 0.0,
          "sp_correct_aspect": true,
          "sp_scale_to_bounds": false,
          "sp_margin_method": "SCALED", // Options: 'SCALED', 'ABSOLUTE', 'FRACTION'
          "sp_rotate_method": "AXIS_ALIGNED_Y", // Options: 'AXIS_ALIGNED', 'AXIS_ALIGNED_X', 'AXIS_ALIGNED_Y'
          "uv_fill_holes": false,
          "scale_factor": 100.0, // Factor to scale the model by
          "apply_scale": true // Apply original model scale before the main scaling
        }
      },
      "painter_settings": {
        // This path is for reference by the Python script if needed, but the batch file below uses its own hardcoded path to launch Painter.
        "executable_path_windows": "C:\\Program Files\\Adobe\\Adobe Substance 3D Painter\\Adobe Substance 3D painter.exe",
        "smart_material_name": "HullTextureColor", // Name of your smart material
        "smart_material_location": "Yourassets", // Shelf where the smart material is located (e.g., "Shelf", "Yourassets", "Project")
        "bakers_to_enable": [ // Names of mesh maps to bake
          "Normal",
          "AO",
          "Curvature",
          "Position",
          "Thickness",
          "WorldSpaceNormal"
        ]
      }
    }
    ```
    *   **Note on Paths (Windows):** Use double backslashes `\\` or forward slashes `/` for paths in `config.json`.

3.  **Prepare Input Assets:**
    *   Your raw `.obj` files should be organized into subfolders within the `input_base_folder` specified in `config.json`. Each subfolder represents a single asset.
    *   Example structure for `input_base_folder`:
        ```
        E:\Path\To\Your\Raw\OBJs\
        ├── Asset001\
        │   └── model_source.obj
        ├── Asset002\
        │   └── another_model.obj
        └── ...
        ```
    *   The `process_assets.py` script will use the subfolder name (e.g., `Asset001`) as the base name for output files.

## Workflow / Usage

You can run the processing stages manually or use the provided Windows batch file for a more automated flow.

### Manual Execution

1.  **Run Blender Processing:**
    *   Open a terminal or command prompt.
    *   Navigate to the directory containing the scripts.
    *   Execute `process_assets.py`:
        ```bash
        python process_assets.py
        ```
    *   This script will:
        *   Read your `config.json`.
        *   Iterate through asset subfolders in `input_base_folder`.
        *   Copy the `.obj` from each asset's subfolder to `processed_objs_folder` (e.g., `Asset001.obj`).
        *   Call Blender in the background to run `blender_decimate_unwrap.py` on the copied OBJ.
        *   Blender will output `Asset001.blend`, `Asset001_high.obj`, and `Asset001_low.obj` into `processed_objs_folder`.
    *   Check the console output for progress and any errors.

2.  **Run Substance Painter Processing:**
    *   **Important:** Launch Adobe Substance 3D Painter with remote scripting enabled (see Prerequisites).
    *   Once Painter is running, open a new terminal or command prompt (or use the existing one).
    *   Navigate to the directory containing the scripts.
    *   Execute `painter_automate.py`:
        ```bash
        python painter_automate.py
        ```
    *   This script will:
        *   Read your `config.json`.
        *   Connect to the running Substance Painter instance.
        *   Scan `processed_objs_folder` for `*_low.obj` files.
        *   For each `_low.obj` file:
            *   Automate project creation, material application, baking, saving, and texture export within Painter.
            *   Outputs (`Asset001.spp`, texture files) will be saved in a subfolder named after the asset (e.g., `Asset001`) inside `painter_output_base_folder`.
    *   Monitor both the script's console output and the Substance Painter Log window for detailed progress and potential errors.

### Automated Workflow (Windows Batch File)

A Windows batch file (`.bat`) can be used to run both stages sequentially and launch Substance Painter automatically.

1.  **Save the Batch File:**
    Copy the content below and save it as `run_automation.bat` (or any name with a `.bat` extension) in the *same directory* as your Python scripts and `config.json`.

    ```batch
    @echo off
    echo ============================================================
    echo  STARTING KITBASH AUTOMATION
    echo ============================================================
    echo.

    REM Set the directory where the scripts are located
    set SCRIPT_DIR=%~dp0
    REM For older systems or if %~dp0 doesn't work as expected, you can hardcode:
    REM set SCRIPT_DIR=E:\Path\To\Your\Scripts\

    echo Changing directory to: %SCRIPT_DIR%
    cd /d "%SCRIPT_DIR%"

    echo.
    echo ============================================================
    echo  STAGE 1: RUNNING BLENDER PROCESSING (process_assets.py)
    echo ============================================================
    echo.
    python process_assets.py
    echo.
    echo STAGE 1 (Blender Processing) COMPLETE.
    echo Press any key to continue to Substance Painter processing...
    pause >nul
    echo.

    echo ============================================================
    echo  STAGE 2: RUNNING SUBSTANCE PAINTER PROCESSING
    echo ============================================================
    echo.
    REM Ensure this path to Substance Painter is correct for your system.
    "C:\Program Files\Adobe\Adobe Substance 3D Painter\Adobe Substance 3D painter.exe" --enable-remote-scripting
    echo Starting Substance Painter and waiting for it to load...
    REM Wait for 30 seconds for Painter to initialize. Adjust if needed.
    TIMEOUT /T 30
    echo Continuing after wait...
    REM --- IMPORTANT: Ensure the Python script name below matches your file. ---
    REM The provided Python script is 'painter_automate.py'.
    REM If your script is named 'substance_painter_batch.py', use that instead.
    python painter_automate.py
    REM If your script is named differently, e.g. 'substance_painter_batch.py', change the line above.
    REM python substance_painter_batch.py
    echo.
    echo STAGE 2 (Substance Painter Processing) COMPLETE.
    echo.

    echo ============================================================
    echo  AUTOMATION SCRIPT FINISHED
    echo ============================================================
    echo The command window will remain open. Close it manually.
    pause
    ```

2.  **Verify Batch File Settings:**
    *   **`SCRIPT_DIR`**: The line `set SCRIPT_DIR=%~dp0` should automatically set the script directory correctly if the batch file is in the same folder as the Python scripts. If you encounter issues, you can uncomment and hardcode the path: `REM set SCRIPT_DIR=E:\Path\To\Your\Scripts\`.
    *   **Substance Painter Path**: Ensure the path `"C:\Program Files\Adobe\Adobe Substance 3D Painter\Adobe Substance 3D painter.exe"` in the batch file matches your Substance Painter installation.
    *   **Painter Script Name**: The batch file currently calls `python painter_automate.py`. If your Painter automation script is named differently (e.g., `substance_painter_batch.py` as suggested by the original batch file content), update this line in the batch file.
    *   **Timeout**: The `TIMEOUT /T 30` gives Painter 30 seconds to load. If your system is slower or Painter takes longer to initialize, you might need to increase this value.

3.  **Run the Batch File:**
    *   Ensure your `config.json` is correctly configured.
    *   Double-click the `run_automation.bat` file.
    *   The script will execute `process_assets.py` first.
    *   It will then pause, waiting for you to press any key.
    *   After you press a key, it will launch Substance Painter with remote scripting enabled, wait for a bit, and then run `painter_automate.py` (or the script name you specified).
    *   The command window will remain open at the end; you can close it manually.

## File Descriptions

*   **`config.json`**: Main configuration file for all paths and processing parameters. **User must edit this.**
*   **`process_assets.py`**: Orchestrator script for the Blender part. It finds input OBJs, copies them, and calls Blender with `blender_decimate_unwrap.py`.
*   **`blender_decimate_unwrap.py`**: The Blender Python script that performs mesh operations (scaling, decimation, UV unwrapping, high/low poly export).
*   **`painter_automate.py`**: Main Python script for Substance Painter automation. Connects to Painter and orchestrates project creation, material application, baking, saving, and export.
    *   *(Note: The batch file originally referred to `substance_painter_batch.py`. Ensure the name called in the batch file matches this script if you use it.)*
*   **`lib_remote.py`**: A library module used by `painter_automate.py` to communicate with Substance Painter's remote scripting server.
*   **`run_automation.bat` (Optional):** A Windows batch file to automate running both the Blender and Substance Painter processing stages.

## Troubleshooting & Notes

*   **Permissions:** Ensure the scripts have permission to read from input folders and write to output folders.
*   **Paths in `config.json`:** Double-check all paths. Incorrect paths are a common source of errors. Use `\\` or `/` for Windows paths.
*   **Substance Painter Version:** The Painter Python API can change between versions. If you encounter errors in `painter_automate.py` related to API calls, you might need to adjust them for your Painter version. Consult the Substance Painter Python API documentation.
*   **Blender Version:** Similarly, Blender's Python API can have changes, though it's generally more stable for the operations used here.
*   **Smart Material Not Found:** If `painter_automate.py` reports it cannot find your smart material:
    *   Verify `smart_material_name` and `smart_material_location` in `config.json`.
    *   The `smart_material_location` refers to the shelf in Painter (e.g., "shelf" for default assets, "yourassets" or "starterassets" for user-imported ones, or "project" if it's specific to a project). Check Painter's UI for the correct shelf name.
    *   The script includes a fallback search with wildcards, but an exact match is preferred.
*   **Long Waits:** The `time.sleep()` calls in `painter_automate.py` and `TIMEOUT` in the batch file are there to give Painter time to process commands. If operations seem to fail because Painter hasn't finished the previous step, you might need to increase these wait times.
*   **Error Messages:** Pay close attention to error messages in both the Python script console output and the Substance Painter Log window (usually accessible via `Window > Log` in Painter).

## License

This project is licensed under the MIT License - see the [LICENSE.md](LICENSE.md) file for details (assuming you will create a separate LICENSE.md file with the MIT license text).
