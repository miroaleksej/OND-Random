FROM ubuntu:22.04

RUN apt-get update && apt-get install -y build-essential ca-certificates libtestu01-dev && rm -rf /var/lib/apt/lists/*

COPY testu01_file_runner.c /opt/testu01_file_runner.c
RUN gcc -O2 -o /usr/local/bin/testu01_file_runner /opt/testu01_file_runner.c -ltestu01 -lm

COPY run_testu01.sh /usr/local/bin/run_testu01.sh
RUN chmod +x /usr/local/bin/run_testu01.sh

ENTRYPOINT ["/usr/local/bin/run_testu01.sh"]
