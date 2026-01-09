from pydantic import BaseModel, Field

class ToneScore(BaseModel):
    clarity: float = Field(..., ge=0, le=1, description="명확성")
    neutrality: float = Field(..., ge=0, le=1, description="중립성")
    politeness: float = Field(..., ge=0, le=1, description="공손함")

    @property
    def total(self) -> float:
        return round((self.clarity + self.neutrality + self.politeness) / 3, 3)
