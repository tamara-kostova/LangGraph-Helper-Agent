from fastapi import Request

from app.agent import HelperAgent


def get_helper_agent(request: Request) -> HelperAgent:
    return request.app.state.helper_agent  # type: ignore
