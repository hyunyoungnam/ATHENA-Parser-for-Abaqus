"""
Part 2 & 3: Abaqus Parser with Lark Grammar
Parses Abaqus input files using Lark to extract useful data.
"""

from lark import Lark
from typing import Dict, List, Any, Optional
from abaqus_transformer import AbaqusTransformer
from abaqus_vtk_writer import VTKWriter


class AbaqusParser:
    """Parser for Abaqus INP files using Lark."""
    
    # Lark grammar for Abaqus INP files
    GRAMMAR = r"""
        start: (section | empty_line)*
        
        section: keyword_line data_lines?
        
        keyword_line: "*" keyword params? NEWLINE
        keyword: keyword_word (keyword_word)*
        keyword_word: WORD
        params: "," param ("," param)*
        param: param_with_value | param_flag
        param_with_value: WORD "=" param_value
        param_flag: WORD
        param_value: IDENTIFIER | WORD | NUMBER | QUOTED_STRING
        
        data_lines: (data_line | empty_line)+
        data_line: (value ("," value)* (","?) | ",") NEWLINE
        value: NUMBER | WORD | IDENTIFIER | QUOTED_STRING
        
        empty_line: NEWLINE
        
        QUOTED_STRING: /"[^"]*"/ | /'[^']*'/
        WORD: /[A-Za-z_][A-Za-z0-9_]*/
        IDENTIFIER: /[A-Za-z_][A-Za-z0-9_-]*/
        NUMBER: /-?\d+\.?\d*([eE][+-]?\d+)?/
        
        %import common.NEWLINE
        %import common.WS
        %ignore WS
        %ignore /^\*\*.*$/m
    """
    
    def __init__(self, vtk_output: Optional[str] = None):
        """
        Initialize the parser with Lark grammar.
        
        Args:
            vtk_output: Path to VTK output file for geometry data (nodes/elements).
                       If None, defaults to "geometry.vtk". Geometry data is always
                       written to VTK to reduce memory usage.
        """
        self.parser = Lark(self.GRAMMAR, parser='lalr', start='start')
        self.transformer = AbaqusTransformer()
        self.parsed_data = {}  # Stores non-geometry data only
        
        # Geometry data always goes to VTK
        if vtk_output is None:
            vtk_output = "geometry.vtk"
        self.vtk_writer = VTKWriter(vtk_output)
        self.vtk_output_file = vtk_output
        
        # Define geometry vs non-geometry keywords
        # Geometry keywords: mesh data and geometry-related definitions
        self.geometry_keywords = {
            'NODE', 'ELEMENT',      # Mesh data (written to VTK)
            'NSET', 'ELSET',        # Node/element sets (geometry references)
            'SURFACE',              # Surface definitions (geometry)
            'INSTANCE',             # Instance definitions (geometry/assembly)
            'SECTION'               # Section definitions (Solid Section, Shell Section, etc.)
        }
        # Non-geometry keywords: material properties, loads, analysis setup
        self.non_geometry_keywords = {
            'MATERIAL', 'ELASTIC', 'PLASTIC', 'DENSITY', 'EXPANSION',
            'BOUNDARY', 'CLOAD', 'DLOAD', 'DSLOAD',
            'STEP', 'STATIC', 'DYNAMIC',
            'ASSEMBLY', 'PART',
            'INTERACTION', 'CONTACT'
        }
        
        # Store geometry metadata separately (NSET, ELSET, SURFACE, INSTANCE)
        self.geometry_metadata = {}
    
    def parse_file(self, file_path: str) -> Dict[str, Any]:
        """
        Parse an Abaqus INP file.
        
        Args:
            file_path: Path to the INP file
            
        Returns:
            Dictionary containing parsed sections
        """
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            return self.parse_string(content)
        except ValueError as e:
            # Re-raise with file path information
            error_msg = str(e)
            if file_path not in error_msg:
                error_msg = f"Error in file '{file_path}':\n{error_msg}"
            raise ValueError(error_msg)
        except Exception as e:
            raise ValueError(f"Error reading file '{file_path}': {e}")
    
    def parse_string(self, content: str) -> Dict[str, Any]:
        """
        Parse Abaqus INP content from a string.
        Separates geometry (nodes/elements) → VTK and non-geometry → Python dict.
        
        Args:
            content: String content of INP file
            
        Returns:
            Dictionary containing non-geometry parsed sections (materials, sets, BCs, etc.)
        """
        try:
            tree = self.parser.parse(content)
            all_parsed_data = self.transformer.transform(tree)
            
            # Separate geometry from non-geometry
            self._separate_geometry_and_non_geometry(all_parsed_data)
            
            # Write geometry to VTK
            self.vtk_writer.write()
            
            return self.parsed_data  # Returns only non-geometry data
        except Exception as e:
            # Extract line number from error if available
            error_msg = str(e)
            line_num = None
            line_content = None
            
            # Try to extract line number from Lark error messages
            import re
            lines = content.split('\n')
            
            # Look for patterns like "at line 123, column 456" or "line 123"
            match = re.search(r'line\s+(\d+)', error_msg, re.IGNORECASE)
            if match:
                line_num = int(match.group(1))
            else:
                # Try alternative patterns
                match = re.search(r'line\s*:\s*(\d+)', error_msg, re.IGNORECASE)
                if match:
                    line_num = int(match.group(1))
            
            # Build detailed error message
            error_details = f"Error parsing INP file: {e}"
            
            if line_num:
                error_details += f"\n\n{'='*60}"
                error_details += f"\n[DEBUG] Error at line {line_num}:"
                error_details += f"\n{'='*60}"
                
                # Get the actual line content
                if 1 <= line_num <= len(lines):
                    line_content = lines[line_num - 1]
                    error_details += f"\n  Line content: {repr(line_content)}"
                    error_details += f"\n  (Length: {len(line_content)} chars)"
                else:
                    error_details += f"\n  (Line {line_num} not found - file has {len(lines)} lines)"
                
                # Show context (previous and next lines)
                error_details += f"\n\n  Context:"
                if line_num > 1:
                    prev_line = lines[line_num - 2].strip()
                    error_details += f"\n    Line {line_num - 1}: {prev_line[:80]}"
                if 1 <= line_num <= len(lines):
                    error_details += f"\n  → Line {line_num}: {lines[line_num - 1].strip()[:80]}"
                if line_num < len(lines):
                    next_line = lines[line_num].strip()
                    error_details += f"\n    Line {line_num + 1}: {next_line[:80]}"
            else:
                # If we can't find line number, show the raw error
                error_details += f"\n\n[DEBUG] Could not extract line number from error message."
                error_details += f"\n  Error message: {error_msg}"
            
            raise ValueError(error_details)
    
    def _separate_geometry_and_non_geometry(self, all_data: Dict[str, Any]):
        """
        Separate geometry data (→ VTK) from non-geometry data (→ Python dict).
        Also converts node/element data to IR (Intermediate Representation) format.
        
        Args:
            all_data: All parsed data from transformer
        """
        # Process all sections
        for section_key, data in all_data.items():
            section_key_upper = section_key.upper()
            
            # Check if this is geometry data
            is_geometry = False
            geometry_type = None
            for geo_keyword in self.geometry_keywords:
                if geo_keyword in section_key_upper:
                    is_geometry = True
                    geometry_type = geo_keyword
                    break
            
            if is_geometry:
                # Handle different types of geometry data
                if geometry_type in ('NODE', 'ELEMENT'):
                    # Stream nodes/elements to VTK (using original data)
                    self._stream_geometry_to_vtk(section_key, data)
                    # Create IR (Intermediate Representation) with placeholder instead of full data
                    ir_data = self._create_geometry_ir(section_key, data)
                    # Store IR in geometry_metadata (replaces full data with IR)
                    self.geometry_metadata[section_key] = ir_data
                    # Also update all_data to IR format for consistency
                    all_data[section_key] = ir_data
                elif geometry_type == 'SECTION':
                    # Store section definitions with full command line and data
                    # Section command line is stored as key, data lines as value
                    self.geometry_metadata[section_key] = {
                        'command': section_key,  # Full command line (e.g., "*Solid Section, elset=_PickedSet2, material=Steel")
                        'data': data  # Data lines that follow (e.g., the line with just ",")
                    }
                else:
                    # Store geometry metadata (NSET, ELSET, SURFACE, INSTANCE)
                    # These are geometry-related but don't have coordinates for VTK
                    self.geometry_metadata[section_key] = data
            else:
                # Keep non-geometry data in parsed_data
                self.parsed_data[section_key] = data
    
    def _create_geometry_ir(self, section_key: str, data: Any) -> List[Any]:
        """
        Create Intermediate Representation (IR) for geometry data.
        Replaces large data arrays with placeholders for efficiency.
        
        Args:
            section_key: Section keyword (e.g., 'NODE', 'ELEMENT, TYPE=C3D4')
            data: Section data (list of lists)
            
        Returns:
            IR representation with placeholders
        """
        ir = []
        
        if 'ELEMENT' in section_key.upper():
            # Extract element type from section key
            element_type = None
            if 'TYPE=' in section_key:
                element_type = section_key.split('TYPE=')[1].split(',')[0].strip()
            
            # Add type information
            if element_type:
                ir.append([f"type = {element_type}"])
            else:
                ir.append(["type = UNKNOWN"])
            
            # Add data placeholder
            if isinstance(data, list) and len(data) > 0:
                ir.append(["data"])  # Placeholder indicating data exists
            else:
                ir.append([])
        else:
            # For NODE, just add data placeholder
            if isinstance(data, list) and len(data) > 0:
                ir.append(["data"])  # Placeholder indicating data exists
            else:
                ir.append([])
        
        return ir
    
    def _stream_geometry_to_vtk(self, section_key: str, data: Any):
        """
        Stream geometry data (nodes/elements) to VTK writer.
        
        Args:
            section_key: Section keyword (e.g., 'NODE', 'ELEMENT, TYPE=C3D4')
            data: Section data (list of lists)
        """
        section_key_upper = section_key.upper()
        
        # Process nodes
        if 'NODE' in section_key_upper:
            if isinstance(data, list):
                for line in data:
                    if isinstance(line, list) and len(line) >= 4:
                        node_id = int(line[0])
                        x = float(line[1])
                        y = float(line[2])
                        z = float(line[3]) if len(line) > 3 else 0.0
                        self.vtk_writer.add_node(node_id, x, y, z)
        
        # Process elements
        elif 'ELEMENT' in section_key_upper:
            # Extract element type from section key
            if 'TYPE=' in section_key:
                elem_type = section_key.split('TYPE=')[1].split(',')[0].strip()
                self.vtk_writer.set_element_type(elem_type)
            
            if isinstance(data, list):
                for line in data:
                    if isinstance(line, list) and len(line) >= 2:
                        elem_id = int(line[0])
                        node_ids = []
                        for x in line[1:]:
                            if isinstance(x, (int, float)):
                                node_ids.append(int(x))
                            elif isinstance(x, str):
                                try:
                                    node_ids.append(int(float(x)))
                                except (ValueError, TypeError):
                                    pass
                        if node_ids:
                            self.vtk_writer.add_element(elem_id, node_ids)
    
    def get_nodes(self) -> Dict[str, Any]:
        """
        Get node information. Geometry data is in VTK file, not in memory.
        
        Returns:
            Dictionary with VTK file information and node count
        """
        return {
            'vtk_file': self.vtk_output_file,
            'node_count': self.vtk_writer.node_count,
            'message': 'Node coordinates are stored in VTK file, not in memory'
        }
    
    def get_elements(self) -> Dict[str, Any]:
        """
        Get element information. Geometry data is in VTK file, not in memory.
        
        Returns:
            Dictionary with VTK file information and element count
        """
        return {
            'vtk_file': self.vtk_output_file,
            'element_count': self.vtk_writer.element_count,
            'message': 'Element connectivity is stored in VTK file, not in memory'
        }
    
    def get_materials(self) -> List[Dict[str, Any]]:
        """
        Extract material definitions from the parsed file.
        
        Returns:
            List of material dictionaries
        """
        materials = []
        material_sections = [k for k in self.parsed_data.keys() if 'MATERIAL' in k]
        
        for section_key in material_sections:
            # Material name is typically in the keyword parameters
            material_name = section_key.split(',')[0].replace('MATERIAL', '').strip()
            if not material_name:
                material_name = f"Material_{len(materials) + 1}"
            
            materials.append({
                'name': material_name,
                'section': section_key,
                'data': self.parsed_data[section_key]
            })
        
        return materials
    
    def get_all_sections(self) -> Dict[str, List[str]]:
        """
        Get list of all section keywords found in the file, separated by category.
        
        Returns:
            Dictionary with 'geometry', 'geometry_metadata', and 'non_geometry' sections
        """
        geometry_sections = []
        for key in self.geometry_metadata.keys():
            if 'NODE' in key.upper() or 'ELEMENT' in key.upper():
                geometry_sections.append(key)
        
        return {
            'geometry': geometry_sections,
            'geometry_metadata': list(self.geometry_metadata.keys()),
            'non_geometry': list(self.parsed_data.keys())
        }
    
    def get_section_data(self, keyword: str) -> Any:
        """
        Get data for a specific section keyword.
        
        Args:
            keyword: Section keyword (e.g., 'NODE', 'ELEMENT', 'MATERIAL')
            
        Returns:
            Data associated with the keyword
        """
        keyword_upper = keyword.upper()
        matching_keys = [k for k in self.parsed_data.keys() if keyword_upper in k.upper()]
        
        if not matching_keys:
            return None
        
        if len(matching_keys) == 1:
            return self.parsed_data[matching_keys[0]]
        
        # Return all matching sections
        return {k: self.parsed_data[k] for k in matching_keys}
    
    def get_boundary_conditions(self) -> List[Dict[str, Any]]:
        """
        Extract boundary condition definitions.
        
        Returns:
            List of boundary condition dictionaries
        """
        bc_sections = [k for k in self.parsed_data.keys() if 'BOUNDARY' in k.upper()]
        boundary_conditions = []
        
        for section_key in bc_sections:
            data = self.parsed_data[section_key]
            if isinstance(data, list):
                for line in data:
                    if isinstance(line, list) and len(line) >= 1:
                        # Convert numeric strings to numbers
                        processed_data = []
                        for val in line[1:]:
                            if isinstance(val, (int, float)):
                                processed_data.append(val)
                            elif isinstance(val, str):
                                try:
                                    if '.' in val or 'e' in val.lower() or 'E' in val:
                                        processed_data.append(float(val))
                                    else:
                                        processed_data.append(int(val))
                                except (ValueError, TypeError):
                                    processed_data.append(val)
                            else:
                                processed_data.append(val)
                        
                        bc = {
                            'node_set': line[0] if isinstance(line[0], str) else str(line[0]),
                            'data': processed_data
                        }
                        boundary_conditions.append(bc)
        
        return boundary_conditions
    
    def get_loads(self) -> List[Dict[str, Any]]:
        """
        Extract load definitions.
        
        Returns:
            List of load dictionaries
        """
        load_keywords = ['CLOAD', 'DLOAD', 'DSLOAD']
        loads = []
        
        for keyword in load_keywords:
            sections = [k for k in self.parsed_data.keys() if keyword in k.upper()]
            for section_key in sections:
                data = self.parsed_data[section_key]
                if isinstance(data, list):
                    for line in data:
                        if isinstance(line, list) and len(line) >= 1:
                            load = {
                                'type': keyword,
                                'data': line
                            }
                            loads.append(load)
        
        return loads
    
    def get_node_sets(self) -> List[Dict[str, Any]]:
        """
        Extract node set definitions (geometry metadata).
        
        Returns:
            List of node set dictionaries
        """
        nsets = []
        # Look in geometry_metadata (NSET is geometry keyword)
        nset_sections = [k for k in self.geometry_metadata.keys() if 'NSET' in k.upper()]
        
        for section_key in nset_sections:
            data = self.geometry_metadata[section_key]
            # Extract set name from keyword line
            set_name = section_key.split(',')[0].replace('NSET', '').strip()
            if not set_name:
                set_name = f"NSET_{len(nsets) + 1}"
            
            node_ids = []
            if isinstance(data, list):
                for line in data:
                    if isinstance(line, list):
                        for x in line:
                            if isinstance(x, (int, float)):
                                node_ids.append(int(x))
                            elif isinstance(x, str):
                                try:
                                    node_ids.append(int(float(x)))
                                except (ValueError, TypeError):
                                    pass
            
            nsets.append({
                'name': set_name,
                'nodes': node_ids
            })
        
        return nsets
    
    def get_element_sets(self) -> List[Dict[str, Any]]:
        """
        Extract element set definitions (geometry metadata).
        
        Returns:
            List of element set dictionaries
        """
        elsets = []
        # Look in geometry_metadata (ELSET is geometry keyword)
        elset_sections = [k for k in self.geometry_metadata.keys() if 'ELSET' in k.upper()]
        
        for section_key in elset_sections:
            data = self.geometry_metadata[section_key]
            # Extract set name from keyword line
            set_name = section_key.split(',')[0].replace('ELSET', '').strip()
            if not set_name:
                set_name = f"ELSET_{len(elsets) + 1}"
            
            element_ids = []
            if isinstance(data, list):
                for line in data:
                    if isinstance(line, list):
                        for x in line:
                            if isinstance(x, (int, float)):
                                element_ids.append(int(x))
                            elif isinstance(x, str):
                                try:
                                    element_ids.append(int(float(x)))
                                except (ValueError, TypeError):
                                    pass
            
            elsets.append({
                'name': set_name,
                'elements': element_ids
            })
        
        return elsets
    
    def get_surfaces(self) -> List[Dict[str, Any]]:
        """
        Extract surface definitions (geometry metadata).
        
        Returns:
            List of surface dictionaries
        """
        surfaces = []
        surface_sections = [k for k in self.geometry_metadata.keys() if 'SURFACE' in k.upper()]
        
        for section_key in surface_sections:
            data = self.geometry_metadata[section_key]
            # Extract surface name from keyword line
            surface_name = section_key.split(',')[0].replace('SURFACE', '').strip()
            if not surface_name:
                surface_name = f"SURFACE_{len(surfaces) + 1}"
            
            surfaces.append({
                'name': surface_name,
                'section': section_key,
                'data': data
            })
        
        return surfaces
    
    def get_instances(self) -> List[Dict[str, Any]]:
        """
        Extract instance definitions (geometry metadata).
        
        Returns:
            List of instance dictionaries
        """
        instances = []
        instance_sections = [k for k in self.geometry_metadata.keys() if 'INSTANCE' in k.upper()]
        
        for section_key in instance_sections:
            data = self.geometry_metadata[section_key]
            # Extract instance name from keyword line
            instance_name = section_key.split(',')[0].replace('INSTANCE', '').strip()
            if not instance_name:
                instance_name = f"INSTANCE_{len(instances) + 1}"
            
            instances.append({
                'name': instance_name,
                'section': section_key,
                'data': data
            })
        
        return instances
    
    def get_sections(self) -> List[Dict[str, Any]]:
        """
        Extract section definitions (geometry metadata).
        Sections like "Solid Section", "Shell Section", etc.
        
        Returns:
            List of section dictionaries with command line and data
        """
        sections = []
        section_keys = [k for k in self.geometry_metadata.keys() if 'SECTION' in k.upper()]
        
        for section_key in section_keys:
            section_data = self.geometry_metadata[section_key]
            
            # Handle both old format (just data) and new format (dict with command and data)
            if isinstance(section_data, dict) and 'command' in section_data:
                # New format: has command and data
                sections.append({
                    'command': section_data['command'],
                    'data': section_data['data']
                })
            else:
                # Old format: just data
                sections.append({
                    'command': section_key,
                    'data': section_data
                })
        
        return sections
    
    def get_geometry_metadata(self) -> Dict[str, Any]:
        """
        Get all geometry metadata (NSET, ELSET, SURFACE, INSTANCE, SECTION).
        
        Returns:
            Dictionary containing all geometry metadata sections
        """
        return self.geometry_metadata.copy()
    
    def summary(self) -> Dict[str, Any]:
        """
        Get a summary of the parsed file.
        
        Returns:
            Dictionary with summary statistics
        """
        materials = self.get_materials()
        nsets = self.get_node_sets()
        elsets = self.get_element_sets()
        boundary_conditions = self.get_boundary_conditions()
        loads = self.get_loads()
        
        surfaces = self.get_surfaces()
        instances = self.get_instances()
        sections = self.get_sections()
        
        summary = {
            # Geometry data
            'geometry': {
                # Mesh data in VTK file
                'mesh': {
                    'vtk_file': self.vtk_output_file,
                    'total_nodes': self.vtk_writer.node_count,
                    'total_elements': self.vtk_writer.element_count,
                },
                # Geometry metadata (NSET, ELSET, SURFACE, INSTANCE, SECTION)
                'metadata': {
                    'total_node_sets': len(nsets),
                    'total_element_sets': len(elsets),
                    'total_surfaces': len(surfaces),
                    'total_instances': len(instances),
                    'total_sections': len(sections),
                }
            },
            # Non-geometry data (in Python dict)
            'non_geometry': {
                'total_materials': len(materials),
                'total_boundary_conditions': len(boundary_conditions),
                'total_loads': len(loads),
            },
            'sections_found': self.get_all_sections()
        }
        
        return summary


if __name__ == "__main__":
    # Example usage
    import sys
    
    if len(sys.argv) > 1:
        file_path = sys.argv[1]
        parser = AbaqusParser()
        
        print(f"Parsing {file_path}...")
        parsed = parser.parse_file(file_path)
        
        print("\n=== Summary ===")
        summary = parser.summary()
        for key, value in summary.items():
            print(f"{key}: {value}")
        
        print("\n=== First 5 Nodes ===")
        nodes = parser.get_nodes()
        for node in nodes[:5]:
            print(f"Node {node['id']}: ({node['x']}, {node['y']}, {node['z']})")
        
        print("\n=== First 5 Elements ===")
        elements = parser.get_elements()
        for elem in elements[:5]:
            print(f"Element {elem['id']}: nodes {elem['nodes']}")
    else:
        print("Usage: python abaqus_parser.py <path_to_inp_file>")

