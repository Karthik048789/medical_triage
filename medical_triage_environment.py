import uuid

from models import TriageAction, TriageObservation, TriageState


TASKS = [
    {
        "id": "task1",
        "name": "Chest Pain Triage",
        "patient_id": "PT-001",
        "chief_complaint": "Chest pain",
        "vitals": {"HR": "110"},
        "history": "65-year-old male",
        "description": "Triage a 65-year-old male with chest pain.",
        "difficulty": "easy",
        "expected_triage_level": "1",
    },
    {
        "id": "task2",
        "name": "Fever and Cough Triage",
        "patient_id": "PT-002",
        "chief_complaint": "Fever and cough",
        "vitals": {"HR": "90"},
        "history": "30-year-old female",
        "description": "Triage a 30-year-old female with fever and cough.",
        "difficulty": "medium",
        "expected_triage_level": "3",
    },
    {
        "id": "task3",
        "name": "Minor Cut Triage",
        "patient_id": "PT-003",
        "chief_complaint": "Minor cut",
        "vitals": {"HR": "80"},
        "history": "20-year-old male",
        "description": "Triage a 20-year-old male with a minor cut.",
        "difficulty": "hard",
        "expected_triage_level": "5",
    },
]

TASKS_BY_ID = {task["id"]: task for task in TASKS}


def grade_action(task: dict, action: TriageAction) -> tuple[float, str, bool]:
    if action.triage_level == task["expected_triage_level"]:
        return 0.8, "Correct", True
    return 0.2, "Incorrect", False


class MedicalTriageEnvironment:
    SUPPORTS_CONCURRENT_SESSIONS = False

    def __init__(self) -> None:
        self._active_tasks = list(TASKS)
        self._state = self._build_state(self._active_tasks[0])

    def _build_state(self, task: dict) -> TriageState:
        return TriageState(
            current_task_index=0,
            current_task_id=task["id"],
            total_tasks=len(self._active_tasks),
            cumulative_reward=0.0,
            tasks_completed=0,
            difficulty=task["difficulty"],
            episode_id=str(uuid.uuid4()),
            step_count=0,
        )

    def _build_observation(
        self,
        task: dict,
        *,
        feedback: str,
        is_correct: bool,
        reward: float | None,
        partial_score: float,
        episode_done: bool,
    ) -> TriageObservation:
        return TriageObservation(
            patient_id=task["patient_id"],
            chief_complaint=task["chief_complaint"],
            vitals=task["vitals"],
            history=task["history"],
            task_id=task["id"],
            task_description=task["description"],
            feedback=feedback,
            is_correct=is_correct,
            reward=reward,
            done=episode_done,
            partial_score=partial_score,
            episode_done=episode_done,
        )

    def get_tasks(self) -> list[dict]:
        return [
            {
                "id": task["id"],
                "name": task["name"],
                "description": task["description"],
                "difficulty": task["difficulty"],
                "max_steps": 1,
                "grader": {
                    "module": "grader",
                    "function": "openenv_grade",
                },
            }
            for task in TASKS
        ]

    def reset(
        self,
        seed: int | None = None,
        episode_id: str | None = None,
        task_id: str | None = None,
        **_: object,
    ) -> TriageObservation:
        if task_id and task_id in TASKS_BY_ID:
            self._active_tasks = [TASKS_BY_ID[task_id]]
        else:
            self._active_tasks = list(TASKS)

        current_task = self._active_tasks[0]
        self._state = self._build_state(current_task)
        if episode_id:
            self._state.episode_id = episode_id

        return self._build_observation(
            current_task,
            feedback="Start",
            is_correct=False,
            reward=None,
            partial_score=0.5,
            episode_done=False,
        )

    async def reset_async(
        self,
        seed: int | None = None,
        episode_id: str | None = None,
        task_id: str | None = None,
        **kwargs: object,
    ) -> TriageObservation:
        return self.reset(
            seed=seed,
            episode_id=episode_id,
            task_id=task_id,
            **kwargs,
        )

    def step(
        self,
        action: TriageAction,
        timeout_s: float | None = None,
        **_: object,
    ) -> TriageObservation:
        task = self._active_tasks[self._state.current_task_index]
        reward, feedback, is_correct = grade_action(task, action)

        self._state.tasks_completed += 1
        self._state.step_count += 1
        self._state.cumulative_reward += reward
        self._state.current_task_index += 1

        done = self._state.current_task_index >= len(self._active_tasks)
        if done:
            self._state.current_task_id = "completed"
            return TriageObservation(
                patient_id="END",
                chief_complaint="",
                vitals={},
                history="",
                task_id="completed",
                task_description="Done",
                feedback=feedback,
                is_correct=is_correct,
                reward=reward,
                done=True,
                partial_score=reward,
                episode_done=True,
            )

        next_task = self._active_tasks[self._state.current_task_index]
        self._state.current_task_id = next_task["id"]
        self._state.difficulty = next_task["difficulty"]

        return self._build_observation(
            next_task,
            feedback=feedback,
            is_correct=is_correct,
            reward=reward,
            partial_score=reward,
            episode_done=False,
        )

    async def step_async(
        self,
        action: TriageAction,
        timeout_s: float | None = None,
        **kwargs: object,
    ) -> TriageObservation:
        return self.step(action, timeout_s=timeout_s, **kwargs)

    @property
    def state(self) -> TriageState:
        return self._state

    def get_metadata(self) -> dict[str, str]:
        return {
            "name": "Medical Triage OpenEnv",
            "description": "A medical triage environment with three sample tasks.",
            "version": "1.0.0",
        }

    def close(self) -> None:
        return None
