FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    build-essential \
    portaudio19-dev \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY meet_transcriber/ ./meet_transcriber/
COPY RealtimeTTS/ ./RealtimeTTS/
COPY setup.py .
COPY README.md .
COPY MANIFEST.in .

RUN pip install -e ".[meet]"

ENV MEET_TRANSCRIBER_HOST=0.0.0.0
ENV MEET_TRANSCRIBER_PORT=8765
ENV MEET_TRANSCRIBER_LOG_LEVEL=INFO

EXPOSE 8765

CMD ["python", "-m", "meet_transcriber.main"]
