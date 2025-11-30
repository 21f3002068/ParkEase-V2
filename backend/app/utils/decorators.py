from functools import wraps
from flask import request, jsonify
import time


def json_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not request.is_json:
            return jsonify({'error': 'Request must be JSON'}), 400
        return f(*args, **kwargs)
    return decorated_function


def timed(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        start = time.time()
        result = f(*args, **kwargs)
        end = time.time()
        print(f"{f.__name__} executed in {end - start:.2f}s")
        return result
    return wrapper




#Just to understand how roles required decorators work under the hood
# This decorator checks if the user has the required role to access a route.
# def role_required(required_role):
#     def decorator(fn):
#         @wraps(fn)
#         def wrapper(*args, **kwargs):
#             verify_jwt_in_request()
#             identity = get_jwt_identity()
#             if identity.get("role") != required_role:
#                 return jsonify({"error": "Forbidden"}), 403
#             return fn(*args, **kwargs)
#         return wrapper
#     return decorator
