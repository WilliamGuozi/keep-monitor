FROM python:2.7.18-alpine
MAINTAINER "WilliamGuo <634206396@qq.com>"

RUN apk update && \
    apk add curl && \
    apk add openssh-client && \
    apk add jq

RUN pip install --upgrade pip && \
    pip install graphyte && \
    pip install requests && \
    pip install colorlog

WORKDIR /scripts/
ADD entrypoint.sh /bin/
RUN chmod +x /bin/entrypoint.sh

COPY keep-monitor.py /scripts
CMD ["/usr/local/bin/python", "/scripts/keep-monitor.py"]
ENTRYPOINT ["/bin/entrypoint.sh"]