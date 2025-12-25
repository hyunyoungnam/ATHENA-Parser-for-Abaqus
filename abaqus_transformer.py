"""
Part 1: Abaqus Transformer
Transforms the Lark parse tree into structured Python data.
"""

from lark import Transformer


class AbaqusTransformer(Transformer):
    """Transforms the parse tree into structured data."""
    
    def start(self, items):
        """Root node - returns a dictionary of all sections."""
        result = {}
        for item in items:
            if isinstance(item, tuple) and len(item) == 2:
                keyword, data = item
                result[keyword] = data
        return result
    
    def section(self, items):
        """A section consists of a keyword and its data."""
        keyword_line_data = items[0]
        data = items[1] if len(items) > 1 else []
        
        # Extract keyword name from keyword_line
        if isinstance(keyword_line_data, dict):
            keyword = keyword_line_data.get("name", "")
        elif isinstance(keyword_line_data, str):
            keyword = keyword_line_data
        else:
            keyword = str(keyword_line_data)
        
        return (keyword, data)
    
    def keyword_line(self, items):
        """Extract keyword name and parameters."""
        keyword_name = items[0].upper() if items else ""
        params = {}
        for item in items[1:]:
            if isinstance(item, dict):
                params.update(item)
        return {"name": keyword_name, "params": params}
    
    def keyword(self, items):
        """Process keyword - can be single or multiple words."""
        if items:
            # Join multiple keyword words with space
            keyword_parts = [str(item).upper() for item in items]
            return " ".join(keyword_parts)
        return ""
    
    def keyword_word(self, items):
        """Single keyword word."""
        if items:
            return items[0].upper()
        return ""
    
    def params(self, items):
        """Process parameters."""
        params_dict = {}
        for item in items:
            if isinstance(item, dict):
                params_dict.update(item)
        return params_dict
    
    def param(self, items):
        """Single parameter - receives result from param_with_value or param_flag."""
        # Items will be a dict from either param_with_value or param_flag
        if items and isinstance(items[0], dict):
            return items[0]
        return {}
    
    def param_with_value(self, items):
        """Parameter with value (key=value)."""
        if len(items) >= 2:
            key = items[0].upper()
            value = items[1]
            return {key: value}
        return {}
    
    def param_flag(self, items):
        """Parameter flag (just key, no value)."""
        if len(items) >= 1:
            key = items[0].upper()
            return {key: True}
        return {}
    
    def data_lines(self, items):
        """Collection of data lines."""
        return list(items)
    
    def data_line(self, items):
        """Single data line - list of values."""
        result = []
        for item in items:
            if item is None:
                continue
            # Skip NEWLINE tokens
            if hasattr(item, 'type') and item.type == 'NEWLINE':
                continue
            if isinstance(item, str) and item == '\n':
                continue
            # Handle Token objects
            if hasattr(item, 'type') and item.type == 'COMMA':
                # Standalone comma - keep it as a special marker
                result.append(',')
                continue
            if hasattr(item, 'value'):
                val = item.value
                if val != '\n':
                    result.append(val)
            elif hasattr(item, 'type'):  # Token object
                if item.type == 'NEWLINE':
                    continue
                val = str(item)
                # Try to convert to number if it's a NUMBER token
                if item.type == 'NUMBER':
                    try:
                        if '.' in val or 'e' in val.lower() or 'E' in val:
                            result.append(float(val))
                        else:
                            result.append(int(val))
                    except ValueError:
                        result.append(val)
                elif item.type != 'NEWLINE':
                    result.append(val)
            else:
                if item != '\n' and not (isinstance(item, str) and item.strip() == ''):
                    result.append(item)
        
        # If result is empty or only contains comma, return comma as data
        if not result or (len(result) == 1 and result[0] == ','):
            return [',']
        
        return result
    
    def value(self, items):
        """A single value (number or string)."""
        if not items:
            return None
        item = items[0]
        # Handle Token objects
        if hasattr(item, 'value'):
            return item.value
        elif hasattr(item, 'type'):  # Token object
            val = str(item)
            if item.type == 'NUMBER':
                try:
                    if '.' in val or 'e' in val.lower() or 'E' in val:
                        return float(val)
                    return int(val)
                except ValueError:
                    return val
            return val
        return item
    
    def number(self, items):
        """Convert to float or int."""
        val = items[0]
        if hasattr(val, 'value'):
            val = val.value
        elif hasattr(val, 'type'):
            val = str(val)
        try:
            if '.' in str(val) or 'e' in str(val).lower() or 'E' in str(val):
                return float(val)
            return int(val)
        except ValueError:
            return val
    
    def string(self, items):
        """String value."""
        if not items:
            return ""
        item = items[0]
        if hasattr(item, 'value'):
            return item.value
        elif hasattr(item, 'type'):
            return str(item)
        return item
    
    def quoted_string(self, items):
        """Quoted string value."""
        if not items:
            return ""
        item = items[0]
        if hasattr(item, 'value'):
            val = item.value
        elif hasattr(item, 'type'):
            val = str(item)
        else:
            val = str(item)
        # Remove quotes
        if val.startswith('"') and val.endswith('"'):
            return val[1:-1]
        elif val.startswith("'") and val.endswith("'"):
            return val[1:-1]
        return val
    
    def identifier(self, items):
        """Identifier value (allows hyphens)."""
        if not items:
            return ""
        item = items[0]
        if hasattr(item, 'value'):
            return item.value
        elif hasattr(item, 'type'):
            return str(item)
        return item
    
    def param_value(self, items):
        """Parameter value (can be WORD, IDENTIFIER, NUMBER, or QUOTED_STRING)."""
        if not items:
            return ""
        return items[0]
    
    def comment_text(self, items):
        """Comment text."""
        if not items:
            return ""
        return str(items[0])

