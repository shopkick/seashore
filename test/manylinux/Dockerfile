FROM gitlab.internal.shopkick.com:5050/open-source/manylinux
COPY repo /mnt/repo
RUN /opt/python/cp27-cp27mu/bin/pip install tox
RUN cd /mnt/repo && /opt/python/cp27-cp27mu/bin/tox -e py27-unit
