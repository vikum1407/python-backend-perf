import docker
import requests
import time
import subprocess
import json
import logging

logging.basicConfig(
    filename="logging_file.log",
    level=logging.INFO,
    format='%(asctime)s-%(levelname)s-%(message)s'
)

def config_file_load(filename="config.json"):
    try:
        with open(filename, "r") as config_file:
            return json.load(config_file)
    except FileNotFoundError:
        print(f"")
        return None


def docker_pull(image_name):
    client = docker.from_env()
    try:
        client.images.pull(image_name)
        return True
    except docker.errors.ImageNotFound:
        print(f"Image '{image_name}' not found.")
    except docker.errors.APIError as e:
        print(f"Error pulling image '{image_name}': {e}")

    return False


def docker_run(image_name, container_name, ports=None):
    client = docker.from_env()
    try:
        container = client.containers.run(
            image=image_name,
            name=container_name,
            detach=True,
            ports=ports
        )
        return container.id
    except docker.errors.ImageNotFound:
        print(f"Image '{image_name}' not found.")
    except docker.errors.APIError as e:
        print(f"Error running container from image '{image_name}': {e}")

    return None

def is_container_running(container_name):
    try:
        # Replace 'http://localhost:8081' with the appropriate URL for your container's test endpoint.
        response = requests.get(f'http://localhost:{container_name}', timeout=5)
        #print(response.content)
        return response.status_code == 200
    except requests.exceptions.RequestException:
        return False


def delete_container(container_name):
    try:
        # Use subprocess to run the 'pumba' command
        command = [
            'docker', 'run', '-v', '/var/run/docker.sock:/var/run/docker.sock',
            '--rm', 'gaiaadm/pumba', 'rm', container_name
        ]
        subprocess.run(command, check=True)
        return True
    except subprocess.CalledProcessError:
        return False


config = config_file_load()
if not config:
    exit(1)
if __name__ == "__main__":
    image_name = config["image_name"]
    containers = config["containers"]
    docker_timeout = config["docker_timeout"]

    if docker_pull(image_name):
        for container_name, ports in containers:
            container_id = docker_run(image_name, container_name, ports)
            if container_id:
                print(
                    f"Container '{container_name}' (ID: {container_id}) is running on port {list(ports.values())[0]}.")
                time.sleep(20)  # Allow some time for the container to start

                if is_container_running(list(ports.values())[0]):
                    print(f"Container '{container_name}' is responding.")
                else:
                    print(f"Container '{container_name}' is not responding.")
            else:
                print(f"Container '{container_name}' run failed.")
        #time.sleep(5)
        if delete_container("lio1"):
            print(f"Container 'lio1' has been deleted.")
        else:
            print(f"Failed to delete container 'lio1'.")

        time.sleep(10)
        if is_container_running("lio1"):
            print(f"Container 'lio1' is responding.")
        else:
            print(f"Container 'lio1' is not responding.")
    else:
        print(f"Image pull for '{image_name}' failed.")
