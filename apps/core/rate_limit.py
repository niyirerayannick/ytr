"""Lightweight request throttling for anonymous public forms.

The default cache is process-local, so production deployments must also configure
shared-cache and reverse-proxy limits as described in docs/security.md.
"""
import hashlib

from django.core.cache import cache


def is_rate_limited(request, *, scope, limit, window_seconds):
    ip_address = request.META.get("REMOTE_ADDR", "unknown")
    digest = hashlib.sha256(f"{scope}:{ip_address}".encode()).hexdigest()
    key = f"ytr:rate-limit:{digest}"
    if cache.add(key, 1, timeout=window_seconds):
        return False
    try:
        current = cache.incr(key)
    except ValueError:
        cache.set(key, 1, timeout=window_seconds)
        return False
    return current > limit
