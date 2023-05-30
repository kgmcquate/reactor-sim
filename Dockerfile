FROM ubuntu:20.04

ARG DEBIAN_FRONTEND=noninteractive
ENV TZ=America/New_York

ENV VIRTUAL_ENV=/opt/django_env
ENV PATH="$VIRTUAL_ENV/bin:$PATH"

RUN mkdir /var/www && cd /var/www && \
    apt -y update && \
    cd /var/www && \
    apt-get -y install python3.7 python3-pip python3-venv wget git && \
    python3 -m venv $VIRTUAL_ENV && \
    chmod +x $VIRTUAL_ENV/bin/activate && $VIRTUAL_ENV/bin/activate && \
    apt-get -y install m4 make gcc g++ findutils && \ 
    apt-get -y install libgsl-dev petsc-dev slepc-dev && \
    apt-get -y install gnuplot paraview pandoc && \
    git clone https://github.com/seamplex/milonga/ && \
    cd milonga && \
    ./autogen.sh && \
    ./configure && \
    make && make check && make install && \
    cd /var/www && \
    wget http://gmsh.info/bin/Linux/gmsh-4.5.1-Linux64.tgz && \
    tar -xvzf gmsh-4.5.1-Linux64.tgz 
    # && \    apt-get -y install apache2 libapache2-mod-wsgi-py3 libglu1 certbot

RUN cd /var/www && \
    pip install asgiref pytz sqlparse django numpy six python-dateutil pandas gmsh-api

RUN cd /var/www && \
    ls && \
    git clone https://github.com/kgmcquate/django_site.git && \
    pip install -r django_site/requirements.txt

