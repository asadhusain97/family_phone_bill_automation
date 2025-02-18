# Use an official Python 3 image as the base
FROM python:3

# Set the working directory to /app
WORKDIR /app

# Copy the requirements file into the working directory
COPY requirements.txt .

# Install the dependencies
RUN mkdir -p /attachments
RUN apt-get update && apt-get install -y tesseract-ocr
RUN apt-get update && apt-get install -y poppler-utils
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code into the working directory
COPY . .

# Expose the port that the application will run on
EXPOSE 80

# Run the command to start the application when the container launches
CMD ["python", "main.py"]