import pulumi
from pulumi_docker import Image, DockerBuild, Container, ContainerPortArgs

config = pulumi.Config()
port = config.require_int("port")

stack = pulumi.get_stack()
image_name = "my-first-app"


# build our image!
image = Image(image_name,
              build=DockerBuild(context="app"),
              image_name=f"{image_name}:{stack}",
              skip_push=True)

container = Container('my-first-app',
                      image=image.base_image_name,
                      envs=[
                          f"LISTEN_PORT={port}"
                      ],
                      ports=[ContainerPortArgs(
                          internal=port,
                          external=port,
                      )])

pulumi.export("container_id", container.id)
