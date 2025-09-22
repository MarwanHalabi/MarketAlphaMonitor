from pydantic import BaseModel


class ModelV1Compat(BaseModel):
    """
    Pydantic compatibility base class.

    - On Pydantic v2: inherits BaseModel which already provides model_dump.
    - On Pydantic v1: add model_dump/model_dump_json that delegate to dict/json.
    """


# If running under Pydantic v1, BaseModel has no model_dump method.
if not hasattr(BaseModel, "model_dump"):
    def _model_dump(self, *args, **kwargs):
        return self.dict(*args, **kwargs)

    def _model_dump_json(self, *args, **kwargs):
        return self.json(*args, **kwargs)

    # Attach only on this compat subclass to avoid changing global BaseModel
    ModelV1Compat.model_dump = _model_dump  # type: ignore[attr-defined]
    ModelV1Compat.model_dump_json = _model_dump_json  # type: ignore[attr-defined]

