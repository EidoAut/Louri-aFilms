# ==========================================================================
"""exceptions.py
Provide exceptions operations for explicit application requests.

Developed by EIDO Automation
"""

# ==========================================================================
from __future__ import annotations


class ServiceError(Exception):
    """A safe, user-facing service failure; never includes credentials."""
