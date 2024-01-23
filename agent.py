
from component_creation import create_tea_component, create_loading_component, create_steep_component
from helpers import FileContext, SteepContext, set_import
from prompt import write_component_prompt
from llama_index.llms import LLM, ChatMessage
from llama_index import VectorStoreIndex
from langchain_community.llms.ollama import Ollama
import os


class TeaAgent():
    """
        The agent has 3 tasks it is able to do (in order of process):
        1. Pour - pour the tea into a component, removes the steeped tea
        2. Steep - steep the tea into a WIP component, this is temporary until the user pours it
        3. Sweeten - sweeten an already made component, this is temporary until the user pours it (Later??)
    """
    def __init__(self, llm: LLM = None, index: VectorStoreIndex =None):
        self.llm = llm
        self.index = index

    def pour(self, pour_path: str, ctx: FileContext):

        pass

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

        llm = Ollama(model="deepseek-coder:6.7b-instruct", temperature=0)
        response = ""
        for chunk in llm.stream(prompt):
            print(chunk, end="", flush=True)
            response += chunk
        # chat_engine = self.index.as_chat_engine()
        # response = chat_engine.stream_chat(prompt)
        # response.print_response_stream()

        # Grab the code from between the backticks
        code = response.split("```")[1].strip("\n")

        # If the first 3 letters are "vue" then we need to remove them (It adds it to type the markdown)
        if code[:3] == "vue":
            code = code[3:]

        # Once we get the response, we want to write it to the file
        with open(ctx.steep_path, "w") as file:
            file.write(code)
