# VTK Streaming Guide

## Overview

For large Abaqus INP files with many nodes and elements, storing all data in memory can be memory-intensive. The VTK streaming feature allows you to write nodes and elements directly to a VTK file during parsing, significantly reducing memory usage.

## Benefits

- **Reduced Memory Usage**: Nodes and elements are written to VTK file instead of stored in memory
- **Efficient for Large Files**: Ideal for files with millions of nodes/elements
- **Standard Format**: VTK files can be opened in ParaView, VisIt, or other visualization tools
- **Preserves Data**: All node coordinates and element connectivity are preserved

## Usage

### Basic VTK Streaming

```python
from abaqus_parser import AbaqusParser

# Initialize parser with VTK output
parser = AbaqusParser(vtk_output="mesh_output.vtk")

# Parse file - nodes/elements will be streamed to VTK
parsed_data = parser.parse_file("large_model.inp")

# Get summary (includes VTK info)
summary = parser.summary()
print(f"Nodes: {summary['total_nodes']}")
print(f"Elements: {summary['total_elements']}")
print(f"VTK file: {summary['vtk_output_file']}")
```

### Without VTK Streaming (Standard Mode)

```python
# Standard mode - all data in memory
parser = AbaqusParser()  # No vtk_output parameter
parsed_data = parser.parse_file("model.inp")

# Access nodes and elements
nodes = parser.get_nodes()
elements = parser.get_elements()
```

### With VTK Streaming

```python
# VTK streaming mode - data written to file
parser = AbaqusParser(vtk_output="mesh.vtk")
parsed_data = parser.parse_file("model.inp")

# Note: get_nodes() and get_elements() return empty lists
# because data is in VTK file, not memory
nodes = parser.get_nodes()  # Returns []
elements = parser.get_elements()  # Returns []

# But other data (materials, sets, BCs) is still available
materials = parser.get_materials()
nsets = parser.get_node_sets()
```

## VTK File Format

The generated VTK file uses the **Legacy VTK ASCII format** and includes:

- **Points**: All node coordinates (x, y, z)
- **Cells**: All elements with connectivity
- **Point Data**: Abaqus node IDs as scalar data
- **Cell Data**: Element IDs as scalar data

### VTK File Structure

```
# vtk DataFile Version 2.0
Abaqus INP File - Parsed Mesh Data
ASCII

DATASET UNSTRUCTURED_GRID
POINTS <count> float
<x1> <y1> <z1>
<x2> <y2> <z2>
...

CELLS <count> <total_size>
<num_nodes> <node_idx1> <node_idx2> ...
...

CELL_TYPES <count>
<cell_type_code>
...

POINT_DATA <count>
SCALARS AbaqusNodeID int 1
LOOKUP_TABLE default
<node_id1>
<node_id2>
...

CELL_DATA <count>
SCALARS AbaqusElementID int 1
LOOKUP_TABLE default
<elem_id1>
<elem_id2>
...
```

## Element Type Mapping

The parser automatically maps Abaqus element types to VTK cell types:

| Abaqus Type | VTK Cell Type | Description |
|------------|--------------|-------------|
| C3D4 | 10 | Tetrahedron |
| C3D8 | 12 | Hexahedron |
| C3D6 | 13 | Wedge |
| C3D10 | 24 | Quadratic Tetrahedron |
| C3D20 | 25 | Quadratic Hexahedron |
| S4 | 9 | Quad |
| S3 | 5 | Triangle |
| S8 | 23 | Quadratic Quad |
| S6 | 22 | Quadratic Triangle |
| T3D2 | 3 | Line |
| T3D3 | 21 | Quadratic Line |

If element type is not specified, the parser infers it from the number of nodes.

## Memory Comparison

### Standard Mode (No VTK Streaming)
- Stores all nodes in memory: `List[Dict]` with coordinates
- Stores all elements in memory: `List[Dict]` with connectivity
- Memory usage: ~O(n) where n = number of nodes/elements
- For 1M nodes: ~100-200 MB in memory

### VTK Streaming Mode
- Nodes: Only coordinates stored temporarily during writing
- Elements: Only connectivity stored temporarily during writing
- Memory usage: ~O(1) - constant memory regardless of file size
- For 1M nodes: ~10-20 MB in memory (just for parsing)

## Viewing VTK Files

### ParaView
1. Open ParaView
2. File → Open → Select `mesh_output.vtk`
3. Click "Apply" to visualize

### VisIt
1. Open VisIt
2. File → Open → Select `mesh_output.vtk`
3. Add plot (Mesh, Contour, etc.)

### Python (using pyvista)
```python
import pyvista as pv

mesh = pv.read("mesh_output.vtk")
mesh.plot()
```

## Example

See `example_usage.py` for a complete example that:
1. Parses `inputs/example3.inp`
2. Streams nodes/elements to `mesh_output.vtk`
3. Creates XML output for other data (materials, sets, etc.)

## Notes

- When VTK streaming is enabled, `get_nodes()` and `get_elements()` return empty lists
- Other data (materials, boundary conditions, sets) is still available in memory
- VTK file is written after parsing completes
- The VTK file can be very large for big models (ASCII format)
- For binary VTK (smaller file size), consider using pyvista or vtk libraries

