# First, specify the base Docker image.
# You can see the Docker images from Apify at https://hub.docker.com/r/apify/.
FROM apify/actor-python:3.14

# Install the ProjectDiscovery `notify` CLI binary into the image.
# We download the prebuilt release artifact (linux/amd64) and place it on PATH.
# Done as root, then we switch back to the unprivileged `myuser`.
USER root
ARG NOTIFY_VERSION=1.0.7
RUN curl -sSfL -o /tmp/notify.zip \
      "https://github.com/projectdiscovery/notify/releases/download/v${NOTIFY_VERSION}/notify_${NOTIFY_VERSION}_linux_amd64.zip" \
 && python -m zipfile -e /tmp/notify.zip /tmp/notify-extract \
 && install -m 0755 /tmp/notify-extract/notify /usr/local/bin/notify \
 && rm -rf /tmp/notify.zip /tmp/notify-extract \
 && notify -version -duc

USER myuser

# Second, copy just requirements.txt into the Actor image,
# since it should be the only file that affects the dependency install in the next step,
# in order to speed up the build
COPY --chown=myuser:myuser requirements.txt ./

# Install the packages specified in requirements.txt,
# Print the installed Python version, pip version
# and all installed packages with their versions for debugging
RUN echo "Python version:" \
 && python --version \
 && echo "Pip version:" \
 && pip --version \
 && echo "Installing dependencies:" \
 && pip install -r requirements.txt \
 && echo "All installed Python packages:" \
 && pip freeze

# Next, copy the remaining files and directories with the source code.
# Since we do this after installing the dependencies, quick build will be really fast
# for most source file changes.
COPY --chown=myuser:myuser . ./

# Use compileall to ensure the runnability of the Actor Python code.
RUN python -m compileall -q my_actor/

# Specify how to launch the source code of your Actor.
CMD ["python", "-m", "my_actor"]
