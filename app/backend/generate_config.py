import json

class product_info:
    def __init__(self, product, product_full_name, version, language):
        self.product = product
        self.product_full_name = product_full_name
        self.version = version
        self.language = language

    # Method to convert object to dictionary
    def to_dict(self):
        return {
            'product': self.product,
            'product_full_name': self.product_full_name,
            'version': self.version,
            'language': self.language
        }

# Your existing code to create the list of product_info objects
products = []
products.append(product_info('red_hat_openshift_ai_self-managed',
                             'Red Hat OpenShift AI Self-Managed',
                             '2.8',
                             'en-US'))
products.append(product_info('red_hat_openshift_ai_self-managed',
                             'Red Hat OpenShift AI Self-Managed',
                             '2.7',
                             'en-US'))
products.append(product_info('red_hat_openshift_ai_self-managed',
                             'Red Hat OpenShift AI Self-Managed',
                             '2.6',
                             'en-US'))
products.append(product_info('red_hat_advanced_cluster_management_for_kubernetes',
                             'Red Hat Advanced Cluster Management for Kubernetes',
                             '2.10',
                             'en-US'))
products.append(product_info('red_hat_advanced_cluster_security_for_kubernetes',
                             'Red Hat Advanced Cluster Security for Kubernetes',
                             '4.4',
                             'en-US'))
products.append(product_info('red_hat_amq_streams',
                             'Red Hat AMQ Streams',
                             '2.6',
                             'en-US'))
products.append(product_info('red_hat_ansible_automation_platform',
                             'Red Hat Ansible Automation Platform',
                             '2.4',
                             'en-US'))
products.append(product_info('red_hat_ansible_lightspeed_with_ibm_watsonx_code_assistant',
                             'Red Hat Ansible Lightspeed with IBM watsonx Code Assistant',
                             '2.x_latest',
                             'en-US'))
products.append(product_info('red_hat_data_grid',
                             'Red Hat Data Grid',
                             '8.4',
                             'en-US'))
products.append(product_info('red_hat_developer_hub',
                             'Red Hat Developer Hub',
                             '1.1',
                             'en-US'))
products.append(product_info('red_hat_enterprise_linux',
                             'Red Hat Enterprise Linux',
                             '9',
                             'en-US'))
products.append(product_info('red_hat_enterprise_linux',
                             'Red Hat Enterprise Linux',
                             '8',
                             'en-US'))
products.append(product_info('red_hat_build_of_microshift',
                             'Red Hat build of MicroShift',
                             '4.15',
                             'en-US'))
products.append(product_info('red_hat_openshift_data_foundation',
                             'Red Hat OpenShift Data Foundation',
                             '4.15',
                             'en-US'))
products.append(product_info('red_hat_satellite',
                             'Red Hat Satellite',
                             '6.14',
                             'en-US'))
products.append(product_info('red_hat_single_sign-on',
                             'Red Hat Single Sign-On',
                             '7.6',
                             'en-US'))
products.append(product_info('red_hat_3scale_api_management',
                             'Red Hat 3scale API Management',
                             '2.14',
                             'en-US'))
products.append(product_info('red_hat_advanced_cluster_security_for_kubernetes',
                             'Red Hat Advanced Cluster Security for Kubernetes',
                             '4.4',
                             'en-US'))
products.append(product_info('red_hat_enterprise_linux',
                             'Red Hat Enterprise Linux',
                             '7',
                             'en-US'))
products.append(product_info('openshift_container_platform',
                             'Red Hat OpenShift Container Platform',
                             '4.15',
                             'en-US'))
products.append(product_info('openshift_container_platform',
                             'Red Hat OpenShift Container Platform',
                             '4.14',
                             'en-US'))
products.append(product_info('openshift_container_platform',
                             'Red Hat OpenShift Container Platform',
                             '4.13',
                             'en-US'))
products.append(product_info('openshift_container_platform',
                             'Red Hat OpenShift Container Platform',
                             '4.12',
                             'en-US'))
products.append(product_info('red_hat_openshift_serverless',
                             'Red Hat OpenShift Serverless',
                             '1.32',
                             'en-US'))
products.append(product_info('red_hat_hybrid_cloud_console',
                             'Red Hat Hybrid Cloud Console',
                             '1-latest',
                             'en-US'))
products.append(product_info('red_hat_insights',
                             'Red Hat Insights',
                             '1-latest',
                             'en-US'))

# Convert list of product_info objects to list of dictionaries
products_dict_list = [product.to_dict() for product in products]

# Create a dictionary to hold the transformed data
transformed_data = {}

# Iterate over the data
for item in products_dict_list:
    # If the product is not already in the transformed data, add it
    if item['product'] not in transformed_data:
        transformed_data[item['product']] = {
            'product': item['product'],
            'product_full_name': item['product_full_name'],
            'version': [],
            'language': item['language']
        }
    # Add the version to the version array for the product
    transformed_data[item['product']]['version'].append(item['version'])

# Convert the transformed data back into a list
transformed_data = list(transformed_data.values())

# Sort the transformed data by 'product_full_name'
transformed_data = sorted(transformed_data, key=lambda x: x['product_full_name'])

# Save the transformed data back to the file
with open('collections.json.env', 'w') as f:
    json.dump(transformed_data, f, indent=4)