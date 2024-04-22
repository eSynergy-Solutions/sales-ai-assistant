FROM ubuntu:20.04

# Install runtime dependencies and Python 3.11
RUN apt-get update && apt-get install -y \
    software-properties-common \
 && add-apt-repository ppa:deadsnakes/ppa \
 && apt-get update \
 && apt-get install -y \
    python3.11 \
    python3.11-dev \
    python3.11-venv \
    python3-pip \
    libxml2-dev \
    libxslt1-dev \
    antiword \
    unrtf \
    poppler-utils \
    pstotext \
    tesseract-ocr \
    flac \
    ffmpeg \
    lame \
    libmad0 \
    libsox-fmt-mp3 \
    sox \
    libjpeg-dev \
    swig \
    libpulse-dev \
    curl \
    libreoffice \
    pandoc \
 && rm -rf /var/lib/apt/lists/* \
 && curl -sS https://bootstrap.pypa.io/get-pip.py | python3.11 \
 && ln -sf /usr/bin/python3.11 /usr/bin/python3 \
 && ln -sf /usr/bin/pip3.11 /usr/bin/pip3 \
 && python3 -m pip install --upgrade pip

COPY ./requirements.txt .
RUN pip3 install --no-cache-dir -r requirements.txt

COPY ./*.py .
COPY ./*.sh .

ENV NAME sharepoint_bulk_ingestion
RUN chmod +x run.sh
CMD ["./run.sh"]
