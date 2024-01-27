
from pathlib import Path
import shutil
from component_creation import create_tea_component, create_loading_component, create_steep_component
from helpers import FileContext, SteepContext, pour_tag, get_paths_from_tsconfig, get_ts_configs, set_import
from prompt import ComponentLocation, make_component_output_parser, write_component_location_prompt, write_component_prompt
from llama_index import VectorStoreIndex
from langchain_community.llms.ollama import Ollama
from langchain_core.language_models.llms import BaseLLM
from typing import Dict, Iterator, Union
from langchain_core.runnables import RunnableSerializable

import os


class TeaAgent():
    """
        The agent has 3 tasks it is able to do (in order of process):
        1. Pour - pour the tea into a component, removes the steeped tea
        2. Steep - steep the tea into a WIP component, this is temporary until the user pours it
        3. Sweeten - sweeten an already made component, this is temporary until the user pours it (Later??)
    """
    def __init__(self, llm: BaseLLM = None, index: VectorStoreIndex =None):
        self.llm = llm
        self.index = index

    def _process_response(self, chain: RunnableSerializable, args: Union[Dict, str]) -> str:
        response = ""
        for chunk in chain.stream(args):
            print(chunk, end="", flush=True)
            response += chunk

        return response

    def pour(self, component_name: str, ctx: SteepContext):
        print("Pouring tea...")
        # Get the root files
        # component_name=component_name, ts_configs=get_ts_configs(ctx.root_directory, "tsconfig.json"), root_files=os.listdir(ctx.root_directory), parent_component_path=ctx.file_path
        component_location_parser = make_component_output_parser()
        component_location_prompt = write_component_location_prompt(component_location_parser)
        paths = get_paths_from_tsconfig(ctx.root_directory)
        print("The prompt!")
        print(component_location_prompt.format(**{
            "component_name": component_name, 
            "path_aliases": paths, 
            "root_files": os.listdir(ctx.root_directory), 
            "parent_component_path": ctx.file_path,
            "root_path": ctx.root_directory,
        }
        ))
        chain = component_location_prompt | self.llm

        def handle_response(retries=2):
            """
                Retry in case the model tries to do something stupid
            """
            full_response = self._process_response(chain, {
                "component_name": component_name, 
                "path_aliases": paths, 
                "root_files": os.listdir(ctx.root_directory), 
                "parent_component_path": ctx.file_path,
                "root_path": ctx.root_directory,
            })

            print("The response!")
            print(full_response)
            try:
                output_dict: dict = component_location_parser.parse(full_response)
                # Defensively protect in case model outputs wrong format
                if output_dict.get("properties", None) is not None:
                    output_dict = output_dict["properties"]
                print("The output dict!")
                print(output_dict)
                return output_dict
            except Exception as e:
                if retries > 0:
                    return handle_response(retries - 1)
                else:
                    raise e

        output_dict: dict = handle_response()
        print("The output dict!")
        print(output_dict)
        
        # Now that we have the paths, we just have to do some writing and cleanup
        # First, make the component at the path (create directories if need be)
        logical_path = str(output_dict["logical_path"])
        import_statement = f"import {component_name} from \"{output_dict['import_statement_from_root']}\""
        
        new_component_path = Path(logical_path)
        new_component_path.parent.mkdir(parents=True, exist_ok=True)
        steeped_content = ""
        # Read from the steep file
        with open(ctx.steep_path, "r") as file:
            steeped_content = file.read()

        # Write new component
        with new_component_path.open('w') as file:
            file.write(steeped_content)

        # Update the import statement and component in the parent component
        file_content_no_import, _ = set_import(ctx.file_content, ctx.tea_import_statement, remove=True)
        file_content_with_import, _ = set_import(file_content_no_import, import_statement)
        final_parent_content = pour_tag(file_content_with_import, component_name)

        # Finally, write the updated component to the parent
        with open(ctx.file_path, "w") as file:
            file.write(final_parent_content)

        # Then, remove the entire cup directory
        # Remove the teacup directory and everything inside it
        shutil.rmtree(ctx.path_to_teacup_folder)

    def steep(self, ctx: SteepContext):
        """
            Writes a temporary component and adds an import to the top of the saved file
        """
        loading_component = create_loading_component()
        steep_component = create_steep_component()
        tea_component = create_tea_component()

        prompt = write_component_prompt(
            user_query=ctx.tea_tag.children,
            steep_component_content=ctx.steep_content,
            parent_file_content=ctx.file_content,
            packages=ctx.packages.model_dump(exclude_none=True),
            source_file=ctx.steep_path,
        )
        print("The prompt!")
        print(prompt)

        # Add the import to the top of the file
        modified = False
        file_content_with_tea_import, modified = set_import(ctx.file_content, ctx.tea_import_statement)
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


        # Now the component is brewing, this is where we ask the llm for code
        print("Creating component... This could take a while.")

        full_response = self._process_response(self.llm, prompt)
        # chat_engine = self.index.as_chat_engine()
        # response = chat_engine.stream_chat(prompt)
        # response.print_response_stream()

        # Grab the code from between the backticks
        code = full_response.split("```")[1].strip("\n")

        # If the first 3 letters are "vue" then we need to remove them (It adds it to type the markdown)
        if code[:3] == "vue":
            code = code[4:] # Also remove newline

        # Once we get the response, we want to write it to the file
        with open(ctx.steep_path, "w") as file:
            file.write(code)
