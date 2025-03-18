FROM python:3.13.2-slim

WORKDIR /app

# Install Pipenv
RUN pip install --no-cache-dir pipenv

# Copy Pipfile and Pipfile.lock first
COPY Pipfile Pipfile.lock ./

# Install dependencies inside Docker
RUN pipenv install --deploy --system

# Copy project files
COPY . .

# Expose the Django port
# EXPOSE 8000

# Run app.py
CMD ["python3", "./app.py"]
