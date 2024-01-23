import re
from typing import Dict, List, Literal, Union
from pydantic import BaseModel


class Packages(BaseModel):
    dependencies: Dict[str, str] | None
    devDependencies: Dict[str, str] | None

class FileContext(BaseModel):
    path_to_teacup_folder: str
    file_path: str
    file_content: str
    root_directory: str
    packages: Packages


class TeaTag(BaseModel):
    match: re.Match[str]
    tag: str
    props: dict
    children: str
    attributes: str

    class Config:
        arbitrary_types_allowed = True

class SteepContext(FileContext):
    steep_path: str
    steep_content: str
    loading_component_path: str
    tea_import_statement: str
    tea_tag: TeaTag

def extract_tag(file_content, tag="\w+", attribute=""):
    """
    Extracts a tag from the file content based on the tag name and additional attributes.
    """
    pattern = rf"<({tag})\s?([^>/]*?{attribute}[^>/]*)(?:>(.*?)</{tag}>|/>)"
    match = re.search(pattern, file_content, re.DOTALL)

    if match:
        tag_name, attributes, content = match.groups()
        props = {
            m[0]: m[1] or True
            for m in re.findall(r'(\w+)(?:=["\']([^"\']+)["\']|\b)', attributes)
        }
        return TeaTag(
            match=match,
            tag=tag_name,
            props=props,
            children=content.strip() if content else "",
            attributes=attributes,
        )

    return None

def set_import(file_content: str, import_statement: str, remove=False) -> tuple[str, bool]:
    # Pattern to match the script tag and any content inside it
    script_pattern = r"(<script[^>]*>)([\s\S]*?)(<\/script>)"
    # Pattern to match import statements
    import_pattern = r"(import .*?;)"
    
    def add_import(script_content: str) -> str:
        # Check if the import statement already exists
        if import_statement in script_content:
            return script_content  # No change needed

        # Check for existing import statements
        existing_imports = re.findall(import_pattern, script_content)
        if existing_imports:
            # Add the new import after the last existing import
            last_import = existing_imports[-1]
            return script_content.replace(last_import, last_import + '\n' + import_statement)
        else:
            # No existing imports, add after <script> tag
            return import_statement + '\n' + script_content

    def remove_import(script_content: str) -> str:
        # Remove the specified import statement
        return re.sub(rf"{import_statement}\s*\n?", "", script_content)

    # Find the script tag content
    match = re.search(script_pattern, file_content)
    if match:
        script_tag, script_content, script_end_tag = match.groups()
        new_script_content = remove_import(script_content) if remove else add_import(script_content)
        # Replace old script content with new script content
        return file_content.replace(script_tag + script_content + script_end_tag, script_tag + new_script_content + script_end_tag), True
    else:
        # If no script tag is found, add one with the import if it's not being removed
        return (file_content, False) if remove else (f"\n<script setup>\n{import_statement}\n</script>\n{file_content}", True)