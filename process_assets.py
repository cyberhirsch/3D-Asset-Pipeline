import os
import shutil
import subprocess
import platform
import json # For loading config

# --- CONFIG FILE LOADING ---
CONFIG_FILE_PATH = os.path.join(os.path.dirname(__file__), "config.json")

def load_app_config():
    """Loads the main application configuration from config.json"""
    try:
        with open(CONFIG_FILE_PATH, 'r') as f:
            config_data = json.load(f)
        return config_data
    except FileNotFoundError:
        print(f"ERROR: Configuration file not found at {CONFIG_FILE_PATH}")
        print("Please ensure 'config.json' exists in the same directory as this script.")
        exit(1)
    except json.JSONDecodeError as e:
        print(f"ERROR: Could not decode JSON from {CONFIG_FILE_PATH}. Check for syntax errors: {e}")
        exit(1)
    except Exception as e:
        print(f"ERROR: An unexpected error occurred while loading config: {e}")
        exit(1)

config = load_app_config()

# --- Configuration (from config.json) ---
try:
    INPUT_BASE_FOLDER = config["global_paths"]["input_base_folder"]
    OUTPUT_PROCESSED_OBJS_FOLDER = config["global_paths"]["processed_objs_folder"]

    blender_settings = config["blender_settings"]
    if platform.system() == "Windows":
        BLENDER_EXECUTABLE = blender_settings["executable_path_windows"]
    elif platform.system() == "Darwin": # macOS
        BLENDER_EXECUTABLE = blender_settings["executable_path_macos"]
    else: # Linux
        BLENDER_EXECUTABLE = blender_settings["executable_path_linux"]

    # Blender script parameters from config to be passed to blender_decimate_unwrap.py
    blender_script_params = blender_settings["script_params"]
    DECIMATE_RATIO = blender_script_params["decimate_ratio"]
    SCALE_FACTOR = blender_script_params["scale_factor"] # Changed from UPSCALE_FACTOR
    SP_UV_ANGLE_DEGREES = blender_script_params["sp_angle_degrees"]
    SP_ISLAND_MARGIN = blender_script_params["sp_island_margin"]
    SP_AREA_WEIGHT = blender_script_params["sp_area_weight"]
    SP_CORRECT_ASPECT = blender_script_params["sp_correct_aspect"]
    SP_SCALE_TO_BOUNDS = blender_script_params["sp_scale_to_bounds"]
    SP_MARGIN_METHOD = blender_script_params["sp_margin_method"]
    SP_ROTATE_METHOD = blender_script_params["sp_rotate_method"]
    UV_FILL_HOLES_BEFORE_UNWRAP = blender_script_params["uv_fill_holes"]
    APPLY_SCALE_BEFORE_UNWRAP = blender_script_params["apply_scale"] # For original scale

except KeyError as e:
    print(f"ERROR: Missing a required key in config.json: {e}")
    print("Please check your config.json structure. Full structure required for process_assets.py.")
    exit(1)

# Assuming blender_decimate_unwrap.py is in the same directory as this script
BLENDER_SCRIPT_PATH = os.path.join(os.path.dirname(__file__), "blender_decimate_unwrap.py")

# --- Main Logic ---
if not os.path.exists(OUTPUT_PROCESSED_OBJS_FOLDER):
    os.makedirs(OUTPUT_PROCESSED_OBJS_FOLDER)
    print(f"Created output directory: {OUTPUT_PROCESSED_OBJS_FOLDER}")

print(" STAGE 1: RUNNING BLENDER PROCESSING (process_assets.py)")
print("=" * 60 + "\n")

print(f"Starting asset processing for Blender...")
print(f"Input base: {INPUT_BASE_FOLDER}")
print(f"Outputting .blend, _high.obj & _low.obj OBJs to: {OUTPUT_PROCESSED_OBJS_FOLDER}")
print(f"Using Blender: {BLENDER_EXECUTABLE}")
print(f"Using Blender script: {BLENDER_SCRIPT_PATH}")


processed_count = 0
skipped_count = 0
overwrite_all_decision = None

if not os.path.isdir(INPUT_BASE_FOLDER):
    print(f"ERROR: Input base folder '{INPUT_BASE_FOLDER}' does not exist or is not a directory. Please check config.json.")
    exit(1)
if not os.path.exists(BLENDER_SCRIPT_PATH):
    print(f"ERROR: Blender script '{BLENDER_SCRIPT_PATH}' not found. Ensure it's in the same directory as process_assets.py.")
    exit(1)


for folder_name in os.listdir(INPUT_BASE_FOLDER):
    current_asset_folder_path = os.path.join(INPUT_BASE_FOLDER, folder_name)

    if os.path.isdir(current_asset_folder_path):
        print(f"\nProcessing asset folder: {folder_name}")
        original_obj_from_input_folder_path = None
        for item_in_folder in os.listdir(current_asset_folder_path):
            if item_in_folder.lower().endswith(".obj"):
                original_obj_from_input_folder_path = os.path.join(current_asset_folder_path, item_in_folder)
                break

        if not original_obj_from_input_folder_path:
            print(f"  WARNING: No .obj file found in folder '{folder_name}'. Skipping.")
            skipped_count += 1
            continue

        # Path for the copied original OBJ in the 'Meshes' folder (e.g., Meshes/AssetName.obj)
        # This will be the input to the Blender script.
        intermediate_obj_for_blender_path = os.path.join(OUTPUT_PROCESSED_OBJS_FOLDER, f"{folder_name}.obj")
        
        # Paths for files Blender script will create (used for checking existence)
        blend_output_path = os.path.join(OUTPUT_PROCESSED_OBJS_FOLDER, f"{folder_name}.blend")
        high_poly_output_path = os.path.join(OUTPUT_PROCESSED_OBJS_FOLDER, f"{folder_name}_high.obj")
        low_poly_output_path = os.path.join(OUTPUT_PROCESSED_OBJS_FOLDER, f"{folder_name}_low.obj")


        # Check existence of files that will be created or overwritten
        intermediate_exists = os.path.exists(intermediate_obj_for_blender_path)
        blend_exists = os.path.exists(blend_output_path)
        high_exists = os.path.exists(high_poly_output_path)
        low_exists = os.path.exists(low_poly_output_path)

        if intermediate_exists or blend_exists or high_exists or low_exists:
            if overwrite_all_decision is None:
                while True:
                    existing_files_msg_parts = []
                    if intermediate_exists: existing_files_msg_parts.append(f"'{folder_name}.obj' (intermediate)")
                    if blend_exists: existing_files_msg_parts.append(f"'{folder_name}.blend'")
                    if high_exists: existing_files_msg_parts.append(f"'{folder_name}_high.obj'")
                    if low_exists: existing_files_msg_parts.append(f"'{folder_name}_low.obj'")
                    existing_files_display = ', '.join(existing_files_msg_parts)

                    choice = input(f"  Output file(s) {existing_files_display} (and potentially for others) already exist.\n"
                                   f"  Choose an action: (O)verwrite all existing, (S)kip all existing? [O/S]: ").strip().upper()
                    if choice == 'O':
                        overwrite_all_decision = True
                        print("  User chose to OVERWRITE ALL existing files for this session.")
                        break
                    elif choice == 'S':
                        overwrite_all_decision = False
                        print("  User chose to SKIP ALL assets with existing files for this session.")
                        break
                    else:
                        print("  Invalid choice. Please enter O or S.")
            
            if not overwrite_all_decision:
                print(f"  Skipping asset '{folder_name}' as output files exist and user chose to skip all.")
                skipped_count += 1
                continue
            else:
                print(f"  Output files for '{folder_name}' exist and will be overwritten based on user choice.")

        try:
            print(f"  Copying '{original_obj_from_input_folder_path}' to '{intermediate_obj_for_blender_path}' for Blender input...")
            shutil.copy2(original_obj_from_input_folder_path, intermediate_obj_for_blender_path)
        except Exception as e:
            print(f"  ERROR: Could not copy original OBJ for {folder_name}: {e}. Skipping.")
            skipped_count += 1
            continue

        print(f"  Launching Blender for full processing pipeline...")
        blender_cmd = [
            BLENDER_EXECUTABLE,
            "--background",
            "--python", BLENDER_SCRIPT_PATH,
            "--", # Separator for script arguments
            "--input_mesh", intermediate_obj_for_blender_path, # Blender script reads this
            "--output_mesh", low_poly_output_path,         # Blender script saves final _low.obj here
            
            "--decimate_ratio", str(DECIMATE_RATIO),
            "--scale_factor", str(SCALE_FACTOR), # Changed from --upscale_factor
            "--sp_angle", str(SP_UV_ANGLE_DEGREES),
            "--sp_margin", str(SP_ISLAND_MARGIN),
            "--sp_area_weight", str(SP_AREA_WEIGHT),
            "--sp_correct_aspect", str(SP_CORRECT_ASPECT),
            "--sp_scale_to_bounds", str(SP_SCALE_TO_BOUNDS),
            "--sp_margin_method", SP_MARGIN_METHOD,
            "--sp_rotate_method", SP_ROTATE_METHOD,
            "--uv_fill_holes", str(UV_FILL_HOLES_BEFORE_UNWRAP),
            "--apply_scale", str(APPLY_SCALE_BEFORE_UNWRAP), # For original model's scale
        ]

        try:
            completed_process = subprocess.run(blender_cmd, check=True, capture_output=True, text=True, encoding='utf-8')
            print(f"  Blender processing successful for {folder_name}.")
            if completed_process.stdout and completed_process.stdout.strip():
                 print("  Blender stdout:\n", completed_process.stdout.strip())
            if completed_process.stderr and completed_process.stderr.strip():
                 print("  Blender stderr:\n", completed_process.stderr.strip())
            processed_count += 1
        except subprocess.CalledProcessError as e:
            print(f"  ERROR: Blender script failed for {folder_name}.")
            print(f"  Return code: {e.returncode}")
            print(f"  Stdout: {e.stdout.strip() if e.stdout else 'N/A'}")
            print(f"  Stderr: {e.stderr.strip() if e.stderr else 'N/A'}")
            skipped_count += 1
        except FileNotFoundError:
            print(f"  ERROR: Blender executable not found at '{BLENDER_EXECUTABLE}'. Please check path in config.json.")
            print("  Halting script.")
            exit(1)
        except Exception as e:
            print(f"  An unexpected error occurred during Blender processing for {folder_name}: {e}")
            skipped_count += 1

print(f"\n--- Blender Processing Complete ---")
print(f"Successfully processed: {processed_count} assets.")
print(f"Skipped: {skipped_count} assets.")