FROM python:3.10
WORKDIR /home

# HEALTHCHECK instruction
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/ || exit 1

# Create a non-root user and switch to it
RUN useradd -m tea
USER tea

# Install parallel
RUN apt-get update && apt-get install -y parallel=20231222 --no-install-recommends && \
    rm -rf /var/lib/apt/lists/*

# Alias python3 to python
RUN ln -s /usr/bin/python3 /usr/bin/python

# Copy the current directory contents into the container at /home
COPY app app
COPY requirements.txt requirements.txt
COPY run_local.sh run_local.sh

# Set SHELL to use pipefail
SHELL ["/bin/bash", "-o", "pipefail", "-c"]

# Install ollama command line tool
RUN curl https://ollama.ai/install.sh | sh

ENV ROOT_DIRECTORY="/mount"
# ENV FILE_LOG_PATH="/home/tea-output.log"
ENV OLLAMA_HOST="host.docker.internal:11434"

# Install python dependencies
RUN pip3 install --no-cache-dir -r requirements.txt

ENTRYPOINT ["/bin/bash"]

CMD ["run_local.sh"]