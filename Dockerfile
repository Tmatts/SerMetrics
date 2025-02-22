FROM python:3.12

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
EXPOSE 8000

# Run Django
CMD ["gunicorn", "myproject.wsgi:application", "--bind", "0.0.0.0:8000"]
