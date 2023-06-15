FROM python:3.7-alpine

RUN apk add --no-cache gcc musl-dev libffi-dev linux-headers curl mongodb-tools
WORKDIR /opt/app

COPY . .

RUN --mount=type=secret,id=my_env source /run/secrets/my_env

RUN pip install --no-cache-dir -r requirements.txt

# Copy a custom configuration script
COPY mongo-setup.sh /docker-entrypoint-initdb.d/setup.sh

# Make the script executable
RUN chmod +x /docker-entrypoint-initdb.d/setup.sh

EXPOSE 5000

CMD ["python3", "-m", "flask", "run", "--host=0.0.0.0"]

