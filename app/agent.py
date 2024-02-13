import os
import shutil
from pathlib import Path
from typing import Dict, Union

from component_creation import (
    create_loading_component,
    create_steep_component,
    create_tea_component,
)
from helpers import (
    SteepContext,
    file_log,
    get_available_components,
    get_paths_from_tsconfig,
    log,
    pour_tag,
    set_import,
)
from langchain_core.language_models.llms import BaseLLM
from langchain_core.runnables import RunnableSerializable
from prompt import (
    IMPORT_STATEMENT_EXAMPLES,
    LOGICAL_PATH_EXAMPLES,
    make_component_output_parser,
    write_component_location_prompt,
    write_component_prompt,
)


class TeaAgent:
    """
    The agent has 2 tasks it is able to do (in order of process):
    1. Steep - steep the tea into a WIP component, this is temporary until the user pours it
    2. Pour - pour the tea into a component, removes the steeped tea
    """

    def __init__(self, llm: BaseLLM = None):
        self.llm = llm

    def print_chunk(self, chunk: str, end: str = ""):
        if file_log:
            print(chunk, end=end, flush=True, file=file_log)
        else:
            print(chunk, end=end, flush=True)

    def _process_response(
        self, chain: RunnableSerializable, args: Union[Dict, str]
    ) -> str:
        response = ""
        for chunk in chain.stream(args):
            self.print_chunk(chunk)
            response += chunk

        self.print_chunk("\n\n\n-------\n\n\n")
        log.debug(response)
        return response

    def pour(self, component_name: str, ctx: SteepContext):
        log.info("Pouring tea...")
        # Get the root files
        component_location_parser = make_component_output_parser()
        component_location_prompt = write_component_location_prompt(
            component_location_parser
        )
        paths = get_paths_from_tsconfig(ctx.root_directory)
        log.debug("Using the following prompt:")
        log.debug(
            component_location_prompt.format(
                **{
                    "component_name": component_name,
                    "path_aliases": paths,
                    "root_files": os.listdir(ctx.root_directory),
                    "parent_component_path": ctx.file_path,
                    "root_path": ctx.root_directory,
                    "logical_path_examples": LOGICAL_PATH_EXAMPLES,
                    "import_statement_examples": IMPORT_STATEMENT_EXAMPLES,
                }
            )
        )
        chain = component_location_prompt | self.llm

        def handle_response(retries=2):
            """
            Retry in case the model tries to do something stupid
            """
            full_response = self._process_response(
                chain,
                {
                    "component_name": component_name,
                    "path_aliases": paths,
                    "root_files": os.listdir(ctx.root_directory),
                    "parent_component_path": ctx.file_path,
                    "root_path": ctx.root_directory,
                    "logical_path_examples": LOGICAL_PATH_EXAMPLES,
                    "import_statement_examples": IMPORT_STATEMENT_EXAMPLES,
                },
            )
            try:
                output_dict: dict = component_location_parser.parse(full_response)
                # Defensively protect in case model outputs wrong format
                if output_dict.get("properties", None) is not None:
                    output_dict = output_dict["properties"]
                return output_dict
            except Exception as e:
                if retries > 0:
                    return handle_response(retries - 1)
                else:
                    raise e

        output_dict: dict = handle_response()
        log.debug("Output from location path prompt:")
        log.debug(output_dict)

        # Now that we have the paths, we just have to do some writing and cleanup
        # First, make the component at the path (create directories if need be)
        logical_path = str(output_dict["logical_path"])
        import_statement = f"import {component_name} from \"{output_dict['import_statement_from_root']}\""

        # Add .vue onto the end if the model messed up
        if logical_path[-4:] != ".vue":
            logical_path += '.vue"'

        # Add .vue onto the end if the model messed up
        if import_statement[-5:] != '.vue"':
            import_statement += '.vue"'

        new_component_path = Path(logical_path)
        new_component_path.parent.mkdir(parents=True, exist_ok=True)
        steeped_content = ""
        # Read from the steep file
        with open(ctx.steep_path, "r") as file:
            steeped_content = file.read()

        # Write new component
        with new_component_path.open("w") as file:
            file.write(steeped_content)

        # Update the import statement and component in the parent component
        file_content_no_import, _ = set_import(
            ctx.file_content, ctx.tea_import_statement, remove=True
        )
        file_content_with_import, _ = set_import(
            file_content_no_import, import_statement
        )
        final_parent_content = pour_tag(file_content_with_import, component_name)

        # Finally, write the updated component to the parent
        with open(ctx.file_path, "w") as file:
            file.write(final_parent_content)

        # Remove the teacup directory and everything inside it
        shutil.rmtree(ctx.path_to_teacup_folder)

    def steep(self, ctx: SteepContext):
        """
        Writes a temporary component and adds an import to the top of the saved file
        """

        loading_component = create_loading_component()
        steep_component = create_steep_component()
        tea_component = create_tea_component()
        available_components = get_available_components(ctx.root_directory)

        prompt = write_component_prompt(
            user_query=ctx.tea_tag.children,
            steep_component_content=ctx.steep_content,
            parent_file_content=ctx.file_content,
            available_components=available_components,
            packages=ctx.packages.model_dump(exclude_none=True),
            source_file=ctx.steep_path,
        )
        log.debug("Steeping with the following prompt:")
        log.debug(prompt)

        # Add the import to the top of the file
        modified = False
        file_content_with_tea_import, modified = set_import(
            ctx.file_content, ctx.tea_import_statement
        )
        # Write the loading component and container
        with open(ctx.loading_component_path, "w") as file:
            file.write(loading_component)

        with open(ctx.steep_path, "w") as file:
            file.write(steep_component)

        with open(os.path.join(ctx.path_to_teacup_folder, "Tea.vue"), "w") as file:
            file.write(tea_component)

        # Then write to file_content if modified
        if modified:
            with open(ctx.file_path, "w") as file:
                file.write(file_content_with_tea_import)

        # Now the component is heating, this is where we ask the llm for code
        log.info("Creating component. This could take a while...")

        full_response = self._process_response(self.llm, prompt)

        try:
            # Grab the code from between the backticks
            code = full_response.split("```")[1].strip("\n")
        except Exception as e:
            log.error("Failed to get code from response. Please try again")
            log.error(e)
            return

        # If the first 3 letters are "vue" then we need to remove them (It adds it to type the markdown)
        if code[:3] == "vue":
            code = code[4:]  # Also remove newline

        # Once we get the response, we want to write it to the file
        with open(ctx.steep_path, "w") as file:
            file.write(code)
