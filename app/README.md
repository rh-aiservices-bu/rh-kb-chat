# Application image

## Building

The npm build happens during the image build. To do it successfully, you may have to augment the limits on open files in your system. Ex:

`podman build --no-cache --ulimit nofile=10000:10000 -t rh-kb-chat:1.1.0 .`

## Deployment

The application supports browser voice input, image upload, and camera capture.
Voice transcription and answer playback use browser APIs. Images are sent only
to models configured with `"supports_vision": true`; text retrieval and source
citations continue to use the existing Milvus collections.

Each LLM endpoint must expose an OpenAI-compatible `/v1/chat/completions` API.
Set `supports_vision` to `true` only when the deployed model and serving runtime
accept OpenAI `image_url` message content. Images are limited to JPEG, PNG, or
WebP files no larger than 5 MB.

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
