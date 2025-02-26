# Doc Ingestion Pipeline

This pipeline automates the process of ingesting documentation into a data science pipeline ([doc ingestion pipeline](./../products-documentation-ingestion/)) when changes are detected in the [collections](./../collections/) directory. It uses GitHub webhooks to detect pushes to the main branch and executes a series of tasks to process the documentation.

## Components

### PersistentVolumeClaim
- **Name**: `shared-workspace`
- **Storage**: 3Gi
- **Access Mode**: ReadWriteOnce
- **Provisioner**: AWS EBS

### Event Listener
- **Name**: `doc-ingestion-listener`
- Listens for GitHub push events via a webhook

### Trigger
- **Name**: `doc-ingestion-trigger`
- Includes a CEL interceptor that filters for:
  - Push events to the `main` branch
  - Changes (modified, added, or removed) in the `collections` directory

### Pipeline
- **Name**: `doc-ingestion`
- **Parameters**:
  - `APPLICATION_NAME`: Repository name
  - `GIT_URL`: Git repository URL
  - `GIT_BRANCH`: Git branch name (default: main)

### Tasks

1. **fetch-ds-pipeline-repository**
   - Clones the Git repository to a shared workspace
   - Uses the OpenShift Pipelines git-clone task

2. **execute-doc-ingestion-pipeline**
   - Executes the data science pipeline for document ingestion
   - Uses a custom task that connects to Data Science Pipelines via Kubernetes API
   - Creates a run in the Data Science Pipeline environment

3. **doc-process-status**
   - Monitors the status of the data science pipeline run
   - Streams logs from the system-container-impl pod
   - Reports success or failure based on the pod status
   - Times out after 10 hours

## Execution Flow

1. A push to the main branch with changes in the collections directory triggers the pipeline
2. The repository is cloned to a shared workspace
3. The document ingestion data science pipeline is executed
4. Logs are streamed and the status is monitored until completion

## Route Configuration

The EventListener is exposed via an OpenShift Route with TLS edge termination.

## Requirements

- OpenShift cluster with Tekton Pipelines installed
- Data Science Pipeline Application is deployed in the same namespace
- GitHub repository configured with webhooks pointing to the EventListener route