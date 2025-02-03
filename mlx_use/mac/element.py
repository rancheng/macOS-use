# --- START OF FILE mac_use/mac/element.py ---
from dataclasses import dataclass, field
from typing import Optional, Dict, List, Any
from functools import cached_property

@dataclass
class MacElementNode:
    """Represents a UI element in macOS"""
    # Required fields
    role: str
    identifier: str
    attributes: Dict[str, Any]
    is_visible: bool
    app_pid: int

    # Optional fields
    children: List['MacElementNode'] = field(default_factory=list)
    parent: Optional['MacElementNode'] = None
    is_interactive: bool = False
    highlight_index: Optional[int] = None
    _element = None  # Store AX element reference

    def __repr__(self) -> str:
        role_str = f'<{self.role}'
        for key, value in self.attributes.items():
            if key in ['title', 'value', 'description']:
                role_str += f' {key}="{value}"'
        role_str += '>'

        extras = []
        if self.is_interactive:
            extras.append('interactive')
        if self.highlight_index is not None:
            extras.append(f'highlight:{self.highlight_index}')
        if extras:
            role_str += f' [{", ".join(extras)}]'

        return role_str

    def get_clickable_elements_string(self) -> str:
        """Convert the UI tree to a string representation focusing on interactive elements"""
        formatted_text = []

        def process_node(node: 'MacElementNode', depth: int) -> None:
            if node.highlight_index is not None:
                attrs_str = ''
                for key in ['title', 'value', 'description']:
                    if key in node.attributes:
                        attrs_str += f' {key}="{node.attributes[key]}"'
                formatted_text.append(
                    f'{node.highlight_index}[:]<{node.role}{attrs_str}>'
                )
            for child in node.children:
                process_node(child, depth + 1)

        process_node(self, 0)
        return '\n'.join(formatted_text)

    def get_detailed_info(self) -> str:
        """Return a detailed string with all attributes of the element"""
        details = [f"Role: {self.role}", f"Identifier: {self.identifier}"]
        for key, value in self.attributes.items():
            details.append(f"{key}: {value}")
        return ", ".join(details)

    def get_detailed_string(self, indent: int = 0) -> str:
        """Recursively build a detailed string representation of the UI tree"""
        spaces = "  " * indent
        result = f"{spaces}{self.__repr__()} - {self.get_detailed_info()}"
        for child in self.children:
            result += "\n" + child.get_detailed_string(indent + 1)
        return result

    @cached_property
    def accessibility_path(self) -> str:
        """Generate a unique path to this element"""
        path_components = []
        current = self
        while current.parent is not None:
            role = current.role
            siblings = [s for s in current.parent.children if s.role == role]
            if len(siblings) > 1:
                idx = siblings.index(current) + 1
                path_components.append(f"{role}[{idx}]")
            else:
                path_components.append(role)
            current = current.parent
        path_components.reverse()
        return '/' + '/'.join(path_components)

    def find_element_by_path(self, path: str) -> Optional['MacElementNode']:
        """Find an element using its accessibility path"""
        if self.accessibility_path == path:
            return self
        for child in self.children:
            result = child.find_element_by_path(path)
            if result:
                return result
        return None