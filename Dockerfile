FROM python:3.10

WORKDIR /home

# Install python3 and parallel
RUN apt update && apt install -y parallel

# Alias python3 to python
RUN ln -s /usr/bin/python3 /usr/bin/python

# Copy the current directory contents into the container at /home
COPY app app
COPY requirements.txt requirements.txt
COPY run_local.sh run_local.sh

# Install python dependencies
RUN pip3 install --no-cache-dir -r requirements.txt

# Install ollama command line tool
RUN curl https://ollama.ai/install.sh | sh

ENV ROOT_DIRECTORY="/mount"
# ENV FILE_LOG_PATH="/home/tea-output.log"
ENV OLLAMA_HOST="host.docker.internal:11434"

ENTRYPOINT ["/bin/bash"]

CMD ["run_local.sh"]