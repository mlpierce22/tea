import os
import sys
import time
from pathlib import Path
from agent import TeaAgent
from helpers import FileContext, Packages, SteepContext, TeaTag, extract_tag, get_packages
from watcher import FileWatcher
from langchain_community.llms.ollama import Ollama
from langchain_core.language_models.llms import BaseLLM

watcher: FileWatcher = None

class Main:
    __default_config = {
        "patterns": ["*.vue"],
        "root_directory": "/Users/mason/Code/maestro",
        "ignore_patterns": ["Tea.vue", "Steep.vue", "Brewing.vue"],
    }

    def __init__(self, llm: BaseLLM = None, config: dict = None):
        if not config:
            config = self.__default_config

        if llm:
            self.llm = llm
        else:
            raise Exception("LLM not provided")

        self.tea_agent = TeaAgent(llm=llm)
        self.patterns = config["patterns"] or ["*.vue"]
        self.root_directory = config["root_directory"]
        self.ignore_patterns = list(set(["Tea.vue", "Steep.vue", "Brewing.vue"] + (config["ignore_patterns"] or [])))
    
    def run(self):
        print("Starting...")

        watcher = FileWatcher(
            root_directory=self.root_directory,
            watch_patterns=self.patterns,
            ignore_patterns=self.ignore_patterns,
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
                        root_directory=self.root_directory,
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
            print(f"Pouring {pour} component...")
            self.tea_agent.pour(component_name=pour, ctx=steep_ctx)
        else:
            print("Steeping new component...")
            self.tea_agent.steep(ctx=steep_ctx)

    def process_file(self, file_path, root_directory=None):
        """
        Detects and processes <Tea> tags.
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
            packages=get_packages(root_directory),
        )

        # Extract and process <Tea> tag
        tea_tag = extract_tag(file_content, tag="Tea")
        if tea_tag:
            print(f"<Tea> tag found in {file_path}")
            self.process_tea_tag(tea_tag=tea_tag, ctx=ctx)
            return

def get_config_from_environment():
    """
    Returns a config dict from the environment variables.
    """
    CONFIG_DEFAULTS = {
        "MODEL": "deepseek-coder:6.7b-instruct",
        "ROOT_DIRECTORY": os.getcwd(),
        "TEMPERATURE": "0.5",
        "PATTERNS": "*.vue",
        "IGNORE_PATTERNS": "Tea.vue,Steep.vue,Brewing.vue",
    }
    config = {
        "patterns": os.getenv("PATTERNS", CONFIG_DEFAULTS["PATTERNS"]).split(","),
        "root_directory": os.getenv("ROOT_DIRECTORY", CONFIG_DEFAULTS["ROOT_DIRECTORY"]),
        "ignore_patterns": os.getenv("IGNORE_PATTERNS", CONFIG_DEFAULTS["IGNORE_PATTERNS"]).split(","),
        "model": os.getenv("MODEL", CONFIG_DEFAULTS["MODEL"]),
        "temperature": float(os.getenv("TEMPERATURE", CONFIG_DEFAULTS["TEMPERATURE"])),
    }
    return config

if __name__ == "__main__":
    if watcher:
        watcher.stop()

    config = get_config_from_environment()

    model_name = config.get('model')

    print(f"Using model: {model_name}")
    llm = Ollama(model=model_name, temperature=config.get('temperature'))

    main = Main(llm=llm, config=config)
    main.run()