# Production Deployment Guide

## 1. Containerized Deployment with Docker Compose

The platform is fully containerized with dedicated services for the FastAPI backend, React dashboard, PostgreSQL database, and Redis cache.

### Start All Services:
```bash
docker compose up --build -d
```

### Inspect Health:
```bash
docker compose ps
```

All services configure explicit Docker healthchecks:
- `backend`: `curl -f http://localhost:8000/health/ready`
- `postgres`: `pg_isready -U vision_user -d yolo_vision_db`
- `redis`: `redis-cli ping`

### Access Services:
- Web Dashboard: `http://localhost:5173`
- Backend API & OpenAPI Docs: `http://localhost:8000/docs`
- Prometheus Metrics: `http://localhost:8000/api/v1/metrics`

---

## 2. GPU Hardware Acceleration (NVIDIA CUDA)

To deploy on systems equipped with NVIDIA GPUs:

1. Install the [NVIDIA Container Toolkit](https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/latest/install-guide.html).
2. Configure `.env`:
   ```env
   DEVICE=cuda
   ```
3. Update `docker-compose.yml` for the backend service:
   ```yaml
   deploy:
     resources:
       reservations:
         devices:
           - driver: nvidia
             count: all
             capabilities: [gpu]
   ```
4. Verify CUDA is active by calling:
   ```bash
   curl http://localhost:8000/api/v1/system/status
   ```
   Should output `"active_device": "cuda:0"`.

---

## 3. Kubernetes Deployment Notes

The application adheres to cloud-native production standards:
- **Liveness Probe**: `GET /health/live`
- **Readiness Probe**: `GET /health/ready`
- **Observability**: Prometheus metrics at `/api/v1/metrics` with header `Accept: text/plain`.
- **Stateless Vision Processing**: Bounded frame buffers, clean temp file lifecycle, no memory leaks across stream disconnections.

