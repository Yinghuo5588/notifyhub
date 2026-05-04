# ------------------------------------------------------------
# Frontend build stage
# ------------------------------------------------------------
FROM node:20-alpine AS frontend-build

WORKDIR /build/frontend

COPY frontend/package*.json ./
RUN npm ci

COPY frontend/ ./

# vite.config.ts outputs to ../app/static/frontend
RUN npm run build


# ------------------------------------------------------------
# Backend runtime stage
# ------------------------------------------------------------
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple/

COPY . .

# Copy Vue build output from frontend stage
COPY --from=frontend-build /build/app/static/frontend /app/static/frontend

RUN mkdir -p /app/data

EXPOSE 9800

CMD ["python", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "9800"]