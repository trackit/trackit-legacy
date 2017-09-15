#!/bin/sh -x

# We consider the deployer image is named trackit/deployer.

ssh_auth_sock_dir=$(dirname $SSH_AUTH_SOCK)

docker run -it --rm \
	--volume="${ssh_auth_sock_dir}":"${ssh_auth_sock_dir}" \
	--env=SSH_AUTH_SOCK="${SSH_AUTH_SOCK}" \
	--env=AWS_ACCESS_KEY_ID="${AWS_ACCESS_KEY_ID}" \
	--env=AWS_SECRET_ACCESS_KEY="${AWS_SECRET_ACCESS_KEY}" \
	--env=AWS_DEFAULT_REGION="${AWS_DEFAULT_REGION}" \
	--env=ECR_IMAGE_TAG="${ECR_IMAGE_TAG}" \
	--env=DEPLOYMENT_ENVIRONMENT="${DEPLOYMENT_ENVIRONMENT}" \
	--env=DEPLOYMENT_COMMIT="${DEPLOYMENT_COMMIT}" \
	trackit/deployer
