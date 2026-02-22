from csv import DictReader
from datetime import date
from typing import Literal
from pydantic import BaseModel, ValidationError, NonNegativeFloat, field_validator


FILENAME = "openpowerlifting-2026-02-21-6461ed68.csv"
EXPECTED_HEADER = ["Name","Sex","Event","Equipment","Age","AgeClass","BirthYearClass","Division","BodyweightKg","WeightClassKg","Squat1Kg","Squat2Kg","Squat3Kg","Squat4Kg","Best3SquatKg","Bench1Kg","Bench2Kg","Bench3Kg","Bench4Kg","Best3BenchKg","Deadlift1Kg","Deadlift2Kg","Deadlift3Kg","Deadlift4Kg","Best3DeadliftKg","TotalKg","Place","Dots","Wilks","Glossbrenner","Goodlift","Tested","Country","State","Federation","ParentFederation","Date","MeetCountry","MeetState","MeetTown","MeetName","Sanctioned"]


class Record(BaseModel):
    Name: str
    Sex: Literal["M", "F", "Mx"]
    Event: Literal["S", "B", "D", "SB", "SD", "BD", "SBD"]
    Equipment: Literal["Raw", "Straps", "Wraps", "Single-ply", "Multi-ply", "Unlimited"]
    Age: NonNegativeFloat | None
    AgeClass: str
    BirthYearClass: str
    Division: str
    BodyweightKg: float | None
    WeightClassKg: str
    Squat1Kg: float | None
    Squat2Kg: float | None
    Squat3Kg: float | None
    Squat4Kg: float | None
    Best3SquatKg: float | None
    Bench1Kg: float | None
    Bench2Kg: float | None
    Bench3Kg: float | None
    Bench4Kg: float | None
    Best3BenchKg: float | None
    Deadlift1Kg: float | None
    Deadlift2Kg: float | None
    Deadlift3Kg: float | None
    Deadlift4Kg: float | None
    Best3DeadliftKg: float | None
    TotalKg: NonNegativeFloat | None
    Place: int | Literal["DQ", "DD", "NS", "G"]
    Dots: NonNegativeFloat | None
    Wilks: NonNegativeFloat | None
    Glossbrenner: NonNegativeFloat | None
    Goodlift: NonNegativeFloat | None
    Tested: Literal["Yes", "No"] | None
    Country: str
    State: str
    Federation: str
    ParentFederation: str
    Date: date
    MeetCountry: str
    MeetState: str
    MeetTown: str
    MeetName: str
    Sanctioned: Literal["Yes", "No"]

    @field_validator("Age", "BodyweightKg", "Squat1Kg", "Squat2Kg", "Squat3Kg", "Squat4Kg", "Best3SquatKg", "Bench1Kg", "Bench2Kg", "Bench3Kg", "Bench4Kg", "Best3BenchKg", "Deadlift1Kg", "Deadlift2Kg", "Deadlift3Kg", "Deadlift4Kg", "Best3DeadliftKg", "TotalKg", "Place", "Dots", "Wilks", "Glossbrenner", "Goodlift", "Tested", mode="before")
    @classmethod
    def empty_string_to_none(cls, v):
        if v == "":
            return None
        return v


def main():

    valid_count = 0
    invalid_count = 0
    invalid_rows = []

    with open(FILENAME, newline="", encoding="utf-8") as f:
        reader = DictReader(f)

        if reader.fieldnames != EXPECTED_HEADER:
            raise ValueError(
                f"Header mismatch. \nExpected: {EXPECTED_HEADER} \nFound: {reader.fieldnames}"
            )
        
        for line_number, row in enumerate(reader, start=2):
                
                try:
                    Record.model_validate(row)
                    valid_count += 1

                except ValidationError as e:
                    invalid_rows.append({
                        "line_number": line_number,
                        "errors": e.errors()
                    })
                    invalid_count += 1

    print("Invalid_rows: ")
    for row in invalid_rows:
        print(row)
    print(f"Valid count: {valid_count}")
    print(f"Invalid count: {invalid_count}")