FROM python:3.11.2 AS backend

RUN apt-get update && apt-get install -y \
   libgdal-dev

ENV VIRTUAL_ENV=/opt/venv
ADD https://github.com/astral-sh/uv/releases/download/0.2.6/uv-installer.sh /install.sh
RUN chmod -R 655 /install.sh && /install.sh && rm /install.sh

COPY server server
COPY neptyne_kernel neptyne_kernel
COPY testing testing
COPY release_notes.md release_notes.md

ENV VIRTUAL_ENV=/opt/venv
COPY requirements.txt ./
RUN /root/.cargo/bin/uv venv ${VIRTUAL_ENV}
RUN /root/.cargo/bin/uv pip install --no-cache -r requirements.txt
RUN /root/.cargo/bin/uv pip uninstall -y json-fix || true

FROM node:16 AS frontend
WORKDIR /app
COPY frontend/package.json frontend/yarn.lock ./frontend/
RUN cd frontend && yarn install
COPY frontend ./frontend
RUN cd frontend && yarn build

FROM backend
COPY --from=frontend /app/frontend/build /frontend/build

EXPOSE 8877/tcp
ENV PATH="/opt/venv/bin:$PATH"
ENV PYTHONPATH="/"
ENV PYTHONUNBUFFERED=1

CMD [ "python", "server/application.py", "--sqlite-db", "/db/sqlite.db" ]
