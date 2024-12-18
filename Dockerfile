# Declare build-time arguments
ARG TOKEN
ARG SERVER_ID
ARG CLAN_ID
ARG MIN_RATIO

FROM python:3.10-slim

WORKDIR /usr/src/app

COPY requirements.txt .

RUN pip install -r requirements.txt

RUN mkdir -p data

COPY . .

# Pass the arguments as environment variables inside the container (optional)
ENV TOKEN=${TOKEN}
ENV SERVER_ID=${SERVER_ID}
ENV CLAN_ID=${CLAN_ID}
ENV MIN_RATIO=${MIN_RATIO}

CMD ["python3", "bot.py"]