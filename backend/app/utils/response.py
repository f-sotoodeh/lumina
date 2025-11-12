# backend/app/utils/response.py
from fastapi import Request
from typing import Any, Dict, List, TypeVar, Generic
from app.core.i18n import Translator
from app.schemas.response import APIResponse, MessageDict, ErrorItem

T = TypeVar("T")

def api_response(
    *,
    request: Request | None = None,
    data: Any = None,
    message_key: str | None = None,
    errors: List[dict] | None = None,
    success: bool = True,
    lang: str | None = None
) -> Dict[str, Any]:
    """
    Lumina API response
    Returns a dict that will be validated against APIResponse[T] model
    {
        "success": bool,
        "data": dict | list | null,
        "message": {"en": "...", "ru": "...", "hy": "..."},
        "errors": [{"field": "email", "message": {"en": "...", ...}}, ...]
    }
    """
    # 
    if lang:
        language = lang
    elif request:
        language = request.headers.get("accept-language", "en")[:2]
    else:
        language = "en"

    t = Translator.get(language)

    # message translations
    message = None
    if message_key:
        keys = message_key.split(".")
        msg = t
        for k in keys:
            msg = msg.get(k)
            if msg is None:
                msg = message_key  # fallback
                break
        if isinstance(msg, dict):
            message = msg
        else:
            message = {"en": msg, "ru": msg, "hy": msg}

    # error translations
    translated_errors = None
    if errors:
        translated_errors = []
        for err in errors:
            field = err.get("field")
            key = err.get("message")
            if isinstance(key, str) and "." in key:
                subkeys = key.split(".")
                err_msg = t
                for sk in subkeys:
                    err_msg = err_msg.get(sk)
                    if err_msg is None:
                        err_msg = key
                        break
                if isinstance(err_msg, dict):
                    translated_errors.append({"field": field, "message": err_msg})
                else:
                    translated_errors.append({"field": field, "message": {"en": err_msg}})
            else:
                msg_text = key if isinstance(key, dict) else {"en": key or ""}
                translated_errors.append({"field": field, "message": msg_text})

    return {
        "success": success,
        "data": data,
        "message": message,
        "errors": translated_errors
    }
