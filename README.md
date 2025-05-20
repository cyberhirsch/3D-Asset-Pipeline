# 3D Asset Processing & Texturing Automation Pipeline

This repository contains a set of Python scripts designed to automate common tasks in a 3D asset creation workflow, from mesh preparation in Blender to texturing in Substance Painter.

## Overview

The pipeline consists of three main scripts:

1.  **`blender_decimate_unwrap.py`**: A Blender script for mesh processing.
2.  **`process_assets.py`**: A Python script to batch process assets using the Blender script.
3.  **`painter_automate_open_rename_material_bake_export_save.py`**: A Python script to automate texturing tasks in Adobe Substance Painter.

## Scripts

### 1. `blender_decimate_unwrap.py`

*   **Purpose**: Automates mesh processing tasks within Blender. This script is intended to be called by Blender's Python interpreter via the command line (e.g., in background mode).
*   **Key Functions**:
    *   Imports an `.obj` mesh.
    *   Optionally applies object scale.
    *   Applies a **Decimate** modifier (Collapse mode) to reduce polygon count based on a given ratio.
    *   Optionally fills holes in the mesh.
    *   Performs **Smart UV Project** to automatically generate UV coordinates.
    *   Exports the processed mesh as an `.obj` file.
*   **Configurable**: Decimation ratio, Smart UV Project parameters (angle limit, island margin, area weight, etc.), apply scale, fill holes.

### 2. `process_assets.py`

*   **Purpose**: Batch processes multiple 3D assets found in a specified input directory structure. It orchestrates the use of `blender_decimate_unwrap.py`.
*   **Key Functions**:
    *   Scans an input folder for subfolders, each assumed to contain one asset's `.obj` file.
    *   For each asset:
        *   Copies the original `.obj` to an output directory as `[asset_name]_high.obj`.
        *   Invokes Blender in the background to run `blender_decimate_unwrap.py` on the `_high.obj` file.
        *   Saves the result from Blender as `[asset_name]_low.obj` (decimated and UV unwrapped).
    *   Handles existing output files with user prompts (Overwrite All / Skip All).
*   **Configurable**: Input/output base folders, Blender executable path, and all parameters passed to `blender_decimate_unwrap.py`.

### 3. `painter_automate_open_rename_material_bake_export_save.py`

*   **Purpose**: Automates a sequence of operations within Adobe Substance Painter using its remote Python scripting API (requires Painter to be running with `--enable-remote-scripting` and the `lib_remote.py` helper).
*   **Key Functions (performed sequentially for a given low-poly and high-poly mesh pair)**:
    1.  **Project Creation**: Creates a new Substance Painter project with the specified low-poly mesh and project settings.
    2.  **Texture Set Renaming**: Renames the default texture set (e.g., to `M_[mesh_name]`).
    3.  **Smart Material Application**: Applies a specified Smart Material from a defined shelf location.
    4.  **Mesh Baking**:
        *   Configures baking parameters (output size, high-poly mesh path).
        *   Enables specified bakers (Normal, AO, Curvature, Position, Thickness, etc.).
        *   Initiates the asynchronous baking process.
        *   Includes pauses to allow Painter to process.
    5.  **Texture Export**: Exports textures using a predefined export preset (e.g., "glTF PBR Metal Roughness").
    6.  **Project Saving**: Saves the Substance Painter project (`.spp` file).
*   **Configurable**: Paths to low/high-poly meshes, output directory, Smart Material name/location, baking parameters (output size, enabled bakers), export preset.

## Workflow

1.  **Prepare Assets**: Place your original `.obj` 3D models into subfolders within the `INPUT_BASE_FOLDER` defined in `process_assets.py`.
2.  **Generate Low/High Poly**: Run `python process_assets.py`. This will:
    *   Create `_high.obj` copies in `OUTPUT_PROCESSED_OBJS_FOLDER`.
    *   Generate `_low.obj` (decimated, UV unwrapped) versions in the same folder using Blender.
3.  **Automate Texturing**:
    *   Ensure Substance Painter is running with remote scripting enabled (`--enable-remote-scripting`).
    *   Configure `painter_automate_open_rename_material_bake_export_save.py` with the paths to the `_low.obj` and `_high.obj` files generated in step 2, along with other Painter-specific settings.
    *   Run `python painter_automate_open_rename_material_bake_export_save.py`.
    *   The script will connect to Painter and perform the configured actions, resulting in exported textures and a saved `.spp` project file.

## Prerequisites

*   Python 3.x
*   Blender (ensure `BLENDER_EXECUTABLE` path is correctly set in `process_assets.py`)
*   Adobe Substance Painter
    *   Must be launched with the `--enable-remote-scripting` flag.
    *   Requires the `lib_remote.py` (or similar) Python library for Substance Painter remote control (usually provided by Adobe or found in community resources for Painter scripting). This file is not included in this repository and must be obtained separately.

## Configuration

*   Key paths (input/output folders, executable paths, specific asset files for Painter) and processing parameters are defined as constants at the top of each respective script.
*   Review and modify these configurations to match your environment and desired processing settings before running.

## Usage

1.  Configure the scripts as described above.
2.  To process meshes with Blender:
    ```bash
    python process_assets.py
    ```
3.  To automate Substance Painter tasks (ensure Painter is running with remote scripting):
    ```bash
    python painter_automate_open_rename_material_bake_export_save.py
    ```

---

This pipeline can significantly speed up repetitive tasks in 3D asset production, especially for projects involving many similar assets requiring decimation, UV unwrapping, and standardized texturing.
