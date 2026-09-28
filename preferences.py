"""Preferences and keymap wiring for Model Reset.

The shortcut is stored as a plain string (``"Shift+Alt+R"``) so it can be typed
into the add-on preferences, and is re-parsed into a real keymap entry every time
it changes.
"""

import bpy
from bpy.props import BoolProperty, EnumProperty, StringProperty

DEFAULT_SHORTCUT = "Shift+Alt+R"

# Which Blender key type the shortcut should land in.
KEYMAP_NAME = "3D View"
KEYMAP_SPACE = "VIEW_3D"

_MODIFIER_ALIASES = {
    "shift": "shift",
    "ctrl": "ctrl",
    "control": "ctrl",
    "alt": "alt",
    "option": "alt",
    "oskey": "oskey",
    "cmd": "oskey",
    "command": "oskey",
    "super": "oskey",
    "win": "oskey",
}

_KEY_ALIASES = {
    "ESC": "ESC",
    "ESCAPE": "ESC",
    "RETURN": "RETURN",
    "ENTER": "RETURN",
    "SPACE": "SPACE",
    "DEL": "DEL",
    "DELETE": "DEL",
    "TAB": "TAB",
    "BACKSPACE": "BACKSPACE",
    "HOME": "HOME",
    "END": "END",
    "PAGEUP": "PAGE_UP",
    "PAGEDOWN": "PAGE_DOWN",
    "UP": "UP_ARROW",
    "DOWN": "DOWN_ARROW",
    "LEFT": "LEFT_ARROW",
    "RIGHT": "RIGHT_ARROW",
}

# Module state: the keymaps we registered, and the last problem we hit.
_keymaps = []
_keymap_error = ""
_valid_keys_cache = None


def parse_shortcut(text):
    """Turn ``"Shift+Alt+R"`` into ``("R", {"shift": True, "alt": True, ...})``.

    Returns ``(None, error_message)`` when the text cannot be understood.
    """
    parts = [p.strip() for p in str(text).replace(" ", "").split("+")]
    parts = [p for p in parts if p]
    if not parts:
        return None, "Shortcut is empty"

    key = _KEY_ALIASES.get(parts[-1].upper(), parts[-1].upper())
    flags = {"shift": False, "ctrl": False, "alt": False, "oskey": False}
    for modifier in parts[:-1]:
        slot = _MODIFIER_ALIASES.get(modifier.lower())
        if slot is None:
            return None, "Unknown modifier '%s'" % modifier
        flags[slot] = True
    return (key, flags), ""


def valid_key_types():
    """Every key type Blender's keymap editor would accept."""
    global _valid_keys_cache
    if _valid_keys_cache is None:
        prop = bpy.types.KeyMapItem.bl_rna.properties.get("type")
        _valid_keys_cache = {e.identifier for e in prop.enum_items} if prop else set()
    return _valid_keys_cache


def get_preferences(context=None):
    """The live preferences instance, or None if the add-on is not enabled."""
    addon = (context or bpy.context).preferences.addons.get(__package__ or __name__)
    return addon.preferences if addon else None


def last_keymap_error():
    """The reason the shortcut could not be bound, if any."""
    return _keymap_error


def unregister_keymap():
    """Drop every keymap entry we created."""
    keyconfig = bpy.context.window_manager.keyconfigs.addon
    if keyconfig is not None:
        for keymap in _keymaps:
            try:
                keyconfig.keymaps.remove(keymap)
            except (RuntimeError, ReferenceError):
                pass
    del _keymaps[:]


def register_keymap():
    """(Re)bind the operator to the shortcut currently in the preferences."""
    global _keymap_error
    unregister_keymap()
    _keymap_error = ""

    keyconfig = bpy.context.window_manager.keyconfigs.addon
    if keyconfig is None:  # background mode: no windows, so no keymaps
        return

    # Fall back to the stock shortcut rather than ending up with no binding at
    # all, should the preferences not be reachable for any reason.
    prefs = get_preferences()
    source = prefs.shortcut if prefs is not None else DEFAULT_SHORTCUT

    parsed, error = parse_shortcut(source)
    if parsed is None:
        _keymap_error = error
        return

    key, flags = parsed
    known = valid_key_types()
    if known and key not in known:
        _keymap_error = "'%s' is not a key Blender recognises" % key
        return

    try:
        keymap = keyconfig.keymaps.new(name=KEYMAP_NAME, space_type=KEYMAP_SPACE)
        keymap.keymap_items.new("model_reset.reset_view", key, "PRESS", **flags)
    except Exception as ex:  # noqa: BLE001 - surface any binding failure in the UI
        _keymap_error = "Could not bind %s (%s)" % (source, ex)
        return
    _keymaps.append(keymap)


def _on_shortcut_changed(self, context):
    register_keymap()


class MODELRESET_AP_preferences(bpy.types.AddonPreferences):
    bl_idname = __package__ or __name__

    shortcut: StringProperty(
        name="Shortcut",
        description="Key combination that runs the reset, e.g. Shift+Alt+R",
        default=DEFAULT_SHORTCUT,
        update=_on_shortcut_changed,
    )
    scope: EnumProperty(
        name="Viewports",
        description="Which 3D viewports get reset",
        items=[
            ("CURRENT_SCREEN", "Current window",
             "Only the 3D viewports of the window you trigger it from"),
            ("ALL_WINDOWS", "All windows",
             "Every 3D viewport in every open Blender window"),
        ],
        default="CURRENT_SCREEN",
    )
    reset_guides: BoolProperty(
        name="Grid and axis lines",
        description="Re-enable overlays and restore the floor grid and the X/Y/Z axis lines",
        default=True,
    )
    reset_selection: BoolProperty(
        name="Selection highlight",
        description="Bring back the outline drawn around selected objects",
        default=True,
    )
    reset_bones: BoolProperty(
        name="Bone display",
        description="Armatures go back to the stock opaque octahedral (grey prism) bones",
        default=True,
    )
    reset_perspective: BoolProperty(
        name="Viewport projection",
        description="3D viewports go back to perspective instead of orthographic or camera view",
        default=True,
    )
    reset_camera_object: BoolProperty(
        name="Camera lens type",
        description="Also force every camera datablock back to a perspective lens",
        default=False,
    )

    def draw(self, context):
        from .operators import MODELRESET_OT_reset_view

        layout = self.layout

        box = layout.box()
        box.label(text="Shortcut", icon="KEYINGSET")
        row = box.row(align=True)
        row.prop(self, "shortcut", text="")
        row.operator(MODELRESET_OT_reset_view.bl_idname, text="", icon="PLAY")
        error = last_keymap_error()
        if error:
            box.label(text=error, icon="ERROR")
        else:
            box.label(text="Bound in the 3D Viewport keymap", icon="CHECKMARK")

        box = layout.box()
        box.label(text="What gets reset", icon="PREFERENCES")
        box.prop(self, "reset_guides")
        box.prop(self, "reset_selection")
        box.prop(self, "reset_bones")
        box.prop(self, "reset_perspective")
        box.prop(self, "reset_camera_object")

        box = layout.box()
        box.label(text="Scope", icon="VIEW3D")
        box.prop(self, "scope")
