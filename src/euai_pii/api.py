"""Private FastAPI boundary for F-007."""

from __future__ import annotations

import asyncio
import multiprocessing
import json
import os
import uuid
from dataclasses import dataclass
from contextlib import asynccontextmanager
from typing import Literal, Union

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ConfigDict, Field, field_validator
from starlette.types import ASGIApp, Message, Receive, Scope, Send

from .screening import Profile, ScreeningFailure, ScreeningService, constant_time_credential_match
from .detectors import ConfiguredPattern, ConfiguredPatternRecognizer, CprRecognizer, CvrRecognizer
from .screening import PresidioDetector

MAX_BODY_BYTES = 1024 * 1024
MAX_TEXT_CODEPOINTS = 100_000
RESERVED_PREFIX = "[[EUAI_PII_"


class ScreenRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    mode: Literal["block", "redact"]
    profile_id: str = Field(min_length=1, max_length=128, pattern=r"^[A-Za-z0-9_-]+$")
    language: Literal["da"]
    text: str = Field(min_length=1)

    @field_validator("text")
    @classmethod
    def validate_text(cls, value: str) -> str:
        if RESERVED_PREFIX in value or any(0xD800 <= ord(character) <= 0xDFFF for character in value):
            raise ValueError("invalid text")
        if len(value) > MAX_TEXT_CODEPOINTS:
            raise ValueError("text limit exceeded")
        return value


class ReplacementResponse(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    key: str
    value: str
    entity_types: list[str]


class CommonResponse(BaseModel):
    schema_version: Literal[1]
    request_id: str
    screening_id: str
    profile_id: str
    screening_version: str


class AllowedResponse(CommonResponse):
    action: Literal["allowed"]
    text: str
    replacements: list[ReplacementResponse]


class BlockedResponse(CommonResponse):
    action: Literal["blocked"]
    code: Literal["protected_content"]


class RedactedResponse(CommonResponse):
    action: Literal["redacted"]
    text: str
    replacements: list[ReplacementResponse]


ScreenResponse = Union[AllowedResponse, BlockedResponse, RedactedResponse]


@dataclass(frozen=True, slots=True)
class CredentialBinding:
    credential: str
    profiles: frozenset[str]
    modes: frozenset[str]


class CredentialStore:
    def __init__(self, bindings: tuple[CredentialBinding, ...]):
        self.bindings = bindings

    def authorize(self, credential: str, profile_id: str, mode: str) -> bool:
        allowed = False
        for binding in self.bindings:
            if constant_time_credential_match(credential, (binding.credential,)):
                allowed = profile_id in binding.profiles and mode in binding.modes or allowed
        return allowed


class LimitBodyMiddleware:
    def __init__(self, app: ASGIApp, limit: int = MAX_BODY_BYTES):
        self.app = app
        self.limit = limit

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        total = 0
        messages: list[Message] = []
        while True:
            message = await receive()
            messages.append(message)
            if message["type"] == "http.request":
                total += len(message.get("body", b""))
                if total > self.limit:
                    await send_json_error(send, 413, "screening_limit_exceeded", str(uuid.uuid4()))
                    return
                if not message.get("more_body", False):
                    break
            elif message["type"] == "http.disconnect":
                return
        index = 0

        async def replay_receive() -> Message:
            nonlocal index
            message = messages[index]
            index += 1
            return message

        await self.app(scope, replay_receive, send)


async def send_json_error(send: Send, status: int, code: str, request_id: str) -> None:
    body = json.dumps({"error": {"code": code, "message": error_message(code), "request_id": request_id}}).encode()
    headers = [(b"content-type", b"application/json"), (b"content-length", str(len(body)).encode()), (b"cache-control", b"no-store"), (b"x-request-id", request_id.encode())]
    await send({"type": "http.response.start", "status": status, "headers": headers})
    await send({"type": "http.response.body", "body": body})


def error_message(code: str) -> str:
    if code == "invalid_request":
        return "The request is invalid."
    if code == "unauthorized":
        return "Authentication failed."
    if code == "screening_not_authorized":
        return "Screening is not authorized."
    if code == "screening_limit_exceeded":
        return "The screening limits were exceeded."
    return "Screening could not complete."


def _worker_loop(connection, service: ScreeningService) -> None:
    while True:
        try:
            payload = connection.recv()
        except EOFError:
            return
        if payload is None:
            return
        if payload == ("warmup",):
            connection.send(("ready", bool(service.profiles)))
            continue
        text, profile_id, mode = payload
        try:
            profile = service.profiles[profile_id]
            connection.send(("ok", service.screen(text, profile, mode)))
        except ScreeningFailure as failure:
            connection.send(("failure", failure.code, failure.status))
        except Exception:
            connection.send(("error",))


class WorkerProcess:
    def __init__(self, service: ScreeningService):
        self.context = multiprocessing.get_context("fork")
        self.service = service
        self.connection = None
        self.process = None
        self.start()

    def start(self) -> None:
        parent, child = self.context.Pipe()
        process = self.context.Process(target=_worker_loop, args=(child, self.service), daemon=True)
        process.start()
        child.close()
        self.connection = parent
        self.process = process
        try:
            self.connection.send(("warmup",))
            result = self.connection.recv()
        except (BrokenPipeError, EOFError, OSError) as error:
            self.close()
            raise ScreeningFailure() from error
        if result != ("ready", True):
            self.close()
            raise ScreeningFailure()

    def run(self, text: str, profile_id: str, mode: str) -> dict[str, object]:
        if self.process is None or not self.process.is_alive():
            raise ScreeningFailure()
        try:
            self.connection.send((text, profile_id, mode))
            result = self.connection.recv()
        except (BrokenPipeError, EOFError, OSError) as error:
            raise ScreeningFailure() from error
        if result[0] == "ok":
            return result[1]
        if result[0] == "failure":
            raise ScreeningFailure(result[1], result[2])
        raise ScreeningFailure()

    def restart(self) -> None:
        self.close()
        self.start()

    def close(self) -> None:
        if self.process is None:
            return
        if self.process.is_alive():
            try:
                self.connection.send(None)
            except (BrokenPipeError, OSError):
                pass
            self.process.join(2)
        if self.process.is_alive():
            self.process.terminate()
            self.process.join(2)
        self.connection.close()
        self.process = None


class ScreeningRuntime:
    def __init__(self, service: ScreeningService, credentials: CredentialStore, deadline_seconds: float = 10):
        self.service = service
        self.credentials = credentials
        self.deadline_seconds = deadline_seconds
        self.ready = True
        self.busy = asyncio.Lock()
        self.worker = WorkerProcess(service)

    def restart_worker(self) -> None:
        self.worker.restart()
        self.ready = True

    def close(self) -> None:
        self.worker.close()

    async def screen(self, request: ScreenRequest, credential: str) -> dict[str, object]:
        if not self.credentials.authorize(credential, request.profile_id, request.mode):
            raise ScreeningFailure("screening_not_authorized", 403)
        profile = self.service.profiles.get(request.profile_id)
        if profile is None or request.mode not in profile.allowed_modes:
            raise ScreeningFailure("screening_not_authorized", 403)
        if self.busy.locked():
            raise ScreeningFailure("screening_unavailable", 503)
        async with self.busy:
            try:
                return await asyncio.wait_for(
                    asyncio.to_thread(self.worker.run, request.text, profile.profile_id, request.mode),
                    timeout=self.deadline_seconds,
                )
            except asyncio.TimeoutError as error:
                self.ready = False
                self.restart_worker()
                raise ScreeningFailure() from error
            except ScreeningFailure:
                raise
            except Exception as error:
                raise ScreeningFailure() from error


def _load_json(path: str) -> dict:
    with open(path, encoding="utf-8") as configuration:
        value = json.load(configuration)
    if not isinstance(value, dict):
        raise ValueError("configuration root must be an object")
    return value


def load_runtime_from_environment() -> ScreeningRuntime | None:
    config_path = os.environ.get("SCREENING_CONFIG_PATH")
    credentials_path = os.environ.get("SCREENING_CREDENTIALS_PATH")
    if not config_path or not credentials_path:
        return None
    configuration = _load_json(config_path)
    credentials_config = _load_json(credentials_path)
    from presidio_analyzer import AnalyzerEngine
    from presidio_analyzer.predefined_recognizers import PhoneRecognizer
    from presidio_analyzer.nlp_engine import NerModelConfiguration, SpacyNlpEngine

    model_name = configuration.get("model_name", "da_core_news_md")
    nlp_engine = SpacyNlpEngine(
        models=[{"lang_code": "da", "model_name": model_name}],
        ner_model_configuration=NerModelConfiguration(
            model_to_presidio_entity_mapping={"PER": "PERSON", "PERSON": "PERSON", "LOC": "LOCATION", "GPE": "LOCATION", "LOCATION": "LOCATION"},
            labels_to_ignore={"ORG", "MISC"},
        ),
    )
    nlp_engine.load()
    profiles: dict[str, Profile] = {}
    for profile_id, profile_config in configuration.get("profiles", {}).items():
        patterns = tuple(
            ConfiguredPattern(
                rule_id=pattern["rule_id"],
                entity_type=pattern["entity_type"],
                expression=pattern["expression"],
                case_sensitive=pattern.get("case_sensitive", True),
            )
            for pattern in profile_config.get("patterns", [])
        )
        custom = (
            CprRecognizer(),
            CvrRecognizer(),
            PhoneRecognizer(supported_language="da", supported_regions=("DK",)),
        )
        if patterns:
            custom += (ConfiguredPatternRecognizer(list(patterns)),)
        engine = AnalyzerEngine(nlp_engine=nlp_engine, supported_languages=["da"])
        for recognizer in custom:
            engine.registry.add_recognizer(recognizer)
        categories = frozenset(profile_config["categories"])
        profiles[profile_id] = Profile(
            profile_id=profile_id,
            allowed_modes=frozenset(profile_config["allowed_modes"]),
            detectors=(PresidioDetector(engine),),
            categories=categories,
            thresholds={key: float(value) for key, value in profile_config["thresholds"].items()},
            version_material=json.dumps(
                {
                    "profile": profile_config,
                    "model": model_name,
                    "presidio_analyzer": "2.2.364",
                    "spacy": "3.8.16",
                    "recognizer_contract": "f007-v1",
                },
                sort_keys=True,
            ),
        )
    bindings = tuple(
        CredentialBinding(
            credential=binding["credential"],
            profiles=frozenset(binding["profiles"]),
            modes=frozenset(binding["modes"]),
        )
        for binding in credentials_config.get("bindings", [])
    )
    return ScreeningRuntime(ScreeningService(profiles), CredentialStore(bindings))


def create_app(runtime: ScreeningRuntime | None = None) -> FastAPI:
    @asynccontextmanager
    async def lifespan(application: FastAPI):
        yield
        if application.state.runtime is not None:
            application.state.runtime.close()

    app = FastAPI(docs_url=None, redoc_url=None, openapi_url=None, lifespan=lifespan)
    app.add_middleware(LimitBodyMiddleware)
    app.state.runtime = runtime

    @app.middleware("http")
    async def request_headers(request: Request, call_next):
        request_id = str(uuid.uuid4())
        request.state.request_id = request_id
        if request.url.path == "/v1/screen" and not request.headers.get("content-type", "").lower().startswith("application/json"):
            response = JSONResponse(
                {"error": {"code": "unsupported_media_type", "message": "JSON is required.", "request_id": request_id}},
                status_code=415,
            )
            response.headers["x-request-id"] = request_id
            response.headers["cache-control"] = "no-store"
            return response
        try:
            response = await call_next(request)
        except ScreeningFailure as failure:
            response = JSONResponse(
                {"error": {"code": failure.code, "message": error_message(failure.code), "request_id": request_id}},
                status_code=failure.status,
            )
        response.headers["x-request-id"] = request_id
        response.headers["cache-control"] = "no-store"
        return response

    @app.exception_handler(RequestValidationError)
    async def validation_error(request: Request, exception: RequestValidationError):
        limit_exceeded = "text limit exceeded" in str(exception.errors())
        code = "screening_limit_exceeded" if limit_exceeded else "invalid_request"
        status = 413 if limit_exceeded else 400
        return JSONResponse(
            {"error": {"code": code, "message": error_message(code), "request_id": request.state.request_id}},
            status_code=status,
        )

    @app.exception_handler(ScreeningFailure)
    async def screening_error(request: Request, exception: ScreeningFailure):
        return JSONResponse(
            {"error": {"code": exception.code, "message": error_message(exception.code), "request_id": request.state.request_id}},
            status_code=exception.status,
        )

    @app.get("/health/live")
    async def live():
        return {"status": "ok"}

    @app.get("/health/ready")
    async def ready():
        if app.state.runtime is None or not app.state.runtime.ready:
            raise ScreeningFailure()
        return {"status": "ready"}

    @app.post("/v1/screen", response_model=ScreenResponse)
    async def screen(request: Request, payload: ScreenRequest):
        runtime = app.state.runtime
        if runtime is None:
            raise ScreeningFailure()
        authorization = request.headers.get("authorization", "")
        if not authorization.startswith("Bearer ") or not authorization[7:]:
            raise ScreeningFailure("unauthorized", 401)
        response = await runtime.screen(payload, authorization[7:])
        response["request_id"] = request.state.request_id
        return response

    return app


app = create_app(load_runtime_from_environment())
