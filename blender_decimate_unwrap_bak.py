import bpy
import sys
import argparse
import math # For math.radians
import os   # For path manipulation

# --- CONFIGURABLE DEFAULT VALUES (Internal to this script) ---
# These are used if the script is run standalone or if the calling script
# (like process_assets.py) doesn't provide overriding arguments.
DEFAULT_DECIMATE_RATIO = 0.1
DEFAULT_SP_UV_ANGLE_DEGREES = 20.0
DEFAULT_SP_ISLAND_MARGIN = 0.0
DEFAULT_SP_AREA_WEIGHT = 0.0
DEFAULT_SP_CORRECT_ASPECT = True
DEFAULT_SP_SCALE_TO_BOUNDS = False
DEFAULT_SP_MARGIN_METHOD = 'SCALED'
DEFAULT_SP_ROTATE_METHOD = 'AXIS_ALIGNED_Y'
DEFAULT_UV_FILL_HOLES_BEFORE_UNWRAP = False
DEFAULT_APPLY_SCALE_BEFORE_UNWRAP = True
# --- END CONFIGURABLE DEFAULT VALUES ---


def str_to_bool(val):
    if isinstance(val, bool): return val
    if val.lower() in ('yes', 'true', 't', 'y', '1'): return True
    elif val.lower() in ('no', 'false', 'f', 'n', '0'): return False
    else: raise argparse.ArgumentTypeError(f"Boolean value expected, got '{val}'")

def _obj_export_core(obj_to_export, filepath_to_save):
    print(f"    Core Export: Exporting {obj_to_export.name} to {filepath_to_save}")
    bpy.ops.wm.obj_export(
        filepath=filepath_to_save,
        export_selected_objects=True,
    )
    print(f"    Core Export: Successfully exported {obj_to_export.name} to {filepath_to_save}")


def export_object_as_obj(obj_to_export, filepath_to_save, exit_on_error=False):
    print(f"  Preparing to export '{obj_to_export.name}' to '{filepath_to_save}'...")

    original_mode = None
    if obj_to_export:
        original_mode = obj_to_export.mode
    
    mode_switched_for_export = False
    original_active = bpy.context.view_layer.objects.active
    original_selection_names = [obj.name for obj in bpy.context.selected_objects]

    if not obj_to_export:
        print(f"  ERROR: obj_to_export is None in export_object_as_obj. Cannot export.")
        if exit_on_error: sys.exit(1)
        return

    try:
        if bpy.context.mode != 'OBJECT':
            if obj_to_export and obj_to_export == bpy.context.active_object and bpy.context.active_object.mode != 'OBJECT':
                print(f"    Switching '{obj_to_export.name}' from {obj_to_export.mode} to OBJECT mode for export.")
                bpy.ops.object.mode_set(mode='OBJECT')
                mode_switched_for_export = True
            elif bpy.context.mode != 'OBJECT':
                print(f"    Global context is {bpy.context.mode}. Attempting to switch to OBJECT mode.")
                bpy.ops.object.mode_set(mode='OBJECT')
                mode_switched_for_export = True

        bpy.ops.object.select_all(action='DESELECT')
        bpy.context.view_layer.objects.active = obj_to_export
        obj_to_export.select_set(True)
        
        _obj_export_core(obj_to_export, filepath_to_save)

    except Exception as e:
        print(f"  ERROR exporting '{obj_to_export.name}' to '{filepath_to_save}': {e}")
        if exit_on_error:
            if mode_switched_for_export and original_mode and obj_to_export and obj_to_export == bpy.context.active_object:
                try:
                    bpy.ops.object.mode_set(mode=original_mode)
                except RuntimeError:
                    print(f"    Warning: Could not restore original mode {original_mode} for {obj_to_export.name} after export error.")
            try:
                if bpy.context.mode == 'OBJECT':
                    bpy.ops.object.select_all(action='DESELECT')
                    for name in original_selection_names:
                        obj = bpy.data.objects.get(name)
                        if obj: obj.select_set(True)
                    if original_active and original_active.name in bpy.data.objects:
                        bpy.context.view_layer.objects.active = original_active
            except Exception as restore_e:
                 print(f"    Warning: Exception during context restoration after export error: {restore_e}")
            sys.exit(1)
    finally:
        if mode_switched_for_export and original_mode and obj_to_export and obj_to_export == bpy.context.active_object:
            try:
                print(f"    Restoring mode for '{obj_to_export.name}' to {original_mode}.")
                bpy.ops.object.mode_set(mode=original_mode)
            except RuntimeError as e:
                print(f"    Warning: Could not restore original mode {original_mode} for {obj_to_export.name} after export. Error: {e}")
        
        if not (mode_switched_for_export and original_mode == bpy.context.mode):
            if original_mode != 'OBJECT':
                print(f"    Export function finished. Original mode was {original_mode}. Calling function will handle context.")
            else:
                try:
                    if bpy.context.mode == 'OBJECT':
                        bpy.ops.object.select_all(action='DESELECT')
                        for name in original_selection_names:
                            obj = bpy.data.objects.get(name)
                            if obj: obj.select_set(True)
                        if original_active and original_active.name in bpy.data.objects:
                            bpy.context.view_layer.objects.active = original_active
                except Exception as restore_e:
                    print(f"    Warning: Exception during final context restoration: {restore_e}")

# Renamed output_path_processed_mesh to output_path_low_poly_mesh for clarity
def process_mesh(input_path, output_path_low_poly_mesh,
                 decimate_ratio_val,
                 sp_angle_degrees_val, sp_island_margin_val, sp_area_weight_val,
                 sp_correct_aspect_val, sp_scale_to_bounds_val, sp_margin_method_val,
                 sp_rotate_method_val,
                 apply_scale_val, uv_fill_holes_val):

    print(f"Blender script (blender_decimate_unwrap.py): Processing {input_path}")
    print(f"  Output (decimated & smart UV projected _low) will be: {output_path_low_poly_mesh}") # Updated print
    print(f"  Parameters: Decimate Ratio: {decimate_ratio_val}, SP Angle: {sp_angle_degrees_val}, SP Margin: {sp_island_margin_val}, etc.")
    print("-" * 30)

    if bpy.context.active_object and bpy.context.active_object.mode != 'OBJECT':
        bpy.ops.object.mode_set(mode='OBJECT')
    bpy.ops.object.select_all(action='SELECT')
    if bpy.context.selected_objects: bpy.ops.object.delete(use_global=False)
    bpy.ops.object.select_all(action='DESELECT')

    print(f"  Attempting to import OBJ: {input_path}")
    try:
        bpy.ops.wm.obj_import(filepath=input_path)
    except Exception as e:
        print(f"  ERROR importing OBJ '{input_path}': {e}")
        sys.exit(1)
    print("  OBJ import successful.")

    imported_obj = None
    if bpy.context.selected_objects:
        imported_obj = bpy.context.selected_objects[0]
    else:
        mesh_objects = [obj for obj in bpy.data.objects if obj.type == 'MESH']
        if mesh_objects: imported_obj = mesh_objects[-1]
    
    if not imported_obj or imported_obj.type != 'MESH':
        print(f"  Error: No MESH object found/selected after import (Name: {imported_obj.name if imported_obj else 'None'}, Type: {imported_obj.type if imported_obj else 'None'}).")
        sys.exit(1)
    
    bpy.context.view_layer.objects.active = imported_obj
    imported_obj.select_set(True)
    print(f"  Successfully selected imported object: {imported_obj.name}")

    if apply_scale_val:
        print("  Applying object scale...")
        bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
        print("  Scale applied.")

    print("  Applying Decimate modifier...")
    mod = imported_obj.modifiers.new(name="Decimate", type='DECIMATE')
    mod.decimate_type = 'COLLAPSE'
    mod.ratio = decimate_ratio_val
    try:
        bpy.ops.object.modifier_apply(modifier=mod.name)
    except RuntimeError as e:
        print(f"  Error applying Decimate modifier: {e}")
        sys.exit(1)
    print("  Decimation complete.")

    print("  Entering Edit Mode for UV operations...")
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='SELECT')
    print("    Clearing any pre-existing seams...")
    bpy.ops.mesh.mark_seam(clear=True)

    if uv_fill_holes_val:
        print("    Filling holes...")
        try:
            bpy.ops.mesh.fill_holes()
            bpy.ops.mesh.select_all(action='SELECT') # Re-select after fill holes
            print("    Holes filled.")
        except RuntimeError as e: print(f"    Warning: Could not fill holes: {e}")

    print("  Performing Smart UV Project...")
    sp_angle_radians_val = math.radians(sp_angle_degrees_val)
    print(f"    (Using angle_limit: {sp_angle_radians_val:.4f} rad for Smart Project)")
    try:
        bpy.ops.uv.smart_project(
            angle_limit=sp_angle_radians_val, island_margin=sp_island_margin_val,
            area_weight=sp_area_weight_val, correct_aspect=sp_correct_aspect_val,
            scale_to_bounds=sp_scale_to_bounds_val, margin_method=sp_margin_method_val,
            rotate_method=sp_rotate_method_val
        )
    except Exception as e:
        print(f"  Error during Smart UV Project: {e}")
        if bpy.context.mode != 'OBJECT': bpy.ops.object.mode_set(mode='OBJECT')
        sys.exit(1)
    print("  Smart UV Project complete.") # Still in EDIT mode

    print("  Decimation and Smart UV Project workflow complete.")
    export_object_as_obj(imported_obj, output_path_low_poly_mesh, exit_on_error=True) # Renamed variable

    print(f"Blender script: Successfully processed. Saved to '{output_path_low_poly_mesh}'.") # Renamed variable


if __name__ == "__main__":
    argv = sys.argv
    argv = argv[argv.index("--") + 1:] if "--" in argv else []
    parser = argparse.ArgumentParser(description="Blender: Decimate, Smart UV Unwrap, and Export.")
    parser.add_argument("--input_mesh", type=str, required=True)
    # Updated help text for output_mesh
    parser.add_argument("--output_mesh", type=str, required=True, help="Output path for the low poly mesh (e.g., 'mymodel_low.obj').")
    
    # Arguments now use the internal script defaults.
    # These will be overridden if specified on the command line (e.g., by process_assets.py).
    parser.add_argument("--decimate_ratio", type=float, default=DEFAULT_DECIMATE_RATIO)
    parser.add_argument("--sp_angle", type=float, default=DEFAULT_SP_UV_ANGLE_DEGREES)
    parser.add_argument("--sp_margin", type=float, default=DEFAULT_SP_ISLAND_MARGIN)
    parser.add_argument("--sp_area_weight", type=float, default=DEFAULT_SP_AREA_WEIGHT)
    parser.add_argument("--sp_correct_aspect", type=str_to_bool, default=DEFAULT_SP_CORRECT_ASPECT)
    parser.add_argument("--sp_scale_to_bounds", type=str_to_bool, default=DEFAULT_SP_SCALE_TO_BOUNDS)
    parser.add_argument("--sp_margin_method", type=str, default=DEFAULT_SP_MARGIN_METHOD, choices=['SCALED', 'ABSOLUTE', 'FRACTION'])
    parser.add_argument("--sp_rotate_method", type=str, default=DEFAULT_SP_ROTATE_METHOD, choices=['AXIS_ALIGNED', 'AXIS_ALIGNED_X', 'AXIS_ALIGNED_Y'])
    parser.add_argument("--uv_fill_holes", type=str_to_bool, default=DEFAULT_UV_FILL_HOLES_BEFORE_UNWRAP)
    parser.add_argument("--apply_scale", type=str_to_bool, default=DEFAULT_APPLY_SCALE_BEFORE_UNWRAP)
    
    args = parser.parse_args(args=argv)
    print("Blender script (blender_decimate_unwrap.py) started with effective arguments:")
    for arg, value in vars(args).items(): print(f"  {arg}: {value}")
    print("-" * 30)
    process_mesh(
        args.input_mesh, args.output_mesh, args.decimate_ratio,
        args.sp_angle, args.sp_margin, args.sp_area_weight,
        args.sp_correct_aspect, args.sp_scale_to_bounds, args.sp_margin_method,
        args.sp_rotate_method,
        args.apply_scale, args.uv_fill_holes
    )