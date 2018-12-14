
class ResponseException(Exception):
    def __init__(self, code, description=""):
        super().__init__(description)
        self.code = code
        self.description = description

class BadRequestException(ResponseException):
    def __init__(self, description="Bad request format!"):
        super().__init__(400, description)

class UnauthorizedException(ResponseException):
    def __init__(self, description="Unauthorized access!"):
        super().__init__(401, description)
        self.authentication_header = {'WWW-Authenticate': 'Basic'}

class NotFoundException(ResponseException):
    def __init__(self, description="Resource not found!"):
        super().__init__(404, description)

class ConflictException(ResponseException):
    def __init__(self, description="Resource conflict!"):
        super().__init__(409, description)

class InternalErrorException(ResponseException):
        def __init__(self, description="Internal server error!"):
            super().__init__(501, description)