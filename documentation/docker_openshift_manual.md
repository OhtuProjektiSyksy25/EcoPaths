# Docker and Openshift Manual

This manual provides instructions for building, testing, and deploying the EcoPaths application using Docker and OpenShift.

The build and deployment process is already automated through the project’s CI/CD pipeline, so these steps are mainly intended for debugging, local testing, or manual redeployment when needed.

## Docker

### Building a Docker image

1. Make sure you're in the **root directory** of the project.

2. Build the image:

```bash
docker build --build-arg REACT_APP_MAPBOX_TOKEN=<MAPBOX_TOKEN> --build-arg REACT_APP_MAPBOX_STYLE=mapbox://styles/mapbox/streets-v11 -t <DOCKER_HUB_USERNAME>/ecopaths:staging .
```

> **Note:** The map component doesn't render when running the image locally, but will work when it's deployed to OpenShift. 

**To build an image that works locally**, use this command instead:

```bash
docker build --build-arg REACT_APP_MAPBOX_TOKEN=<MAPBOX_TOKEN> --build-arg REACT_APP_MAPBOX_STYLE=mapbox://styles/mapbox/streets-v11 --build-arg REACT_APP_API_URL=http://localhost:8000 -t <IMAGE_NAME> .
```

### Creating and running a Docker container

Create and run a container:

```bash
docker run -p 8000:8000 <IMAGE_NAME>
```

## Docker Hub

### Logging in to Docker Hub

1. Log in to Docker Hub:

```bash
docker login -u <DOCKER_HUB_USERNAME>
```

2. Enter the password or token.

### Pushing the Docker image to Docker Hub

Push the image with:

```bash
docker push <DOCKER_HUB_USERNAME>/ecopaths:staging
```

## OpenShift

To access the OpenShift cluster, you need to be connected to Eduroam or the University of Helsinki VPN. Make sure you're logged into the OpenShift cluster before running any `oc` commands.

Instructions for logging into the cluster can be found [here](https://github.com/HY-TKTL/TKT20007-Ohjelmistotuotantoprojekti/tree/master/openshift#openshift).
If you need to install the OpenShift client, instructions for that can be found below.

### Installation

Install the `oc` CLI using [these](https://devops.pages.helsinki.fi/guides/platforms/tike-container-platform.html#openshift-client) instructions.
> For Linux users, download `openshift-client-linux-amd64-rhel8-4.19.15.tar.gz`.

### General

Whenever a new Docker image is pushed to Docker Hub under `<DOCKER_HUB_USERNAME>/ecopaths:staging`, the OpenShift imagestream updates automatically. There might be a slight delay, but it should take at most 15 minutes. 
To update the imagestream immediately, run:

```bash
oc import-image ecopaths:staging
```

### Creating the ConfigMap

If the ConfigMap doesn't exist yet:

1. Make sure you're in the **root directory** of the project.

2. Create a configmap-yaml based on configmap-template.yaml with the command

```bash
cp manifests/configmap_template.yaml manifests/configmap.yaml
 
```

3. Update the `DB_URL` in `manifests/configmap.yaml` with the correct database credentials.

> **Note:** The `DB_URL` contains sensitive information, so it should be kept private.

### Applying the OpenShift Configuration

Apply the manifests whenever you make changes in the `manifests/` directory.

1. Make sure you're in the **root directory** of the project.

2. Apply the manifests:

```bash
oc apply -k .
```

### Checking Pod Status

List all pods in the cluster:

```bash
oc get pods
```

This will list the pods in the cluster and their current status. We can find out our pod name from this list.

### Viewing Pod Details

Get detailed information about a specific pod:

```bash
oc describe pod <POD_NAME>
```

### Viewing Pod Logs

View the logs for a specific pod:

```bash
oc logs <POD_NAME>
```