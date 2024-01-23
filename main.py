import re
import os
import sys
import time
# from llama_index.llms import Ollama, LLM

from pydantic import BaseModel
from agent import TeaAgent
from helpers import FileContext, Packages, SteepContext, TeaTag, extract_tag
from watcher import FileWatcher
import shutil
import json
from rag import index_project
from langchain_community.llms.ollama import Ollama
from langchain_core.language_models.llms import BaseLLM

from typing import Any, Dict, Optional
watcher: FileWatcher = None

class Main:
    def __init__(self, index=None, llm: BaseLLM = None):
        # TODO: Take in a config file
        self.tea_agent = TeaAgent(index=index, llm=llm)
        self.config = {
            "patterns": ["*.vue"],
            "root_directory": "/Users/mason/Code/maestro",
            "ignore_patterns": ["Tea.vue", "Steep.vue", "Brewing.vue"],
        }

        # if index:
        #     self.index = index
        # else:
        #     raise Exception("Index not provided")
        
        if llm:
            self.llm = llm
        else:
            raise Exception("LLM not provided")
    
    def run(self):
        print("Starting...")

        watcher = FileWatcher(
            root_directory=self.config["root_directory"],
            watch_patterns=self.config["patterns"],
            ignore_patterns=self.config["ignore_patterns"],
        )
        watcher.start()
        prev_inc = 0

        try:
            while True:
                time.sleep(1)
                if prev_inc != watcher.last_modified_file_inc:
                    print(f"File changed: {watcher.last_modified_file}")

                    self.process_file(
                        watcher.last_modified_file,
                        root_directory=self.config["root_directory"],
                    )
                    time.sleep(1)
                    prev_inc = watcher.last_modified_file_inc
        except KeyboardInterrupt:
            print("Stopping...")
            watcher.stop()
            exit()

    def process_tea_tag(self, tea_tag: TeaTag, ctx: FileContext = None):
        """
        Steeps (WIP version) or Pours (finalizes) <Tea> components.
        """
        tea_import_statement = f"import Tea from './cup/Tea.vue'"
        extension = ctx.file_path.split(".")[-1]
        
        steep_path = os.path.join(ctx.path_to_teacup_folder, "Steep." + extension)
        loading_component_path = os.path.join(ctx.path_to_teacup_folder, "Brewing." + extension)
        steep_content = ""

        if os.path.exists(steep_path):
            with open(steep_path, "r") as steep_file:
                steep_content = steep_file.read()

        steep_ctx = SteepContext(
            **ctx.model_dump(),
            loading_component_path=loading_component_path,
            steep_path=steep_path,
            steep_content=steep_content,
            tea_import_statement=tea_import_statement,
            tea_tag=tea_tag,
        )
        pour = tea_tag.model_dump().get("props", {}).get("pour", None)

        if pour:
            print(f"Pouring component to {pour}...")
            self.tea_agent.pour(pour_path=pour, ctx=steep_ctx)
            # TODO
            # mount_coffee_files("./mount", working_dir, False, cleanup=[steep_path])
            # pour_component(pour_path=pour, ctx=steep_ctx)
        else:
            print("Steeping new component...")
            self.tea_agent.steep(ctx=steep_ctx)

    def process_file(self, file_path, root_directory=None):
        """
        Detects and processes <Tea> and <Component tea="..."> tags.
        """
        with open(file_path, "r") as file:
            file_content = file.read()

        path_to_file_folder = "/".join(file_path.split("/")[:-1])
        path_to_teacup_folder = os.path.join(path_to_file_folder, "cup")
        if not os.path.exists(path_to_teacup_folder):
            os.mkdir(path_to_teacup_folder)

        ctx = FileContext(
            file_path=file_path,
            file_content=file_content,
            root_directory=root_directory,
            path_to_teacup_folder=path_to_teacup_folder,
            packages=self.get_packages(root_directory),
        )

        # Extract and process <Tea> tag
        tea_tag = extract_tag(file_content, tag="Tea")
        if tea_tag:
            print(f"<Tea> tag found in {file_path}")
            self.process_tea_tag(tea_tag=tea_tag, ctx=ctx)

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

    def get_packages(self, root_directory: str) -> Packages:
        """
        Gets the packages from the package.json file
        """
        with open(os.path.join(root_directory, "package.json"), "r") as package_file:
            package_json: Dict = json.load(package_file)
            return Packages(
                dependencies=package_json.get("dependencies", None),
                devDependencies=package_json.get("devDependencies", None),
            )



if __name__ == "__main__":
    if watcher:
        watcher.stop()
    print("Indexing project...")

    # Check for argument passed when running this file for the model name
    model_name = sys.argv[1] if len(sys.argv) > 1 else "deepseek-coder:6.7b-instruct"

    print(f"Using model: {model_name}")
    llm = Ollama(model=model_name, temperature=0)
    # llm = Ollama(model="codellama:7b-instruct", request_timeout=30, temperature=0)
    # index = index_project("/Users/mason/Code/maestro", "./index", llm=llm)

    main = Main(llm=llm)
    main.run()