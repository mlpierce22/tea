#!/bin/bash

# Check if exactly one argument is provided
if [ "$#" -ne 1 ]; then
    echo "Usage: $0 <ollama_model>"
    echo "See available models at https://ollama.ai/library"
    exit 1
fi

# Define your tasks here. Each task should be a function
run_watcher() {
    python main.py $1
}

run_ollama() {
    ollama run "$1"  
}

# Pull the requested model before starting
ollama pull "$1"

# Store the names of the task functions in an array
tasks=(run_watcher run_ollama) # Add more task names to this array as needed

# Export the functions
for task in "${tasks[@]}"; do
    export -f "$task"
done

# Run the tasks in parallel with --line-buffer for immediate output and --halt now,fail=1 to stop immediately on failure
parallel --line-buffer --halt now,fail=1 ::: "${tasks[@]}"

