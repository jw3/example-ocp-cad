PyCharm + build123d + OCP Viewer
===

### Example cad dev env

1. Using PyCharm + uv
2. run `uv run python -m ocp_viewer`
3. Viewer in IDE brower - http://127.0.0.1:3939

### Interop with FreeCAD

1. Export `export_step(whatever.part, "whatever.step")`
2. In FreeCAD:
    - File -> Open or Import the STEP file
    - Switch to Part Design workbench
    - Part Design → New Body.
    - FreeCAD creates a Body containing the imported geometry as a BaseFeature
    - Add sketches, pads, pockets, fillets, and other features
