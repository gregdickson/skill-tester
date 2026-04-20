from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import PlainTextResponse
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.network import Network
from app.models.component import Component
from app.models.output import OutputTemplate, GeneratedOutput
from app.schemas.output import (
    OutputTemplateCreate, OutputTemplateUpdate, OutputTemplateOut,
    GenerateOutputRequest, GeneratedOutputOut,
)
from app.services.generator import Generator
from app.services.evaluator import Evaluator

router = APIRouter()


@router.get("/{network_id}/outputs", response_model=list[GeneratedOutputOut])
async def list_outputs(network_id: UUID, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(GeneratedOutput)
        .where(GeneratedOutput.network_id == network_id)
        .order_by(GeneratedOutput.created_at.desc())
    )
    return result.scalars().all()


@router.post("/{network_id}/outputs/generate", response_model=GeneratedOutputOut)
async def generate_output(
    network_id: UUID,
    body: GenerateOutputRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    network = await db.get(Network, network_id)
    if not network:
        raise HTTPException(404, "Network not found")

    components = (
        await db.execute(
            select(Component)
            .where(Component.network_id == network_id)
            .order_by(Component.sort_order)
        )
    ).scalars().all()

    if not components:
        raise HTTPException(400, "No components")

    template = None
    template_prompt = None
    if body.template_id:
        template = await db.get(OutputTemplate, body.template_id)
        if template:
            template_prompt = template.prompt_template

    comp_dicts = [
        {"id": str(c.id), "name": c.name, "description": c.description or "", "priority": c.priority}
        for c in components
    ]
    weights = {str(c.id): c.weight for c in components}

    llm = request.app.state.openrouter
    generator = Generator(llm)

    content = await generator.generate(
        goal=network.ultimate_end_goal,
        components=comp_dicts,
        weights=weights,
        how_it_works=network.how_it_works,
        template_prompt=template_prompt,
    )

    # Score the output
    evaluator = Evaluator(llm)
    scores = await evaluator.batch_score(content, comp_dicts, weights)
    avg_score = sum(scores.values()) / len(scores) if scores else 0.0

    # Get next version
    max_v = await db.execute(
        select(func.max(GeneratedOutput.version)).where(GeneratedOutput.network_id == network_id)
    )
    version = (max_v.scalar() or 0) + 1

    output = GeneratedOutput(
        network_id=network_id,
        template_id=body.template_id,
        version=version,
        content=content,
        weights_snapshot=weights,
        quality_score=avg_score,
    )
    db.add(output)
    await db.commit()
    await db.refresh(output)
    return output


@router.get("/{network_id}/outputs/{output_id}/download")
async def download_output(network_id: UUID, output_id: UUID, db: AsyncSession = Depends(get_db)):
    output = await db.get(GeneratedOutput, output_id)
    if not output or output.network_id != network_id:
        raise HTTPException(404, "Output not found")
    return PlainTextResponse(
        content=output.content,
        media_type="text/markdown",
        headers={"Content-Disposition": f"attachment; filename=skill-v{output.version}.md"},
    )
