
from helpers import Packages


def write_component_prompt(user_query: str, steep_component_content: str, parent_file_content: str, packages: Packages, source_file: str, example_content: str = None):
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