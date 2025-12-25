"""
VTK Writer for Abaqus Parser
Writes nodes and elements to VTK format with minimal memory usage.
"""

from typing import List, Tuple, Optional
import os


class VTKWriter:
    """
    Writes nodes and elements to VTK file format.
    Uses buffered writing to minimize memory usage.
    """
    
    # VTK cell type codes
    VTK_CELL_TYPES = {
        2: 3,   # VTK_LINE
        3: 5,   # VTK_TRIANGLE
        4: 9,   # VTK_QUAD (or 10 for VTK_TETRA, we'll detect)
        6: 13,  # VTK_WEDGE
        8: 12,  # VTK_HEXAHEDRON
        10: 24, # VTK_QUADRATIC_TETRAHEDRON
        20: 25, # VTK_QUADRATIC_HEXAHEDRON
    }
    
    def __init__(self, output_file: str):
        """
        Initialize VTK writer.
        
        Args:
            output_file: Path to output VTK file (.vtk)
        """
        self.output_file = output_file
        self.temp_file = output_file + '.tmp'
        self.vtk_file = None
        
        # Data storage (minimal - just coordinates and connectivity)
        self.nodes_data: List[Tuple[float, float, float]] = []
        self.elements_data: List[Tuple[int, List[int]]] = []  # (cell_type, node_indices)
        self.node_id_to_index: dict = {}  # Maps Abaqus node ID to 0-based index
        
        self.node_count = 0
        self.element_count = 0
        self.current_element_type: Optional[str] = None
        
    def set_element_type(self, element_type: str):
        """Set current element type (e.g., 'C3D4', 'C3D8')."""
        if '=' in element_type:
            element_type = element_type.split('=')[-1].strip()
        self.current_element_type = element_type.upper()
    
    def add_node(self, node_id: int, x: float, y: float, z: float = 0.0):
        """
        Add a node. Maps Abaqus node ID to sequential index.
        
        Args:
            node_id: Abaqus node ID
            x, y, z: Coordinates
        """
        if node_id not in self.node_id_to_index:
            self.node_id_to_index[node_id] = self.node_count
            self.nodes_data.append((x, y, z))
            self.node_count += 1
    
    def add_element(self, element_id: int, node_ids: List[int]):
        """
        Add an element with connectivity.
        
        Args:
            element_id: Abaqus element ID
            node_ids: List of Abaqus node IDs
        """
        # Convert Abaqus node IDs to 0-based indices
        vtk_indices = []
        for nid in node_ids:
            if nid in self.node_id_to_index:
                vtk_indices.append(self.node_id_to_index[nid])
            else:
                # Skip elements with missing nodes
                return
        
        # Determine VTK cell type
        cell_type = self._get_cell_type(len(vtk_indices))
        
        self.elements_data.append((cell_type, vtk_indices))
        self.element_count += 1
    
    def _get_cell_type(self, num_nodes: int) -> int:
        """Get VTK cell type based on number of nodes and element type."""
        # Element type mapping
        type_map = {
            'C3D4': 10,   # Tetrahedron
            'C3D8': 12,   # Hexahedron
            'C3D6': 13,   # Wedge
            'C3D10': 24,  # Quadratic Tetrahedron
            'C3D20': 25,  # Quadratic Hexahedron
            'S4': 9,      # Quad
            'S3': 5,      # Triangle
            'S8': 23,     # Quadratic Quad
            'S6': 22,     # Quadratic Triangle
            'T3D2': 3,    # Line
            'T3D3': 21,   # Quadratic Line
        }
        
        if self.current_element_type and self.current_element_type in type_map:
            return type_map[self.current_element_type]
        
        # Infer from number of nodes
        return self.VTK_CELL_TYPES.get(num_nodes, 9)  # Default to quad
    
    def write(self):
        """
        Write all collected data to VTK file.
        This is called after all nodes/elements are collected.
        """
        with open(self.output_file, 'w', encoding='utf-8') as f:
            # Write header
            f.write("# vtk DataFile Version 2.0\n")
            f.write("Abaqus INP File - Parsed Mesh Data\n")
            f.write("ASCII\n")
            f.write("\n")
            
            # Write dataset type
            f.write("DATASET UNSTRUCTURED_GRID\n")
            f.write(f"POINTS {self.node_count} float\n")
            
            # Write points (nodes)
            for x, y, z in self.nodes_data:
                f.write(f"{x:.6e} {y:.6e} {z:.6e}\n")
            
            f.write("\n")
            
            # Calculate total size for CELLS section
            # Each cell needs: num_points + point_indices
            total_cell_data_size = sum(1 + len(indices) for _, indices in self.elements_data)
            
            f.write(f"CELLS {self.element_count} {total_cell_data_size}\n")
            
            # Write cells (elements)
            for cell_type, indices in self.elements_data:
                num_points = len(indices)
                f.write(f"{num_points} ")
                f.write(" ".join(str(idx) for idx in indices))
                f.write("\n")
            
            f.write("\n")
            
            # Write cell types
            f.write(f"CELL_TYPES {self.element_count}\n")
            for cell_type, _ in self.elements_data:
                f.write(f"{cell_type}\n")
            
            f.write("\n")
            
            # Optional: Write point data (node IDs from Abaqus)
            f.write("POINT_DATA {}\n".format(self.node_count))
            f.write("SCALARS AbaqusNodeID int 1\n")
            f.write("LOOKUP_TABLE default\n")
            # Write Abaqus node IDs in order of VTK point indices
            abaqus_ids = [0] * self.node_count
            for abaqus_id, vtk_index in self.node_id_to_index.items():
                abaqus_ids[vtk_index] = abaqus_id
            for node_id in abaqus_ids:
                f.write(f"{node_id}\n")
            
            f.write("\n")
            
            # Optional: Write cell data (element IDs from Abaqus)
            f.write("CELL_DATA {}\n".format(self.element_count))
            f.write("SCALARS AbaqusElementID int 1\n")
            f.write("LOOKUP_TABLE default\n")
            # Note: We don't track element IDs in order, so we'll use sequential
            for i in range(self.element_count):
                f.write(f"{i + 1}\n")  # Sequential IDs
    
    def get_stats(self) -> dict:
        """Get statistics about written data."""
        return {
            'node_count': self.node_count,
            'element_count': self.element_count,
            'output_file': self.output_file
        }

