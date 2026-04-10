"""
Medical Triage Environment — HTTP Client
=========================================
Provides MedicalTriageEnv, an HTTP client wrapper used by inference.py to
communicate with the deployed FastAPI environment server.

Usage (from inference.py):
    with MedicalTriageEnv(base_url=env_url).sync() as env:
        obs = env.reset()
        result = env.step(action)
        reward = result.reward
        obs = result.observation
        done = result.done
"""

from contextlib import contextmanager
from dataclasses import dataclass, field
from typing import Dict, List, Optional

import requests

from models import TriageAction


@dataclass
class ObsData:
    """
    Plain observation container used internally by the client.
    Does NOT inherit from openenv's Observation to avoid __init__ conflicts.
    Exposes the same attributes that inference.py reads.
    """
    patient_id: str = ""
    chief_complaint: str = ""
    vitals: Dict[str, str] = field(default_factory=dict)
    history: str = ""
    task_description: str = ""
    feedback: str = ""
    is_correct: bool = False
    partial_score: float = 0.0
    episode_done: bool = False


@dataclass
class StepResult:
    """Returned by SyncEnvClient.step()."""
    observation: ObsData
    reward: float
    done: bool
    info: dict = field(default_factory=dict)


def _parse_observation(data: dict) -> ObsData:
    """Convert a raw server JSON dict into an ObsData instance."""
    return ObsData(
        patient_id=str(data.get("patient_id", "")),
        chief_complaint=str(data.get("chief_complaint", "")),
        vitals=data.get("vitals") or {},
        history=str(data.get("history", "")),
        task_description=str(data.get("task_description", "")),
        feedback=str(data.get("feedback", "")),
        is_correct=bool(data.get("is_correct", False)),
        partial_score=float(data.get("partial_score", 0.0)),
        episode_done=bool(data.get("episode_done", False)),
    )


class SyncEnvClient:
    """Synchronous HTTP client that talks to the FastAPI env server."""

    def __init__(self, base_url: str, timeout: float = 60.0):
        self._base_url = base_url.rstrip("/")
        self._timeout = timeout
        self._session = requests.Session()

    def reset(self, task_id: Optional[str] = None) -> ObsData:
        payload = {}
        if task_id:
            payload["task_id"] = task_id
        resp = self._session.post(
            f"{self._base_url}/reset",
            json=payload,
            timeout=self._timeout,
        )
        resp.raise_for_status()
        data = resp.json()
        if "error" in data:
            raise RuntimeError(f"Server error on /reset: {data['error']}")
        return _parse_observation(data)

    def step(self, action: TriageAction) -> StepResult:
        action_dict = {
            "patient_id": action.patient_id,
            "triage_level": action.triage_level,
            "reasoning": action.reasoning,
            "order_tests": action.order_tests,
            "disposition": action.disposition,
        }
        resp = self._session.post(
            f"{self._base_url}/step",
            json=action_dict,
            timeout=self._timeout,
        )
        resp.raise_for_status()
        data = resp.json()
        if "error" in data:
            raise RuntimeError(f"Server error on /step: {data['error']}")
        obs = _parse_observation(data)
        reward = float(data.get("partial_score", 0.0))
        done = obs.episode_done
        return StepResult(observation=obs, reward=reward, done=done)

    def close(self):
        self._session.close()

    def __enter__(self):
        return self

    def __exit__(self, *_):
        self.close()


class MedicalTriageEnv:
    """
    Factory / wrapper class.
    Call .sync() to get a context manager yielding a SyncEnvClient.

    Example:
        with MedicalTriageEnv(base_url="http://localhost:7860").sync() as env:
            obs = env.reset()
    """

    def __init__(self, base_url: str, timeout: float = 60.0):
        self._base_url = base_url
        self._timeout = timeout

    @contextmanager
    def sync(self):
        client = SyncEnvClient(base_url=self._base_url, timeout=self._timeout)
        try:
            yield client
        finally:
            client.close()
