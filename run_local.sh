#!/bin/bash

if [[ -z ${MODEL} ]]; then
	MODEL="deepseek-coder:6.7b-instruct"
	echo "Using \"${MODEL}\" by default, you can specify a model with:"
	echo "bash $0 <ollama_model>"
	echo "See available models at https://ollama.ai/library"
	export MODEL
fi

# Define your tasks here. Each task should be a function
run_watcher() {
	echo "Running watcher"
	python app/main.py
}

run_ollama() {
	echo "Running ollama with model ${MODEL}"
	ollama run "${MODEL}"
}

# Store the names of the task functions in an array
tasks=(run_watcher)
if [[ -z ${OPENAI_KEY} ]]; then
	# Pull the model first if OPENAI_KEY is not set
	ollama pull "${MODEL}"
	tasks+=(run_ollama)
else
	echo "Skipping ollama run due to OPENAI_KEY being set"
fi

# Export the functions
for task in "${tasks[@]}"; do
	export -f "${task?}"
done

# Run the tasks in parallel with --line-buffer for immediate output and --halt now,fail=1 to stop immediately on failure
parallel --line-buffer --halt now,fail=1 ::: "${tasks[@]}"
