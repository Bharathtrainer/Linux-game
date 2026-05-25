FROM ubuntu:22.04

# Tools used by the scenario setup scripts and by players.
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        coreutils procps grep sed gawk \
        findutils less vim-tiny \
        net-tools curl iputils-ping \
        psmisc sudo ca-certificates && \
    rm -rf /var/lib/apt/lists/*

# Non-root sandbox user (UID matches docker run --user 1000:1000)
RUN useradd -m -u 1000 -s /bin/bash sandbox

WORKDIR /home/sandbox
USER sandbox

CMD ["/bin/bash"]
