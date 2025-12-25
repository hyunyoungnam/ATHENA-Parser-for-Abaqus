# Transformer Expected Output

## Overview

The `AbaqusTransformer` converts the Lark parse tree into a structured Python dictionary. This document explains the expected output format.

## Output Structure

The transformer's `start()` method returns a **dictionary** where:
- **Keys**: Section keywords (e.g., "NODE", "ELEMENT", "SOLID SECTION")
- **Values**: Lists of data lines, where each line is a list of values

## General Format

```python
{
    "KEYWORD": [
        [value1, value2, value3, ...],  # Data line 1
        [value4, value5, value6, ...],  # Data line 2
        ...
    ],
    "ANOTHER KEYWORD": [
        [data_line_1],
        [data_line_2],
        ...
    ]
}
```

## Examples

### Example 1: Node Section

**Input INP:**
```
*NODE
1, 0.0, 0.0, 0.0
2, 1.0, 0.0, 0.0
3, 0.0, 1.0, 0.0
```

**Transformer Output (IR - Intermediate Representation):**
```python
{
    "NODE": [
        ["data"]  # Placeholder - actual data saved to VTK file
    ]
}
```

**Notes:**
- Keyword is uppercased: "NODE"
- Full node data is streamed to VTK file (not shown in IR)
- IR shows placeholder `["data"]` to indicate data exists
- This makes IR efficient for large datasets

### Example 2: Element Section

**Input INP:**
```
*ELEMENT, TYPE=C3D4
1, 1, 2, 3, 4
2, 2, 3, 4, 5
```

**Transformer Output (IR - Intermediate Representation):**
```python
{
    "ELEMENT": [
        ["type = C3D4"],  # Element type extracted from parameters
        ["data"]          # Placeholder - actual data saved to VTK file
    ]
}
```

**Notes:**
- Element type is extracted and shown as `["type = C3D4"]`
- Full element data (connectivity) is streamed to VTK file (not shown in IR)
- IR shows placeholder `["data"]` to indicate data exists
- Element type comes from non-geometry parameters (TYPE=)

### Example 3: Section with Parameters

**Input INP:**
```
*Solid Section, elset=_PickedSet2, material=Steel
,
```

**Transformer Output:**
```python
{
    "SOLID SECTION": [
        [","]  # or [] if comma is filtered
    ]
}
```

**Notes:**
- Multi-word keywords are joined with space: "SOLID SECTION"
- Parameters (elset, material) are in the keyword string, not separate
- Data line with just comma becomes a list

### Example 4: Node Set

**Input INP:**
```
*Nset, nset=Set-1, internal, generate
1, 2, 3, 4, 5
```

**Transformer Output:**
```python
{
    "NSET": [
        [1, 2, 3, 4, 5]
    ]
}
```

**Notes:**
- Parameters (nset, internal, generate) are in keyword string
- Node IDs are converted to `int`
- Multiple values on one line become one list

### Example 5: Material Section

**Input INP:**
```
*MATERIAL, NAME=Steel
*ELASTIC
200000, 0.3
```

**Transformer Output:**
```python
{
    "MATERIAL": [
        []  # No data lines for MATERIAL keyword itself
    ],
    "ELASTIC": [
        [200000.0, 0.3]
    ]
}
```

**Notes:**
- Each keyword becomes a separate entry
- Material name is in the keyword string
- Elastic properties are floats

### Example 6: Boundary Condition

**Input INP:**
```
*BOUNDARY
ALL_NODES, 1, 1, 0.0
```

**Transformer Output:**
```python
{
    "BOUNDARY": [
        ["ALL_NODES", 1, 1, 0.0]
    ]
}
```

**Notes:**
- Node set name is a string
- DOF numbers are `int`
- Value is `float`

## Data Type Conversions

The transformer automatically converts:

| Input | Output Type | Example |
|-------|-------------|---------|
| `"1"` | `int` | `1` |
| `"1.0"` | `float` | `1.0` |
| `"1e-5"` | `float` | `1e-5` |
| `"Part-1"` | `str` | `"Part-1"` |
| `"Steel"` | `str` | `"Steel"` |
| `'"quoted"'` | `str` | `"quoted"` (quotes removed) |

## Special Cases

### Empty Sections
```python
{
    "KEYWORD": []  # No data lines
}
```

### Single Value Lines
```python
{
    "KEYWORD": [
        [single_value]
    ]
}
```

### Multi-line Data
```python
{
    "KEYWORD": [
        [val1, val2],  # Line 1
        [val3, val4],  # Line 2
        [val5]         # Line 3
    ]
}
```

### Parameters in Keywords

Parameters are **not** extracted separately. They remain part of the keyword string:

**Input:**
```
*Nset, nset=MySet, internal
```

**Output Key:**
```
"NSET"  # Just the keyword, parameters are lost in current implementation
```

**Note:** The full command line with parameters is available in the parse tree but simplified in the final output. To preserve parameters, you'd need to modify the transformer.

## Complete Example

**Input INP:**
```
*NODE
1, 0.0, 0.0, 0.0
2, 1.0, 0.0, 0.0
*ELEMENT, TYPE=C3D4
1, 1, 2, 3, 4
*MATERIAL, NAME=Steel
*ELASTIC
200000, 0.3
*BOUNDARY
ALL_NODES, 1, 1, 0.0
```

**Transformer Output (IR - Intermediate Representation):**
```python
{
    "NODE": [
        ["data"]  # Actual node data saved to VTK
    ],
    "ELEMENT": [
        ["type = C3D4"],  # Element type from parameters
        ["data"]          # Actual element data saved to VTK
    ],
    "MATERIAL": [
        []
    ],
    "ELASTIC": [
        [200000.0, 0.3]
    ],
    "BOUNDARY": [
        ["ALL_NODES", 1, 1, 0.0]
    ]
}
```

**Notes:**
- NODE and ELEMENT use IR format (placeholders)
- Actual geometry data is in VTK file
- Non-geometry data (MATERIAL, ELASTIC, BOUNDARY) shows full data
- Element type is extracted and shown separately

## Key Points

1. **Dictionary Structure**: Always a dict with keyword → data mapping
2. **Keyword Format**: Uppercased, multi-word keywords joined with spaces
3. **Data Format**: List of lists (lines → values)
4. **Type Conversion**: Automatic (strings → int/float where appropriate)
5. **IR Format for Geometry**: NODE and ELEMENT use placeholders (`["data"]`) instead of full data
6. **Element Type Extraction**: Element type is shown as `["type = TYPE_NAME"]` in IR
7. **VTK Storage**: Actual node/element data is saved to VTK file, not in IR
8. **Non-Geometry Data**: Shows full data (not IR format)
9. **Comments Ignored**: Comment lines (`**`) are not included in output
10. **Empty Lines Ignored**: Empty lines don't create entries

## IR Format Benefits

- **Efficiency**: Large node/element data doesn't bloat the IR
- **Readability**: Easy to see structure without millions of numbers
- **Separation**: Geometry data (VTK) vs metadata (IR) clearly separated
- **Type Information**: Element types preserved and visible in IR

## Accessing Transformer Output

In the parser:
```python
tree = self.parser.parse(content)
all_parsed_data = self.transformer.transform(tree)
# all_parsed_data is the dictionary described above
```

## What Happens Next

After transformer output, the parser:
1. Separates geometry (NODE, ELEMENT) → VTK
2. Separates geometry metadata (NSET, ELSET, SECTION, etc.) → geometry_metadata
3. Keeps non-geometry (MATERIAL, BOUNDARY, etc.) → parsed_data

So the transformer output is the **raw parsed data** before any separation or processing.

