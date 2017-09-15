from flask import request, jsonify
from functools import wraps


def with_request_schema(schema, arg_name=None):
    def wrapper(view_fun):
        @wraps(view_fun)
        def schema_getter(*args, **kwargs):
            # TODO: update this to call request.is_json on next flask reelease
            if request.mimetype != 'application/json':
                return jsonify(error="Request must be JSON"), 415
            json_data = request.get_json(silent=True)
            if json_data is None:
                return jsonify(error="Bad JSON"), 400
            data, errors = schema.load(json_data)
            if errors:
                return jsonify(error="Validation error", fields=errors), 422
            if arg_name:
                kwargs[arg_name] = data
            else:
                args += (data,)
            return view_fun(*args, **kwargs)
        return schema_getter
    return wrapper
