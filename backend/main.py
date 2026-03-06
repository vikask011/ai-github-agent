from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from graph import graph
from state import AgentState
from dotenv import load_dotenv
import uuid
import sys
import io
import queue
import threading
import asyncio

load_dotenv()

app = FastAPI(title="AI GitHub Agent")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_methods=["*"],
    allow_headers=["*"],
)

log_queues: dict[str, queue.Queue] = {}
run_results: dict[str, dict] = {}
run_status: dict[str, str] = {}


class QueueWriter(io.TextIOBase):
    def __init__(self, q: queue.Queue):
        self.q = q

    def write(self, msg: str):
        if msg.strip():
            self.q.put(msg.strip())
        return len(msg)

    def flush(self):
        pass


class IssueRequest(BaseModel):
    issue_url: str

class ApproveRequest(BaseModel):
    thread_id: str


def get_initial_state(issue_url: str) -> AgentState:
    return {
        "issue_url": issue_url,
        "issue_title": "",
        "issue_body": "",
        "issue_labels": [],
        "issue_comments": [],
        "repo_name": "",
        "issue_number": 0,
        "keywords": [],
        "relevant_files": [],
        "file_contents": {},
        "root_cause": "",
        "files_to_edit": [],
        "fix_approach": "",
        "proposed_fix": {},
        "diff": {},
        "should_proceed": True,
        "skip_reason": "",
        "test_passed": False,
        "test_output": "",
        "retry_count": 0,
        "pr_url": "",
        "branch_name": ""
    }


def run_agent_in_background(thread_id: str, issue_url: str):
    q = log_queues[thread_id]
    config = {"configurable": {"thread_id": thread_id}}
    old_stdout = sys.stdout
    sys.stdout = QueueWriter(q)

    try:
        run_status[thread_id] = "running"
        state = get_initial_state(issue_url)
        result = graph.invoke(state, config)

        if not result.get("should_proceed", True):
            run_results[thread_id] = {
                "status": "already_fixed",
                "thread_id": thread_id,
                "data": {
                    "title": result["issue_title"],
                    "reason": result["skip_reason"]
                }
            }
        elif not result.get("test_passed"):
            run_results[thread_id] = {
                "status": "fix_failed",
                "thread_id": thread_id,
                "data": {
                    "title": result["issue_title"],
                    "test_output": result["test_output"]
                }
            }
        else:
            run_results[thread_id] = {
                "status": "awaiting_approval",
                "thread_id": thread_id,
                "data": {
                    "title": result["issue_title"],
                    "root_cause": result["root_cause"],
                    "files_fixed": list(result["proposed_fix"].keys()),
                    "tests_passed": result["test_passed"],
                    "test_output": result["test_output"],
                    "diff": {
                        path: diff[:500]
                        for path, diff in result["diff"].items()
                    }
                }
            }
        run_status[thread_id] = "done"

    except Exception as e:
        run_results[thread_id] = {"status": "error", "message": str(e)}
        run_status[thread_id] = "error"
    finally:
        sys.stdout = old_stdout
        q.put("__DONE__")


@app.get("/")
def root():
    return {"status": "AI GitHub Agent is running"}


@app.post("/solve")
def solve(request: IssueRequest):
    """Returns thread_id immediately. Agent runs in background."""
    thread_id = str(uuid.uuid4())
    log_queues[thread_id] = queue.Queue()
    run_status[thread_id] = "starting"

    threading.Thread(
        target=run_agent_in_background,
        args=(thread_id, request.issue_url),
        daemon=True
    ).start()

    # ← returns instantly, agent keeps running in background
    return {"thread_id": thread_id, "status": "started"}


@app.get("/status/{thread_id}")
def get_status(thread_id: str):
    """Frontend polls this every second to get final result."""
    status = run_status.get(thread_id, "not_found")
    if status in ("done", "error"):
        return {"status": status, "result": run_results.get(thread_id, {})}
    return {"status": status}


@app.get("/logs/{thread_id}")
async def stream_logs(thread_id: str):
    """SSE — streams live logs. Closes when agent sends __DONE__."""
    q = log_queues.get(thread_id)

    if not q:
        async def not_found():
            yield "data: thread not found\n\n"
        return StreamingResponse(not_found(), media_type="text/event-stream")

    async def event_generator():
        loop = asyncio.get_event_loop()
        while True:
            try:
                msg = await loop.run_in_executor(None, lambda: q.get(timeout=0.5))
                if msg == "__DONE__":
                    yield "data: __DONE__\n\n"
                    break
                yield f"data: {msg}\n\n"
            except Exception:
                yield ": keepalive\n\n"
                await asyncio.sleep(0.1)

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"}
    )


@app.post("/approve-pr")
def approve_pr(request: ApproveRequest):
    thread_id = request.thread_id
    config = {"configurable": {"thread_id": thread_id}}

    log_queues[thread_id] = queue.Queue()
    run_status[thread_id] = "running"

    def run():
        q = log_queues[thread_id]
        old_stdout = sys.stdout
        sys.stdout = QueueWriter(q)
        try:
            result = graph.invoke(None, config)
            if not result.get("pr_url"):
                run_results[thread_id] = {"status": "error", "message": "PR creation failed"}
            else:
                run_results[thread_id] = {
                    "status": "success",
                    "data": {
                        "pr_url": result["pr_url"],
                        "branch_name": result["branch_name"]
                    }
                }
            run_status[thread_id] = "done"
        except Exception as e:
            run_results[thread_id] = {"status": "error", "message": str(e)}
            run_status[thread_id] = "error"
        finally:
            sys.stdout = old_stdout
            q.put("__DONE__")

    threading.Thread(target=run, daemon=True).start()
    return {"thread_id": thread_id, "status": "started"}


@app.post("/cancel-pr")
def cancel_pr(request: ApproveRequest):
    return {"status": "cancelled", "message": "PR creation cancelled by user"}