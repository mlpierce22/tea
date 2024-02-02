
from pathlib import Path
import shutil
from component_creation import create_tea_component, create_loading_component, create_steep_component
from helpers import FileContext, SteepContext, get_available_components, pour_tag, get_paths_from_tsconfig, get_ts_configs, set_import, log, file_log
from prompt import EXAMPLE_COMPONENT, ComponentLocation, make_component_output_parser, write_component_location_prompt, write_component_prompt, write_double_check_prompt
from langchain_community.llms.ollama import Ollama
from langchain_core.language_models.llms import BaseLLM
from typing import Dict, Iterator, Union
from langchain_core.runnables import RunnableSerializable


import os


class TeaAgent():
    """
        The agent has 2 tasks it is able to do (in order of process):
        1. Steep - steep the tea into a WIP component, this is temporary until the user pours it
        2. Pour - pour the tea into a component, removes the steeped tea
    """
    def __init__(self, llm: BaseLLM = None, should_think: bool = True):
        self.llm = llm
        self.should_think = should_think

    def print_chunk(self, chunk: str, end: str = ""):
        if file_log:
            print(chunk, end=end, flush=True, file=file_log)
        else:
            print(chunk, end=end, flush=True)

    def _process_response(self, chain: RunnableSerializable, args: Union[Dict, str]) -> str:
        response = ""
        for chunk in chain.stream(args):
            self.print_chunk(chunk)
            response += chunk

        self.print_chunk("\n\n\n-------\n\n\n")
        log.info(response)
        return response

    def pour(self, component_name: str, ctx: SteepContext):
        log.info("Pouring tea...")
        # Get the root files
        component_location_parser = make_component_output_parser()
        component_location_prompt = write_component_location_prompt(component_location_parser)
        paths = get_paths_from_tsconfig(ctx.root_directory)
        log.info("The prompt!")
        log.info(component_location_prompt.format(**{
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

            log.info("The response!")
            log.info(full_response)
            try:
                output_dict: dict = component_location_parser.parse(full_response)
                # Defensively protect in case model outputs wrong format
                if output_dict.get("properties", None) is not None:
                    output_dict = output_dict["properties"]
                log.info("The output dict!")
                log.info(output_dict)
                return output_dict
            except Exception as e:
                if retries > 0:
                    return handle_response(retries - 1)
                else:
                    raise e

        output_dict: dict = handle_response()
        log.info("The output dict!")
        log.info(output_dict)
        
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
        # thought_process = self.requirements_thinking(ctx, available_components=available_components)

        prompt = write_component_prompt(
            user_query=ctx.tea_tag.children,
            steep_component_content=ctx.steep_content,
            parent_file_content=ctx.file_content,
            available_components=available_components,
            packages=ctx.packages.model_dump(exclude_none=True),
            source_file=ctx.steep_path,
        )
        log.info("The prompt!")
        log.info(prompt)

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


        # Now the component is heating, this is where we ask the llm for code
        log.info("Creating component. This could take a while...")

        full_response = self._process_response(self.llm, prompt)

        # Make model come up with requirements
        # thought_process = self.requirements_thinking(ctx, available_components=available_components)

        # code = self.generate_code(ctx, thought_process)
        # Grab the code from between the backticks
        code = full_response.split("```")[1].strip("\n")

        # If the first 3 letters are "vue" then we need to remove them (It adds it to type the markdown)
        if code[:3] == "vue":
            code = code[4:] # Also remove newline

        # if self.should_think:
        #     check = self.double_check(ctx, generated_component_code=code, available_components=available_components)
        #     if check == True:
        #         log.info("The component was approved!")
        #     else:
        #         code = check

        # Once we get the response, we want to write it to the file
        with open(ctx.steep_path, "w") as file:
            file.write(code)

    def double_check(self, ctx: SteepContext, generated_component_code: str, available_components: str = None):
        """
            Double checks the steeped component to make sure it adheres to the user's requirements
        """
        approved_string = "Approved"
        double_check_prompt = write_double_check_prompt(generated_component_code=generated_component_code, user_query=ctx.tea_tag.children, available_components=available_components, approved_string=approved_string)

        log.info("The double check prompt!")
        log.info(double_check_prompt)

        full_response = self._process_response(self.llm, double_check_prompt)

        # Grab the code from between the backticks
        code = full_response.split("```")[1].strip("\n")

        # If the first 3 letters are "vue" then we need to remove them (It adds it to type the markdown)
        if code[:3] == "vue":
            code = code[4:] # Also remove newline
        
        if code == approved_string:
            return True
        else:
            return code

    def requirements_thinking(self, ctx: SteepContext, available_components: str = None):
        """
            Takes a user's query and expands it to think about the requirements and constraints
        """

#         prompt = f"""
# You are a pragmatic principal open-source frontend engineer specializing in the Vue ecosystem. Your task is to take the user's query and expand it to think about the requirements, constraints, and make assumptions.

# Below is the parent component. it uses the <Tea> component to render the component that you make a plan to create. Copy the style and syntax decisions but DO NOT COPY THIS COMPONENT VERBATIM.
# ```
# {ctx.file_content}
# ```

# Some of this component has potentially already been written. Here is the starter code:
# ```
# {ctx.steep_content}
# ```

# You have access to the following packages:
# ```
# {ctx.packages}
# ```

# {available_components if available_components else ''}

# The user's query is:
# ```
# {ctx.tea_tag.children}
# ```

# An engineer will implement the outline you generate in a Vue file. The component should be as simple and easy to understand as possible, while still fully expressing the functionality required. It is not your job to write code! You should choose reasonable defaults and make reasonable assumptions where necessary. You should try to use the packages and components provided to you, wherever possible.

# For example, if the user query is `Generate a 3 by 3 grid of images`, your output might be:
# ```markdown
# # Overall Instructions and assumptions:
# - The user wants a 3 by 3 grid of images.
# - The user likely wants the images to be responsive, square, evenly spaced, and fill the screen.
# - The NuxtImg and UContainer components are available as a component and therefore should be used. No import statement is required because this is a Nuxt component.
# - Based on the parent component, it looks like Tailwind is used in this repository, that should be relied on for styling.

# # Script section:
# - The parent uses the script setup syntax, so the component should use the script setup syntax.
# - The image urls is not passed in as a prop, and therefore should be represented as an array of strings inside this component. There should be 9 image urls in the array.

# # Template
# - Use TailwindCSS to create a 3 column grid.
# - Loop through the array of image urls in a v-for loop.

# # Style:
# - Relying on tailwind classes for now since they are present in this repository
# ```

# Now it's your turn. The plan for this component is as follows:
#         """
        prompt = f"""
You are a pragmatic principal open-source frontend engineer specializing in the Vue ecosystem. Your task is to take the user's query and expand it to think about the requirements, constraints, and make assumptions.

User's Query:
```
{ctx.tea_tag.children}
```
"""
        log.info("The requirements thinking prompt!")
        log.info(prompt)
        log.info("\n=====\n")
        return self._process_response(self.llm, prompt)

    def generate_code(self, ctx: SteepContext, thought_process: str):
        """
            Generates the code for the component
        """
        prompt = f"""
You are a pragmatic principal open-source frontend engineer specializing in the Vue ecosystem.
You are about to get detailed instructions for code to write to generate {ctx.steep_path}.

# Instructions:
===
{thought_process}
===

# Rules:
===
- There should be NO MORE THAN 1 <script> tag, NO MORE THAN 1 <template> tag, and NO MORE THAN 1 <style> tag in the output file.
- DO NOT add any new libraries or assume any classes or components that you don't see, other than those clearly used by the component. Put everything into this single file: styles, types, etc.
- The code should be complete and fully functional. NO PLACEHOLDERS. DO NOT ADD ANY COMMENTS. NO OMISSIONS. Any omission or deviation will completely break the system.
- DO NOT OMIT ANYTHING FOR BREVITY
- DO NOT OMIT ANYTHING FOR BREVITY
- DO NOT OMIT ANYTHING FOR BREVITY
- Output a whole new Vue file within triple backticks (```) AND NOTHING ELSE.
- The ouputted code should be complete and fully functional. The code you output will be written directly to a file, as-is.
- The code must make sense and be easy to understand. It should be as simple as possible, but no simpler.
===

Output whole new component file WITHIN triple backticks (```) AND NOTHING ELSE. It will be saved as is to the component file and should work out of the box.
        """
        log.info("The generate code prompt!")
        log.info(prompt)
        log.info("\n=====\n")
        return self._process_response(self.llm, prompt)