FROM python:3.12-slim AS build
WORKDIR /src
COPY pyproject.toml ./
COPY src ./src
RUN pip install --no-cache-dir --prefix=/install .

FROM python:3.12-slim
RUN useradd --uid 10001 --no-create-home metrics
COPY --from=build /install /usr/local
USER 10001
EXPOSE 9109
ENTRYPOINT ["delivery-metrics"]
