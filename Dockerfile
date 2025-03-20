FROM python:3.13.2-slim
WORKDIR /app
COPY meowmaker.py .
RUN echo "deb https://deb.debian.org/debian trixie main contrib" > /etc/apt/sources.list
RUN echo "" > /etc/apt/sources.list.d/debian.sources
RUN apt-get update && apt-get full-upgrade -y && apt-get clean && apt-get autoremove -y
RUN apt-get install -y git jq wget
RUN wget $(wget -q -O - https://api.github.com/repos/catppuccin/whiskers/releases/latest  |  jq -r '.assets[] | select(.name | contains ("linux")) | .browser_download_url') -O whiskers
RUN chmod +x ./whiskers
RUN git config --global --add safe.directory /github/workspace
RUN apt-get remove --purge -y jq wget
CMD ["python", "/app/meowmaker.py"]