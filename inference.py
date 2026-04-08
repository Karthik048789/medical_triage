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
from typing import Optional

from openai import OpenAI

# ── Import environment client ──────────────────────────────────────────────────
# Support both local (dev) and Docker (prod) import paths
try:
    sys.path.insert(0, os.path.dirname(__file__))
    from models import TriageAction, TriageObservation
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


def build_user_message(obs: TriageObservation) -> str:
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
    # Strip markdown fences if present
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
    return json.loads(raw.strip())


def log_start(episode_id: str, env_url: str, model: str):
    print(json.dumps({
        "event": "[START]",
        "episode_id": episode_id,
        "env_url": env_url,
        "model": model,
        "timestamp": time.time(),
    }), flush=True)


def log_step(
    step: int,
    task_id: str,
    action: dict,
    reward: float,
    is_correct: bool,
    feedback: str,
    done: bool,
):
    print(json.dumps({
        "event": "[STEP]",
        "step": step,
        "task_id": task_id,
        "action": action,
        "reward": reward,
        "is_correct": is_correct,
        "feedback": feedback,
        "done": done,
        "timestamp": time.time(),
    }), flush=True)


def log_end(
    episode_id: str,
    total_steps: int,
    total_reward: float,
    avg_reward: float,
    success: bool,
):
    print(json.dumps({
        "event": "[END]",
        "episode_id": episode_id,
        "total_steps": total_steps,
        "total_reward": total_reward,
        "avg_reward": avg_reward,
        "success": success,
        "timestamp": time.time(),
    }), flush=True)


def run_episode(env_url: str) -> dict:
    """Run one full episode and return summary metrics."""
    llm_client = OpenAI(
        base_url=API_BASE_URL,
        api_key=HF_TOKEN or "dummy-key",  # some providers use HF_TOKEN
    )

    results = {
        "episode_id": "",
        "steps": 0,
        "total_reward": 0.0,
        "scores": [],
        "success": False,
    }

    with MedicalTriageEnv(base_url=env_url).sync() as env:
        # Reset
        obs = env.reset()
        episode_id = f"ep_{int(time.time())}"
        results["episode_id"] = episode_id
        log_start(episode_id, env_url, MODEL_NAME)

        step = 0
        done = False

        while not done:
            # Build prompt and call LLM
            user_msg = build_user_message(obs)
            try:
                llm_output = call_llm(llm_client, user_msg)
            except (json.JSONDecodeError, Exception) as e:
                # Fallback action on LLM parse failure
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

            # Step
            result = env.step(action)
            reward = result.reward or 0.0
            obs = result.observation

            results["total_reward"] += reward
            results["scores"].append(reward)
            results["steps"] += 1
            step += 1
            done = result.done or obs.episode_done

            log_step(
                step=step,
                task_id=obs.patient_id if not done else f"task_{step}",
                action=llm_output,
                reward=reward,
                is_correct=obs.is_correct,
                feedback=obs.feedback,
                done=done,
            )

        results["success"] = results["total_reward"] / max(results["steps"], 1) >= 0.5
        avg = results["total_reward"] / max(results["steps"], 1)

        log_end(
            episode_id=episode_id,
            total_steps=results["steps"],
            total_reward=results["total_reward"],
            avg_reward=avg,
            success=results["success"],
        )

    return results


def main():
    parser = argparse.ArgumentParser(description="Medical Triage Inference Script")
    parser.add_argument(
        "--env-url",
        default=os.environ.get("ENV_URL", "http://localhost:7860"),
        help="Base URL of the deployed environment (default: http://localhost:7860)",
    )
    parser.add_argument(
        "--episodes",
        type=int,
        default=3,
        help="Number of episodes to run (default: 3)",
    )
    args = parser.parse_args()

    all_rewards = []
    all_scores = []

    for ep in range(args.episodes):
        print(f"\n{'='*60}", flush=True)
        print(f"Running episode {ep + 1}/{args.episodes} ...", flush=True)
        print(f"{'='*60}", flush=True)
        try:
            result = run_episode(args.env_url)
            all_rewards.append(result["total_reward"])
            all_scores.extend(result["scores"])
        except Exception:
            traceback.print_exc()
            sys.exit(1)

    # Final summary
    print("\n" + "="*60, flush=True)
    print("INFERENCE COMPLETE", flush=True)
    print(f"Episodes run : {args.episodes}", flush=True)
    print(f"Mean episode reward: {sum(all_rewards)/max(len(all_rewards),1):.4f}", flush=True)
    print(f"Mean step reward   : {sum(all_scores)/max(len(all_scores),1):.4f}", flush=True)
    print("="*60, flush=True)


if __name__ == "__main__":
    main()
