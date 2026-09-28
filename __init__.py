"""Model Reset - one keystroke back to stock viewport defaults.

Resets the handful of settings that modelling sessions tend to leave changed:

* the floor grid and the X / Y / Z axis lines (and overlays as a whole),
* the outline highlight around selected objects,
* armatures back to the stock octahedral "grey prism" bones,
* 3D viewports back to perspective instead of orthographic or camera view.

The shortcut is configurable in this add-on's preferences, and the reset can also
be triggered from Viewport > View.
"""

import bpy

from . import operators, preferences

_classes = (
    preferences.MODELRESET_AP_preferences,
    operators.MODELRESET_OT_reset_view,
)

_menu_added = False


def _draw_view_menu(self, context):
    """Add the reset to the 3D viewport's View menu."""
    prefs = preferences.get_preferences(context)
    label = "Reset Modelling Overrides"
    if prefs is not None and prefs.shortcut:
        label += "\t(%s)" % prefs.shortcut
    self.layout.separator()
    self.layout.operator(operators.MODELRESET_OT_reset_view.bl_idname, text=label)


def _add_menu_entry():
    global _menu_added
    menu = getattr(bpy.types, "VIEW3D_MT_view", None)
    if menu is None or _menu_added:
        return
    menu.append(_draw_view_menu)
    _menu_added = True


def _remove_menu_entry():
    global _menu_added
    menu = getattr(bpy.types, "VIEW3D_MT_view", None)
    if menu is None or not _menu_added:
        return
    menu.remove(_draw_view_menu)
    _menu_added = False


def register():
    for cls in _classes:
        bpy.utils.register_class(cls)
    _add_menu_entry()
    try:
        preferences.register_keymap()
    except (AttributeError, RuntimeError):
        # No window manager yet (e.g. --background); the menu entry still works.
        pass


def unregister():
    try:
        preferences.unregister_keymap()
    except (AttributeError, RuntimeError):
        pass
    _remove_menu_entry()
    for cls in reversed(_classes):
        bpy.utils.unregister_class(cls)
