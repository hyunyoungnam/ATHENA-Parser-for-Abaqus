"""
Test code for the ATHENA Parser for Abaqus INP files.
Loads and parses example3.inp from the inputs folder and outputs to XML.
"""

import os
import xml.etree.ElementTree as ET
from xml.dom import minidom
from abaqus_parser import AbaqusParser


def create_xml_output(parser, output_file="parsed-output.xml"):
    """
    Create XML output from parsed Abaqus data.
    
    Args:
        parser: AbaqusParser instance with parsed data
        output_file: Path to output XML file
    """
    # Create root element
    root = ET.Element("abaqus_parsed_data")
    
    # Add summary
    summary = parser.summary()
    summary_elem = ET.SubElement(root, "summary")
    for key, value in summary.items():
        summary_item = ET.SubElement(summary_elem, key)
        summary_item.text = str(value)
    
    # Add geometry info (nodes/elements are in VTK file)
    nodes_info = parser.get_nodes()
    geometry_elem = ET.SubElement(root, "geometry")
    geometry_elem.set("vtk_file", nodes_info['vtk_file'])
    geometry_elem.set("node_count", str(nodes_info['node_count']))
    elements_info = parser.get_elements()
    geometry_elem.set("element_count", str(elements_info['element_count']))
    geometry_elem.text = "Geometry data (nodes/elements) is stored in VTK file"
    
    # Add node sets
    nsets = parser.get_node_sets()
    if nsets:
        nsets_elem = ET.SubElement(root, "node_sets")
        for nset in nsets:
            nset_elem = ET.SubElement(nsets_elem, "node_set")
            nset_elem.set("name", nset['name'])
            nodes_attr = ",".join(str(n) for n in nset['nodes'])
            nset_elem.set("nodes", nodes_attr)
            nset_elem.set("count", str(len(nset['nodes'])))
    
    # Add element sets
    elsets = parser.get_element_sets()
    if elsets:
        elsets_elem = ET.SubElement(root, "element_sets")
        for elset in elsets:
            elset_elem = ET.SubElement(elsets_elem, "element_set")
            elset_elem.set("name", elset['name'])
            elements_attr = ",".join(str(e) for e in elset['elements'])
            elset_elem.set("elements", elements_attr)
            elset_elem.set("count", str(len(elset['elements'])))
    
    # Add materials
    materials = parser.get_materials()
    if materials:
        materials_elem = ET.SubElement(root, "materials")
        for mat in materials:
            mat_elem = ET.SubElement(materials_elem, "material")
            mat_elem.set("name", mat['name'])
            mat_elem.set("section", mat['section'])
    
    # Add boundary conditions
    bcs = parser.get_boundary_conditions()
    if bcs:
        bcs_elem = ET.SubElement(root, "boundary_conditions")
        for bc in bcs:
            bc_elem = ET.SubElement(bcs_elem, "boundary_condition")
            bc_elem.set("node_set", str(bc['node_set']))
            data_attr = ",".join(str(d) for d in bc['data'])
            bc_elem.set("data", data_attr)
    
    # Add loads
    loads = parser.get_loads()
    if loads:
        loads_elem = ET.SubElement(root, "loads")
        for load in loads:
            load_elem = ET.SubElement(loads_elem, "load")
            load_elem.set("type", load['type'])
            data_attr = ",".join(str(d) for d in load['data'])
            load_elem.set("data", data_attr)
    
    # Add all sections found (separated by category)
    sections = parser.get_sections()
    if sections:
        sections_elem = ET.SubElement(root, "sections")
        
        # Geometry sections
        if sections.get('geometry'):
            geometry_elem = ET.SubElement(sections_elem, "geometry")
            for section in sections['geometry']:
                section_elem = ET.SubElement(geometry_elem, "section")
                section_elem.text = section
        
        # Geometry metadata sections
        if sections.get('geometry_metadata'):
            metadata_elem = ET.SubElement(sections_elem, "geometry_metadata")
            for section in sections['geometry_metadata']:
                section_elem = ET.SubElement(metadata_elem, "section")
                section_elem.text = section
        
        # Non-geometry sections
        if sections.get('non_geometry'):
            non_geo_elem = ET.SubElement(sections_elem, "non_geometry")
            for section in sections['non_geometry']:
                section_elem = ET.SubElement(non_geo_elem, "section")
                section_elem.text = section
    
    # Create tree and write to file with pretty formatting
    tree = ET.ElementTree(root)
    
    # Pretty print XML
    xml_str = ET.tostring(root, encoding='unicode')
    dom = minidom.parseString(xml_str)
    pretty_xml = dom.toprettyxml(indent="  ")
    
    # Remove extra blank lines
    lines = [line for line in pretty_xml.split('\n') if line.strip()]
    pretty_xml = '\n'.join(lines)
    
    # Write to file
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(pretty_xml)
    
    return output_file


def create_txt_output(parser, output_file="transformer-output.txt"):
    """
    Create transformer output (IR format) from parsed Abaqus data.
    
    Args:
        parser: AbaqusParser instance with parsed data
        output_file: Path to output text file
    """
    # Ensure output directory exists
    output_dir = os.path.dirname(output_file) if os.path.dirname(output_file) else "output"
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir, exist_ok=True)
    
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write("=" * 80 + "\n")
        f.write("ATHENA Parser for Abaqus - Transformer Output (IR Format)\n")
        f.write("=" * 80 + "\n\n")
        f.write("This file shows the Intermediate Representation (IR) from the transformer.\n")
        f.write("Geometry data (NODE, ELEMENT) shows placeholders - actual data is in VTK file.\n\n")
        
        # Summary
        summary = parser.summary()
        f.write("SUMMARY\n")
        f.write("-" * 80 + "\n")
        f.write(f"Geometry (VTK):\n")
        f.write(f"  File: {summary['geometry']['mesh']['vtk_file']}\n")
        f.write(f"  Nodes: {summary['geometry']['mesh']['total_nodes']}\n")
        f.write(f"  Elements: {summary['geometry']['mesh']['total_elements']}\n")
        f.write(f"\nGeometry Metadata:\n")
        for key, value in summary['geometry']['metadata'].items():
            f.write(f"  {key}: {value}\n")
        f.write(f"\nNon-Geometry:\n")
        for key, value in summary['non_geometry'].items():
            f.write(f"  {key}: {value}\n")
        f.write("\n" + "=" * 80 + "\n\n")
        
        # Geometry Metadata
        f.write("GEOMETRY METADATA\n")
        f.write("-" * 80 + "\n")
        
        # Sections
        sections = parser.get_sections()
        if sections:
            f.write("\nSECTIONS:\n")
            for i, section in enumerate(sections, 1):
                f.write(f"\n  Section {i}:\n")
                f.write(f"    Command: {section['command']}\n")
                f.write(f"    Data: {section['data']}\n")
        
        # Node Sets
        nsets = parser.get_node_sets()
        if nsets:
            f.write("\nNODE SETS:\n")
            for nset in nsets:
                f.write(f"  {nset['name']}: {len(nset['nodes'])} nodes\n")
                if len(nset['nodes']) <= 20:
                    f.write(f"    Nodes: {nset['nodes']}\n")
                else:
                    f.write(f"    Nodes: {nset['nodes'][:20]} ... (and {len(nset['nodes']) - 20} more)\n")
        
        # Element Sets
        elsets = parser.get_element_sets()
        if elsets:
            f.write("\nELEMENT SETS:\n")
            for elset in elsets:
                f.write(f"  {elset['name']}: {len(elset['elements'])} elements\n")
                if len(elset['elements']) <= 20:
                    f.write(f"    Elements: {elset['elements']}\n")
                else:
                    f.write(f"    Elements: {elset['elements'][:20]} ... (and {len(elset['elements']) - 20} more)\n")
        
        # Surfaces
        surfaces = parser.get_surfaces()
        if surfaces:
            f.write("\nSURFACES:\n")
            for surface in surfaces:
                f.write(f"  {surface['name']}: {surface['section']}\n")
        
        # Instances
        instances = parser.get_instances()
        if instances:
            f.write("\nINSTANCES:\n")
            for instance in instances:
                f.write(f"  {instance['name']}: {instance['section']}\n")
        
        f.write("\n" + "=" * 80 + "\n\n")
        
        # Non-Geometry Data
        f.write("NON-GEOMETRY DATA\n")
        f.write("-" * 80 + "\n")
        
        # Materials
        materials = parser.get_materials()
        if materials:
            f.write("\nMATERIALS:\n")
            for mat in materials:
                f.write(f"  {mat['name']}: {mat['section']}\n")
        
        # Boundary Conditions
        bcs = parser.get_boundary_conditions()
        if bcs:
            f.write("\nBOUNDARY CONDITIONS:\n")
            for bc in bcs:
                f.write(f"  Node Set: {bc['node_set']}, Data: {bc['data']}\n")
        
        # Loads
        loads = parser.get_loads()
        if loads:
            f.write("\nLOADS:\n")
            for load in loads:
                f.write(f"  Type: {load['type']}, Data: {load['data']}\n")
        
        # All sections found
        all_sections = parser.get_all_sections()
        f.write("\n" + "=" * 80 + "\n")
        f.write("ALL SECTIONS FOUND\n")
        f.write("-" * 80 + "\n")
        f.write(f"Geometry: {all_sections['geometry']}\n")
        f.write(f"Geometry Metadata: {all_sections['geometry_metadata']}\n")
        f.write(f"Non-Geometry: {all_sections['non_geometry']}\n")
        
        f.write("\n" + "=" * 80 + "\n")
        f.write("END OF PARSED OUTPUT\n")
        f.write("=" * 80 + "\n")
    
    return output_file


def create_lark_output(parser, inp_file_path: str, output_file="lark-output.txt"):
    """
    Create Lark parse tree output from parsed Abaqus data.
    
    Args:
        parser: AbaqusParser instance (already initialized)
        inp_file_path: Path to the original INP file (to re-parse for tree)
        output_file: Path to output text file
    """
    # Ensure output directory exists
    output_dir = os.path.dirname(output_file) if os.path.dirname(output_file) else "output"
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir, exist_ok=True)
    
    # Re-read and parse the file to get the parse tree
    with open(inp_file_path, 'r', encoding='utf-8', errors='ignore') as f:
        content = f.read()
    
    # Parse to get the tree
    tree = parser.parser.parse(content)
    
    # Write parse tree to file
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write("=" * 80 + "\n")
        f.write("Lark Parse Tree Output\n")
        f.write("=" * 80 + "\n\n")
        f.write("This file shows the raw parse tree structure from Lark.\n")
        f.write("The tree represents the grammatical structure of the INP file.\n\n")
        f.write("-" * 80 + "\n\n")
        
        # Write tree in pretty format
        f.write("PARSE TREE:\n")
        f.write("-" * 80 + "\n")
        f.write(str(tree.pretty()))
        f.write("\n\n")
        
        f.write("=" * 80 + "\n")
        f.write("TREE STRUCTURE (Text Format):\n")
        f.write("-" * 80 + "\n")
        f.write(str(tree))
        f.write("\n\n")
        
        f.write("=" * 80 + "\n")
        f.write("END OF LARK PARSE TREE\n")
        f.write("=" * 80 + "\n")
    
    return output_file


def main():
    # Force output to be visible immediately
    import sys
    sys.stdout.flush()
    
    print("=" * 60)
    print("ATHENA Parser for Abaqus - Starting...")
    print("=" * 60)
    sys.stdout.flush()
    
    # Load INP file from inputs folder
    file_path = os.path.join("inputs", "example3.inp")
    
    # Check if file exists
    if not os.path.exists(file_path):
        print(f"ERROR: File '{file_path}' not found!")
        print(f"Please ensure the file exists in the inputs folder.")
        sys.stdout.flush()
        return
    
    print(f"\nFile found: {file_path}")
    sys.stdout.flush()
    
    # Parse with automatic separation:
    # - Geometry (nodes/elements) → VTK file
    # - Non-geometry (materials, sets, BCs, etc.) → Python dict
    vtk_output = "geometry.vtk"
    print(f"\n{'='*60}")
    print(f"Loading and parsing: {file_path}")
    print(f"{'='*60}")
    print(f"Geometry data (nodes/elements) → {vtk_output}")
    print(f"Non-geometry data (materials, sets, BCs) → Python dict")
    sys.stdout.flush()
    
    try:
        # Initialize parser - geometry always goes to VTK
        parser = AbaqusParser(vtk_output=vtk_output)
        
        # Parse file - returns only non-geometry data
        print("\n[INFO] Starting parse...")
        sys.stdout.flush()
        non_geometry_data = parser.parse_file(file_path)
        print("[SUCCESS] Parsing completed successfully!")
        sys.stdout.flush()
        
        print(f"\n{'='*60}")
        print("DATA SEPARATION RESULTS")
        print(f"{'='*60}")
        print(f"\nGeometry (in VTK file):")
        print(f"  VTK file: {vtk_output}")
        print(f"  Nodes: {parser.vtk_writer.node_count}")
        print(f"  Elements: {parser.vtk_writer.element_count}")
        
        print(f"\nGeometry Metadata (NSET, ELSET, SURFACE, INSTANCE):")
        geometry_metadata = parser.get_geometry_metadata()
        print(f"  Sections found: {list(geometry_metadata.keys())}")
        
        print(f"\nNon-geometry (in Python dict):")
        print(f"  Sections found: {list(non_geometry_data.keys())}")
        sys.stdout.flush()
        
    except Exception as e:
        print(f"\n{'='*60}")
        print("ERROR PARSING FILE")
        print(f"{'='*60}")
        print(f"Error: {e}")
        import traceback
        print("\nFull traceback:")
        traceback.print_exc()
        sys.stdout.flush()
        return
    
    # Create XML output
    xml_output_file = "parsed-output.xml"
    print(f"\n{'='*60}")
    print(f"Creating XML output file: {xml_output_file}...")
    sys.stdout.flush()
    try:
        create_xml_output(parser, xml_output_file)
        print(f"[SUCCESS] XML output created: {xml_output_file}")
        sys.stdout.flush()
    except Exception as e:
        print(f"[ERROR] Error creating XML output: {e}")
        import traceback
        traceback.print_exc()
        sys.stdout.flush()
    
    # Create output directory
    output_dir = os.path.join(os.getcwd(), "output")
    if not os.path.exists(output_dir):
        os.makedirs(output_dir, exist_ok=True)
        print(f"\n[INFO] Created output directory: {output_dir}")
        sys.stdout.flush()
    
    # Create transformer output (text file)
    transformer_output_file = os.path.join(output_dir, "transformer-output.txt")
    print(f"\n{'='*60}")
    print(f"Creating transformer output file: {transformer_output_file}...")
    sys.stdout.flush()
    try:
        create_txt_output(parser, transformer_output_file)
        print(f"[SUCCESS] Transformer output created: {transformer_output_file}")
        sys.stdout.flush()
    except Exception as e:
        print(f"[ERROR] Error creating transformer output: {e}")
        import traceback
        traceback.print_exc()
        sys.stdout.flush()
    
    # Create Lark parse tree output
    lark_output_file = os.path.join(output_dir, "lark-output.txt")
    print(f"\n{'='*60}")
    print(f"Creating Lark parse tree output file: {lark_output_file}...")
    sys.stdout.flush()
    try:
        create_lark_output(parser, file_path, lark_output_file)
        print(f"[SUCCESS] Lark output created: {lark_output_file}")
        sys.stdout.flush()
    except Exception as e:
        print(f"[ERROR] Error creating Lark output: {e}")
        import traceback
        traceback.print_exc()
        sys.stdout.flush()
    
    print(f"\n{'='*60}")
    print("PROCESS COMPLETE")
    print(f"{'='*60}")
    print(f"Output files created:")
    print(f"  - {vtk_output} (geometry mesh)")
    print(f"  - {xml_output_file} (XML format)")
    print(f"  - {transformer_output_file} (transformer IR format)")
    print(f"  - {lark_output_file} (Lark parse tree)")
    sys.stdout.flush()


if __name__ == "__main__":
    # Immediate test output
    import sys
    print("Script started!", flush=True)
    sys.stdout.flush()
    
    try:
        main()
    except Exception as e:
        print(f"\nFATAL ERROR: {e}", flush=True)
        import traceback
        traceback.print_exc()
        sys.stdout.flush()

