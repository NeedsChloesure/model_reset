"""The reset operator.

Every value is restored from its RNA default where Blender exposes one, so the
reset keeps matching whatever stock Blender ships rather than a list of numbers
hard-coded here. The one deliberate exception is the viewport projection: its RNA
default is ``ORTHO``, but what a modeller means by "back to normal" is
perspective, so that is set explicitly.
"""

import bpy

from .preferences import get_preferences

# Guided overlays that a modelling session tends to toggle off.
GUIDE_ATTRS = ("show_overlays", "show_floor", "show_axis_x", "show_axis_y", "show_axis_z")

# The outline drawn around selected objects. It lives behind the master overlay
# switch too, so that has to come back on as well or the highlight stays hidden.
SELECTION_ATTRS = ("show_overlays", "show_outline_selected")

VIEW_PERSPECTIVE = "PERSP"
VIEW3D_AREA = "VIEW_3D"


def _rna_default(rna_owner, attr):
    prop = rna_owner.bl_rna.properties.get(attr)
    return getattr(prop, "default", None) if prop is not None else None


def _restore(holder, rna_owner, attrs):
    """Put each attribute back on its Blender default; returns how many moved."""
    changed = 0
    for attr in attrs:
        default = _rna_default(rna_owner, attr)
        if default is None or getattr(holder, attr, None) == default:
            continue
        setattr(holder, attr, default)
        changed += 1
    return changed


def _view_regions(space):
    """The region view(s) of a 3D viewport, including every quad view pane."""
    regions = []
    main = getattr(space, "region_3d", None)
    if main is not None:
        regions.append(main)
    quad = getattr(space, "region_quadviews", None)
    if quad:
        regions.extend(quad)
    return regions


def _reset_viewport(space, prefs):
    changed = 0
    if prefs is None or prefs.reset_guides:
        changed += _restore(space.overlay, bpy.types.View3DOverlay, GUIDE_ATTRS)
    if prefs is None or prefs.reset_selection:
        changed += _restore(space.overlay, bpy.types.View3DOverlay, SELECTION_ATTRS)
    if prefs is None or prefs.reset_perspective:
        for region in _view_regions(space):
            if region.view_perspective != VIEW_PERSPECTIVE:
                region.view_perspective = VIEW_PERSPECTIVE
                changed += 1
    return changed


def _reset_bones(context):
    """Armatures back to octahedral bones, drawn normally in object mode."""
    bone_default = _rna_default(bpy.types.Armature, "display_type")
    object_default = _rna_default(bpy.types.Object, "display_type")
    changed = 0
    done = set()
    for obj in context.scene.objects:
        if obj.type != "ARMATURE" or obj.data is None:
            continue
        if bone_default is not None and obj.data.name not in done:
            done.add(obj.data.name)
            if obj.data.display_type != bone_default:
                obj.data.display_type = bone_default
                changed += 1
        if object_default is not None and obj.display_type != object_default:
            obj.display_type = object_default
            changed += 1
    return changed


def _reset_cameras():
    default = _rna_default(bpy.types.Camera, "type")
    if default is None:
        return 0
    changed = 0
    for camera in bpy.data.cameras:
        if camera.type != default:
            camera.type = default
            changed += 1
    return changed


class MODELRESET_OT_reset_view(bpy.types.Operator):
    bl_idname = "model_reset.reset_view"
    bl_label = "Reset Modelling Overrides"
    bl_description = (
        "Put the settings a modelling session tends to change back to stock: grid "
        "and axis overlays, the selection highlight, octahedral bones, and "
        "perspective viewports"
    )
    bl_options = {"REGISTER"}

    @classmethod
    def poll(cls, context):
        return context.window is not None

    def execute(self, context):
        prefs = get_preferences(context)

        if prefs is not None and prefs.scope == "ALL_WINDOWS":
            windows = list(context.window_manager.windows)
        else:
            windows = [context.window] if context.window else []

        viewports = 0
        viewport_changes = 0
        for window in windows:
            screen = window.screen
            if screen is None:
                continue
            for area in screen.areas:
                if area.type != VIEW3D_AREA:
                    continue
                space = area.spaces.active
                if space is None:
                    continue
                viewports += 1
                viewport_changes += _reset_viewport(space, prefs)

        bone_changes = 0
        if prefs is None or prefs.reset_bones:
            bone_changes = _reset_bones(context)

        camera_changes = 0
        if prefs is not None and prefs.reset_camera_object:
            camera_changes = _reset_cameras()

        total = viewport_changes + bone_changes + camera_changes
        if total == 0:
            self.report({"INFO"}, "Model Reset: %d viewport(s) already at defaults" % viewports)
            return {"FINISHED"}

        parts = []
        if viewport_changes:
            parts.append("%d viewport setting(s)" % viewport_changes)
        if bone_changes:
            parts.append("%d armature(s)" % bone_changes)
        if camera_changes:
            parts.append("%d camera(s)" % camera_changes)
        self.report({"INFO"}, "Model Reset: restored " + ", ".join(parts))
        return {"FINISHED"}
