"""
Presentation Layer — Ingestion Bounded Context.

FastAPI app factory, DI wiring, middleware stack, exception handlers,
health endpoints, structured logging, and sync→async bridge.

This package provides the HTTP/REST foundation that all future endpoint
sprints (6.2+) build on. NO business endpoints — only the skeleton.

Public API
----------
>>> from ingestion.presentation import create_app
>>> app = create_app()
"""
