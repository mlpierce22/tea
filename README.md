# Tea 🫖

> ⚠️ **This project is in early development. I appreciate constructive feedback and help!** ⚠️

## Introduction

Tea makes frontend Vue development as easy as making a cup of tea: just heat, steep, and pour. This tool allows you to utilize the power of local large language models to quickly create Vue3 components.

## Demos

### Running 100% locally on a Macbook Pro, 18GB GPU

<video src="videos/local-only-generation.mp4" alt="Tea Demo with Local Model"></video>

> The generation in this video is REAL TIME. I only sped up the sections of the video where I was typing!

### Running via GPT-3.5

<video src="videos/gpt-3.5-generation.mp4" alt="Tea Demo with GPT-3.5"></video>

> The generation in this video is REAL TIME. I only sped up the sections of the video where I was typing!

## Table of Contents

- [Introduction](#introduction)
- [Usage](#usage)
- [Examples](#examples)
- [Features](#features)
- [Configuration](#configuration)
- [Choosing a Model](#choosing-a-model)
- [Improvements](#improvements)
- [Contributors](#contributors)
- [Inspirations](#inspirations)
- [Connect](#connect)
- [License](#license)

## Usage

### Running locally

0. For now, this project assumes you...
   1. Have a GPU. While this will work on a CPU, it is much much slower, which will likely significantly effect your experience.
   2. Have Ollama installed on your computer. Instructions on how to do that can be found [here](https://ollama.ai/)
   3. Have `docker` installed on your computer. Instructions on how to do that can be found [here](https://docs.docker.com/engine/install/)
1. Start Ollama with `ollama serve` in a terminal or by clicking on the icon if you downloaded the app
2. Go to the root directory of your `Vue` project and run the following docker command

```bash
docker run -d \
    --pull=always \
    -v ollama:/root/.ollama \
    -v $(pwd):/mount \
    -p 11434:11434 \
    -e MODEL=deepseek-coder:6.7b-instruct \
    --name tea mlpierce22/tea:latest
```

3. Add a `<Tea>` component into your `Vue` template like you were creating a component and save. Generation should begin!
4. When you have generated to your heart's content, you can pour the tea by adding the `pour` prop like `pour="ComponentName"` and it will generate a component with that name, replacing the Tea component.

### Running via GPT 3.5

1. Go to the root directory of your `Vue` project and run the following docker command (replace <Open-AI-Key> with your OpenAI key)

```bash
docker run -d \
    --pull=always \
    -v ollama:/root/.ollama \
    -v $(pwd):/mount \
    -p 11434:11434 \
    -e OPENAI_KEY=<Open-AI-Key> \
    --name tea mlpierce22/tea:latest
```

3. Add a `<Tea>` component into your `Vue` template like you were creating a component and save. Generation should begin!
4. When you have generated to your heart's content, you can pour the tea by adding the `pour` prop like `pour="ComponentName"` and it will generate a component with that name, replacing the Tea component.

## Examples

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
<script setup></script>
<template>
  <UContainer>
    <UCard class="mt-10">
      <template #header>
        <div class="flex justify-between">
          <h1>Welcome to Nuxt UI Starter</h1>
          <ColorScheme>
            <USelect
              v-model="$colorMode.preference"
              :options="['system', 'light', 'dark']"
            />
          </ColorScheme>
        </div>
      </template>
      <UButton
        icon="i-heroicons-book-open"
        to="https://ui.nuxt.com"
        target="_blank"
        >Open Nuxt UI Documentation</UButton
      >
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
- **Generates Working Vue Code semi-reliably**: This should at least be a much better start than a static generator. If you can run 34b models locally, you will get much better results.
- **Use any model supported by Ollama**: Find every available model at [https://ollama.ai](https://ollama.ai/). If you have a beefy computer, you can even use the larger, 13B or 70B models that will approach the performance of GPT-3.5/4.

## Configuration

Currently, Tea accepts environment variables to determine it's behavior.

- `MODEL`: Choose from any model on [https://ollama.ai/library](https://ollama.ai/library). See [Choosing a model](#Choosing-a-Model) or any OpenAI model if you have an OpenAI key set.
  - **Default**: `deepseek-coder:6.7b-instruct` OR `gpt-3.5-turbo`
- `OPENAI_KEY`: Use OpenAI's models. There is no need to use Ollama if this is supplied.
  - **Default**: `None`
- `ROOT_DIRECTORY`: Helpful if you want to run the docker container in a different terminal than your Vue repository
  - **Default**: the working directory of the docker run command
- `TEMPERATURE`: Helpful if you want the model to be more ✨creative✨
  - **Default**: 0.5
- `LOG_LEVEL`: Set the log level for the container
  - **Options**: `DEBUG`, `INFO`, `WARNING`
  - **Default**: `INFO`

## Choosing a Model

After running tests on all the Ollama models that weren't too big for me to run, here are my general takeaways:

- Generally speaking, bigger models perform better, but slower
- I would recommend going for `instruct` models or models trained on coding
- Don't bother with models that are used for completion, they won't follow the instructions and you will get gibberish

These are the models I recommend that perform fairly well and are fast enough to be viable
Key
Quality: High (H), Medium (M), Low (L)
Time: Seconds (avg)

| Model                             | Quality | Time to complete |
| --------------------------------- | ------- | ---------------- |
| mistral:v0.2                      | M       | 14               |
| deepseek-coder:6.7b-instruct-q4_0 | M       | 19               |
| deepseek-coder:6.7b-instruct      | M       | 19               |
| deepseek-coder:6.7b               | M       | 23               |
| codellama:7b-instruct-q4_0        | M       | 26               |
| codellama:13b-instruct-q4_0       | H       | 26               |
| codellama:7b-instruct             | H       | 29               |

## Improvements

- [ ] Add updating existing components. This gets tricky because it's unclear how UX should work if the user want's to undo generation.
- [ ] Fine-tune an instructor model to generate consistently. [Kevind13's finetune works okay, but not great](https://huggingface.co/kevind13/codeLlama-7b-Instruct-hf-vuejs-nuxt-tailwind-finetuned-examples)
- [ ] Don't add quite so much thinking to the LLM. Currently, some of the assumptions may not work for everybody, but in the interest of getting this out, I figured that was the best approach
- [ ] Add regeneration in case first generation was bad, and/or generate multiple versions and select the best one.

## Contributors

I welcome contributions and bug fixes! If you find something isn't working, please open an issue. Feel free to contribute pull requests!

### Running locally

1. Clone this repository
2. [Recommended] Create a virtual environment and activate it
3. Install dependencies from the `requirements.txt` file: `pip install -r requirements.txt`
4. Run the watcher with `ROOT_DIRECTORY=/path/to/vue/project bash run_local.sh`
   - Create any of the environment variables from the [Configuration](#Configuration) section above as needed

## Inspirations

This project was HEAVILY inspired by [Coffee](https://github.com/Coframe/coffee) from the Coframe team.

Thank you also to these other cool projects that acted as inspirations:

- [Cursor](https://cursor.sh/)
- [Vue0](https://www.vue0.dev/)

## Connect

Hey! My name is Mason and I'm a full-stack developer based out of San Francisco! Always open to chat!  
Website: https://masonpierce.dev/  
Twitter: https://twitter.com/mlpierce22

## License

[Apache License](LICENSE.md)
