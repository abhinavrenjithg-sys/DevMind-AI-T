from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List

from app.core.database import get_db
from app.models import (
    RepositoryRevision, Repository, SourceFile, Symbol,
    Conversation, ConversationMessage, EvidenceReference
)
from app.schemas import QuestionRequest, MessageResponse, ConversationResponse, EvidenceItem
from app.ai.assistant import CodebaseAssistant

router = APIRouter()

@router.post("/{revision_id}/ask", response_model=MessageResponse)
async def ask_codebase_question(
    revision_id: str,
    payload: QuestionRequest,
    db: AsyncSession = Depends(get_db)
):
    rev_res = await db.execute(
        select(RepositoryRevision, Repository)
        .join(Repository, Repository.id == RepositoryRevision.repository_id)
        .where(RepositoryRevision.id == revision_id)
    )
    row = rev_res.first()
    if not row:
        raise HTTPException(status_code=404, detail="Revision not found")
    rev, repo = row

    # 1. Get or create conversation
    conv_id = payload.conversation_id
    conversation = None
    if conv_id:
        c_res = await db.execute(select(Conversation).where(Conversation.id == conv_id))
        conversation = c_res.scalar_one_or_none()

    if not conversation:
        title = payload.question[:40] + ("..." if len(payload.question) > 40 else "")
        conversation = Conversation(
            workspace_id=repo.workspace_id,
            repository_id=repo.id,
            revision_id=rev.id,
            title=title
        )
        db.add(conversation)
        await db.flush()

    # 2. Record user message
    user_msg = ConversationMessage(
        conversation_id=conversation.id,
        sender="user",
        content=payload.question
    )
    db.add(user_msg)
    await db.flush()

    # 3. Load repository files and symbols
    files_res = await db.execute(select(SourceFile).where(SourceFile.revision_id == revision_id))
    files = files_res.scalars().all()
    files_data = [
        {"path": f.path, "file_name": f.file_name, "lines_of_code": f.lines_of_code, "language": f.language, "layer": f.layer}
        for f in files
    ]

    syms_res = await db.execute(
        select(Symbol, SourceFile.path)
        .join(SourceFile, SourceFile.id == Symbol.file_id)
        .where(Symbol.revision_id == revision_id)
    )
    symbols_data = []
    for s, fpath in syms_res.all():
        symbols_data.append({
            "name": s.name,
            "qualified_name": s.qualified_name,
            "kind": s.kind,
            "signature": s.signature,
            "docstring": s.docstring,
            "start_line": s.start_line,
            "end_line": s.end_line,
            "file_path": fpath
        })

    # 4. Invoke grounded assistant
    assistant = CodebaseAssistant(repo.local_path, files_data, symbols_data)
    ai_result = await assistant.answer_question(payload.question)

    # 5. Record assistant response
    asst_msg = ConversationMessage(
        conversation_id=conversation.id,
        sender="assistant",
        content=ai_result["answer"]
    )
    db.add(asst_msg)
    await db.flush()

    evidence_items = []
    for ev in ai_result["evidence"]:
        ev_ref = EvidenceReference(
            message_id=asst_msg.id,
            file_path=ev["file_path"],
            start_line=ev["start_line"],
            end_line=ev["end_line"],
            symbol_name=ev.get("symbol_name"),
            snippet=ev.get("snippet"),
            explanation=ev.get("explanation")
        )
        db.add(ev_ref)
        evidence_items.append(EvidenceItem(
            file_path=ev["file_path"],
            start_line=ev["start_line"],
            end_line=ev["end_line"],
            symbol_name=ev.get("symbol_name"),
            snippet=ev.get("snippet", ""),
            explanation=ev.get("explanation")
        ))

    await db.commit()

    return MessageResponse(
        id=asst_msg.id,
        sender="assistant",
        content=asst_msg.content,
        created_at=asst_msg.created_at,
        evidence=evidence_items
    )

@router.get("/{revision_id}/conversations", response_model=List[ConversationResponse])
async def list_conversations(revision_id: str, db: AsyncSession = Depends(get_db)):
    res = await db.execute(
        select(Conversation)
        .where(Conversation.revision_id == revision_id)
        .order_by(Conversation.updated_at.desc())
    )
    convs = res.scalars().all()
    out = []
    for c in convs:
        # Load messages
        m_res = await db.execute(
            select(ConversationMessage)
            .where(ConversationMessage.conversation_id == c.id)
            .order_by(ConversationMessage.created_at.asc())
        )
        msgs = m_res.scalars().all()
        msg_responses = []
        for m in msgs:
            # Load evidence
            e_res = await db.execute(
                select(EvidenceReference).where(EvidenceReference.message_id == m.id)
            )
            evs = e_res.scalars().all()
            ev_items = [
                EvidenceItem(
                    file_path=e.file_path,
                    start_line=e.start_line,
                    end_line=e.end_line,
                    symbol_name=e.symbol_name,
                    snippet=e.snippet or "",
                    explanation=e.explanation
                )
                for e in evs
            ]
            msg_responses.append(MessageResponse(
                id=m.id,
                sender=m.sender,
                content=m.content,
                created_at=m.created_at,
                evidence=ev_items
            ))

        out.append(ConversationResponse(
            id=c.id,
            title=c.title,
            created_at=c.created_at,
            messages=msg_responses
        ))
    return out
