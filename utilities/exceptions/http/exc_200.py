import fastapi


def http_200_resent_confirmation_code_details() -> str:
    return "Confirmation code resent"


async def http_exc_200_resent_confirmation_code() -> fastapi.Response:
    return fastapi.Response(
        status_code=fastapi.status.HTTP_400_BAD_REQUEST,
        content=http_200_resent_confirmation_code_details(),
    )


