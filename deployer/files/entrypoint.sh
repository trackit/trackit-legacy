#!/bin/bash -x

set -e

ssh-add -l
env | sort

BASTION_HOST=bastion.us-west-2.trackit.io
BASTION_USER=circleci

BASTION_SSH_CONTROL_MASTER_DIR=/tmp/cm
BASTION_SSH_OPTIONS=( \
	-o ControlMaster='auto' \
	-o ControlPath="${BASTION_SSH_CONTROL_MASTER_DIR}/%r@%h:%p" \
)

mkdir -p "${BASTION_SSH_CONTROL_MASTER_DIR}" # SSH ControlMaster directory

nomad_agent=$(ssh \
	"${BASTION_SSH_OPTIONS[@]}" \
	"${BASTION_USER}@${BASTION_HOST}" \
	get-nomad-agent-address \
)

# Open SSH forwarding to Nomad and Consul
ssh \
	-fNT \
	-L "127.0.0.1:4646:${nomad_agent}:4646" \
	-L "127.0.0.1:8500:127.0.0.1:8500" \
	"${BASTION_SSH_OPTIONS[@]}" \
	"${BASTION_USER}@${BASTION_HOST}"

export NOMAD_ADDR=http://127.0.0.1:4646
export CONSUL_HTTP_ADDR=127.0.0.1:8500

consul kv put "circleci/${DEPLOYMENT_ENVIRONMENT}/docker/tag" "${ECR_IMAGE_TAG}"
consul kv put "circleci/${DEPLOYMENT_ENVIRONMENT}/commit/id" "${DEPLOYMENT_COMMIT}"

git clone \
	--depth=1 \
	--recurse-submodules \
	git@bitbucket.org:msolutionio/infrastructure.trackit.io.git
cd infrastructure.trackit.io/terraform/
terraform init
terraform get
terraform plan -out tf.plan
terraform apply tf.plan

# Close SSH forwarding
ssh \
	"${BASTION_SSH_OPTIONS[@]}" \
	-O exit \
	"${BASTION_USER}@${BASTION_HOST}"
