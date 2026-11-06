"""Shared synchronous Redis client; connections are opened on first use."""

import redis
from redis.backoff import NoBackoff
from redis.retry import Retry

from app.core.config import settings


redis_client = redis.Redis(
    host=settings.REDIS_HOST,
    port=settings.REDIS_PORT,
    decode_responses=True,
    socket_connect_timeout=2,
    socket_timeout=2,
    # Cache failures fall back to the database instead of retrying requests.
    retry=Retry(NoBackoff(), 0),
)
