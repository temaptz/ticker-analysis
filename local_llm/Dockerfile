FROM python:3.12-slim as requirements

WORKDIR /app
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

COPY ./local_llm/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r requirements.txt


FROM requirements

COPY ./local_llm/llm.py /app/llm.py
COPY ./local_llm/dataset.csv /app/dataset.csv

CMD ["python", "llm.py"]
