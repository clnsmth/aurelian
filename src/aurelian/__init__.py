"""ubergraph-agent package."""

import importlib_metadata

try:
    __version__ = importlib_metadata.version(__name__)
except importlib_metadata.PackageNotFoundError:
    # package is not installed
    __version__ = "0.0.0"  # pragma: no cover

# Backward compatibility shim for pydantic-ai 2.x
try:
    from pydantic_ai.agent import Agent, AgentRunResult

    _orig_agent_init = Agent.__init__

    def _patched_agent_init(self, *args, **kwargs):
        if "result_type" in kwargs and "output_type" not in kwargs:
            kwargs["output_type"] = kwargs.pop("result_type")
        return _orig_agent_init(self, *args, **kwargs)

    Agent.__init__ = _patched_agent_init

    if not hasattr(AgentRunResult, "data"):
        AgentRunResult.data = property(lambda self: self.output)

    import pydantic_ai.models
    _orig_infer_model = pydantic_ai.models.infer_model

    def _patched_infer_model(model, *args, **kwargs):
        if isinstance(model, str) and model.startswith("gemini-"):
            model = f"google:{model}"
        return _orig_infer_model(model, *args, **kwargs)

    pydantic_ai.models.infer_model = _patched_infer_model
except (ImportError, AttributeError):
    pass
