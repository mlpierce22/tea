import os
import shutil
import time
from typing import Union

from agent import TeaAgent
from helpers import (
    CONFIG_DEFAULTS,
    EnvConfig,
    FileContext,
    SteepContext,
    TeaTag,
    extract_tag,
    get_packages,
    log,
    set_import,
    tea_import_statement,
)
from langchain_community.llms.ollama import Ollama
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.language_models.llms import BaseLLM
from langchain_openai import ChatOpenAI
from watcher import FileWatcher

watcher: FileWatcher = None


class Main:
    def __init__(self, llm: Union[BaseLLM, BaseChatModel], config: EnvConfig):
        if llm:
            self.llm = llm
        else:
            raise Exception("LLM not provided")

        self.tea_agent = TeaAgent(llm=llm)
        self.patterns = config.patterns
        self.root_directory = config.root_directory
        self.ignore_patterns = config.ignore_patterns

    def run(self):
        log.info("Starting...")

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
                    log.info(f"File changed: {watcher.last_modified_file}")

                    self.process_file(
                        watcher.last_modified_file,
                        root_directory=self.root_directory,
                    )
                    time.sleep(1)
                    prev_inc = watcher.last_modified_file_inc
        except KeyboardInterrupt:
            log.warning("Stopping...")
            watcher.stop()
            exit()

    def process_tea_tag(self, tea_tag: TeaTag, ctx: FileContext = None):
        """
        Steeps (WIP version) or Pours (finalizes) <Tea> components.
        """
        extension = ctx.file_path.split(".")[-1]

        steep_path = os.path.join(ctx.path_to_teacup_folder, "Steep." + extension)
        loading_component_path = os.path.join(
            ctx.path_to_teacup_folder, "Heating." + extension
        )
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
            log.info(f"Pouring {pour} component...")
            self.tea_agent.pour(component_name=pour, ctx=steep_ctx)
            self.tea_agent.print_costs()
        else:
            log.info("Steeping new component...")
            self.tea_agent.steep(ctx=steep_ctx)
            self.tea_agent.print_costs()

    def process_file(self, file_path: str, root_directory=None):
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
            log.info(f"<Tea> tag found in {file_path}")
            self.process_tea_tag(tea_tag=tea_tag, ctx=ctx)
            return
        else:
            log.info(f"No <Tea> tag found in {file_path}")
            # Remove the teacup directory and everything inside it
            # TODO: Only remove when no <Tea> tags are found in the repo in general
            log.warning(f"Removing {path_to_teacup_folder}...")
            shutil.rmtree(ctx.path_to_teacup_folder)

            # Remove import from file
            file_content_no_import, _ = set_import(
                ctx.file_content, tea_import_statement, remove=True
            )

            # Write the updated content without the import
            with open(file_path, "w") as file:
                file.write(file_content_no_import)


def get_config_from_environment():
    """
    Returns a config dict from the environment variables.
    """
    config = EnvConfig(
        patterns=os.getenv("PATTERNS", CONFIG_DEFAULTS["PATTERNS"]).split(","),
        root_directory=os.getenv("ROOT_DIRECTORY", CONFIG_DEFAULTS["ROOT_DIRECTORY"]),
        ignore_patterns=os.getenv(
            "IGNORE_PATTERNS", CONFIG_DEFAULTS["IGNORE_PATTERNS"]
        ).split(","),
        model=os.getenv("MODEL", CONFIG_DEFAULTS["MODEL"]),
        temperature=float(os.getenv("TEMPERATURE", CONFIG_DEFAULTS["TEMPERATURE"])),
        base_url="http://" + os.getenv("OLLAMA_HOST", "localhost:11434"),
        openai_key=os.getenv("OPENAI_KEY", None),
        log_level=os.getenv("LOG_LEVEL", CONFIG_DEFAULTS["LOG_LEVEL"]),
    )

    if not config.root_directory:
        raise Exception("ROOT_DIRECTORY must be provided in environment!")

    return config


if __name__ == "__main__":
    if watcher:
        watcher.stop()

    config = get_config_from_environment()
    if config.openai_key:
        model = (
            "gpt-3.5-turbo"
            if config.model == CONFIG_DEFAULTS["MODEL"]
            else config.model
        )
        llm = ChatOpenAI(
            name=model,
            model=model,
            temperature=config.temperature,
            api_key=config.openai_key,
            max_tokens=1000,
        )
    else:
        llm = Ollama(
            name=config.model,
            model=config.model,
            temperature=config.temperature,
            base_url=config.base_url,
        )

    main = Main(llm=llm, config=config)
    main.run()
