### Tea 🫖

## Introduction

Tea makes frontend Vue development as easy as making a cup of tea: just heat, steep, and pour. This tool allows you to utilize the power of local large language models to quickly create Vue components.

## Table of Contents

- [Introduction](#introduction)
- [Usage](#Usage)
- [Examples](#Examples)
- [Features](#Features)
- [Configuration](#Configuration)
- [Contributors](#Contributors)
- [Inspirations](#Inspirations)
- [Connect](#Connect)
- [License](#License)

## Usage

0. For now, this project assumes you...
    1. Have a GPU. While this will work on a CPU, it is much much slower, which will likely significantly effect your experience.
    2. Have Ollama installed on your computer. Instructions on how to do that can be found [here](https://ollama.ai/)
    3. Have `docker` installed on your computer. Instructions on how to do that can be found [here](https://docs.docker.com/engine/install/)
1. Start Ollama with `ollama serve` in a terminal or by clicking on the icon if you downloaded the app
2. Go to the root directory of your `Vue` project and run the following docker command
    ```
    docker run -d \
        -v ollama:/root/.ollama \
        -v $(pwd):/mount \
        -p 11434:11434 \
        -e MODEL=deepseek-coder:6.7b-instruct \
        --name tea tea:0.0.1
    ```
3. Add a `<Tea>` component into your `Vue` template like you were creating a component and save. Generation should begin!
4. When you have generated to your heart's content, you can pour the tea by adding the `pour` prop like `pour="ComponentName"` and it will generate a component with that name, replacing the Tea component.

## Examples:

### Generating a Tea component
```vue
<Tea>Make a large green button with the text, hello world.</Tea>
```
Every time you update this text, it will update the component with the context of your previous generation.

```vue
<Tea>Change the buttons's color to blue.</Tea>
```

In context, it looks like this. Don't worry about imports, that will happen for you automagically 🙌

```vue
<script setup>

</script>
<template>
  <UContainer>
    <UCard class="mt-10">
      <template #header>
        <div class="flex justify-between">
          <h1>Welcome to Nuxt UI Starter</h1>
          <ColorScheme>
            <USelect v-model="$colorMode.preference" :options="['system', 'light', 'dark']" />
          </ColorScheme>
        </div>
      </template>
      <UButton icon="i-heroicons-book-open" to="https://ui.nuxt.com" target="_blank">Open Nuxt UI Documentation</UButton>
    </UCard>
    <Tea>Change the buttons's color to blue.</Tea>
  </UContainer>
</template>
```

### Finalizing the component 
When you are done with your changes, simply `pour` the component which will intelligently choose a location for the component and replace the `Tea` component with your new one. For example:
```vue
<Tea pour="BigBlueButton">Change the buttons's color to blue.</Tea>
```

Becomes
```vue
<BigBlueButton></BigBlueButton>
```

## Features

- **Privacy-Friendly**: Nothing ever leaves your device, pretty cool right?
- **Fast-Setup**: Get going in minutes - if you're already set up... seconds.
- **Works With All Vue 3 Projects**: The model guesses the desired syntax based on the parent component, so you can just plug and play.
- **Prototype Rapidly and Cheaply**: You don't have to worry about api keys or cost, which is one of the biggest gating factors to current code generation solutions. If it doesn't work at first, just keep iterating.
- **Generates Working Vue Code Reliably**: This should at least be a much better start than a static generator.
- **Use any model supported by Ollama**: Find every available model at [https://ollama.ai](https://ollama.ai/). If you have a beefy computer, you can even use the larger, 13B or 70B models that will approach the performance of GPT-3.5/4.

## Configuration

Currently, Tea accepts environment variables to determine it's behavior.
- `MODEL`: Choose from any model on [https://ollama.ai/library](https://ollama.ai/library)
    - **Default**: `deepseek-coder:6.7b-instruct`
- `OPENAI_KEY`: Use OpenAI's models. There is no need to use Ollama if this is supplied.
    - **Default**: `None`
- `ROOT_DIRECTORY`: Helpful if you want to run the docker container in a different terminal than your Vue repository
    - **Default**: the working directory of the docker run command 
- `TEMPERATURE`: Helpful if you want the model to be more ✨creative✨
    - **Default**: 0.5


## Contributors
I welcome contributions and bug fixes! If you find something isn't working, please open an issue. Feel free to contribute pull requests!

### Running locally
1. Clone this repository
2. [Recommended] Create a virtual environment and activate it
3. Install dependencies from the `requirements.txt` file: `pip install -r requirements.txt`
4. Run the watcher with `ROOT_DIRECTORY=/path/to/vue/project bash run_local.sh`
  - Create any of the environment variables from the [Configuration][#Configuration] section above as needed

## Inspirations
This project was HEAVILY inspired by [Coffee](https://github.com/Coframe/coffee) from the Coframe team.

Thank you also to these other cool projects that acted as inspirations:
- [Cursor](https://cursor.sh/)
- [Vue0](https://www.vue0.dev/)

## Connect
Hey! My name is Mason and I'm a full-stack developer based out of San Francisco! Please reach out if you want to
Website: https://masonpierce.dev/
Twitter: https://twitter.com/mlpierce22

## License

[Apache License](LICENSE.md)

