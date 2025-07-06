# Use AWS Lambda Python base image
FROM public.ecr.aws/lambda/python:3.10

# Set work directory
WORKDIR ${LAMBDA_TASK_ROOT}

# Copy requirements first for better caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Set the Lambda handler
CMD ["lambda_function.lambda_handler"] 