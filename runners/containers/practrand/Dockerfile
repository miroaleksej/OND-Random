FROM ubuntu:22.04

RUN apt-get update && apt-get install -y git build-essential ca-certificates && rm -rf /var/lib/apt/lists/*
RUN git clone --depth 1 https://github.com/CHerum/PractRand.git /opt/PractRand && make -C /opt/PractRand
ENV PATH="/opt/PractRand/bin:${PATH}"

COPY run_practrand.sh /usr/local/bin/run_practrand.sh
RUN chmod +x /usr/local/bin/run_practrand.sh

ENTRYPOINT ["/usr/local/bin/run_practrand.sh"]
