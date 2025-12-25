# ATHENA-Parser-for-Abaqus

Parser that utilizes ATHENA (agent team for hierarchical numerical algorithm) for Abaqus INP files.

This parser uses [Lark](https://github.com/lark-parser/lark) to parse Abaqus input files (.inp) and extract useful data such as nodes, elements, materials, boundary conditions, loads, and more.

## Features

- Parse Abaqus INP files using Lark grammar
- Extract nodes with coordinates
- Extract elements with connectivity
- Extract material definitions
- Extract boundary conditions
- Extract loads (CLOAD, DLOAD, DSLOAD)
- Extract node sets (NSET)
- Extract element sets (ELSET)
- Get summary statistics of the parsed file
- **VTK Streaming**: Stream large node/element data directly to VTK files to reduce memory usage (see [VTK Streaming Guide](VTK_STREAMING_GUIDE.md))

## Installation

```bash
pip install -r requirements.txt
```

## Usage

### Basic Usage

```python
from abaqus_parser import AbaqusParser

# Initialize parser
parser = AbaqusParser()

# Parse a file
parsed_data = parser.parse_file("model.inp")

# For large files, use VTK streaming to reduce memory usage:
parser = AbaqusParser(vtk_output="mesh.vtk")
parsed_data = parser.parse_file("large_model.inp")
# Nodes and elements are written to VTK file instead of stored in memory

# Or parse from string
inp_content = """
*NODE
1, 0.0, 0.0, 0.0
2, 1.0, 0.0, 0.0
*ELEMENT, TYPE=C3D4
1, 1, 2, 3, 4
"""
parsed_data = parser.parse_string(inp_content)
```

### Extract Specific Data

```python
# Get all nodes
nodes = parser.get_nodes()
for node in nodes:
    print(f"Node {node['id']}: ({node['x']}, {node['y']}, {node['z']})")

# Get all elements
elements = parser.get_elements()
for elem in elements:
    print(f"Element {elem['id']}: nodes {elem['nodes']}")

# Get node sets
nsets = parser.get_node_sets()
for nset in nsets:
    print(f"Node Set '{nset['name']}': {nset['nodes']}")

# Get materials
materials = parser.get_materials()
for mat in materials:
    print(f"Material: {mat['name']}")

# Get boundary conditions
bcs = parser.get_boundary_conditions()
for bc in bcs:
    print(f"BC on {bc['node_set']}: {bc['data']}")

# Get summary
summary = parser.summary()
print(summary)
```

### Command Line Usage

```bash
python abaqus_parser.py model.inp
```

## Example

See `example_usage.py` for a complete example.

## Supported Abaqus Keywords

The parser supports common Abaqus keywords including:
- `*NODE` - Node definitions
- `*ELEMENT` - Element definitions
- `*MATERIAL` - Material definitions
- `*NSET` - Node set definitions
- `*ELSET` - Element set definitions
- `*BOUNDARY` - Boundary conditions
- `*CLOAD`, `*DLOAD`, `*DSLOAD` - Load definitions
- And more...

## License

This project is part of the ATHENA framework for hierarchical numerical algorithms.
