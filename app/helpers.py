import logging
import os
import re
from pathlib import Path
from typing import Any, Dict, List

import json5
from pydantic import BaseModel

file_log = os.getenv("FILE_LOG_PATH", None)
log_level = os.getenv("LOG_LEVEL", "INFO")
logging.basicConfig(filename=file_log, level=getattr(logging, log_level.upper()))
log = logging.getLogger("Tea")


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


class EnvConfig(BaseModel):
    patterns: List[str]
    root_directory: str
    ignore_patterns: List[str]
    model: str
    temperature: float
    base_url: str
    log_level: str
    openai_key: str | None


CONFIG_DEFAULTS = {
    "MODEL": "deepseek-coder:6.7b-instruct",
    "LOG_LEVEL": "INFO",
    "ROOT_DIRECTORY": None,
    "TEMPERATURE": "0.5",
    "PATTERNS": "*.vue",
    "IGNORE_PATTERNS": "Tea.vue,Steep.vue,Heating.vue",
}


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


def pour_tag(file_content: str, new_component_name: str):
    """
    Replaces a tag with the newly created component
    """
    script_pattern = r"(<Tea)([^>]*)>([\s\S]*?)(<\/Tea>)"
    match = re.search(script_pattern, file_content)
    if match:
        tag, attributes, content, end_tag = match.groups()
        # Remove the pour attribute
        new_attributes = re.sub(
            rf"pour=[\"']{new_component_name}[\"']", "", attributes
        ).rstrip()

        return re.sub(
            script_pattern,
            f"<{new_component_name}{new_attributes}></{new_component_name}>",
            file_content,
        )
    else:
        # No script tag found, return original file content
        return file_content


def set_import(
    file_content: str, import_statement: str, remove=False
) -> tuple[str, bool]:
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
            return script_content.replace(
                last_import, last_import + "\n" + import_statement
            )
        else:
            # No existing imports, add after <script> tag
            return "\n" + import_statement + "\n" + script_content

    def remove_import(script_content: str) -> str:
        # Remove the specified import statement
        return re.sub(rf"{import_statement}\s*\n?", "", script_content)

    # Find the script tag content
    match = re.search(script_pattern, file_content)
    if match:
        script_tag, script_content, script_end_tag = match.groups()
        new_script_content = (
            remove_import(script_content) if remove else add_import(script_content)
        )
        # Replace old script content with new script content
        return (
            file_content.replace(
                script_tag + script_content + script_end_tag,
                script_tag + new_script_content + script_end_tag,
            ),
            True,
        )
    else:
        # If no script tag is found, add one with the import if it's not being removed
        return (
            (file_content, False)
            if remove
            else (f"\n<script setup>\n{import_statement}\n</T>\n{file_content}", True)
        )


def get_packages(root_directory: str) -> Packages:
    """
    Gets the packages from the package.json file
    """
    with open(os.path.join(root_directory, "package.json"), "r") as package_file:
        package_json: Dict = json5.load(package_file)
        return Packages(
            dependencies=package_json.get("dependencies", None),
            devDependencies=package_json.get("devDependencies", None),
        )


def get_ts_configs(root_directory: str, file_name: str) -> Dict[str, Any]:
    """
    Gets the ts configs from the tsconfig.json file
    """
    ts_config_path = Path(root_directory, file_name)
    with open(ts_config_path, "r") as tsconfig_file:
        tsconfig_json: Dict = json5.loads(tsconfig_file.read())
        if "extends" in tsconfig_json:
            extended_path = str(Path(root_directory, tsconfig_json["extends"]))
            extended = get_ts_configs(extended_path, "")
            del tsconfig_json["extends"]
            # Merge two configs, overwriting the second one
            extended.update(tsconfig_json)
            return extended
        else:
            return tsconfig_json


def get_paths_from_tsconfig(root_directory: str) -> Dict[str, List[str]]:
    """
    Gets the paths from the tsconfig.json file
    """
    tsconfig_json = get_ts_configs(root_directory, "tsconfig.json")
    if "paths" in tsconfig_json.get("compilerOptions", None):
        return tsconfig_json["compilerOptions"]["paths"]
    else:
        return {}


def get_available_components(root_directory: str):
    is_nuxt = ".nuxt" in os.listdir(root_directory)

    if is_nuxt:
        nuxt_components = Path(root_directory, ".nuxt/components.d.ts")
        reg = r"export const ([^:]+): [^\n]*"
        if nuxt_components.exists():
            with open(nuxt_components, "r") as nuxt_components_file:
                file_content = nuxt_components_file.read()
                matches = re.findall(reg, file_content)
                if matches:
                    first_lazy_index = matches.index(lambda x: x.startswith("Lazy"))
                    matches = matches[:first_lazy_index]
                    return f"""
                    This is a Nuxt.js project. COMPONENTS ARE AUTOMATICALLY IMPORTED. DO NOT INCLUDE AN IMPORT STATEMENT WHEN USING THESE COMPONENTS! You have the following components globally available for you. DO NOT IMPORT THESE COMPONENTS:
                    ```
                    {','.join(matches)}
                    ```
                    """
        else:
            return None
    return None
