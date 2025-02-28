# Application image

## Building

The npm build happens during the image build. To do it successfully, you may have to augment the limits on open files in your system. Ex:

`podman build --no-cache --ulimit nofile=10000:10000 -t rh-kb-chat:1.1.0 .`

## Deployment

- Create a secret from `backend/config.json` file:

```bash
oc create secret generic kb-chatbot --from-file=backend/config.json
```

- Create the Deployment, Service and Route from their respective files in the `deployment` folder:

```bash
oc create -f deployment.yaml
oc create -f service.yaml
oc create -f route.yaml
```
