from typing import Optional

from sqlalchemy.sql.expression import insert, select

from api.database.functions import verify_token, get_session, EngineType, sqlalchemy_result
from api.database.models import PredictionsFeedback, Player
from fastapi import APIRouter, status
from pydantic import BaseModel


class Feedback(BaseModel):
    player_name: str
    vote: int
    prediction: str
    confidence: float
    subject_id: int # are they sending a subject id?
    feedback_text: Optional[str] = None
    proposed_label: Optional[str] = None


router = APIRouter()


@router.get("/v1/feedback/", tags=["Feedback"])
async def get_feedback(
    token: str,
    voter_id: Optional[int] = None,
    subject_id: Optional[int] = None ,
    vote:  Optional[int] = None,
    prediction: Optional[str] = None,
    confidence:  Optional[float] = None,
    proposed_label: Optional[str] = None,
    feedback_text: Optional[str] = None):
    '''
        Get player feedback of a player
    '''
    # verify token
    await verify_token(token, verification='verify_ban', route='[GET]/v1/feedback')

    if None == voter_id == subject_id == vote == prediction == confidence == proposed_label == feedback_text:
        raise HTTPException(status_code=404, detail="No param given")

    # query
    table = PredictionsFeedback
    sql = select(table)

    # filters
    if not voter_id is None:
        sql = sql.where(table.voter_id == voter_id)
    if not subject_id is None:
        sql = sql.where(table.subject_id == subject_id)
    if not vote is None:
        sql = sql.where(table.vote == vote)
    if not prediction is None:
        sql = sql.where(table.prediction == prediction)
    if not confidence is None:
        sql = sql.where(table.confidence == confidence)
    if not proposed_label is None:
        sql = sql.where(table.proposed_label == proposed_label)
    if not feedback_text is None:
        sql = sql.where(table.feedback_text == feedback_text)
    
    # execute query
    async with get_session(EngineType.PLAYERDATA) as session:
        data = await session.execute(sql)

    data = sqlalchemy_result(data)
    return data.rows2dict()


@router.post("/v1/feedback/", status_code=status.HTTP_201_CREATED, tags=["Feedback"])
async def post(feedback: Feedback):
    '''
        insert feedback into database
    '''
    feedback = feedback.dict()

    sql_player = select(Player)
    sql_player = sql_player.where(Player.name == feedback.pop('player_name'))

    sql_insert = insert(PredictionsFeedback).prefix_with('ignore')

    async with get_session(EngineType.PLAYERDATA) as session:
        player = session.execute(sql_player)
        player = sqlalchemy_result(player).rows2dict()

        feedback["voter_id"] = player[0]['id']
        sql_insert = sql_insert.values(feedback)
        print(sql_insert)
        await session.execute(sql_insert)

    return {"OK": "OK"}
