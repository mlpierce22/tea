#!/bin/bash

# Check if exactly one argument is provided
USE_MODEL="deepseek-coder:6.7b-instruct"
if [ "$#" -ne 1 ]; then
    echo "Using \"$USE_MODEL\" by default, you can specify a model with:"
    echo "bash $0 <ollama_model>"
    echo "See available models at https://ollama.ai/library"
else
    USE_MODEL=$1
fi

export USE_MODEL

python main.py $USE_MODEL

# # Define your tasks here. Each task should be a function
# run_watcher() {
#     echo "Running watcher with model $USE_MODEL"
#     python main.py $USE_MODEL
# }

# run_ollama() {
#     # echo "Running ollama with model $USE_MODEL"
#     # ollama run $USE_MODEL
# }

# # Store the names of the task functions in an array
# tasks=(run_watcher run_ollama) # Add more task names to this array as needed

# # Export the functions
# for task in "${tasks[@]}"; do
#     export -f "$task"
# done

# Run the tasks in parallel with --line-buffer for immediate output and --halt now,fail=1 to stop immediately on failure
# parallel --line-buffer --results logfiles --halt now,fail=1 ::: "${tasks[@]}"