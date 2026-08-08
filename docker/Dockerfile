FROM python:3.12-slim

WORKDIR /app
COPY pyproject.toml README.md LICENSE NOTICE ./
COPY src ./src
RUN pip install --no-cache-dir .

ENTRYPOINT ["postex"]
CMD ["--help"]

# Office rendering is intentionally absent from the skeleton image.
# Add LibreOffice only in a separately reviewed renderer image.

