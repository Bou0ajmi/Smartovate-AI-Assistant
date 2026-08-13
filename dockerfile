FROM public.ecr.aws/lambda/python:3.12

COPY requirements.txt ${LAMBDA_TASK_ROOT}/
RUN pip install --no-cache-dir --default-timeout=120 --retries 10 -r requirements.txt

# App code
COPY src/ ${LAMBDA_TASK_ROOT}/src/
COPY config.py ${LAMBDA_TASK_ROOT}/
COPY handler.py ${LAMBDA_TASK_ROOT}/

# Vector store data
COPY MyVectorStore/ ${LAMBDA_TASK_ROOT}/MyVectorStore/

CMD ["handler.handler"]