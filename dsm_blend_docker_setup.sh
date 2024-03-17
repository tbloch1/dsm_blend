# User Variables
    CONTAINER_NAME=blender_dem
    VOLUME_NAME=local_vol
    LOCAL_DIR=$(PWD)/
    LOCAL_DIR_MOUNT_NAME=dsm_blend
    # OTHER_DIR1="path"
    # OTHER_DIR1_MOUNT_NAME=name

    PULL_GITHUB=no # yes/no
    GIT_USERNAME=USER
    GIT_PASSWORD=PWRD
    GIT_PROJECT_URL=GITURL

# Fixed Variables
    # Defining the base image as the TensorFlow image.
    BASE_IMAGE=tensorflow/tensorflow
    
    # Identifying the most recent tensorflow image with a version
    # number that supports GPU and Jupyter.
    IMAGE_VERSION=2.9.1-gpu-jupyter

    # Retag the image to something easier to use.
    NEW_IMAGE_NAME=tensorflow

# Pulling the docker image we want:
    
    # Pulling the docker image we want.
    docker pull $BASE_IMAGE:$IMAGE_VERSION

    # Digest to identify the image later:
    # Short - 6345c1f2eaaf
    # Long  - sha256:6345c1f2eaaf7b8efc9b8ec7f62869e6490db80e07ae5b856d5c16b48146daae

    # Retag the image to something easier to use.
    docker image tag $BASE_IMAGE:$IMAGE_VERSION $NEW_IMAGE_NAME:$IMAGE_VERSION
    docker rmi $BASE_IMAGE:$IMAGE_VERSION

# Running the image and mounting the volumes and external folders.

    docker run \
    -d \
    --gpus all \
    -v $VOLUME_NAME:/root/$VOLUME_NAME \
    --mount type=bind,source="$LOCAL_DIR",destination=/root/$LOCAL_DIR_MOUNT_NAME \
    --name $CONTAINER_NAME $NEW_IMAGE_NAME:$IMAGE_VERSION

# Pulling git setup files
    if [ $PULL_GITHUB = "yes" ]
    then
        docker exec -it $CONTAINER_NAME bash -c "
        cd /root/$VOLUME_NAME && \
        git clone $GIT_PROJECT_URL
        "
    fi

# Installing python 3.10
    docker exec -it $CONTAINER_NAME bash -c "
    apt-get update \
    && apt-get install -y software-properties-common \
    && add-apt-repository -y ppa:deadsnakes/ppa \
    && apt-get update \
    && apt install -y python3.10
    "

# Force upgrade to python3.10
    docker exec -it $CONTAINER_NAME bash -c "
    update-alternatives --install /usr/bin/python3 python3 /usr/bin/python3.8 1 \
    && update-alternatives --install /usr/bin/python3 python3 /usr/bin/python3.10 2 \
    && update-alternatives --set python3 /usr/bin/python3.10 \
    && apt-get install -y python3.10-distutils \
    && curl -sS https://bootstrap.pypa.io/get-pip.py | python3.10
    "
    # && update-alternatives --config python3 \

# Installing packages
    docker exec -it $CONTAINER_NAME bash -c "
    pip install --upgrade pip \
    && pip install jupyter \
    && pip install -r /root/dsm_blend/reqs.txt \
    && apt install blender \
    && apt update \
    && apt install -y libsm6 \
    && apt install -y libxext6 \
    && pip install bpy    
    "

# Installing packages for RGB -> CMYK
    docker exec -it $CONTAINER_NAME bash -c "
    apt-get install imagemagick --fix-missing \
    && apt-get install ghostscript
    "