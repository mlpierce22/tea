
from typing import List

from pydantic import BaseModel, Field
from helpers import Packages
from langchain.prompts import PromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.pydantic_v1 import BaseModel, Field

class ComponentLocation(BaseModel):
    logical_path: str = Field(description="The full logical path to the component file. e.g. /full/path/to/component/MyComponent.vue")
    import_statement_from_root: str = Field(description="The import statement from the root of the project. e.g. ~/components/MyComponent.vue")

def write_component_prompt(user_query: str, steep_component_content: str, parent_file_content: str, packages: Packages, source_file: str, available_components: str = None, example_content: str = None):
    return f"""
You are a pragmatic principal open-source frontend engineer specializing in the Vue ecosystem.
You are about to get instructions for code to write.
This code must be as simple and easy to understand, while still fully expressing the functionality required.
Please note that the code should be complete and fully functional. NO PLACEHOLDERS. NO OMISSIONS.
DO NOT OMIT ANYTHING FOR BREVITY as the code you output will be written directly to a file, as-is.
YOUR TASK is to create a Vue component file according to the user query:
```
{user_query}
```
{available_components if available_components else ''}

This is current content of component file:
```
{steep_component_content}
```

This is the parent component file: it uses the <Tea> component to render the component that you should create. Copy the style and syntax decisions but DO NOT COPY THIS COMPONENT VERBATIM. DO NOT COPY THE BELOW COMPONENT. FOLLOW THE INSTRUCTIONS FROM THE USER TO CREATE A NEW COMPONENT.
```
{parent_file_content}
```
{'Follow similar structure and patterns of this example component:```' + {example_content} + '```' if example_content else ''}

You have access to the following packages:
```
{packages}
```

Output whole new file for {source_file} WITHIN ``` AND NOTHING ELSE. It will be saved as is to the component file {source_file} and should work out of the box.

There should be NO MORE THAN 1 <script> tag, NO MORE THAN 1 <template> tag, and NO MORE THAN 1 <style> tag in the output file.

DO NOT add any new libraries or assume any classes that you don't see, other than those clearly used by the parent or child component or are present as available packages above. Put everything into this single file: styles, types, etc.
Finally, please note that the code should be complete and fully functional. NO PLACEHOLDERS.
Do not add any comments.
The code you output will be written directly to a file, as-is. Any omission or deviation will completely break the system.
DO NOT OMIT ANYTHING FOR BREVITY.
DO NOT OMIT ANYTHING FOR BREVITY.
DO NOT OMIT ANYTHING FOR BREVITY.
DO NOT OMIT ANYTHING FOR BREVITY.
DO NOT OMIT ANYTHING FOR BREVITY.
"""

def make_component_output_parser() -> JsonOutputParser:
    """
        Builds the output parser for use in the chain
    """

    return JsonOutputParser(pydantic_object=ComponentLocation)


def write_component_location_prompt(parser: JsonOutputParser):
    """
        Constructs a prompt template for using when determining where to put the component file
    """

    template = """
Your job is to create a new component file called {component_name}.vue in the logical location within the project.
Here is the path to the parent_component:
```
{parent_component_path}
```

Here is the root path to the project:
```
{root_path}
```

Here are the path aliases for the project:
```
{path_aliases}
```

Here are the files located at the root of the project:
```
{root_files}
```

Determine the BEST, MOST LOGICAL PATH for the new component file. Choose a component directory if it exists, otherwise put it close to the parent component so it is easy to find. DO NOT WRITE CODE. KEEP YOUR RESPONSE SHORT AND COMPLY WITH THE FORMAT BELOW.

{format_instructions}
    """
    
    return PromptTemplate(
        template=template,
        input_variables=["component_name", "parent_component_path", "path_aliases", "root_files", "root_path"],
        partial_variables={
            "format_instructions": parser.get_format_instructions()
    })