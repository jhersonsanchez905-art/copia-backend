"""
tests/security/locustfile.py
Stress tests for Majesa Backend API.
Tests rate limiting, authentication and critical endpoints.
Author: charlykj
"""
from locust import HttpUser, task, between


class MajesaUser(HttpUser):
    wait_time = between(1, 3)
    host = "http://127.0.0.1:8000"

    @task(3)
    def listar_productos(self):
        self.client.get("/api/v1/productos")

    @task(2)
    def listar_mesas(self):
        self.client.get("/api/v1/mesas")

    @task(2)
    def listar_reservas(self):
        self.client.get("/api/v1/reservas")

    @task(1)
    def health_check(self):
        self.client.get("/health")


class MajesaDoSSimulation(HttpUser):
    """Simulates a DOS attack on critical endpoints."""
    wait_time = between(0.1, 0.5)
    host = "http://127.0.0.1:8000"

    @task
    def atacar_ventas(self):
        self.client.post(
            "/api/v1/ventas/",
            json={},
            headers={"Authorization": "Bearer token_falso"},
        )

    @task
    def atacar_auth(self):
        self.client.post(
            "/api/v1/auth/register",
            headers={"Authorization": "Bearer token_falso"},
        )