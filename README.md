# Number Verification App

## Overview

This repository contains a **Number Verification App**, which utilizes **Nokia Network as Code APIs** for verifying numbers. The application can be run simply in a **Python environment** or deployed using **Docker and Kubernetes**.

The app uses the 3 following Nokia NaC APIs:

- [NaC Authorization Server](https://dashboard.networkascode.nokia.io/network-as-code-network-as-code-default/api/nac-authorization-server)
- [Well-known metadata](https://dashboard.networkascode.nokia.io/network-as-code-network-as-code-default/api/well-known-metadata)
- [Number Verification](https://dashboard.networkascode.nokia.io/network-as-code-network-as-code-default/api/number-verification)

Note: The used API key in the backend application (given in env / k8s secret) must be corresponding to a API organization that is subscribed to the previous APIs.

All Nokia NaC APIs are listed on the API hub: https://dashboard.networkascode.nokia.io/hub

## Usage Options

Note: To run the app, the environment variables must be set properly in each case. If it is run in Kubernetes, then the values file can be configured easily for Helm install.

### 1. Running in Python

You can run the application directly in a Python environment:

1. Install the required dependencies:

`pip install -r requirements.txt`

2. Set the necessary environment variables. Detailed at #Configuration later.

3. Start the application:

`python scripts/main.py`

### 2. Running with Docker

The app can be containerized using Docker:

1. Build the Docker image:

`docker build -t number-verification-app .`

2. Run the container:

`docker run -p 8080:8080 number-verification-app`


### 3. Deploying on Kubernetes with Helm
For a Kubernetes deployment, you can use **Helm** to install the application:

1. Build and push the Docker image to a repository (e.g., Docker Hub, AWS ECR, or GCR):

```
// Build if not previously done

docker tag number-verification-backend-app <your-repository>/number-verification-backend-app:latest

docker push <your-repository>/number-verification-backend-app:latest
```

2. Package the Helm chart:

```helm package helm```


This will create a `.tgz` Helm package file that can be used for installation.

3. Prepare the values file:

Important configuration values are as follows:

```
global:
  registry: #REGISTRY_URL#

image:
  name: #IMAGE_NAME#
  tag: #IMAGE_TAG#
  pullPolicy: IfNotPresent

ingress:
  url: # Ingress URL of backend app where it is accessible for users.

apiSecretRef: rapidapi-credentials # A kubernetes secret that is installed in the same namespace as the deployment and contains API key as: API_KEY: <base64-encoded-key>.

allowedPhoneNumbers: # The phone numbers that are allowed to be used. Using other numbers return error.
  - "+36373334444"
  - "+36374443333"
```

4. Install the Helm chart:

```helm install number-verification-backend-app -f values.yaml ./number-verification-backend-app-helm-chart.tgz```

## Configuration

This app requires the following environment variables to be set:

| Environment variable | Value |
| :------------------- | :---- |
| `ALLOWED_PHONE_NUMBERS` | The phone numbers allowed to be queried. Space separated list of phone numbers. Optional. |
| `API_KEY` | Your API key to access Network-as-Code services. |
| `HTTP_CLIENT_PROXY` | Depending on your environment you might need a web proxy to access Network-as-Code on the internet. Optional. |
| `INGRESS_URL` | The URL where the app is reachable. The main endpoint of your server. |

A phone number can be just any number. The what allowed numbers mean?
When you have a web service, then you must have some security measures in place to avoid exploiting your service.
For example, you may limit the number of queries from a particular source.
If you are performing some demonstrations, you may want to use the phone number as a weak password
to restrict the use and detect illegitim use of the exposed service.
