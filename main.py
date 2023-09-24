from fastapi import FastAPI, HTTPException, Path, Query
from pandas import read_excel
from typing import Annotated

from . import crud

crud.initialize_database()

app = FastAPI()

LCSQA_stations = read_excel(
"Liste points de mesures 2020 pour site LCSQA_221292021.xlsx"
)["Code station"].tolist()

@app.get("/{station}")
async def get_response(
    station: Annotated[
        str,
        Path(
            description=(
                "Code identifying the air quality monitoring station \
                 whose data will be used by the API".
            ),
            pattern="^FR([0-9]{5}$)"
        )
    ],
    pollutant: Annotated[
        list[str],
        Query(
           alias="p",
           description=(
                "Chemical symbol(s) of the pollutant(s) whose air \
                 concentration(s) during a time slot of a specific \
                 duration we want to minimize."
           )
        )
    ],
    duration: Annotated[
        int,
        Query(
            description=(
                "Duration (expressed in number of hours) of the time \
                 slot(s) that we expect the API to return, that is \
                 the one(s) with the lowest level(s) of air \
                 concentration of the given pollutant(s)."
            ),
            ge=1,
            le=24
        )
    ],
    period: Annotated[
        str,
        Query(
            description=(
            "Part of the day that we want the expected time slot(s) \
             to fall within."
            ),
            examples=["7-15"]
        )
    ] = "0-24",
    n_days: Annotated[
        int,
        Query(
            description=(
                "If specified, the analysis of the API will be based on \
                 pollution data collected over the 'n_days last days."
            ),
            ge=1,
            le=44
        )
    ] = 45
):
    if station not in LCSQA_stations:
        raise HTTPException(status_code=404,detail="Station not found")
    else:
        return crud.get_response(
            station,
            pollutant,
            duration,
            period,
            n_days
        )
