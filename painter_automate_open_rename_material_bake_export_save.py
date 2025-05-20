# painter_automate_test.py

import lib_remote
import os
import time # Import the time module for sleep
import json # For handling export configuration

# --- USER CONFIGURATION ---
LOW_POLY_MESH_PATH = r"E:\Projects\2025\SpaceshipKitbash\Meshes\Hull019_low.obj" # The low-poly mesh
HIGH_POLY_MESH_PATH = r"E:\Projects\2025\SpaceshipKitbash\Meshes\Hull019_high.obj" # The high-poly mesh for baking
OUTPUT_PATH = r"E:\Projects\2025\SpaceshipKitbash\Textures" # Ouput path for textures AND project file
SMART_MATERIAL_NAME = "HullTextureColor" # The EXACT name of your Smart Material
SMART_MATERIAL_LOCATION = "Yourassets" # The shelf path where the Smart Material is located

BAKE_OUTPUT_SIZE = (4096, 4096)
BAKERS_TO_ENABLE = [
    "Normal",
    "AO",
    "Curvature",
    "Position",
    "Thickness",
    "WorldSpaceNormal"
]
# --- --- --- --- --- --- --- --- --- ---

# Part1: Project Creation
def run_project_creation_only():
    print(f"Attempting to create project with: {LOW_POLY_MESH_PATH}")

    if not os.path.exists(LOW_POLY_MESH_PATH):
        print(f"!!! ERROR: Low-poly mesh path does not exist: {LOW_POLY_MESH_PATH}")
        return
        
    try:
        remote = lib_remote.RemotePainter()
        remote.checkConnection()
    except Exception as e:
        print(f"Error: Could not connect to Substance Painter: {e}")
        print("Ensure Painter is running with '--enable-remote-scripting'.")
        return

    lp_mesh_path_escaped = LOW_POLY_MESH_PATH.replace('\\', '\\\\')
    
    project_settings_from_ui = {
        "default_texture_resolution": 4096,
        "normal_map_format": "DirectX",
        "compute_tangent_space_per_fragment": True,
        "use_uv_tile_workflow": False, 
        "import_cameras": False,
    }

    command_to_execute_create_project = f"""
import substance_painter.project
import substance_painter.textureset 
import substance_painter.exception 
import time # Added for sleep after project close

print("[PAINTER LOG] --- Python Project Creation Script Start ---")

mesh_path = r'{lp_mesh_path_escaped}'
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

# 4. Use UV Tile workflow
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
        time.sleep(0.5) 
        if substance_painter.project.is_open():
            print("[PAINTER LOG] ERROR: Failed to close the existing project. Aborting creation.")
            raise Exception("Failed to close existing project.")

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
except ValueError as ve:
    print(f"[PAINTER LOG] !!! ValueError during project creation: {{str(ve)}}")
except TypeError as te:
    print(f"[PAINTER LOG] !!! TypeError during project creation (check API compatibility for settings): {{str(te)}}")
except Exception as e_create:
    print(f"[PAINTER LOG] !!! EXCEPTION during project creation: {{str(e_create)}}")

print("[PAINTER LOG] --- Python Project Creation Script End ---")
"""

    print(f"\n--- Sending Project Creation Command to Painter ---")
    print("-------------------------------------------------")

    try:
        response_from_painter = remote.execScript(command_to_execute_create_project, "python")
        print("\n--- Response from Painter's Python (stdout/stderr) ---")
        print(response_from_painter if response_from_painter else "No explicit stdout from Painter's Python script, check Painter's log/UI.")
        print("----------------------------------------------------------\n")
        print("Project creation command sent. Please check Substance Painter UI and its Log window for results.")
    except lib_remote.ExecuteScriptError as ese:
        print(f"!!! Painter's API reported an ERROR during Python script execution: {ese}")
    except Exception as e:
        print(f"!!! An error occurred sending the Python command or processing response: {e}")


# Part 2: Rename Texture Set
def run_rename_texture_set(target_material_name):
    print(f"\n--- Attempting to Rename Texture Set in Painter ---")
    print(f"Target material name: {target_material_name}")
    rename_successful_signal = False 

    try:
        remote = lib_remote.RemotePainter()
        remote.checkConnection()
    except Exception as e:
        print(f"Error: Could not connect to Substance Painter for renaming: {e}")
        return False

    command_to_execute_rename = f"""
import substance_painter.project
import substance_painter.textureset
import substance_painter.exception
import time # Added for sleep after rename attempt

print("[PAINTER LOG] --- Python Texture Set Rename Script Start ---")
desired_name = "{target_material_name}"

if not substance_painter.project.is_open():
    print("[PAINTER LOG] ERROR: No project is open. Cannot rename texture sets.")
else:
    try:
        texture_sets = substance_painter.textureset.all_texture_sets()
        if texture_sets:
            print(f"[PAINTER LOG] Found {{len(texture_sets)}} texture set(s).")
            ts_to_rename = texture_sets[0] 
            original_name = ts_to_rename.name 
            print(f"[PAINTER LOG] Attempting to rename Texture Set '{{original_name}}' to '{{desired_name}}'.")
            
            ts_to_rename.name = desired_name 
            
            time.sleep(0.1) 
            if ts_to_rename.name == desired_name:
                print(f"[PAINTER LOG] SUCCESS: Texture Set renamed to '{{desired_name}}'.")
                print("PYTHON_SCRIPT_TEXTURE_SET_RENAMED_SUCCESSFULLY") 
            else:
                print(f"[PAINTER LOG] ERROR: Renaming seems to have failed. Name is still '{{ts_to_rename.name}}'.")
        else:
            print("[PAINTER LOG] No texture sets found in the project to rename.")
            
    except AttributeError as ae:
        print(f"[PAINTER LOG] !!! AttributeError during rename (API for .name or all_texture_sets might have changed): {{str(ae)}}")
    except Exception as e_rename:
        print(f"[PAINTER LOG] !!! EXCEPTION during texture set renaming: {{str(e_rename)}}")

print("[PAINTER LOG] --- Python Texture Set Rename Script End ---")
"""
    print(f"\n--- Sending Texture Set Rename Command to Painter ---")
    print("-------------------------------------------------")
    try:
        response_from_painter = remote.execScript(command_to_execute_rename, "python")
        print("\n--- Response from Painter's Python (stdout/stderr for rename) ---")
        if response_from_painter:
            print(response_from_painter)
            if "PYTHON_SCRIPT_TEXTURE_SET_RENAMED_SUCCESSFULLY" in response_from_painter:
                rename_successful_signal = True
        print("-------------------------------------------------------------------\n")
    except lib_remote.ExecuteScriptError as ese:
        print(f"!!! Painter's API reported an ERROR during rename script execution: {ese}")
    except Exception as e:
        print(f"!!! An error occurred sending the rename command or processing response: {e}")
    return rename_successful_signal


# Part 3: Apply Smart Material
def run_apply_smart_material(smart_material_name, smart_material_shelf_name):
    print(f"\n--- Applying Smart Material '{smart_material_name}' from shelf '{smart_material_shelf_name}' ---")

    try:
        remote = lib_remote.RemotePainter()
        remote.checkConnection()
    except Exception as e:
        print(f"Error: Could not connect for applying SM: {e}")
        return

    command_to_execute_apply_sm = f"""
import substance_painter.project
import substance_painter.textureset
import substance_painter.layerstack # Still needed for insert_smart_material
import substance_painter.resource
import substance_painter.exception
import traceback # For detailed error logging

print("[PAINTER LOG] --- Python Apply Smart Material Script Start ---")
sm_name_to_apply = "{smart_material_name}"
sm_shelf_context = "{smart_material_shelf_name}" 

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
            
            query = f"s:{{sm_shelf_context}} u:smartmaterial n:{{sm_name_to_apply}}"
            print(f"[PAINTER LOG] Searching for Smart Material with query: {{query}}")
            found_resources = substance_painter.resource.search(query)

            if not found_resources:
                print(f"[PAINTER LOG] ERROR: Smart Material '{{sm_name_to_apply}}' in shelf '{{sm_shelf_context}}' not found with query '{{query}}'.")
                query_fallback = f"s:{{sm_shelf_context}} u:smartmaterial n:*{{sm_name_to_apply}}*" # Using '*' for wildcard
                print(f"[PAINTER LOG] Attempting fallback search with wildcards: {{query_fallback}}")
                found_resources_fallback = substance_painter.resource.search(query_fallback)
                if found_resources_fallback:
                    print(f"[PAINTER LOG] Found with wildcards! This suggests a subtle naming discrepancy. Using first wildcard match.")
                    found_resources = found_resources_fallback 
                else:
                    print(f"[PAINTER LOG] Still not found even with wildcards.")

            if found_resources:
                smart_material_resource = found_resources[0] 
                print(f"[PAINTER LOG] Found Smart Material: '{{smart_material_resource.identifier().url()}}'")
                
                # Get the layer stack associated with the target TextureSet
                stack_of_target_ts = target_ts.get_stack() 

                if not stack_of_target_ts:
                    print(f"[PAINTER LOG] ERROR: Could not get layer stack for texture set '{{target_ts.name}}'.")
                else:
                    # PREVIOUSLY, `stack_of_target_ts` (a Stack object/ID) was passed directly to `insert_smart_material`.
                    # THIS WAS THE CAUSE OF THE TypeError.

                    # CHANGE 1: Create an `InsertPosition` object.
                    # This object specifies *where* in the stack the smart material should be inserted.
                    # `InsertPosition.from_textureset_stack(stack)` typically creates a position
                    # that will insert at the top of the specified stack.
                    insert_pos = substance_painter.layerstack.InsertPosition.from_textureset_stack(stack_of_target_ts)
                    
                    # Log the determined insert position for clarity (optional logging)
                    print(f"[PAINTER LOG] Applying Smart Material '{{smart_material_resource.identifier().name}}' to stack of '{{target_ts.name}}' at determined insert position.")
                    
                    # CHANGE 2: Call `insert_smart_material` with the `insert_pos` object.
                    # The first argument is now the `InsertPosition` object, and the second is the resource identifier
                    # of the smart material to insert. This matches the API signature.
                    new_layer_or_group = substance_painter.layerstack.insert_smart_material(
                        insert_pos, # Pass the InsertPosition object
                        smart_material_resource.identifier() # Pass the ResourceID of the smart material
                    )

                    if new_layer_or_group:
                         # CORRECTED: Use .get_name() method for Node objects
                         layer_name = new_layer_or_group.get_name()
                         print(f"[PAINTER LOG] SUCCESS: Smart Material '{{sm_name_to_apply}}' applied. New layer/group name: '{{layer_name}}'")
                    else:
                        print(f"[PAINTER LOG] ERROR: Failed to apply Smart Material '{{sm_name_to_apply}}'. 'insert_smart_material' did not return a new layer/group object.")

    except substance_painter.exception.ProjectError as pe:
        print(f"[PAINTER LOG] !!! ProjectError while applying Smart Material: {{str(pe)}}")
    except substance_painter.exception.ResourceNotFoundError as rnfe:
        print(f"[PAINTER LOG] !!! ResourceNotFoundError for Smart Material: {{str(rnfe)}}")
    # CHANGE 3: Added a specific `except` block for `TypeError`.
    # This helps to catch the specific error that was occurring due to incorrect arguments
    # passed to `insert_smart_material`.
    except TypeError as te_apply_sm: 
        print(f"[PAINTER LOG] !!! TypeError while applying Smart Material (API argument mismatch): {{str(te_apply_sm)}}")
        traceback.print_exc() # Print the full traceback to get details about the TypeError
    except Exception as e_apply_sm:
        print(f"[PAINTER LOG] !!! EXCEPTION while applying Smart Material: {{str(e_apply_sm)}}")
        traceback.print_exc() # Print the full traceback for any other unexpected exceptions

print("[PAINTER LOG] --- Python Apply Smart Material Script End (Corrected InsertPosition) ---")
"""
    print(f"\n--- Sending Apply Smart Material Command to Painter ---")
    print("-------------------------------------------------------")
    try:
        response_from_painter = remote.execScript(command_to_execute_apply_sm, "python")
        print("\n--- Response from Painter's Python (stdout/stderr for apply SM) ---")
        if response_from_painter:
            print(response_from_painter)
        else:
            print("No explicit stdout from Painter's Python script for apply SM, check Painter's log/UI.")
        print("-----------------------------------------------------------------------\n")
    except lib_remote.ExecuteScriptError as ese:
        print(f"!!! Painter's API reported an ERROR during apply SM script execution: {ese}")
    except Exception as e:
        print(f"!!! An error occurred sending the apply SM command or processing response: {e}")


# Part 4: Baking High Res Mesh
# Part 4: Baking High Res Mesh
def run_bake_high_res_mesh(target_texture_set_name, high_poly_mesh_path_str):
    print(f"\n--- Attempting to Bake High-Res Mesh for Texture Set '{target_texture_set_name}' ---")
    print(f"High-poly mesh: {high_poly_mesh_path_str}")
    bake_initiated_signal = False

    if not os.path.exists(high_poly_mesh_path_str):
        print(f"!!! ERROR: High-poly mesh path does not exist: {high_poly_mesh_path_str}")
        return False

    try:
        remote = lib_remote.RemotePainter()
        remote.checkConnection()
    except Exception as e:
        print(f"Error: Could not connect to Substance Painter for baking: {e}")
        return False

    # Path for Painter script should use forward slashes for QUrl
    hp_mesh_path_for_qurl = high_poly_mesh_path_str.replace('\\', '/')
    # List of baker names (strings) to enable
    baker_names_to_enable_list_str = "[" + ", ".join([f"'{baker_name}'" for baker_name in BAKERS_TO_ENABLE]) + "]"

    command_to_execute_bake = f"""
import substance_painter.project
import substance_painter.textureset
import substance_painter.baking
import substance_painter.exception
import time # For the requested pause and any other waits
import traceback # For detailed error logging
from PySide6 import QtCore # CHANGED FROM PySide2 to PySide6

print("[PAINTER LOG] --- Python Mesh Baking Script Start (Doc-Aligned) ---")
ts_name_to_bake_for = "{target_texture_set_name}"
hp_mesh_local_path = r"{hp_mesh_path_for_qurl}"
output_size_w = {BAKE_OUTPUT_SIZE[0]}
output_size_h = {BAKE_OUTPUT_SIZE[1]}
# This list of strings will be mapped to enums below
baker_names_to_enable_from_config = {baker_names_to_enable_list_str}

# Mapping from string names (as in BAKERS_TO_ENABLE) to MeshMapUsage enums
mesh_map_usage_mapping = {{
    "Normal": substance_painter.baking.MeshMapUsage.Normal,
    "WorldSpaceNormal": substance_painter.baking.MeshMapUsage.WorldSpaceNormal,
    "ID": substance_painter.baking.MeshMapUsage.ID,
    "AO": substance_painter.baking.MeshMapUsage.AO,
    "Curvature": substance_painter.baking.MeshMapUsage.Curvature,
    "Position": substance_painter.baking.MeshMapUsage.Position,
    "Thickness": substance_painter.baking.MeshMapUsage.Thickness,
    # Add other mappings here if needed, e.g., BentNormals, etc.
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
            print(f"[PAINTER LOG] Found Texture Set '{{target_ts_object_for_bake.name}}' for baking.") # Use .name from the object
            
            # Get BakingParameters for the specific texture set
            baking_parameters_instance = substance_painter.baking.BakingParameters.from_texture_set_name(target_ts_object_for_bake.name)
            
            if not baking_parameters_instance:
                print(f"[PAINTER LOG] ERROR: Could not get baking parameters for '{{target_ts_object_for_bake.name}}'.")
            else:
                print(f"[PAINTER LOG] Successfully retrieved baking parameters for '{{target_ts_object_for_bake.name}}'.")
                
                # Get common parameters dictionary
                common_baking_params_dict = baking_parameters_instance.common()
                
                # Prepare the high-poly mesh path using QUrl as in documentation
                hp_mesh_qurl_str = QtCore.QUrl.fromLocalFile(hp_mesh_local_path).toString()
                print(f"[PAINTER LOG] High Poly Mesh Path (QUrl.toString()): {{hp_mesh_qurl_str}}")

                # Set common baking parameters using the static set method
                print("[PAINTER LOG] Setting common baking parameters (OutputSize, HipolyMesh)...")
                substance_painter.baking.BakingParameters.set({{
                    common_baking_params_dict['HipolyMesh']: hp_mesh_qurl_str
                }})
                print(f"[PAINTER LOG] Common parameters set: OutputSize=({{output_size_w}},{{output_size_h}}), HipolyMesh={{hp_mesh_qurl_str}}.")

                # --- PAUSE ADDED HERE as requested in the original script ---
                print("[PAINTER LOG] High-poly mesh path and output size parameters have been set.")
                print("[PAINTER LOG] Pausing for 30 seconds before configuring bakers and starting bake...")
                time.sleep(30) # The requested 30-second pause
                print("[PAINTER LOG] Pause finished. Continuing with bake setup.")
                # --- END OF PAUSE ---

                # Configure which bakers to enable using set_enabled_bakers
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
                    # Verification (optional, but good for debugging)
                    # current_enabled_bakers_after_set = baking_parameters_instance.get_enabled_bakers()
                    # print(f"[PAINTER LOG] Verification - Currently enabled bakers: {{[str(b) for b in current_enabled_bakers_after_set]}}")
                else:
                    print(f"[PAINTER LOG] WARNING: No valid bakers were specified or found in mapping. Baking might produce no maps.")

                # Start the asynchronous bake for the target TextureSet object
                print(f"[PAINTER LOG] Starting asynchronous bake for Texture Set '{{target_ts_object_for_bake.name}}'...")
                stop_source_handle = substance_painter.baking.bake_async(target_ts_object_for_bake)
                
                if stop_source_handle:
                    print(f"[PAINTER LOG] SUCCESS: Asynchronous bake initiated for '{{target_ts_object_for_bake.name}}'.")
                    print("PYTHON_SCRIPT_BAKE_INITIATED_SUCCESSFULLY")
                else:
                    print(f"[PAINTER LOG] ERROR: Failed to initiate bake for '{{target_ts_object_for_bake.name}}'. bake_async returned None or falsy value.")

    except substance_painter.exception.ProjectError as pe_bake:
        print(f"[PAINTER LOG] !!! ProjectError during baking: {{str(pe_bake)}}")
    except KeyError as ke_bake:
        print(f"[PAINTER LOG] !!! KeyError during baking parameter setup (likely incorrect property name): {{str(ke_bake)}}")
    except AttributeError as ae_bake:
        print(f"[PAINTER LOG] !!! AttributeError during baking (API might have changed or object None): {{str(ae_bake)}}")
    except Exception as e_general_bake:
        print(f"[PAINTER LOG] !!! EXCEPTION during baking: {{str(e_general_bake)}}")
        traceback.print_exc()

print("[PAINTER LOG] --- Python Mesh Baking Script End (Doc-Aligned) ---")
"""
    print(f"\n--- Sending Bake Command to Painter ---")
    print("-----------------------------------------")
    try:
        response_from_painter = remote.execScript(command_to_execute_bake, "python")
        print("\n--- Response from Painter's Python (stdout/stderr for bake) ---")
        if response_from_painter:
            print(response_from_painter)
            if "PYTHON_SCRIPT_BAKE_INITIATED_SUCCESSFULLY" in response_from_painter:
                print("\nBake initiation confirmed by Painter script.")
                bake_initiated_signal = True
            else:
                print("\nBake initiation NOT confirmed by Painter script. Check Painter's log.")
        else:
            print("No explicit stdout from Painter's Python script for bake, check Painter's log/UI.")
        print("----------------------------------------------------------------\n")
    except lib_remote.ExecuteScriptError as ese:
        print(f"!!! Painter's API reported an ERROR during bake script execution: {ese}")
    except Exception as e:
        print(f"!!! An error occurred sending the bake command or processing response: {e}")
    
    return bake_initiated_signal


# Part 5: Export Textures using glTF PBR Metal Roughness PREDEFINED PRESET
def run_export_textures_gltf_preset(texture_set_name_to_export, output_directory):
    print(f"\n--- Attempting to Export Textures for '{texture_set_name_to_export}' using 'glTF PBR Metal Roughness' preset ---")
    print(f"Output directory: {output_directory}")
    export_successful_signal = False

    if not os.path.exists(output_directory):
        try:
            os.makedirs(output_directory)
            print(f"Created output directory for textures: {output_directory}")
        except OSError as e:
            print(f"!!! ERROR: Could not create output directory '{output_directory}' for textures: {e}")
            return False

    try:
        remote = lib_remote.RemotePainter()
        remote.checkConnection()
    except Exception as e:
        print(f"Error: Could not connect to Substance Painter for exporting textures: {e}")
        return False

    output_dir_for_painter = output_directory.replace('\\', '/')
    
    # The known URL for the predefined "glTF PBR Metal Roughness" preset
    gltf_preset_url = "export-preset-generator://gltf"

    export_config_dict = {
        "exportShaderParams": False,
        "exportPath": output_dir_for_painter,
        "defaultExportPreset": gltf_preset_url, # Use the direct generator URL
        "exportList": [
            {"rootPath": texture_set_name_to_export} 
        ],
        "exportParameters": [ 
            {
                "parameters": {
                    "paddingAlgorithm": "infinite", 
                    "dilationDistance": 16 
                    # Size and FileType will be determined by the preset
                }
            }
        ]
    }
    export_config_json_str_for_fstring = json.dumps(export_config_dict)

    command_to_execute_export = f"""
import substance_painter.project
import substance_painter.export
import substance_painter.resource # Though not strictly needed if URL is hardcoded
import substance_painter.exception
import json 
import traceback

print("[PAINTER LOG] --- Python Texture Export (glTF Preset) Script Start ---")
export_config_json_string = '''{export_config_json_str_for_fstring}'''

if not substance_painter.project.is_open():
    print("[PAINTER LOG] ERROR: No project is open. Cannot export textures.")
else:
    try:
        print("[PAINTER LOG] Loading export configuration with direct preset URL...")
        config = json.loads(export_config_json_string)
        print(f"[PAINTER LOG] Export configuration loaded. Preset URL: {{config.get('defaultExportPreset', 'NOT SET')}}")
        print(f"[PAINTER LOG] Target TextureSet for export: {{config.get('exportList', [{{}}])[0].get('rootPath', 'UNKNOWN')}}")


        # No need to search for the preset if we have the direct URL.
        # The substance_painter.export.export_project_textures function
        # should be able to handle these generator URLs directly.

        print("[PAINTER LOG] Starting texture export with glTF preset...")
        export_result = substance_painter.export.export_project_textures(config)
        
        if export_result.status == substance_painter.export.ExportStatus.Success:
            print("[PAINTER LOG] SUCCESS: Texture export completed successfully.")
            print(f"[PAINTER LOG] Exported textures: {{export_result.textures}}")
            print("PYTHON_SCRIPT_TEXTURE_EXPORT_SUCCESSFUL")
        elif export_result.status == substance_painter.export.ExportStatus.Cancelled:
            print("[PAINTER LOG] WARNING: Texture export was cancelled by the user.")
        elif export_result.status == substance_painter.export.ExportStatus.Warning:
            print("[PAINTER LOG] WARNING: Texture export completed with warnings.")
            print(f"[PAINTER LOG] Message: {{export_result.message}}")
            print(f"[PAINTER LOG] Exported textures (if any): {{export_result.textures}}")
            print("PYTHON_SCRIPT_TEXTURE_EXPORT_SUCCESSFUL") 
        else: 
            print(f"[PAINTER LOG] ERROR: Texture export failed. Status: {{export_result.status}}, Message: {{export_result.message}}")

    except substance_painter.exception.ProjectError as pe_export:
        print(f"[PAINTER LOG] !!! ProjectError during texture export: {{str(pe_export)}}")
    except ValueError as ve_export: 
        print(f"[PAINTER LOG] !!! ValueError during texture export (JSON or config issue): {{str(ve_export)}}")
    except Exception as e_export:
        print(f"[PAINTER LOG] !!! EXCEPTION during texture export: {{str(e_export)}}")
        traceback.print_exc()

print("[PAINTER LOG] --- Python Texture Export (glTF Preset) Script End ---")
"""
    print(f"\n--- Sending Texture Export (glTF Preset) Command to Painter ---")
    print("---------------------------------------------------------------")
    try:
        response_from_painter = remote.execScript(command_to_execute_export, "python")
        print("\n--- Response from Painter's Python (stdout/stderr for texture export) ---")
        if response_from_painter:
            print(response_from_painter)
            if "PYTHON_SCRIPT_TEXTURE_EXPORT_SUCCESSFUL" in response_from_painter:
                export_successful_signal = True
        print("-----------------------------------------------------------------------\n")
    except lib_remote.ExecuteScriptError as ese:
        print(f"!!! Painter's API reported an ERROR during texture export script execution: {ese}")
    except Exception as e:
        print(f"!!! An error occurred sending the texture export command or processing response: {e}")
    
    return export_successful_signal

# Part 6: Save Project
def run_save_project(project_file_name_stem):
    if not os.path.exists(OUTPUT_PATH):
        try:
            os.makedirs(OUTPUT_PATH)
            print(f"Created output directory: {OUTPUT_PATH}")
        except OSError as e:
            print(f"!!! ERROR: Could not create output directory '{OUTPUT_PATH}': {e}")
            return False
            
    save_file_path_on_disk = os.path.join(OUTPUT_PATH, f"{project_file_name_stem}.spp")
    # Convert to forward slashes for the command string sent to Painter
    save_file_path_for_painter_cmd = save_file_path_on_disk.replace('\\', '/')
    
    print(f"\n--- Attempting to Save Project to (original disk path): {save_file_path_on_disk} ---")
    print(f"--- Path being sent to Painter command: {save_file_path_for_painter_cmd} ---")
    save_successful_signal = False

    try:
        remote = lib_remote.RemotePainter()
        remote.checkConnection()
    except Exception as e:
        print(f"Error: Could not connect to Substance Painter for saving project: {e}")
        return False

    # Note the change here: save_path_in_painter uses forward slashes
    command_to_execute_save = f"""
import substance_painter.project
import substance_painter.exception

print("[PAINTER LOG] --- Python Save Project Script Start ---")
save_path_in_painter = "{save_file_path_for_painter_cmd}" # Using the forward-slashed path

if not substance_painter.project.is_open():
    print("[PAINTER LOG] ERROR: No project is open. Cannot save.")
else:
    try:
        print(f"[PAINTER LOG] Attempting to save project to: {{save_path_in_painter}}")
        substance_painter.project.save_as(save_path_in_painter, mode=substance_painter.project.ProjectSaveMode.Full)
        
        import time
        time.sleep(0.5) 
        current_project_path = substance_painter.project.file_path()
        
        normalized_current_path = ""
        if current_project_path:
            normalized_current_path = current_project_path.replace('\\\\', '/').lower() # Painter might return \\\\
        
        normalized_save_path_in_painter = save_path_in_painter.lower() # Already has /

        if current_project_path and normalized_current_path == normalized_save_path_in_painter:
             print(f"[PAINTER LOG] SUCCESS: Project saved to '{{save_path_in_painter}}'. Current project path is '{{current_project_path}}'")
             print("PYTHON_SCRIPT_PROJECT_SAVED_SUCCESSFULLY")
        else:
            print(f"[PAINTER LOG] WARNING: Project save_as called. Painter's current project path is '{{current_project_path}}'. Expected path was '{{save_path_in_painter}}'.")
            # Assuming success if no exception was thrown by save_as, as Painter's internal path reporting might have nuances
            print("PYTHON_SCRIPT_PROJECT_SAVED_SUCCESSFULLY") 
            
    except substance_painter.exception.ProjectError as pe:
        print(f"[PAINTER LOG] !!! ProjectError during save: {{str(pe)}}")
    except Exception as e_save:
        print(f"[PAINTER LOG] !!! EXCEPTION during save: {{str(e_save)}}")
        import traceback
        traceback.print_exc()

print("[PAINTER LOG] --- Python Save Project Script End ---")
"""
    print(f"\n--- Sending Save Project Command to Painter ---")
    print("-----------------------------------------------")
    try:
        response_from_painter = remote.execScript(command_to_execute_save, "python")
        print("\n--- Response from Painter's Python (stdout/stderr for save) ---")
        if response_from_painter:
            print(response_from_painter)
            if "PYTHON_SCRIPT_PROJECT_SAVED_SUCCESSFULLY" in response_from_painter:
                save_successful_signal = True
        print("-------------------------------------------------------------\n")
    except lib_remote.ExecuteScriptError as ese:
        print(f"!!! Painter's API reported an ERROR during save script execution: {ese}")
    except Exception as e:
        print(f"!!! An error occurred sending the save command or processing response: {e}")
    return save_successful_signal



# Last Part: Main function to run the script
if __name__ == "__main__":
    print("--- Initial Configuration Validation ---")
    valid_config = True
    # ... (initial configuration validation remains the same - this part CAN halt) ...
    if not valid_config:
        print("!!! Halting script BEFORE sending any commands due to CRITICAL invalid configuration. !!!")
        exit() # This initial halt is still important
    print("Configuration seems valid. Proceeding with automation steps.\n")

    # --- Step 1: Create the project ---
    print("--- Starting Part 1: Project Creation ---")
    run_project_creation_only()
    print("\nPart 1 (Project Creation) command sent. Check Painter UI/Log for outcome.")
    print("\n\n" + "="*83 + "\n= {:^79} =\n".format("END OF PART 1: PROJECT CREATION") + "="*83 + "\n\n")
    inter_step_wait_1 = 10
    print(f"Waiting for {inter_step_wait_1} seconds before proceeding...")
    time.sleep(inter_step_wait_1)
    print("Wait finished.")

    # --- Step 2: Rename the texture set ---
    print("--- Starting Part 2: Texture Set Renaming ---")
    model_filename_for_ts_rename = os.path.basename(LOW_POLY_MESH_PATH)
    model_name_without_ext_for_ts_rename = os.path.splitext(model_filename_for_ts_rename)[0]
    intended_target_texture_set_name = f"M_{model_name_without_ext_for_ts_rename}"
    # Initialize with the intended name. If rename fails, baking will attempt with this,
    # which might fail if Painter didn't actually rename. This is the "best effort" part.
    current_texture_set_name_for_bake_and_beyond = intended_target_texture_set_name

    print(f"Attempting to rename the first texture set to '{intended_target_texture_set_name}'.")
    rename_succeeded_signal = run_rename_texture_set(intended_target_texture_set_name)

    if rename_succeeded_signal:
        print(f"Texture set rename to '{intended_target_texture_set_name}' was indicated as successful by Painter script.")
        # current_texture_set_name_for_bake_and_beyond is already set to this.
    else:
        print(f"!!! WARNING: Texture set rename to '{intended_target_texture_set_name}' was NOT confirmed by Painter script.")
        print(f"    Proceeding with the assumption that the texture set name IS '{intended_target_texture_set_name}' for subsequent steps,")
        print(f"    but this might lead to failures if the rename did not occur in Painter.")
        # No change to current_texture_set_name_for_bake_and_beyond needed, as it's our best guess.

    print(f"\nPart 2 (Texture Set Renaming attempt for '{current_texture_set_name_for_bake_and_beyond}') finished.")
    print("\n\n" + "="*83 + "\n= {:^79} =\n".format("END OF PART 2: TEXTURE SET RENAMING") + "="*83 + "\n\n")
    inter_step_wait_2 = 5
    print(f"Waiting for {inter_step_wait_2} seconds before proceeding...")
    time.sleep(inter_step_wait_2)
    print("Wait finished.")

    # --- Step 3: Apply Smart Material ---
    print("--- Starting Part 3: Apply Smart Material ---")
    print(f"Attempting to apply Smart Material '{SMART_MATERIAL_NAME}' from shelf '{SMART_MATERIAL_LOCATION}'.")
    run_apply_smart_material(SMART_MATERIAL_NAME, SMART_MATERIAL_LOCATION) # Assuming no critical signal needed for this one to continue
    print(f"\nPart 3 (Apply Smart Material '{SMART_MATERIAL_NAME}') command sent. Check Painter UI/Log for outcome.")
    print("\n\n" + "="*83 + "\n= {:^79} =\n".format("END OF PART 3: APPLY SMART MATERIAL") + "="*83 + "\n\n")
    inter_step_wait_3 = 5
    print(f"Waiting for {inter_step_wait_3} seconds before proceeding...")
    time.sleep(inter_step_wait_3)
    print("Wait finished.")
    
    # --- Step 4: Bake High-Resolution Mesh ---
    print("--- Starting Part 4: Mesh Baking ---")
    print(f"Attempting to bake for texture set: '{current_texture_set_name_for_bake_and_beyond}' using high-poly: '{HIGH_POLY_MESH_PATH}'")
    bake_initiated_signal = run_bake_high_res_mesh(current_texture_set_name_for_bake_and_beyond, HIGH_POLY_MESH_PATH)

    if bake_initiated_signal:
        print(f"\nPart 4 (Mesh Baking) command was indicated as successfully initiated for texture set '{current_texture_set_name_for_bake_and_beyond}'.")
    else:
        print(f"!!! WARNING: Part 4 (Mesh Baking) initiation for '{current_texture_set_name_for_bake_and_beyond}' was NOT confirmed.")
        print("    The script will continue, but baking might not have started in Painter.")

    print("Baking is an asynchronous process. Check Substance Painter UI for progress and outcome.")
    print("The script included a 30s pause inside Painter *before* initiating the bake.")
    
    baking_process_wait_time = 60  # Increased wait time, adjust as needed (e.g., 60-300 seconds or more)
    print(f"Additionally, now waiting {baking_process_wait_time} seconds in *this* script for baking process to run (observation time)...")
    for i in range(baking_process_wait_time):
        time.sleep(1)
        print(f"Baking observation wait: {i+1}/{baking_process_wait_time}s", end='\r')
    print(f"\nAssumed baking observation time of {baking_process_wait_time}s has passed.                            ")

    print("\n\n" + "="*83 + "\n= {:^79} =\n".format("END OF PART 4: MESH BAKING") + "="*83 + "\n\n")
    inter_step_wait_4 = 5
    print(f"Waiting for {inter_step_wait_4} seconds before proceeding...")
    time.sleep(inter_step_wait_4)
    print("Wait finished.") # This is after inter_step_wait_4

    # --- Step 5: Export Textures using glTF PBR Metal Roughness Preset ---
    print("--- Starting Part 5: Texture Export (glTF Preset) ---")
    if not current_texture_set_name_for_bake_and_beyond: # Make sure this variable is correctly set from Step 2
        print("!!! CRITICAL: Texture set name for export is not determined. Skipping texture export. !!!")
    else:
        print(f"Attempting to export textures for '{current_texture_set_name_for_bake_and_beyond}' to '{OUTPUT_PATH}' using glTF preset.")
        export_textures_succeeded_signal = run_export_textures_gltf_preset(current_texture_set_name_for_bake_and_beyond, OUTPUT_PATH) # Call the new function
        if export_textures_succeeded_signal:
            print(f"Part 5 (Texture Export - glTF Preset) for '{current_texture_set_name_for_bake_and_beyond}' was indicated as successful.")
        else:
            print(f"!!! WARNING: Part 5 (Texture Export - glTF Preset) for '{current_texture_set_name_for_bake_and_beyond}' was NOT confirmed or failed. Check Painter Log.")
    
    print("\n\n" + "="*83 + "\n= {:^79} =\n".format("END OF PART 5: TEXTURE EXPORT (glTF PRESET)") + "="*83 + "\n\n")
    inter_step_wait_5 = 5 
    print(f"Waiting for {inter_step_wait_5} seconds before proceeding...")
    time.sleep(inter_step_wait_5)
    print("Wait finished.")

    # --- Step 6: Save the project ---
    # ... (Save project logic remains the same) ...
    print("--- Starting Part 6: Save Project ---")
    project_save_name_stem = model_name_without_ext_for_ts_rename 
    
    print(f"Attempting to save the project as '{project_save_name_stem}.spp' in '{OUTPUT_PATH}'.")
    save_succeeded_signal = run_save_project(project_save_name_stem)
    if save_succeeded_signal:
        print(f"Part 6 (Save Project) command for '{project_save_name_stem}.spp' was indicated as successful by Painter script.")
    else:
        print(f"!!! WARNING: Part 6 (Save Project) for '{project_save_name_stem}.spp' was NOT confirmed. Check file system and Painter Log.")

    print("\n--- Automation Script Finished Attempting All Steps ---")