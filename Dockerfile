FROM ubuntu:14.04
MAINTAINER tangym

WORKDIR /workspace
VOLUME /workspace

ADD api.py /workspace
ADD configure.py /workspace
ADD requirements.txt /workspace
ADD sample_config.yml /workspace

RUN apt-get update && \
	apt-get install -y python3 python3-pip sqlite3 libsqlite3-dev && \
	pip3 install -r requirements.txt

ENV CONFIGURATION_FILE sample_config.yml
EXPOSE 5000
ENTRYPOINT ["sh", "-c", "python3 api.py $CONFIGURATION_FILE"]

