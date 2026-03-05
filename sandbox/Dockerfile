FROM python:3.11-slim

WORKDIR /code

COPY . .

RUN if [ -f requirements.txt ]; then \
    pip install -r requirements.txt; \
    fi

RUN pip install pytest

CMD ["pytest", ".", "-v"]