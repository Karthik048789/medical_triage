const BASE_URL = "http://localhost:7860";

export async function getHealth() {
  const res = await fetch(`${BASE_URL}/health`);
  return res.json();
}

export async function getTasks() {
  const res = await fetch(`${BASE_URL}/tasks`);
  return res.json();
}

export async function getState() {
  const res = await fetch(`${BASE_URL}/state`);
  return res.json();
}

export async function resetEnv(taskId = null) {
  const body = taskId ? { task_id: taskId } : {};
  const res = await fetch(`${BASE_URL}/reset`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  return res.json();
}

export async function stepEnv(action) {
  const res = await fetch(`${BASE_URL}/step`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(action),
  });
  return res.json();
}
