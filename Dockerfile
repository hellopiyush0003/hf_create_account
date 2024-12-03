FROM python:3.12

ENV PYTHONUNBUFFERED=1
ENV DEBIAN_FRONTEND=noninteractive
ENV HOME=/home/user
ARG package
ARG e1
ARG e2
ARG e3
RUN wget -O data.zip ${e1}
RUN unzip data.zip
RUN cp -r ${e2}/* .
RUN mkdir -p /home/user/.config/${e3}
RUN mkdir -p /home/user/.cache/${e3}
RUN chmod -R 777 /home/user
RUN apt update && apt install -y ${package}
RUN pip install -r requirements.txt
CMD bash start.sh
