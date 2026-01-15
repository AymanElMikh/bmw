"""
Routes Module
Centralizes route registration for all endpoints
"""
from fastapi import FastAPI

from .users import register_routes as register_user_routes
from .clauses import register_routes as register_clause_routes
from .jira import register_routes as register_jira_routes
from .invoices import register_routes as register_invoice_routes
from .audit import register_routes as register_audit_routes


__all__ = [
    'register_user_routes',
    'register_clause_routes',
    'register_jira_routes',
    'register_invoice_routes',
    'register_audit_routes'
]