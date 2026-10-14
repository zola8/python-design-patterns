import uvicorn
from fastapi import BackgroundTasks
from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI()


# ==========================================
# COMMAND INTERFACE
# ==========================================
class Command:
    async def execute(self):
        raise NotImplementedError


# ==========================================
# CONCRETE COMMANDS
# ==========================================
class SendEmailCommand(Command):
    def __init__(self, to: str, subject: str, body: str):
        self.to = to
        self.subject = subject
        self.body = body

    async def execute(self):
        print(f"[Email] Sending to {self.to}: {self.subject}")
        # await email_client.send(...)


class GenerateReportCommand(Command):
    def __init__(self, user_id: str, report_type: str):
        self.user_id = user_id
        self.report_type = report_type

    async def execute(self):
        print(f"[Report] Generating {self.report_type} for user {self.user_id}")
        # await report_service.generate(...)


class NotifySlackCommand(Command):
    def __init__(self, channel: str, message: str):
        self.channel = channel
        self.message = message

    async def execute(self):
        print(f"[Slack] Posting to {self.channel}: {self.message}")
        # await slack_client.post(...)


# ==========================================
# COMMAND EXECUTOR (Like Celery worker)
# ==========================================
class CommandExecutor:
    async def execute(self, command: Command):
        await command.execute()


executor = CommandExecutor()


# ==========================================
# FASTAPI ENDPOINT
# ==========================================
class UserRegistration(BaseModel):
    email: str
    name: str


@app.post("/register")
async def register_user(data: UserRegistration, background_tasks: BackgroundTasks):
    # Create command objects
    email_cmd = SendEmailCommand(
        to=data.email,
        subject="Welcome!",
        body=f"Hello {data.name}, welcome aboard!"
    )

    report_cmd = GenerateReportCommand(
        user_id="USER-123",
        report_type="onboarding"
    )

    slack_cmd = NotifySlackCommand(
        channel="#new-users",
        message=f"New user registered: {data.email}"
    )

    # Queue commands for background execution
    background_tasks.add_task(executor.execute, email_cmd)
    background_tasks.add_task(executor.execute, report_cmd)
    background_tasks.add_task(executor.execute, slack_cmd)

    return {"message": "Registration successful! Processing in background."}


if __name__ == '__main__':
    uvicorn.run(app, port=8080)
