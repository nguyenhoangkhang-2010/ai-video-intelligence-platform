"""
Intentionally empty.

Every error condition raised throughout this codebase already uses
FastAPI's own `HTTPException` directly and consistently (404 not
found, 401 unauthorized, 422 validation, etc. - see
app/services/*.py). A custom exception hierarchy was not introduced
here: doing so now would mean either leaving new exception classes
unused (nothing raises them) or rewriting every existing `raise
HTTPException(...)` call site across the codebase to adopt them -
a large, unjustified change for this phase.

This module exists as a named, obvious home for custom exception
classes if/when a real, non-HTTPException-shaped error case actually
needs one (e.g. a domain error that must be translated differently in
different callers). See app/exceptions/handlers.py for the one error
handler this phase did add (a generic-exception safety net).
"""
