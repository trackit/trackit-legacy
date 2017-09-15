import config
import functools
import json
import requests
import traceback
from flask import jsonify

def with_g_recaptcha(field='g_recaptcha_response',
                     arg=0,
                     preserve_response=False,
                     success_on_error=True):
    """
    Check that the JSON body of the request contains a valid reCaptcha response
    token.
    
    `arg' describes which argument is the JSON body: if it is an integer, it is
    the nth positional argument, and if it is a string, it is the corresponding
    keyword argument.
    
    The `field' argument describes which top-level field of the body contains
    the response token.

    If `preserve_response' is True, the response token will not be removed from
    the request body before passing it to the wrappee.

    If there is an error during the validation process, `success_on_error'
    defines whether it should be considered a success or a failure. This is to
    avoid refusing access to users when our servers or Google are the cause of
    the failure.
    """
    def wrapper(f):
        @functools.wraps(f)
        def g_recaptcha_check(*args, **kwargs):
            # Check captcha response is present and is a string.
            try:
                if isinstance(arg, int):
                    body = args[arg]
                elif isinstance(arg, basestring):
                    body = kwargs[arg]
                g_recaptcha_response = body[field]
                if not preserve_response:
                    del body[field]
            except:
                return jsonify(
                    error="Captcha error: captcha response must be supplied."
                ), 400
            if not isinstance(g_recaptcha_response, basestring):
                return jsonify(
                    error="Captcha error: captcha response must be string."
                ), 400

            # Check the captcha response is valid.
            assert g_recaptcha_response is not None
            assert isinstance(g_recaptcha_response, basestring)
            verify_payload = {
                'secret': config.GOOGLE_RECAPTCHA_SECRET,
                'response': g_recaptcha_response,
            }
            r = requests.post('https://www.google.com/recaptcha/api/siteverify',
                data=verify_payload,
            )
            try:
                r_json = r.json()
                if r_json['success']:
                    # Actual success
                    success = True
                    error = False
                elif ('error-codes' in r_json
                      and len(r_json['error-codes']) == 1
                      and r_json['error-codes'][0] == 'invalid-input-response'):
                    # Actual failure from the user
                    success = False
                    error = False
                else:
                    # There was an error somewhere on our side of things.
                    success = success_on_error
                    error = True
                    print(
                        'reCaptcha: error verifying {}, API replied with {}.'
                        .format(
                            json.dumps(verify_payload),
                            json.dumps(r_json),
                        )
                    )
            except:
                traceback.print_exc()
                success = success_on_error

            # Call the wrappee, or not
            if success:
                return f(*args, **kwargs)
            elif error:
                return jsonify(
                    error="Captcha error: you failed validation due to a server"
                          " error.",
                ), 500
            else:
                return jsonify(
                    error="Captcha error: you failed validation."
                ), 403
        return g_recaptcha_check
    return wrapper
