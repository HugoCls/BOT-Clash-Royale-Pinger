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

CMD ["python3", "bot.py"]