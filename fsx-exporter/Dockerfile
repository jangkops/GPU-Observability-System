FROM ubuntu:20.04
ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update &&     apt-get install -y wget python3 gnupg ca-certificates &&     wget -O - https://fsx-lustre-client-repo-public-keys.s3.amazonaws.com/fsx-ubuntu-public-key.asc | apt-key add - &&     echo 'deb https://fsx-lustre-client-repo.s3.amazonaws.com/ubuntu focal main' > /etc/apt/sources.list.d/fsxlustreclientrepo.list &&     apt-get update &&     apt-get install -y lustre-client-modules-aws &&     rm -rf /var/lib/apt/lists/*
COPY fsx_exporter.py /app/
WORKDIR /app
CMD ["python3", "fsx_exporter.py"]
