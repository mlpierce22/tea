import re
import os
import time

from pydantic import BaseModel
from watcher import FileWatcher
import shutil
import json

from typing import Optional
watcher: FileWatcher = None

# TODO: Take in a config file
config = {
    "patterns": ["*.vue"],
    "root_directory": "/Users/mason/Code/maestro",
}

class FileContext(BaseModel):
    file_path: str
    file_content: str
    root_directory: str


class BrewContext(FileContext):
    brew_path: str
    brew_content: str
    coffee_import_statement: str
    coffee_tag: dict

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
        return {
            "match": match,
            "tag": tag_name,
            "props": props,
            "children": content.strip() if content else "",
            "attributes": attributes,
        }

    return None

def process_file(file_path, mount_dir=None, root_directory=None, example=None):
    """
    Detects and processes <Tea> and <Component tea="..."> tags.
    """
    with open(file_path, "r") as file:
        file_content = file.read()

    ctx = FileContext(
        file_path=file_path,
        file_content=file_content,
        root_directory=root_directory,
        working_dir=os.path.join(os.path.dirname(file_path), root_directory),
    )

    print(ctx)
    # Extract and process <Tea> tag
    tea_tag = extract_tag(file_content, tag="Tea")
    if tea_tag:
        print(f"<Tea> tag found in {file_path}")
        print("TODO")
        # process_tea_tag(tea_tag=tea_tag, ctx=ctx)

    # Extract and process <Component tea="..."> caffeniated components
    caffeinated_component = extract_tag(
        file_content, attribute="tea=[\"'][^\"']+[\"']"
    )
    if caffeinated_component:
        print(f"Caffeinated component found in {file_path}")
        print("TODO")
        # proccess_caffeinated_component(
        #     caffeinated_component=caffeinated_component, ctx=ctx
        # )
        return

if __name__ == "__main__":
    if watcher:
        watcher.stop()

    print("Starting...")

    watcher = FileWatcher(
        root_directory=config["root_directory"],
        watch_patterns=config["patterns"],
        ignore_patterns=["Tea.jsx", "Tea.d.ts", "Brew.*"],
    )
    watcher.start()
    prev_inc = 0

    try:
        while True:
            time.sleep(1)
            if prev_inc != watcher.last_modified_file_inc:
                print(f"File changed: {watcher.last_modified_file}")

                process_file(
                    watcher.last_modified_file,
                    root_directory=config["root_directory"],
                )
                prev_inc = watcher.last_modified_file_inc
    except KeyboardInterrupt:
        print("Stopping...")
        watcher.stop()
        exit()