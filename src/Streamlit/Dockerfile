FROM python:3.11-slim


WORKDIR /app

ARG PIP_GIT_USER
ARG PIP_GIT_TOKEN
ARG PIP_GIT_BRANCH

ENV PIP_FULL_URL=git+https://${PIP_GIT_USER}:${PIP_GIT_TOKEN}@github.com/eSynergy-Solutions/OpenRag.git@${PIP_GIT_BRANCH}

RUN pip install ${PIP_FULL_URL}

COPY *.py /app
COPY requirements.txt /app

RUN pip install --no-cache-dir -r /app/requirements.txt

EXPOSE 8501

CMD ["streamlit", "run", "salesChat.py"]
