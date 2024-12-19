# Declare build-time arguments
ARG TOKEN
ARG SERVER_ID
ARG CLAN_ID
ARG MIN_RATIO

FROM python:3.10-slim

# Set working directory inside the container
WORKDIR /usr/src/app

# Copy requirements file to the container
COPY requirements.txt .

# Install the required Python dependencies
RUN pip install -r requirements.txt

# Create a data directory for persistent storage
RUN mkdir -p data

# Copy all files into the container
COPY . .

# Pass the build-time arguments as environment variables
ENV TOKEN=${TOKEN}
ENV SERVER_ID=${SERVER_ID}
ENV CLAN_ID=${CLAN_ID}
ENV MIN_RATIO=${MIN_RATIO}

# Install cron to manage scheduled tasks if necessary
RUN apt-get update && apt-get install -y cron

# Copy the crontab file into the container
COPY crontab /etc/cron.d/crontab

# Ensure the cron job has the right permissions
RUN chmod 0644 /etc/cron.d/crontab

# Install the cron job
RUN crontab /etc/cron.d/crontab

# Run both cron and your Python scripts (bot.py and api.py) in the same container
CMD cron && python3 bot.py & python3 api.py