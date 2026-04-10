"""
Medical Triage Environment — Inference Script
=============================================

Runs an LLM agent through the medical triage environment, emitting
structured stdout logs in the exact [START] / [STEP] / [END] format
required by the hackathon evaluation system.

Environment variables required:
  API_BASE_URL  — e.g. https://api.openai.com/v1
  MODEL_NAME    — e.g. gpt-4o-mini
  HF_TOKEN      — Hugging Face token (used to reach the deployed Space)

Usage:
  python inference.py --env-url https://<your-space>.hf.space
  python inference.py --env-url http://localhost:7860
"""

import os
import sys
import json
import time
import argparse
import traceback

from openai import OpenAI

# ── Import environment client ──────────────────────────────────────────────────
try:
    sys.path.insert(0, os.path.dirname(__file__))
    from models import TriageAction
    from client import MedicalTriageEnv
except ImportError:
    raise RuntimeError(
        "Could not import environment modules. "
        "Ensure inference.py is run from the medical_triage_env root directory."
    )

# ── Config ─────────────────────────────────────────────────────────────────────
API_BASE_URL = os.environ.get("API_BASE_URL", "https://api.openai.com/v1")
MODEL_NAME   = os.environ.get("MODEL_NAME", "gpt-4o-mini")
HF_TOKEN     = os.environ.get("HF_TOKEN", "")

# Tasks to evaluate — one episode per task
TASK_IDS = ["task1", "task2", "task3"]

SYSTEM_PROMPT = """You are an expert Emergency Room triage nurse with 10+ years of experience.
You must assess each patient and respond ONLY with a valid JSON object — no prose, no markdown.

JSON schema:
{
  "patient_id": "<copy from observation>",
  "triage_level": "<1|2|3|4|5>",
  "reasoning": "<concise clinical reasoning, ≤ 150 words>",
  "order_tests": ["<test1>", "<test2>", ...],
  "disposition": "<resuscitation_bay|trauma_bay|fast_track|waiting_room|discharge>"
}

ESI Triage Levels:
  1 — Immediate life threat (STEMI, airway compromise, cardiac arrest)
  2 — High risk / severe pain / altered mental status
  3 — Multiple resources needed, stable vitals
  4 — One resource needed
  5 — No resources needed

Always ground your reasoning in the vitals, chief complaint, and history provided."""


def build_user_message(obs) -> str:
    vitals_str = "\n".join(f"  {k}: {v}" for k, v in obs.vitals.items())
    return (
        f"PATIENT: {obs.patient_id}\n"
        f"CHIEF COMPLAINT: {obs.chief_complaint}\n\n"
        f"VITALS:\n{vitals_str}\n\n"
        f"HISTORY: {obs.history}\n\n"
        f"TASK: {obs.task_description}\n\n"
        f"Respond with a JSON object only."
    )


def call_llm(client: OpenAI, user_message: str) -> dict:
    """Call LLM and parse JSON response."""
    response = client.chat.completions.create(
        model=MODEL_NAME,
        max_tokens=512,
        temperature=0.2,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_message},
        ],
    )
    raw = response.choices[0].message.content.strip()
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
    return json.loads(raw.strip())


# ── Logging (exact format required by validator) ───────────────────────────────

def log_start(task_id: str):
    print(f"[START] task={task_id}", flush=True)


def log_step(step: int, task_id: str, reward: float, is_correct: bool, done: bool):
    print(
        f"[STEP] step={step} task={task_id} reward={reward:.4f} "
        f"is_correct={is_correct} done={done}",
        flush=True,
    )


def log_end(task_id: str, steps: int, score: float):
    print(f"[END] task={task_id} score={score:.4f} steps={steps}", flush=True)


# ── Episode runner (one task per episode) ──────────────────────────────────────

def run_task_episode(env_url: str, task_id: str, llm_client: OpenAI) -> dict:
    """Run one episode for a specific task and return its score."""
    with MedicalTriageEnv(base_url=env_url).sync() as env:
        obs = env.reset(task_id=task_id)

        log_start(task_id=task_id)

        step = 0
        total_reward = 0.0
        done = False

        while not done:
            user_msg = build_user_message(obs)
            try:
                llm_output = call_llm(llm_client, user_msg)
            except Exception as e:
                llm_output = {
                    "patient_id": obs.patient_id,
                    "triage_level": "3",
                    "reasoning": f"Parse error: {e}",
                    "order_tests": [],
                    "disposition": "waiting_room",
                }

            action = TriageAction(
                patient_id=llm_output.get("patient_id", obs.patient_id),
                triage_level=str(llm_output.get("triage_level", "3")),
                reasoning=llm_output.get("reasoning", ""),
                order_tests=llm_output.get("order_tests", []),
                disposition=llm_output.get("disposition", "waiting_room"),
            )

            result = env.step(action)
            # Clamp reward strictly within (0, 1) — never 0.0 or 1.0
            raw_reward = float(result.reward) if result.reward is not None else 0.5
            reward = max(0.001, min(0.999, raw_reward))
            obs = result.observation
            total_reward += reward
            step += 1
            done = result.done or obs.episode_done

            log_step(step=step, task_id=task_id, reward=reward,
                     is_correct=obs.is_correct, done=done)

        score = max(0.001, min(0.999, total_reward / max(step, 1)))
        log_end(task_id=task_id, steps=step, score=score)

        return {"task_id": task_id, "score": score, "steps": step}


def main():
    parser = argparse.ArgumentParser(description="Medical Triage Inference Script")
    parser.add_argument(
        "--env-url",
        default=os.environ.get("ENV_URL", "http://localhost:7860"),
        help="Base URL of the deployed environment (default: http://localhost:7860)",
    )
    args = parser.parse_args()

    llm_client = OpenAI(
        base_url=API_BASE_URL,
        api_key=HF_TOKEN or "dummy-key",
    )

    all_scores = []

    for task_id in TASK_IDS:
        try:
            result = run_task_episode(args.env_url, task_id, llm_client)
            all_scores.append(result["score"])
        except Exception:
            traceback.print_exc()
            sys.exit(1)

    print(f"\nAll task scores: {all_scores}", flush=True)
    print(f"Mean score: {sum(all_scores)/max(len(all_scores),1):.4f}", flush=True)


if __name__ == "__main__":
    main()
