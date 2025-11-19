# Docker and Openshift Manual

This manual provides instructions for **building**, **testing**, and **deploying** the EcoPaths application using **Docker** and **OpenShift**.

The build and deployment process is already automated through the project’s CI/CD pipeline, so these steps are mainly intended for **debugging**, **local testing**, or **manual redeployment** when needed.

## Docker

### Building a Docker image

1. Make sure you're in the **root directory** of the project.

2. Build the image for **OpenShift deployment**:

```bash
docker build --build-arg REACT_APP_MAPBOX_TOKEN=<MAPBOX_TOKEN> --build-arg REACT_APP_MAPBOX_STYLE=mapbox://styles/mapbox/streets-v11 --build-arg GOOGLE_API_KEY=<GOOGLE_API_KEY> -t <DOCKER_HUB_USERNAME>/ecopaths:staging .
```

> **Note:** When running this image locally, the map component might not render correctly. The map component will render properly when the image deployed to OpenShift. 

To **test the application locally** with the map component, use this command instead:

```bash
docker build --build-arg REACT_APP_MAPBOX_TOKEN=<MAPBOX_TOKEN> --build-arg REACT_APP_MAPBOX_STYLE=mapbox://styles/mapbox/streets-v11 --build-arg GOOGLE_API_KEY=<GOOGLE_API_KEY> --build-arg REACT_APP_API_URL=http://localhost:8000 -t <IMAGE_NAME> .
```

> [!CAUTION]
> This locally built image is only for testing.  
> **Do not push it to Docker Hub**, as it will **not work in OpenShift**.

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

### Checking and Adjusting Pod Resource Usage

The resource usage (CPU and memory) of pods should be monitored and managed.

Check resource usage:

```bash
oc adm top pods
```

This command displays the current resource usage of the pods in the cluster.

Resource limits are defined in `deployment.yaml`. If the pod needs more resources, you can **modify the values in** `limits` in the following snippet:

```
resources:
  limits:
    memory: "512Mi"
    cpu: "500m"
  requests:
    memory: "128Mi"
    cpu: "50m"
```

> [!CAUTION]
> The values in `requests` can't be increased due to cluster resource constraints.  
> Only change the values in `limits`.

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

## Populate the database manually

1. Populate local database

```bash
bash setup.sh
```

2. Create dump from local database

```bash
export PGPASSWORD=<LOCAL_POSTGRES_PASSWORD>
```

```bash
docker exec -e PGPASSWORD=<LOCAL_POSTGRES_PASSWORD> <DOCKER_CONTAINER_NAME> pg_dump \
  -h localhost \
  -U <LOCAL_POSTGRES_USER> \
  -d <LOCAL_POSTGRES_DB_NAME> \
  -Fc -Z9 --no-owner --no-acl \
  -f /tmp/database_dump.backup
```

```bash
unset PGPASSWORD
```

3. Copy `database_dump.backup` to the root folder if it was created within a Docker container

```bash
docker cp <DOCKER_CONTAINER_NAME>:/tmp/database_dump.backup ./database_dump.backup
```

4. Check that the dump was created

```bash
ls -lh database_dump.backup
```

5. Connect to the OpenShift client

6. Run a temporary client pod

```bash
oc run pg-client --image=postgres:15 --restart=Never -- sleep infinity
```

7. Copy your dump file into the temporary pod

```bash
oc cp ./database_dump.backup pg-client:/tmp/database_dump.backup
```

8. Connect to your existing database service from inside the cluster

```bash
oc exec -it pg-client -- bash
```

9. Inside the shell, run:

```bash
export PGPASSWORD=<DEPLOYMENT_DB_PASSWORD>
```

```bash
pg_restore -h <DEPLOYMENT_DB_HOST> -U <DEPLOYMENT_DB_USER> -d <DEPLOYMENT_DB_NAME> \
  -v --no-owner --no-acl -j 2 --clean --if-exists \
  /tmp/database_dump.backup
```

```bash
unset PGPASSWORD
```

10. When done, exit the shell:

```bash
exit
```

11. Delete the pg-client pod:

```bash
oc delete pod pg-client
```
