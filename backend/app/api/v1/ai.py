import json
from typing import Annotated
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.deps import get_current_user, require_roles
from app.db.session import get_db
from app.models import AIConversation, AIMessage, User
from app.ai.service import chat, list_conversations, get_messages
from app.services.production_job import ProductionJobService

router=APIRouter()
Db=Annotated[AsyncSession,Depends(get_db)]
Current=Annotated[User,Depends(get_current_user)]

class ChatInput(BaseModel):
    message:str=Field(min_length=1,max_length=12000)
    conversation_id:UUID|None=None
class ConfirmPlan(BaseModel):
    recipe_id:UUID
    planned_quantity:float=Field(gt=0)

@router.get('/conversations')
async def conversations(db:Db,user:Current): return await list_conversations(db,user)

@router.get('/conversations/{conversation_id}/messages')
async def messages(conversation_id:UUID,db:Db,user:Current):
    try:return await get_messages(db,user,conversation_id)
    except LookupError as e:raise HTTPException(404,str(e)) from e

@router.delete('/conversations/{conversation_id}',status_code=204)
async def remove_conversation(conversation_id:UUID,db:Db,user:Current):
    conv=await db.scalar(select(AIConversation).where(AIConversation.id==conversation_id,AIConversation.user_id==user.id))
    if not conv:raise HTTPException(404,'Диалог не найден')
    await db.delete(conv);await db.commit()

@router.post('/chat/stream')
async def stream_chat(data:ChatInput,db:Db,user:Current):
    async def events():
        try:
            result=await chat(db,user,data.message,data.conversation_id)
            # SSE framing keeps the transport incremental-friendly; assistant output is persisted before delivery.
            payload=json.dumps({"type":"done",**result},ensure_ascii=False)
            yield f"data: {payload}\n\n"
        except LookupError as e:
            yield f"data: {json.dumps({'type':'error','message':str(e)},ensure_ascii=False)}\n\n"
        except Exception as e:
            yield f"data: {json.dumps({'type':'error','message':str(e)},ensure_ascii=False)}\n\n"
    return StreamingResponse(events(),media_type='text/event-stream',headers={'Cache-Control':'no-cache','X-Accel-Buffering':'no'})

@router.post('/confirm-production-plan')
async def confirm_plan(data:ConfirmPlan,db:Db,user:Annotated[User,Depends(require_roles('technologist','manager'))]):
    try:
        result=await ProductionJobService.create(db,data.recipe_id,data.planned_quantity,user)
        return result
    except LookupError as e:raise HTTPException(404,str(e)) from e
    except ValueError as e:raise HTTPException(409,str(e)) from e
