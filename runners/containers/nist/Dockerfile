FROM ubuntu:22.04

RUN apt-get update && apt-get install -y build-essential ca-certificates && rm -rf /var/lib/apt/lists/*

COPY run_nist_sts.sh /usr/local/bin/run_nist_sts.sh
RUN chmod +x /usr/local/bin/run_nist_sts.sh

ENTRYPOINT ["/usr/local/bin/run_nist_sts.sh"]
