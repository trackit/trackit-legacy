FROM debian:stable-slim

WORKDIR /root/
RUN \
	apt-get update \
	&& apt-get install -y \
		wget \
		git \
		bash \
	&& rm -rf /var/lib/apt/lists/*

COPY files/* ./
COPY ssh .ssh/
RUN ./install-hashicorp.sh
CMD ./entrypoint.sh

# Parameters:
#  ENV AWS_DEFAULT_REGION
#  ENV AWS_ACCESS_KEY_ID
#  ENV AWS_SECRET_ACCESS_KEY
#  ENV SSH_AUTH_SOCK
#  VOL SSH_AUTH_SOCK Directory
