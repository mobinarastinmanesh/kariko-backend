from rest_framework.views import exception_handler


def custom_exception_handler(exc, context):
    response = exception_handler(exc, context)
    if response is not None and isinstance(response.data, dict):
        # Flatten DRF's nested error dicts into a consistent shape
        response.data = {"errors": response.data}
    return response
