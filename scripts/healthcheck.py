"""Probe readiness through HTTP without disabling production HTTPS protection."""
import http.client
import os

host = os.environ.get("HEALTHCHECK_HOST") or os.environ["ALLOWED_HOSTS"].split(",")[0].strip()
connection = http.client.HTTPConnection("127.0.0.1", int(os.environ.get("PORT", "8000")), timeout=4)
connection.request("GET", "/health/", headers={"Host": host, "X-Forwarded-Proto": "https"})
response = connection.getresponse()
raise SystemExit(0 if response.status == 200 else 1)
