"""
Module defining a Falcon resource to provide login session initiation

Copyright (C) 2018 ERT Inc.
"""
import falcon

from api.auth import auth
from api.auth.external import KeycloakBackend

route = "login"

class LoginInvalid(ValueError):
    # raised when login credentials are not valid
    pass

class Login():
    """
    Falcon resource object providing API login session initiation
    """
    allowed_methods = ['POST']

    def on_get(self, request, resp):
        """
        direct user to POST the login details
        """
        allowed = self.allowed_methods
        msg = "GET method not allowed, Please POST credentials to 'login'"
        raise falcon.HTTPMethodNotAllowed(allowed, description = msg)

    def on_post(self, request, resp):
        """
        Issue authenticated session cookie, if request credentials are valid
        """
        username_post_field, password_post_field = 'username', 'password'
        # fetch POSTed auth credentials
        try:
            request_username = request.params[username_post_field]
        except KeyError:
            raise falcon.HTTPMissingParam(username_post_field)

        try:
            request_password = request.params[password_post_field]
        except KeyError:
            raise falcon.HTTPMissingParam(password_post_field)

        # Authenticate
        try:
            user_id, decoded_token = KeycloakBackend.authenticate(
                request_username, request_password)
            if user_id is None:
                raise LoginInvalid('Bad Login!')
            #Indicate user is logged in
            auth.create_login_session(user_id, request, oidc=decoded_token)
        except LoginInvalid as e:
            title = 'Unauthorized'
            description = 'Please check the supplied username or password.'
            raise falcon.HTTPUnauthorized(title, description) from e
