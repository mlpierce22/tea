import chromadb
import os
import re
from pathlib import Path
from llama_index.vector_stores import ChromaVectorStore
from llama_index.indices import VectorStoreIndex
from llama_index.storage import StorageContext
from llama_index import SimpleDirectoryReader
from llama_index import ServiceContext, VectorStoreIndex
from llama_index.embeddings import HuggingFaceEmbedding
from llama_index.llms import Ollama, CustomLLM

def collect_input_files(root, ignore):
    """
        Collect all files in the root directory that we are "allowed" to index
    """
    input_files = []
    files_to_check = list(Path(root).iterdir())
    while len(files_to_check) > 0:
        f = files_to_check.pop()
        if f.name in ignore:
            continue
        
        if f.is_dir():
            files_to_check = files_to_check + list(f.iterdir())
            continue

        input_files.append(str(f))
        
    return input_files

def index_project(root: str, index_path: str, llm: CustomLLM):
    """
        Loop through every folder and file in the root repo and add them to the index
    """

    # Step 2: List of files to ignore during indexing
    ignore_patterns = set(["*.git", '*.jpg', '*.jpeg', '*.png', '*.gif', '*.bmp', '*.tiff', '*.svg'])
    ignore = set(["node_modules", ".git", "bun.lockb", "package-lock.json", "yarn.lock"])
    
    # Read the gitignore file at the root of the codebase and add those files to the ignore list
    gitignore_path = os.path.join(root, ".gitignore")
    if os.path.exists(gitignore_path):
        with open(gitignore_path, "r") as f:
            for line in f.readlines():
                # Skip comments
                if line.startswith("#"):
                    continue

                if "*" in line:
                    ignore_patterns.add(line.strip())
                elif "!" not in line:
                    ignore.add(line.strip())

    # Filter out empty entries
    ignore = {entry for entry in ignore if entry}
    ignore_patterns = {pattern for pattern in ignore_patterns if pattern}

    # Step 3: Read the directory and load the data, excluding the ignored files and images
    documents = SimpleDirectoryReader(input_files=collect_input_files(root, ignore), exclude_hidden=True, exclude=list(ignore_patterns)).load_data()

    index_saved = os.path.exists(index_path)
        
    chroma_client = chromadb.PersistentClient(path=index_path)
    codebase_collection = chroma_client.get_or_create_collection(name="codebase")

    # Make Settings
    vector_store = ChromaVectorStore(chroma_collection=codebase_collection)
    service_context = ServiceContext.from_defaults(embed_model=HuggingFaceEmbedding(), llm=llm)
    storage_context = StorageContext.from_defaults(vector_store=vector_store)

    if index_saved:
        print("Loading index from disk...")
        index = VectorStoreIndex.from_vector_store(
                    vector_store=vector_store,
                    service_context=service_context,
                )
    else:
        print("Creating index...")
        index = VectorStoreIndex.from_documents(
                    documents=documents,
                    service_context=service_context, 
                    storage_context=storage_context
                )

    return index

# if __name__ == "__main__":
#     llm = Ollama(model="codellama:7b-instruct", request_timeout=30)
#     query_engine = index_project(root="/Users/mason/Code/maestro", index_path="./index", llm=llm)
#     response = query_engine.query("path aliases like @, ~, and ~~ used in this repository")
#     print(response)