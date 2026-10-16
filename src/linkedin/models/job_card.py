from pydantic import BaseModel


class JobCardRawData(BaseModel):
    job_id: str
    card_text: str
