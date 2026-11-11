FROM python:3.12-slim

COPY dist/*.whl /wheels/
RUN python -m pip install --no-cache-dir /wheels/*.whl

COPY tests/ /tests/
WORKDIR /work
CMD ["python", "-m", "unittest", "discover", "-s", "/tests"]
