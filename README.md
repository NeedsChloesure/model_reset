# Model Reset

A tiny Blender extension that puts the viewport settings a modelling session
tends to leave changed back to stock, on one keystroke (default **Shift+Alt+R**).

## What it resets

| Group | Restores |
| --- | --- |
| Grid and axis lines | Overlays visible, Floor on, Axis X on, Axis Y on, Axis Z to its stock setting |
| Selection highlight | Overlays visible, **Outline Selected** back on, so selected objects are outlined again |
| Bone display | Every armature back to **octahedral** bones (the grey prisms), and armature objects back to normal object-mode drawing |
| Viewport projection | Every 3D viewport back to **Perspective** (`ORTHO` and `Camera` view both go back to 3D) |

*Two different "outline" settings exist: this add-on resets **Outline Selected**
(the selection highlight, in the Overlays popover). The shading popover's
dark **Outline** option is a separate setting and is left alone.*

Values come from Blender's own RNA defaults where one exists, so the reset keeps
tracking stock Blender instead of a hard-coded list. The single exception is the
viewport projection: its RNA default is orthographic, but "back to normal" for a
modeller means perspective, so that is set explicitly.

The camera *object's* lens type is optional and off by default (see below).

## Install

1. `Edit > Preferences > Add-ons`
2. Top-right dropdown > **Install from Disk...**
3. Pick `model_reset-1.0.0.zip`
4. Tick **Model Reset** to enable it

## Usage

- Press **Shift+Alt+R** with the mouse over a 3D viewport, or
- `Viewport > View > Reset Modelling Overrides`

A status-bar message reports how many settings actually moved, so you can tell
"nothing needed changing" from "it worked".

## Changing the shortcut

`Edit > Preferences > Add-ons > Model Reset`:

- **Shortcut** - type any combination in Blender's usual notation, e.g.
  `Shift+Alt+R`, `Ctrl+Shift+F5`, `Alt+Space`. Modifiers it understands:
  `Shift`, `Ctrl`, `Alt`, `Cmd`/`Super`/`Oskey`. If the key can't be bound, the
  reason is shown right underneath rather than failing silently.
- **Viewports** - reset just the current window, or every open Blender window.
- **What gets reset** - turn off any group you want to leave alone.
- **Camera lens type** - optionally force camera datablocks back to perspective.

The shortcut is only live while the add-on is enabled, and it is added to the
`3D View` keymap so it works in Object, Edit, Pose and Sculpt mode alike.
