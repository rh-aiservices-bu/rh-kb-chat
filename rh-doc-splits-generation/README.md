# Red Hat Documentation Splits Generation

The scripts in this folder will create langchain documents with full metadata on their source as well as the precise location of the split in the original document (chapter, section,...). This location will also be part of the split content to preserve the full context of the excerpt.

Example of a split:

------
    Metadata: {'Header 1': 'Chapter 3. Serving large models', 'Header 2': '3.5. Configuring monitoring for the single-model serving platform', 'source': 'https://access.redhat.com/documentation/en-us/red_hat_openshift_ai_self-managed/2.8/html-single/serving_models', 'title': 'Serving models', 'product': 'red_hat_openshift_ai_self-managed', 'version': '2.8', 'language': 'en-US', 'product_full_name': 'Red Hat OpenShift AI Self-Managed'}
    
    Page Content:
    -------------
    Section: Serving models / Chapter 3. Serving large models / 3.5. Configuring monitoring for the single-model serving platform

    Content:
    The single-model serving platform includes metrics for supported runtimes. You
    can also configure monitoring for OpenShift Service Mesh. The service mesh
    metrics helps you to understand dependencies and traffic flow between
    components in the mesh. When you have configured monitoring, you can grant
    Prometheus access to scrape the available metrics.  
    Prerequisites  
    * You have cluster administrator privileges for your OpenShift Container Platform cluster.
    * You have created OpenShift Service Mesh and Knative Serving instances and installed KServe.
    * You have downloaded and installed the OpenShift command-line interface (CLI). See Installing the OpenShift CLI.
    * You are familiar with creating a config map for monitoring a user-defined workflow. You will perform similar steps in this procedure.
    * You are familiar with enabling monitoring for user-defined projects in OpenShift. You will perform similar steps in this procedure.
    * You have assigned the `monitoring-rules-view` role to users that will monitor metrics.  
    Procedure  
    1. In a terminal window, if you are not already logged in to your OpenShift cluster as a cluster administrator, log in to the OpenShift CLI as shown in the following example:  
    ```console
    $ oc login <openshift_cluster_url> -u <admin_username> -p <password>
    ```  
    2. Define a `ConfigMap` object in a YAML file called `uwm-cm-conf.yaml` with the following contents:  
    ```console
    apiVersion: v1
    kind: ConfigMap
    metadata:
    name: user-workload-monitoring-config
    namespace: openshift-user-workload-monitoring
    data:
    config.yaml: |
    prometheus:
    logLevel: debug
    retention: 15d
    ```  
    The `user-workload-monitoring-config` object configures the components that
    monitor user-defined projects. Observe that the retention time is set to the
    recommended value of 15 days.  
    3. Apply the configuration to create the `user-workload-monitoring-config` object.  
    ```console
    $ oc apply -f uwm-cm-conf.yaml
    ```  
    4. Define another `ConfigMap` object in a YAML file called `uwm-cm-enable.yaml` with the following contents:


## Requirements

The needed Python packages are listed in the `Pipfile` and `requirements.txt` file.

### Local development installation:

- Create a virtual environment with the Pipfile and install the packages:

    ```bash
    pipenv install --dev
    ```

- Activate the virtual environment:

    ```bash
    pipenv shell
    ```

### Usage in an existing Python environment

- Execute the `pip install...` cell from the notebook.

## Usage

- Launch the notebook `rh-doc-splits-generation.ipynb`
- Enter the document information: name, version, language
- Run the cells
