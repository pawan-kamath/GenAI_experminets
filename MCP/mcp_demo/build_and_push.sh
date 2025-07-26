#/bin/bash
export DOCKER_CLI_DEBUG=1
sudo docker build -t travel-assist:latest .
sudo docker tag travel-assist:latest ger-is-registry.caas.intel.com/msoa-irl-registry/travel-assist:latest
docker push ger-is-registry.caas.intel.com/msoa-irl-registry/travel-assist:latest
