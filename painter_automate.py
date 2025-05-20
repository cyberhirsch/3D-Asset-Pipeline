# painter_automate_test.py
import lib_remote
import os
import time
import json # For handling export configuration AND loading config
import glob # For finding files

# --- Load Configuration ---
CONFIG_FILE_PATH = os.path.join(os.path.dirname(__file__), "config.json")
def load_config():
    """Loads the configuration from config.json"""
    try:
        with open(CONFIG_FILE_PATH, 'r') as f:
            config_data = json.load(f)
        return config_data
    except FileNotFoundError:
        print(f"ERROR: Configuration file not found at {CONFIG_FILE_PATH}")
        print("Please ensure 'config.json' exists in the same directory as the script.")
        exit(1)
    except json.JSONDecodeError as e:
        print(f"ERROR: Could not decode JSON from {CONFIG_FILE_PATH}. Check for syntax errors: {e}")
        exit(1)
    except Exception as e:
        print(f"ERROR: An unexpected error occurred while loading config: {e}")
        exit(1)

config = load_config()

# --- CONFIGURATION (loaded from config.json) ---
try:
    PROCESSED_OBJS_FOLDER = config["global_paths"]["processed_objs_folder"]
    PAINTER_OUTPUT_BASE_FOLDER = config["global_paths"]["painter_output_base_folder"]

    SMART_MATERIAL_NAME = config["painter_settings"]["smart_material_name"]
    SMART_MATERIAL_LOCATION = config["painter_settings"]["smart_material_location"]
    BAKERS_TO_ENABLE = config["painter_settings"]["bakers_to_enable"]
except KeyError as e:
    print(f"ERROR: Missing a required key in config.json: {e}")
    print("Please check your config.json structure against the expected format.")
    exit(1)

# Part1: Project Creation
# Part1: Project Creation
def run_project_creation_only(low_poly_mesh_path_for_project): # NEW: Takes specific low-poly mesh path
    print(f"Attempting to create project with: {low_poly_mesh_path_for_project}")

    if not os.path.exists(low_poly_mesh_path_for_project):
        print(f"!!! ERROR: Low-poly mesh path does not exist: {low_poly_mesh_path_for_project}")
        return # Exit this function call if mesh not found

    try:
        remote = lib_remote.RemotePainter()
        remote.checkConnection()
    except Exception as e:
        print(f"Error: Could not connect to Substance Painter: {e}")
        print("Ensure Painter is running with '--enable-remote-scripting'.")
        return # Exit this function call if connection fails

    # Escape backslashes for the Painter script string
    lp_mesh_path_escaped = low_poly_mesh_path_for_project.replace('\\', '\\\\')

    # These project settings could be moved to config.json if more control is needed
    # For now, keeping them here as they are common defaults.
    project_settings_from_ui = {
        "default_texture_resolution": 4096,
        "normal_map_format": "DirectX", # Options: "DirectX", "OpenGL"
        "compute_tangent_space_per_fragment": True,
        "use_uv_tile_workflow": False, # Set to True for UDIM workflows
        "import_cameras": False,
    }

    command_to_execute_create_project = f"""
import substance_painter.project
import substance_painter.textureset
import substance_painter.exception
import time # Added for sleep after project close

print("[PAINTER LOG] --- Python Project Creation Script Start ---")

mesh_path = r'{lp_mesh_path_escaped}' # Uses the escaped path from the function argument
print(f"[PAINTER LOG] Low-poly mesh path for project creation: {{mesh_path}}")

settings = substance_painter.project.Settings()

# 1. Document Resolution
settings.default_texture_resolution = {project_settings_from_ui['default_texture_resolution']}
print(f"[PAINTER LOG] Setting default_texture_resolution to: {{settings.default_texture_resolution}}")

# 2. Normal Map Format
normal_map_format_str = "{project_settings_from_ui['normal_map_format']}"
if normal_map_format_str == "DirectX":
    settings.normal_map_format = substance_painter.project.NormalMapFormat.DirectX
    print("[PAINTER LOG] Setting normal_map_format to DirectX.")
elif normal_map_format_str == "OpenGL":
    settings.normal_map_format = substance_painter.project.NormalMapFormat.OpenGL
    print("[PAINTER LOG] Setting normal_map_format to OpenGL.")
else:
    print(f"[PAINTER LOG] Warning: Unknown normal map format '{{normal_map_format_str}}' specified. Using Painter default.")

# 3. Compute Tangent Space Per Fragment
compute_tangent_per_fragment = {project_settings_from_ui['compute_tangent_space_per_fragment']}
if compute_tangent_per_fragment:
    settings.tangent_space_mode = substance_painter.project.TangentSpace.PerFragment
    print("[PAINTER LOG] Setting tangent_space_mode to PerFragment.")
else:
    settings.tangent_space_mode = substance_painter.project.TangentSpace.PerVertex
    print("[PAINTER LOG] Setting tangent_space_mode to PerVertex.")

# 4. Use UV Tile workflow (UDIMs)
use_uv_workflow = {project_settings_from_ui['use_uv_tile_workflow']}
if use_uv_workflow:
    settings.project_workflow = substance_painter.project.ProjectWorkflow.UVTile
    print("[PAINTER LOG] Setting project_workflow to UVTile.")
else:
    settings.project_workflow = substance_painter.project.ProjectWorkflow.Default
    print("[PAINTER LOG] Setting project_workflow to Default (non-UDIM).")

# 5. Import Cameras
settings.import_cameras = {project_settings_from_ui['import_cameras']}
print(f"[PAINTER LOG] Setting import_cameras to: {{settings.import_cameras}}")

print("[PAINTER LOG] Attempting to create new project with the defined settings...")
try:
    if substance_painter.project.is_open():
        print("[PAINTER LOG] An project is already open. Closing it first.")
        substance_painter.project.close()
        time.sleep(0.5) # Give Painter a moment to process the close
        if substance_painter.project.is_open():
            print("[PAINTER LOG] ERROR: Failed to close the existing project. Aborting creation.")
            # Optionally, raise an exception here to signal failure more strongly
            # raise Exception("Failed to close existing project.")
            # For batch processing, we might want to just log and continue to next asset,
            # but project creation is fundamental for the current asset.
            # However, if it can't close, it likely can't create either.
            # For now, this Painter-side log is the primary error indication.

    # Create the new project
    substance_painter.project.create(
        mesh_file_path=mesh_path,
        settings=settings
    )

    if substance_painter.project.is_open():
        print("[PAINTER LOG] SUCCESS: Project creation call completed. Project is now open.")
    else:
        print("[PAINTER LOG] ERROR: Project creation call completed, but NO project seems to be open. This is unexpected.")

except substance_painter.exception.ProjectError as pe:
    print(f"[PAINTER LOG] !!! ProjectError during project creation: {{str(pe)}}")
except ValueError as ve: # e.g. if mesh_path is invalid from Painter's perspective
    print(f"[PAINTER LOG] !!! ValueError during project creation: {{str(ve)}}")
except TypeError as te: # e.g. if API for settings has changed
    print(f"[PAINTER LOG] !!! TypeError during project creation (check API compatibility for settings): {{str(te)}}")
except Exception as e_create:
    print(f"[PAINTER LOG] !!! EXCEPTION during project creation: {{str(e_create)}}")
    # import traceback # Could add for more detail if needed
    # traceback.print_exc()

print("[PAINTER LOG] --- Python Project Creation Script End ---")
"""

    print(f"\n--- Sending Project Creation Command to Painter ---")
    try:
        response_from_painter = remote.execScript(command_to_execute_create_project, "python")
        print("\n--- Response from Painter's Python (stdout/stderr) ---")
        if response_from_painter:
            print(response_from_painter)
        else:
            print("No explicit stdout from Painter's Python script, check Painter's log/UI.")
        print("----------------------------------------------------------\n")
        print("Project creation command sent. Please check Substance Painter UI and its Log window for results.")
    except lib_remote.ExecuteScriptError as ese:
        print(f"!!! Painter's API reported an ERROR during Python script execution: {ese}")
    except Exception as e:
        print(f"!!! An error occurred sending the Python command or processing response: {e}")


# Part 2: Rename Texture Set
# Part 2: Rename Texture Set
def run_rename_texture_set(target_material_name):
    print(f"\n--- Attempting to Rename Texture Set in Painter ---")
    print(f"Target material name for Texture Set: {target_material_name}")
    rename_successful_signal = False  # To indicate if Painter script confirmed success

    try:
        remote = lib_remote.RemotePainter()
        remote.checkConnection()
    except Exception as e:
        print(f"Error: Could not connect to Substance Painter for renaming: {e}")
        return False # Return False to indicate failure to connect or execute

    command_to_execute_rename = f"""
import substance_painter.project
import substance_painter.textureset
import substance_painter.exception
import time # Added for sleep after rename attempt

print("[PAINTER LOG] --- Python Texture Set Rename Script Start ---")
desired_name = "{target_material_name}" # Uses the argument passed to the Python function

if not substance_painter.project.is_open():
    print("[PAINTER LOG] ERROR: No project is open. Cannot rename texture sets.")
else:
    try:
        texture_sets = substance_painter.textureset.all_texture_sets()
        if texture_sets:
            print(f"[PAINTER LOG] Found {{len(texture_sets)}} texture set(s).")
            # Assuming we want to rename the first texture set, which is typical for new projects
            # For more complex scenarios with multiple texture sets, a more robust selection might be needed.
            ts_to_rename = texture_sets[0]
            original_name = ts_to_rename.name
            print(f"[PAINTER LOG] Attempting to rename Texture Set '{{original_name}}' to '{{desired_name}}'.")

            ts_to_rename.name = desired_name # Attempt the rename

            time.sleep(0.1) # Give Painter a moment to process the change

            # Verify the rename
            # Re-fetch the texture set or check its name property again.
            # Note: Re-fetching all_texture_sets might be safer if the object reference `ts_to_rename`
            # doesn't update its internal `name` property immediately after assignment in all API versions.
            # For simplicity, we'll check the existing reference.
            if ts_to_rename.name == desired_name:
                print(f"[PAINTER LOG] SUCCESS: Texture Set renamed to '{{desired_name}}'.")
                print("PYTHON_SCRIPT_TEXTURE_SET_RENAMED_SUCCESSFULLY") # Signal for external script
            else:
                print(f"[PAINTER LOG] ERROR: Renaming seems to have failed. Name is still '{{ts_to_rename.name}}'. Attempted '{{desired_name}}'.")
        else:
            print("[PAINTER LOG] No texture sets found in the project to rename.")

    except AttributeError as ae: # E.g. if .name is not a settable property or API changed
        print(f"[PAINTER LOG] !!! AttributeError during rename (API for .name or all_texture_sets might have changed): {{str(ae)}}")
    except Exception as e_rename:
        print(f"[PAINTER LOG] !!! EXCEPTION during texture set renaming: {{str(e_rename)}}")

print("[PAINTER LOG] --- Python Texture Set Rename Script End ---")
"""
    print(f"\n--- Sending Texture Set Rename Command to Painter ---")
    try:
        response_from_painter = remote.execScript(command_to_execute_rename, "python")
        print("\n--- Response from Painter's Python (stdout/stderr for rename) ---")
        if response_from_painter:
            print(response_from_painter)
            if "PYTHON_SCRIPT_TEXTURE_SET_RENAMED_SUCCESSFULLY" in response_from_painter:
                rename_successful_signal = True
                print("Texture set rename signaled as successful by Painter.")
            else:
                print("Texture set rename NOT signaled as successful by Painter script. Check logs.")
        else:
            print("No explicit stdout from Painter's Python script for rename, check Painter's log/UI.")
        print("-------------------------------------------------------------------\n")
    except lib_remote.ExecuteScriptError as ese:
        print(f"!!! Painter's API reported an ERROR during rename script execution: {ese}")
    except Exception as e:
        print(f"!!! An error occurred sending the rename command or processing response: {e}")

    return rename_successful_signal

# Part 3: Apply Smart Material
# Part 3: Apply Smart Material
def run_apply_smart_material(smart_material_name_to_apply, smart_material_shelf_context):
    print(f"\n--- Applying Smart Material '{smart_material_name_to_apply}' from shelf '{smart_material_shelf_context}' ---")

    try:
        remote = lib_remote.RemotePainter()
        remote.checkConnection()
    except Exception as e:
        print(f"Error: Could not connect to Substance Painter for applying Smart Material: {e}")
        return # Exit if connection fails

    # The Painter-side Python script to execute
    command_to_execute_apply_sm = f"""
import substance_painter.project
import substance_painter.textureset
import substance_painter.layerstack # For InsertPosition and insert_smart_material
import substance_painter.resource
import substance_painter.exception
import traceback # For detailed error logging

print("[PAINTER LOG] --- Python Apply Smart Material Script Start ---")
sm_name_to_apply_in_painter = "{smart_material_name_to_apply}"
sm_shelf_context_in_painter = "{smart_material_shelf_context}"

if not substance_painter.project.is_open():
    print("[PAINTER LOG] ERROR: No project is open. Cannot apply Smart Material.")
else:
    try:
        all_ts = substance_painter.textureset.all_texture_sets()
        if not all_ts:
            print("[PAINTER LOG] ERROR: No texture sets found in the project.")
        else:
            target_ts = all_ts[0] # Apply to the first texture set
            print(f"[PAINTER LOG] Target Texture Set for Smart Material: '{{target_ts.name}}'")

            # Construct the search query for the smart material
            # Example query: "s:Yourassets u:smartmaterial n:HullTextureColor"
            # s: shelf, u: usage (type), n: name
            query = f"s:{{sm_shelf_context_in_painter}} u:smartmaterial n:{{sm_name_to_apply_in_painter}}"
            print(f"[PAINTER LOG] Searching for Smart Material with query: {{query}}")
            found_resources = substance_painter.resource.search(query)

            if not found_resources:
                print(f"[PAINTER LOG] ERROR: Smart Material '{{sm_name_to_apply_in_painter}}' in shelf '{{sm_shelf_context_in_painter}}' not found with query '{{query}}'.")
                # Optional: Attempt a fallback search with wildcards if exact match fails
                query_fallback = f"s:{{sm_shelf_context_in_painter}} u:smartmaterial n:*{{sm_name_to_apply_in_painter}}*"
                print(f"[PAINTER LOG] Attempting fallback search with wildcards: {{query_fallback}}")
                found_resources_fallback = substance_painter.resource.search(query_fallback)
                if found_resources_fallback:
                    print(f"[PAINTER LOG] Found with wildcards! This suggests a subtle naming discrepancy. Using first wildcard match.")
                    found_resources = found_resources_fallback
                else:
                    print(f"[PAINTER LOG] Still not found even with wildcards. Please check material name and shelf location.")

            if found_resources:
                smart_material_resource = found_resources[0] # Use the first found resource
                print(f"[PAINTER LOG] Found Smart Material: '{{smart_material_resource.identifier().url()}}'")

                stack_of_target_ts = target_ts.get_stack()

                if not stack_of_target_ts:
                    print(f"[PAINTER LOG] ERROR: Could not get layer stack for texture set '{{target_ts.name}}'.")
                else:
                    # Create an InsertPosition object to specify where to insert the material (typically at the top)
                    insert_pos = substance_painter.layerstack.InsertPosition.from_textureset_stack(stack_of_target_ts)
                    
                    print(f"[PAINTER LOG] Applying Smart Material '{{smart_material_resource.identifier().name}}' to stack of '{{target_ts.name}}' at determined insert position.")
                    
                    # Insert the smart material
                    new_layer_or_group = substance_painter.layerstack.insert_smart_material(
                        insert_pos,
                        smart_material_resource.identifier()
                    )

                    if new_layer_or_group:
                         # For Node objects (like layers/groups), use .get_name()
                         layer_name = new_layer_or_group.get_name()
                         print(f"[PAINTER LOG] SUCCESS: Smart Material '{{sm_name_to_apply_in_painter}}' applied. New layer/group name: '{{layer_name}}'")
                         print("PYTHON_SCRIPT_SMART_MATERIAL_APPLIED_SUCCESSFULLY") # Signal for external script
                    else:
                        print(f"[PAINTER LOG] ERROR: Failed to apply Smart Material '{{sm_name_to_apply_in_painter}}'. 'insert_smart_material' did not return a new layer/group object.")
            # else: Smart material not found message already printed

    except substance_painter.exception.ProjectError as pe:
        print(f"[PAINTER LOG] !!! ProjectError while applying Smart Material: {{str(pe)}}")
    except substance_painter.exception.ResourceNotFoundError as rnfe: # Though our search handles this, good to have
        print(f"[PAINTER LOG] !!! ResourceNotFoundError for Smart Material: {{str(rnfe)}}")
    except TypeError as te_apply_sm:
        print(f"[PAINTER LOG] !!! TypeError while applying Smart Material (API argument mismatch for insert_smart_material or similar): {{str(te_apply_sm)}}")
        traceback.print_exc()
    except Exception as e_apply_sm:
        print(f"[PAINTER LOG] !!! EXCEPTION while applying Smart Material: {{str(e_apply_sm)}}")
        traceback.print_exc()

print("[PAINTER LOG] --- Python Apply Smart Material Script End ---")
"""
    print(f"\n--- Sending Apply Smart Material Command to Painter ---")
    apply_sm_successful_signal = False
    try:
        response_from_painter = remote.execScript(command_to_execute_apply_sm, "python")
        print("\n--- Response from Painter's Python (stdout/stderr for apply SM) ---")
        if response_from_painter:
            print(response_from_painter)
            if "PYTHON_SCRIPT_SMART_MATERIAL_APPLIED_SUCCESSFULLY" in response_from_painter:
                apply_sm_successful_signal = True
                print("Smart Material application signaled as successful by Painter.")
            else:
                print("Smart Material application NOT signaled as successful. Check Painter logs.")
        else:
            print("No explicit stdout from Painter's Python script for apply SM, check Painter's log/UI.")
        print("-----------------------------------------------------------------------\n")
    except lib_remote.ExecuteScriptError as ese:
        print(f"!!! Painter's API reported an ERROR during apply SM script execution: {ese}")
    except Exception as e:
        print(f"!!! An error occurred sending the apply SM command or processing response: {e}")
    
    return apply_sm_successful_signal # Return status

# Part 4: Baking High Res Mesh
# Part 4: Baking High Res Mesh
def run_bake_high_res_mesh(target_texture_set_name, high_poly_mesh_path_str):
    print(f"\n--- Attempting to Bake High-Res Mesh for Texture Set '{target_texture_set_name}' ---")
    print(f"High-poly mesh: {high_poly_mesh_path_str}")
    bake_initiated_signal = False # To indicate if Painter script confirmed bake start

    if not os.path.exists(high_poly_mesh_path_str):
        print(f"!!! ERROR: High-poly mesh path does not exist: {high_poly_mesh_path_str}")
        return False # Return False if high-poly mesh is missing

    try:
        remote = lib_remote.RemotePainter()
        remote.checkConnection()
    except Exception as e:
        print(f"Error: Could not connect to Substance Painter for baking: {e}")
        return False # Return False if connection fails

    # Path for Painter script should use forward slashes for QUrl
    hp_mesh_path_for_qurl = high_poly_mesh_path_str.replace('\\', '/')
    # List of baker names (strings) to enable, from global config BAKERS_TO_ENABLE
    baker_names_to_enable_list_str = "[" + ", ".join([f"'{baker_name}'" for baker_name in BAKERS_TO_ENABLE]) + "]"

    command_to_execute_bake = f"""
import substance_painter.project
import substance_painter.textureset
import substance_painter.baking
import substance_painter.exception
import time # For the requested pause and any other waits
import traceback # For detailed error logging
from PySide6 import QtCore # For QUrl

print("[PAINTER LOG] --- Python Mesh Baking Script Start (Default Output Size) ---")
ts_name_to_bake_for = "{target_texture_set_name}" # From function argument
hp_mesh_local_path = r"{hp_mesh_path_for_qurl}" # From function argument, forward slashes
# Bake output size will use Painter's default (typically TextureSet resolution)
baker_names_to_enable_from_config = {baker_names_to_enable_list_str} # From global config

# Mapping from string names (as in BAKERS_TO_ENABLE) to MeshMapUsage enums
mesh_map_usage_mapping = {{
    "Normal": substance_painter.baking.MeshMapUsage.Normal,
    "WorldSpaceNormal": substance_painter.baking.MeshMapUsage.WorldSpaceNormal,
    "ID": substance_painter.baking.MeshMapUsage.ID,
    "AO": substance_painter.baking.MeshMapUsage.AO,
    "Curvature": substance_painter.baking.MeshMapUsage.Curvature,
    "Position": substance_painter.baking.MeshMapUsage.Position,
    "Thickness": substance_painter.baking.MeshMapUsage.Thickness,
    # Add other mappings here if needed (e.g., BentNormals, etc.)
    # "ColorMapFromMesh": substance_painter.baking.MeshMapUsage.ColorMapFromMesh, # Example for vertex color baking
}}

if not substance_painter.project.is_open():
    print("[PAINTER LOG] ERROR: No project is open. Cannot perform baking.")
else:
    try:
        # Find the target TextureSet object
        all_texture_sets_in_project = substance_painter.textureset.all_texture_sets()
        target_ts_object_for_bake = None
        for ts_obj_loop_var in all_texture_sets_in_project:
            if ts_obj_loop_var.name == ts_name_to_bake_for:
                target_ts_object_for_bake = ts_obj_loop_var
                break
        
        if not target_ts_object_for_bake:
            print(f"[PAINTER LOG] ERROR: Texture Set '{{ts_name_to_bake_for}}' not found in the project.")
        else:
            print(f"[PAINTER LOG] Found Texture Set '{{target_ts_object_for_bake.name}}' for baking.")
            
            # Get BakingParameters for the specific texture set
            # Using from_texture_set_name or from_texture_set (if you have the object)
            baking_parameters_instance = substance_painter.baking.BakingParameters.from_texture_set(target_ts_object_for_bake)
            
            if not baking_parameters_instance:
                print(f"[PAINTER LOG] ERROR: Could not get baking parameters for '{{target_ts_object_for_bake.name}}'.")
            else:
                print(f"[PAINTER LOG] Successfully retrieved baking parameters for '{{target_ts_object_for_bake.name}}'.")
                
                common_baking_params_dict = baking_parameters_instance.common()
                
                hp_mesh_qurl_str = QtCore.QUrl.fromLocalFile(hp_mesh_local_path).toString()
                print(f"[PAINTER LOG] High Poly Mesh Path (QUrl.toString()): {{hp_mesh_qurl_str}}")

                # Set common baking parameters (only HipolyMesh, OutputSize will be default)
                print("[PAINTER LOG] Setting common baking parameters (HipolyMesh)...")
                substance_painter.baking.BakingParameters.set({{
                    common_baking_params_dict['HipolyMesh']: hp_mesh_qurl_str
                    # No 'OutputSize' here, so Painter uses default
                }})
                print(f"[PAINTER LOG] Common parameters set: HipolyMesh={{hp_mesh_qurl_str}}. OutputSize will use Painter defaults.")

                # Pause as originally requested in one of the script versions
                print("[PAINTER LOG] High-poly mesh path parameter has been set.")
                print("[PAINTER LOG] Pausing for 30 seconds before configuring bakers and starting bake...")
                time.sleep(30) # The requested 30-second pause
                print("[PAINTER LOG] Pause finished. Continuing with bake setup.")

                # Configure which bakers to enable
                baker_enums_to_enable = []
                print("[PAINTER LOG] Preparing list of bakers to enable:")
                for baker_name_str_config in baker_names_to_enable_from_config:
                    if baker_name_str_config in mesh_map_usage_mapping:
                        baker_enum_val = mesh_map_usage_mapping[baker_name_str_config]
                        baker_enums_to_enable.append(baker_enum_val)
                        print(f"[PAINTER LOG] - Queued for enabling: {{baker_name_str_config}} (Enum: {{baker_enum_val}})")
                    else:
                        print(f"[PAINTER LOG] - WARNING: Unknown baker name '{{baker_name_str_config}}' in configuration. Skipping.")
                
                if baker_enums_to_enable:
                    print(f"[PAINTER LOG] Setting enabled bakers to: {{[str(b) for b in baker_enums_to_enable]}}")
                    baking_parameters_instance.set_enabled_bakers(baker_enums_to_enable)
                    # Optional: Verification log
                    # current_enabled_bakers_after_set = baking_parameters_instance.get_enabled_bakers()
                    # print(f"[PAINTER LOG] Verification - Currently enabled bakers: {{[str(b) for b in current_enabled_bakers_after_set]}}")
                else:
                    print(f"[PAINTER LOG] WARNING: No valid bakers were specified or found in mapping. Baking might produce no maps.")

                # Start the asynchronous bake for the target TextureSet object
                print(f"[PAINTER LOG] Starting asynchronous bake for Texture Set '{{target_ts_object_for_bake.name}}'...")
                # Pass the TextureSet object directly to bake_async
                stop_source_handle = substance_painter.baking.bake_async(target_ts_object_for_bake)
                
                if stop_source_handle:
                    print(f"[PAINTER LOG] SUCCESS: Asynchronous bake initiated for '{{target_ts_object_for_bake.name}}'.")
                    print("PYTHON_SCRIPT_BAKE_INITIATED_SUCCESSFULLY") # Signal for external script
                else:
                    print(f"[PAINTER LOG] ERROR: Failed to initiate bake for '{{target_ts_object_for_bake.name}}'. bake_async returned None or falsy value.")

    except substance_painter.exception.ProjectError as pe_bake:
        print(f"[PAINTER LOG] !!! ProjectError during baking: {{str(pe_bake)}}")
    except KeyError as ke_bake: # If 'HipolyMesh' key is wrong, for example
        print(f"[PAINTER LOG] !!! KeyError during baking parameter setup: {{str(ke_bake)}}")
    except AttributeError as ae_bake: # If an object is None or API changed
        print(f"[PAINTER LOG] !!! AttributeError during baking: {{str(ae_bake)}}")
    except Exception as e_general_bake:
        print(f"[PAINTER LOG] !!! EXCEPTION during baking: {{str(e_general_bake)}}")
        traceback.print_exc()

print("[PAINTER LOG] --- Python Mesh Baking Script End (Default Output Size) ---")
"""
    print(f"\n--- Sending Bake Command to Painter ---")
    try:
        response_from_painter = remote.execScript(command_to_execute_bake, "python")
        print("\n--- Response from Painter's Python (stdout/stderr for bake) ---")
        if response_from_painter:
            print(response_from_painter)
            if "PYTHON_SCRIPT_BAKE_INITIATED_SUCCESSFULLY" in response_from_painter:
                print("Bake initiation confirmed by Painter script.")
                bake_initiated_signal = True
            else:
                print("Bake initiation NOT confirmed by Painter script. Check Painter's log.")
        else:
            print("No explicit stdout from Painter's Python script for bake, check Painter's log/UI.")
        print("----------------------------------------------------------------\n")
    except lib_remote.ExecuteScriptError as ese:
        print(f"!!! Painter's API reported an ERROR during bake script execution: {ese}")
    except Exception as e:
        print(f"!!! An error occurred sending the bake command or processing response: {e}")
    
    return bake_initiated_signal


# Part 5: Save Project
# Part 5: Save Project
def run_save_project(project_full_save_path): # Takes the full path for the .spp file
    project_save_dir = os.path.dirname(project_full_save_path)

    if not os.path.exists(project_save_dir):
        try:
            os.makedirs(project_save_dir)
            print(f"Created output directory for project file: {project_save_dir}")
        except OSError as e:
            print(f"!!! ERROR: Could not create project output directory '{project_save_dir}': {e}")
            return False

    # Convert path to forward slashes for the command string sent to Painter
    save_file_path_for_painter_cmd = project_full_save_path.replace('\\', '/')

    print(f"\n--- Attempting to Save Project to: {project_full_save_path} ---")
    print(f"    (Path being sent to Painter command: {save_file_path_for_painter_cmd})")
    save_successful_signal = False

    try:
        remote = lib_remote.RemotePainter()
        remote.checkConnection()
    except Exception as e:
        print(f"Error: Could not connect to Substance Painter for saving project: {e}")
        return False

    # This Painter script string formatting is IDENTICAL to your old working version,
    # except it uses save_file_path_for_painter_cmd derived from the function argument.
    command_to_execute_save = f"""
import substance_painter.project
import substance_painter.exception
import time # Added for sleep, was in old version too
import os   # Was in old version too (implicitly via time import)

print("[PAINTER LOG] --- Python Save Project Script Start ---")
save_path_in_painter = "{save_file_path_for_painter_cmd}" # Direct embedding with quotes

if not substance_painter.project.is_open():
    print("[PAINTER LOG] ERROR: No project is open. Cannot save.")
else:
    try:
        print(f"[PAINTER LOG] Attempting to save project to: {{save_path_in_painter}}")
        substance_painter.project.save_as(save_path_in_painter, mode=substance_painter.project.ProjectSaveMode.Full)
        
        time.sleep(0.5) 
        current_project_path = substance_painter.project.file_path() # Changed var name to match old
        
        normalized_current_path = ""
        if current_project_path:
            # Using the exact normalization from your old working version
            normalized_current_path = current_project_path.replace('\\\\', '/').lower() 
        
        # In your old version, this was also lowercased for comparison
        normalized_save_path_in_painter_for_compare = save_path_in_painter.lower()

        if current_project_path and normalized_current_path == normalized_save_path_in_painter_for_compare:
             print(f"[PAINTER LOG] SUCCESS: Project saved to '{{save_path_in_painter}}'. Current project path is '{{current_project_path}}'")
             print("PYTHON_SCRIPT_PROJECT_SAVED_SUCCESSFULLY")
        else:
            # This part is slightly different in your old version - let's match it:
            print(f"[PAINTER LOG] WARNING: Project save_as called. Painter's current project path is '{{current_project_path}}'. Expected path was '{{save_path_in_painter}}'.")
            # Old version assumed success if no exception:
            print("PYTHON_SCRIPT_PROJECT_SAVED_SUCCESSFULLY") 
            
    except substance_painter.exception.ProjectError as pe:
        print(f"[PAINTER LOG] !!! ProjectError during save: {{str(pe)}}")
    except Exception as e_save:
        print(f"[PAINTER LOG] !!! EXCEPTION during save: {{str(e_save)}}")
        import traceback
        traceback.print_exc()

print("[PAINTER LOG] --- Python Save Project Script End ---")
"""
    # The rest of the function (sending command, checking response) remains the same as your old version.
    print(f"\n--- Sending Save Project Command to Painter ---")
    try:
        response_from_painter = remote.execScript(command_to_execute_save, "python")
        print("\n--- Response from Painter's Python (stdout/stderr for save) ---")
        if response_from_painter:
            print(response_from_painter)
            if "PYTHON_SCRIPT_PROJECT_SAVED_SUCCESSFULLY" in response_from_painter:
                save_successful_signal = True
                print("Project save signaled as successful by Painter.")
            else:
                if '"error"' in response_from_painter.lower() and 'syntaxerror' in response_from_painter.lower():
                    print("Project save FAILED. Painter reported a SyntaxError in the executed script.")
                else:
                    print("Project save NOT signaled as successful by Painter script. Check logs and file system.")
        else:
            print("No explicit stdout from Painter's Python script for save, check Painter's log/UI.")
        print("-------------------------------------------------------------\n")
    except lib_remote.ExecuteScriptError as ese:
        print(f"!!! Painter's API reported an ERROR during save script execution: {ese}")
    except Exception as e:
        print(f"!!! An error occurred sending the save command or processing response: {e}")
        # print("--- FAILED COMMAND STRING (save) ---") # Optional debug
        # print(command_to_execute_save)
        # print("--- END FAILED COMMAND STRING ---")

    return save_successful_signal

# Part 6: Export Textures using glTF PBR Metal Roughness PREDEFINED PRESET
def run_export_textures_gltf_preset(texture_set_name_to_export, output_directory_for_textures):
    print(f"\n--- Attempting to Export Textures for '{texture_set_name_to_export}' using 'glTF PBR Metal Roughness' preset ---")
    print(f"Output directory for textures: {output_directory_for_textures}")
    export_successful_signal = False

    # Ensure the output directory for textures exists
    if not os.path.exists(output_directory_for_textures):
        try:
            os.makedirs(output_directory_for_textures)
            print(f"Created output directory for textures: {output_directory_for_textures}")
        except OSError as e:
            print(f"!!! ERROR: Could not create output directory '{output_directory_for_textures}' for textures: {e}")
            return False # Cannot export if directory can't be made

    try:
        remote = lib_remote.RemotePainter()
        remote.checkConnection()
    except Exception as e:
        print(f"Error: Could not connect to Substance Painter for exporting textures: {e}")
        return False # Cannot export if not connected

    # Convert output directory path to forward slashes for the Painter script
    output_dir_for_painter_cmd = output_directory_for_textures.replace('\\', '/')

    # The known URL for the predefined "glTF PBR Metal Roughness" export preset
    # This preset is generally built into Painter.
    gltf_preset_url = "export-preset-generator://gltf"

    # Construct the export configuration dictionary
    # This dictionary structure matches what substance_painter.export.export_project_textures expects.
    export_config_dict = {
        "exportShaderParams": False,  # Typically false unless you need shader parameters
        "exportPath": output_dir_for_painter_cmd, # Where the textures will be saved
        "defaultExportPreset": gltf_preset_url, # Using the direct generator URL for the glTF preset
        "exportList": [ # Specifies which texture sets to export
            {"rootPath": texture_set_name_to_export}
            # If exporting multiple texture sets, add more dictionaries here:
            # {"rootPath": "AnotherTextureSetName"}
        ],
        "exportParameters": [ # Parameters for each texture set in exportList (matched by order or rootPath)
            {
                # "rootPath": texture_set_name_to_export, # Optional: can explicitly link params to texture set
                "parameters": {
                    "paddingAlgorithm": "infinite", # Common padding options: "infinite", "dilation" (older), "passthrough"
                    "dilationDistance": 16, # Used if paddingAlgorithm is "dilation" or similar
                    # File format, bit depth, and size are usually determined by the export preset itself.
                    # If you need to override them, you can add keys like:
                    # "fileFormat": "png",
                    # "bitDepth": "8",
                    # "sizeLog2": "11" # for 2048 (2^11), 12 for 4096 (2^12)
                }
            }
        ]
    }
    # Convert the dictionary to a JSON string to safely embed it in the f-string
    export_config_json_str_for_fstring = json.dumps(export_config_dict)

    command_to_execute_export = f"""
import substance_painter.project
import substance_painter.export
import substance_painter.resource # For ResourceID if needed, though preset URL is direct
import substance_painter.exception
import json
import traceback

print("[PAINTER LOG] --- Python Texture Export (glTF Preset) Script Start ---")
# The JSON string is embedded here. Using triple single quotes for multi-line f-string compatibility.
export_config_json_string = '''{export_config_json_str_for_fstring}'''

if not substance_painter.project.is_open():
    print("[PAINTER LOG] ERROR: No project is open. Cannot export textures.")
else:
    try:
        print("[PAINTER LOG] Loading export configuration with direct preset URL...")
        config_from_json = json.loads(export_config_json_string) # Parse the JSON string
        
        # Log some details from the loaded config for verification
        preset_url_in_use = config_from_json.get('defaultExportPreset', 'NOT SET')
        export_path_in_use = config_from_json.get('exportPath', 'NOT SET')
        texture_set_to_export_name = "UNKNOWN"
        if config_from_json.get('exportList') and len(config_from_json['exportList']) > 0:
            texture_set_to_export_name = config_from_json['exportList'][0].get('rootPath', 'UNKNOWN')

        print(f"[PAINTER LOG] Export configuration details:")
        print(f"[PAINTER LOG]   Preset URL: {{preset_url_in_use}}")
        print(f"[PAINTER LOG]   Export Path: {{export_path_in_use}}")
        print(f"[PAINTER LOG]   Target TextureSet: {{texture_set_to_export_name}}")

        # No need to search for the preset resource if we have the direct generator URL.
        # substance_painter.export.export_project_textures can handle these URLs.

        print("[PAINTER LOG] Starting texture export with glTF preset...")
        export_result = substance_painter.export.export_project_textures(config_from_json)

        # Check the status of the export
        if export_result.status == substance_painter.export.ExportStatus.Success:
            print("[PAINTER LOG] SUCCESS: Texture export completed successfully.")
            print(f"[PAINTER LOG] Exported textures: {{export_result.textures}}") # List of exported file paths
            print("PYTHON_SCRIPT_TEXTURE_EXPORT_SUCCESSFUL")
        elif export_result.status == substance_painter.export.ExportStatus.Cancelled:
            # This usually means the user cancelled it if a dialog popped up (e.g. overwrite confirmation)
            # In a fully automated script, this is less likely unless Painter forces a dialog.
            print("[PAINTER LOG] WARNING: Texture export was cancelled.")
        elif export_result.status == substance_painter.export.ExportStatus.Warning:
            print("[PAINTER LOG] WARNING: Texture export completed with warnings.")
            print(f"[PAINTER LOG] Message: {{export_result.message}}")
            print(f"[PAINTER LOG] Exported textures (if any): {{export_result.textures}}")
            # Still consider it a success for automation if files were produced despite warnings
            print("PYTHON_SCRIPT_TEXTURE_EXPORT_SUCCESSFUL_WITH_WARNINGS")
        else: # substance_painter.export.ExportStatus.Error or other
            print(f"[PAINTER LOG] ERROR: Texture export failed.")
            print(f"[PAINTER LOG] Status: {{export_result.status}}")
            print(f"[PAINTER LOG] Message: {{export_result.message}}")

    except substance_painter.exception.ProjectError as pe_export:
        print(f"[PAINTER LOG] !!! ProjectError during texture export: {{str(pe_export)}}")
    except ValueError as ve_export: # e.g., JSON parsing error or invalid config structure
        print(f"[PAINTER LOG] !!! ValueError during texture export (JSON or config issue): {{str(ve_export)}}")
    except Exception as e_export:
        print(f"[PAINTER LOG] !!! EXCEPTION during texture export: {{str(e_export)}}")
        traceback.print_exc()

print("[PAINTER LOG] --- Python Texture Export (glTF Preset) Script End ---")
"""
    print(f"\n--- Sending Texture Export (glTF Preset) Command to Painter ---")
    try:
        response_from_painter = remote.execScript(command_to_execute_export, "python")
        print("\n--- Response from Painter's Python (stdout/stderr for texture export) ---")
        if response_from_painter:
            print(response_from_painter)
            # Check for either pure success or success with warnings
            if "PYTHON_SCRIPT_TEXTURE_EXPORT_SUCCESSFUL" in response_from_painter or \
               "PYTHON_SCRIPT_TEXTURE_EXPORT_SUCCESSFUL_WITH_WARNINGS" in response_from_painter:
                export_successful_signal = True
                print("Texture export signaled as successful (or with warnings) by Painter.")
            else:
                print("Texture export NOT signaled as successful by Painter script. Check logs.")
        else:
            print("No explicit stdout from Painter's Python script for texture export, check Painter's log/UI.")
        print("-----------------------------------------------------------------------\n")
    except lib_remote.ExecuteScriptError as ese:
        print(f"!!! Painter's API reported an ERROR during texture export script execution: {ese}")
    except Exception as e:
        print(f"!!! An error occurred sending the texture export command or processing response: {e}")

    return export_successful_signal



# Last Part: Main Automation Loop (Entry point when script is run directly)

if __name__ == "__main__":
    print("--- Substance Painter Batch Automation Script ---")
    print(f"Loading configuration from: {CONFIG_FILE_PATH}")
    # Config is already loaded globally at the script start, so 'config' variable is available.
    # Global variables like PROCESSED_OBJS_FOLDER, PAINTER_OUTPUT_BASE_FOLDER,
    # SMART_MATERIAL_NAME, SMART_MATERIAL_LOCATION, BAKERS_TO_ENABLE are also set.

    print(f"Scanning for processed meshes in: {PROCESSED_OBJS_FOLDER}")

    # Find all _low.obj files in the processed objects folder
    # os.path.join is used for platform-independent path construction
    # glob.glob finds files matching the pattern
    search_pattern_low_poly = os.path.join(PROCESSED_OBJS_FOLDER, "*_low.obj")
    low_poly_files = glob.glob(search_pattern_low_poly)

    if not low_poly_files:
        print(f"No qualifying '*_low.obj' files found in '{PROCESSED_OBJS_FOLDER}'. Exiting.")
        exit() # Exit if no files to process

    print(f"Found {len(low_poly_files)} low-poly meshes to process.")
    print("-" * 60) # Separator

    assets_processed_count = 0
    assets_skipped_count = 0
    assets_with_errors_count = 0

    # --- Initial Painter Connection Check (Optional but good for early failure) ---
    try:
        print("Attempting initial connection to Substance Painter...")
        remote_check = lib_remote.RemotePainter() # Create an instance
        remote_check.checkConnection()      # Check the connection
        print("Successfully connected to Substance Painter instance.")
    except Exception as e:
        print(f"CRITICAL ERROR: Could not connect to Substance Painter: {e}")
        print("Ensure Painter is running with '--enable-remote-scripting'. Exiting script.")
        exit(1) # Exit if initial connection fails
    print("-" * 60)

    # --- Loop Through Each Asset ---
    for low_poly_path in low_poly_files:
        asset_filename_low = os.path.basename(low_poly_path)  # e.g., Hull019_low.obj
        # Derive asset_base_name by removing "_low.obj"
        asset_base_name = asset_filename_low[:-8] if asset_filename_low.endswith("_low.obj") else os.path.splitext(asset_filename_low)[0]

        high_poly_filename = f"{asset_base_name}_high.obj"
        high_poly_path = os.path.join(PROCESSED_OBJS_FOLDER, high_poly_filename)

        print(f"\n\n{'='*25} Processing Asset: {asset_base_name} {'='*25}")
        print(f"  Low Poly Path: {low_poly_path}")
        print(f"  High Poly Path: {high_poly_path}")

        # Check if the corresponding high-poly mesh exists
        if not os.path.exists(high_poly_path):
            print(f"  WARNING: Corresponding high-poly mesh '{high_poly_path}' not found.")
            print(f"  Skipping asset: {asset_base_name}")
            assets_skipped_count += 1
            print("-" * 60)
            continue # Move to the next asset in the loop

        # Define output paths for this specific asset
        # Textures and .spp project file will go into a subfolder named after the asset_base_name
        asset_specific_output_folder = os.path.join(PAINTER_OUTPUT_BASE_FOLDER, asset_base_name)
        project_spp_full_save_path = os.path.join(asset_specific_output_folder, f"{asset_base_name}.spp")
        # Texture export will also use asset_specific_output_folder

        # --- Step 1: Create the project ---
        print("\n--- Starting Part 1: Project Creation ---")
        # Note: run_project_creation_only handles its own Painter connection and error returns
        run_project_creation_only(low_poly_path)
        print("Part 1 (Project Creation) command sequence sent.")
        inter_step_wait_1 = 30 # Seconds
        print(f"Waiting for {inter_step_wait_1} seconds for Painter to process project creation...")
        time.sleep(inter_step_wait_1)

        # --- Step 2: Rename the texture set ---
        print("\n--- Starting Part 2: Texture Set Renaming ---")
        # Derive texture set name (e.g., M_Hull019)
        intended_texture_set_name = f"M_{asset_base_name}"
        print(f"Target texture set name: '{intended_texture_set_name}'.")
        rename_ok = run_rename_texture_set(intended_texture_set_name)
        if not rename_ok:
            print(f"  WARNING: Renaming texture set for {asset_base_name} might have failed or was not confirmed.")
            # Proceeding with intended_texture_set_name for subsequent steps
        current_texture_set_name_for_ops = intended_texture_set_name # Use this for subsequent steps
        inter_step_wait_2 = 1
        print(f"Waiting for {inter_step_wait_2} seconds...")
        time.sleep(inter_step_wait_2)

        # --- Step 3: Apply Smart Material ---
        print("\n--- Starting Part 3: Apply Smart Material ---")
        print(f"Applying Smart Material '{SMART_MATERIAL_NAME}' from shelf '{SMART_MATERIAL_LOCATION}'.")
        apply_sm_ok = run_apply_smart_material(SMART_MATERIAL_NAME, SMART_MATERIAL_LOCATION)
        if not apply_sm_ok:
            print(f"  WARNING: Applying Smart Material for {asset_base_name} might have failed or was not confirmed.")
        inter_step_wait_3 = 5
        print(f"Waiting for {inter_step_wait_3} seconds...")
        time.sleep(inter_step_wait_3)

        # --- Step 4: Bake High-Resolution Mesh ---
        print("\n--- Starting Part 4: Mesh Baking ---")
        print(f"Baking for texture set '{current_texture_set_name_for_ops}' using high-poly '{high_poly_path}'.")
        bake_initiated_ok = run_bake_high_res_mesh(current_texture_set_name_for_ops, high_poly_path)
        if bake_initiated_ok:
            print("  Bake successfully initiated by Painter. Waiting for baking process to run...")
            baking_process_wait_time = 1  # Adjust as needed based on mesh complexity and PC speed
            for i in range(baking_process_wait_time):
                time.sleep(1)
                print(f"  Baking observation wait: {i+1}/{baking_process_wait_time}s completed.", end='\r')
            print(f"\n  Assumed baking observation time of {baking_process_wait_time}s has passed.                            ")
        else:
            print(f"  WARNING: Bake initiation failed or was not confirmed for {asset_base_name}.")
        inter_step_wait_4 = 60
        print(f"Waiting for {inter_step_wait_4} seconds post-bake-wait...")
        time.sleep(inter_step_wait_4)

        # --- Step 5: Save the project ---
        print("\n--- Starting Part 5: Save Project ---")
        print(f"Saving project to: {project_spp_full_save_path}")
        save_ok = run_save_project(project_spp_full_save_path)
        if not save_ok:
            print(f"  WARNING: Saving project {project_spp_full_save_path} might have failed or was not confirmed.")
        inter_step_wait_5 = 10
        print(f"Waiting for {inter_step_wait_5} seconds post-save...")
        time.sleep(inter_step_wait_5)

        # --- Step 6: Export Textures ---
        print("\n--- Starting Part 6: Texture Export ---")
        print(f"Exporting textures for '{current_texture_set_name_for_ops}' to directory '{asset_specific_output_folder}'.")
        export_ok = run_export_textures_gltf_preset(current_texture_set_name_for_ops, asset_specific_output_folder)
        if not export_ok:
            print(f"  WARNING: Texture export for {asset_base_name} might have failed or was not confirmed.")
            assets_with_errors_count +=1 # Increment if a crucial step like export fails
        else:
            assets_processed_count += 1

        print(f"\n--- Finished processing asset: {asset_base_name} ---")
        print("-" * 60)
        # Optional: Add a longer pause between processing each full asset in Painter if UI seems slow
        # print("Pausing briefly before starting next asset...")
        # time.sleep(10)

    # --- Batch Process Summary ---
    print("\n\n" + "="*70)
    print("Substance Painter Batch Automation Complete.")
    print(f"Total low-poly files found: {len(low_poly_files)}")
    print(f"Successfully processed and exported: {assets_processed_count} assets.")
    print(f"Assets skipped (e.g., missing high-poly): {assets_skipped_count} assets.")
    if assets_with_errors_count > 0 : # Only show if there were errors on processed assets
         print(f"Assets processed but with warnings/errors in later stages (e.g. export): {assets_with_errors_count} assets.")
    print("="*70)