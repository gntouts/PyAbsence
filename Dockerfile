FROM python:3.11.2-alpine as base
WORKDIR /svc
RUN rm -rf /var/cache/apk/* && \
    rm -rf /tmp/*
RUN apk update
COPY requirements.txt .

RUN pip wheel -r requirements.txt --wheel-dir=/svc/wheels
FROM python:3.11.2-alpine
COPY --from=base /svc /svc
WORKDIR /svc
RUN pip install --upgrade pip && pip install --no-index --find-links=/svc/wheels -r requirements.txt
WORKDIR /src
COPY app.py .
CMD ["python", "/src/app.py"]