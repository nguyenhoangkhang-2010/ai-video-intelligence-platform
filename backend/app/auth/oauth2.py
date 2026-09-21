from fastapi.security import HTTPBearer


# auto_error=False so a MISSING token falls through to
# get_current_user's own check, which raises a consistent 401 (the
# default auto_error=True behavior raises 403 for a missing header,
# clashing with the 401 every other auth failure in this app returns).
oauth2_scheme = HTTPBearer(auto_error=False)