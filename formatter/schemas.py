from pydantic import BaseModel


class ShareGPTMessage(BaseModel):
    from_: str  # "system" | "human" | "gpt"
    value: str

    model_config = {"populate_by_name": True}

    def to_dict(self) -> dict:
        return {"from": self.from_, "value": self.value}


class ShareGPTRecord(BaseModel):
    conversations: list[ShareGPTMessage]
    call_id: str | None = None

    def to_jsonl_dict(self) -> dict:
        return {
            "conversations": [m.to_dict() for m in self.conversations],
            **({"call_id": self.call_id} if self.call_id else {}),
        }


class AlpacaRecord(BaseModel):
    instruction: str
    input: str
    output: str
    call_id: str | None = None
