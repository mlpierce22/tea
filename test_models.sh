#! /bin/bash

rm -rf tests
mkdir -p tests
string_list=(
    "codellama:7b-instruct-q4_0"
    "codellama:7b-instruct"
    "codellama:13b-instruct-q4_0"
    "deepseek-coder:6.7b-instruct-q4_0"
    "deepseek-coder:6.7b"
    "deepseek-coder:6.7b-instruct"
    "mistral:v0.2"
)
if [ ! -f prompt.txt ]; then
    echo "Error: prompt.txt does not exist."
    exit 1
fi

count=0
total=${#string_list[@]}
overall_start=$(date +%s)
trap 'echo "Process interrupted by user. Exiting..."; exit' INT
for string_name in "${string_list[@]}"; do
    # Pull the model
    ollama pull "$string_name"

    echo "=====Testing $string_name====="
    avg_time=0
    # Run the model 5 times
    for i in {1..5}; do
        echo "=====Test $i=====" >> "tests/$string_name.md"
        # Record start time
        start_time=$(date +%s)
        gtimeout 45 ollama run "$string_name" "$(cat prompt.txt)" >> "tests/$string_name.md"
        end_time=$(date +%s)
        elapsed_time=$((end_time - start_time))
        avg_time=$((avg_time + elapsed_time))
        echo "=====Test took $elapsed_time seconds=====" >> "tests/$string_name.md"
    done
    # Calculate average time
    avg_time=$((avg_time / 5))

    echo "" >> "tests/$string_name.md"
    echo "=====END $string_name====="
    ((count++))
    echo "$count/$total tests completed"
    echo "=====Test took $avg_time seconds on average=====" >> "tests/$string_name.md"
    echo ""
done
overall_end=$(date +%s)
overall_elapsed=$((overall_end - overall_start))
overall_elapsed_minutes=$((overall_elapsed / 60))
echo "All tests completed in $overall_elapsed_minutes minutes"

