# Geometry vs Non-Geometry Data Separation

## Overview

The parser automatically separates Abaqus INP file data into two categories:

1. **Geometry Data** → Written to VTK file (reduces memory usage)
2. **Non-Geometry Data** → Stored in Python dictionary (from transformer)

## Architecture

```
Abaqus INP File
    ↓
Lark Parser (Grammar)
    ↓
Transformer (Python data structures)
    ↓
Data Separation
    ├── Geometry (NODE, ELEMENT) → VTK Writer → geometry.vtk
    └── Non-Geometry (MATERIAL, NSET, BOUNDARY, etc.) → Python dict
```

## Geometry Data

### Mesh Data (→ VTK File)

**Keywords:** `NODE`, `ELEMENT`

**What gets written to VTK:**
- Node coordinates (x, y, z)
- Element connectivity (node IDs)
- Element types (mapped to VTK cell types)
- Abaqus node IDs (as point data)
- Abaqus element IDs (as cell data)

### Geometry Metadata (→ Python Dict)

**Keywords:** `NSET`, `ELSET`, `SURFACE`, `INSTANCE`

**What gets stored as geometry metadata:**
- Node set definitions (NSET)
- Element set definitions (ELSET)
- Surface definitions (SURFACE)
- Instance definitions (INSTANCE)

**Why separate from non-geometry?**
- These are geometry-related definitions
- They reference nodes/elements (geometry)
- They're part of the mesh structure
- But they don't have coordinate data to write to VTK

**Why VTK?**
- Reduces memory usage for large models
- Standard format for visualization (ParaView, VisIt)
- Efficient storage of mesh data

**Example:**
```python
parser = AbaqusParser(vtk_output="geometry.vtk")
non_geometry_data = parser.parse_file("model.inp")

# Geometry is in VTK file
nodes_info = parser.get_nodes()
# Returns: {'vtk_file': 'geometry.vtk', 'node_count': 1000, ...}
```

## Non-Geometry Data (→ Python Dictionary)

**Keywords:** All other sections including:
- `MATERIAL`, `ELASTIC`, `PLASTIC`, `DENSITY`
- `BOUNDARY`, `CLOAD`, `DLOAD`, `DSLOAD`
- `STEP`, `STATIC`, `DYNAMIC`
- `ASSEMBLY`, `PART`
- `INTERACTION`, `CONTACT`
- And more...

**Note:** `NSET`, `ELSET`, `SURFACE`, and `INSTANCE` are now geometry keywords (geometry metadata).

**What gets stored in Python dict:**
- Material properties
- Node/element set definitions
- Boundary conditions
- Load definitions
- Analysis steps
- Assembly structure
- All other non-geometric data

**Why Python dict?**
- Easy to access and manipulate
- Small memory footprint (compared to geometry)
- Can be easily serialized (JSON, XML, etc.)
- Suitable for programmatic access

**Example:**
```python
parser = AbaqusParser(vtk_output="geometry.vtk")
non_geometry_data = parser.parse_file("model.inp")

# Non-geometry is in Python dict
materials = parser.get_materials()
nsets = parser.get_node_sets()
bcs = parser.get_boundary_conditions()

# Or access directly
print(non_geometry_data.keys())
# ['MATERIAL', 'NSET', 'BOUNDARY', 'CLOAD', ...]
```

## Usage Examples

### Basic Usage

```python
from abaqus_parser import AbaqusParser

# Initialize parser
parser = AbaqusParser(vtk_output="geometry.vtk")

# Parse file - returns non-geometry data
non_geometry = parser.parse_file("model.inp")

# Access geometry info
nodes_info = parser.get_nodes()
print(f"Nodes: {nodes_info['node_count']} in {nodes_info['vtk_file']}")

# Access geometry metadata
nsets = parser.get_node_sets()  # From geometry_metadata
elsets = parser.get_element_sets()  # From geometry_metadata
surfaces = parser.get_surfaces()  # From geometry_metadata
instances = parser.get_instances()  # From geometry_metadata

# Access non-geometry data
materials = parser.get_materials()
bcs = parser.get_boundary_conditions()
```

### Get Summary

```python
summary = parser.summary()

print(summary['geometry'])
# {
#   'mesh': {'vtk_file': 'geometry.vtk', 'total_nodes': 1000, 'total_elements': 500},
#   'metadata': {'total_node_sets': 5, 'total_element_sets': 3, 'total_surfaces': 2, 'total_instances': 1}
# }

print(summary['non_geometry'])
# {'total_materials': 2, 'total_boundary_conditions': 3, 'total_loads': 1}
```

### Access Non-Geometry Data Directly

```python
# The parsed_data dict contains only non-geometry data
non_geometry = parser.parse_file("model.inp")

# Access materials
if 'MATERIAL' in non_geometry:
    material_data = non_geometry['MATERIAL']

# Access node sets
if 'NSET' in non_geometry:
    nset_data = non_geometry['NSET']

# Access boundary conditions
if 'BOUNDARY' in non_geometry:
    bc_data = non_geometry['BOUNDARY']
```

## Data Flow

### During Parsing

1. **Lark parses** INP file → creates parse tree
2. **Transformer converts** parse tree → Python data structures
3. **Parser separates** data:
   - Geometry sections (NODE, ELEMENT) → streamed to VTK writer
   - Non-geometry sections → kept in `parsed_data` dict
4. **VTK writer** writes geometry to file
5. **Returns** non-geometry dict

### After Parsing

- **Geometry**: Available in VTK file (use ParaView, VisIt, or pyvista)
- **Non-Geometry**: Available in Python dict via:
  - `parser.parsed_data` (direct access)
  - `parser.get_materials()` (helper methods)
  - `parser.get_node_sets()` (helper methods)
  - etc.

## Benefits

### Memory Efficiency
- **Before**: All nodes/elements in memory (~100-200 MB for 1M nodes)
- **After**: Only non-geometry in memory (~1-10 MB typically)
- **Geometry**: Written to disk (VTK file)

### Clear Separation
- **Geometry**: Mesh visualization and analysis
- **Non-Geometry**: Material properties, boundary conditions, analysis setup

### Standard Formats
- **VTK**: Industry standard for mesh data
- **Python dict**: Easy to convert to JSON, XML, etc.

## VTK File Structure

The generated VTK file contains:

```
# vtk DataFile Version 2.0
Abaqus INP File - Parsed Mesh Data
ASCII

DATASET UNSTRUCTURED_GRID
POINTS <count> float
<coordinates>

CELLS <count> <size>
<connectivity>

CELL_TYPES <count>
<cell_type_codes>

POINT_DATA <count>
SCALARS AbaqusNodeID int 1
<node_ids>

CELL_DATA <count>
SCALARS AbaqusElementID int 1
<element_ids>
```

## Viewing Results

### Geometry (VTK File)
```python
import pyvista as pv

mesh = pv.read("geometry.vtk")
mesh.plot()
```

### Non-Geometry (Python Dict)
```python
import json

non_geometry = parser.parse_file("model.inp")
with open("non_geometry.json", "w") as f:
    json.dump(non_geometry, f, indent=2)
```

## Summary

- **Geometry** (nodes/elements) → Always in VTK file
- **Non-Geometry** (materials, sets, BCs, etc.) → Always in Python dict
- **Automatic separation** during parsing
- **Memory efficient** for large models
- **Easy access** to both types of data

