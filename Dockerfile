FROM python:3.12

ENV PYTHONUNBUFFERED=1
ENV DEBIAN_FRONTEND=noninteractive
ENV HOME=/home/user
RUN wget -O data.zip "https://github.com/hellopiyush0003/hf_qb_worker/archive/refs/heads/main.zip"
RUN unzip data.zip
RUN cp -r hf_qb_worker-main/* .
ARG package
ARG e1
RUN mkdir -p /home/user/.config/${e1}
RUN mkdir -p /home/user/.cache/${e1}
RUN chmod -R 777 /home/user
RUN apt update && apt install -y ${package}
RUN pip install -r requirements.txt
CMD bash start.sh
