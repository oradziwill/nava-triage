from openai import OpenAI

from config import settings


def openai_client() -> OpenAI:
    return OpenAI(api_key=settings.OPENAI_API_KEY)
