FROM ollama/ollama:latest

WORKDIR /home

# Install python3 and parallel
RUN apt update && apt install -y python3 parallel python3-pip

# Alias python3 to python
RUN ln -s /usr/bin/python3 /usr/bin/python

# Copy the current directory contents into the container at /home
COPY app app
COPY requirements.txt requirements.txt
COPY run_local.sh run_local.sh

# Install python dependencies
RUN pip3 install -r requirements.txt

ENV ROOT_DIRECTORY="/mount"
ENV FILE_LOG_PATH="/home/tea-output.log"

ENTRYPOINT ["/bin/bash"]

CMD ["run_local.sh"]