# builder stage; uses own file system
FROM python:3.12-slim AS builder
# mkdir -p /app && cd /effective_mobile_test_app (-p creates /effective_mobile_test_app if not exists)
WORKDIR /effective_mobile_test_app
# copy pyproject.toml poetry.lock from host to builder ./
COPY pyproject.toml poetry.lock ./
RUN pip install --upgrade pip
# make sure poetry version mathes poetry.lock version
RUN pip install --no-cache-dir poetry==2.2.1
# don't create virtual env
RUN poetry config virtualenvs.create false
# install dependecies from poetry.lock without dev and self package 
RUN poetry install --without=dev --no-root

# final stage: image build
FROM python:3.12-slim
WORKDIR /effective_mobile_test_app
# copy packages from builder to image
COPY --from=builder /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin
# copy from host to image
COPY ./app ./app
COPY ./entrypoint.py ./entrypoint.py
COPY ./alembic.ini ./alembic.ini
