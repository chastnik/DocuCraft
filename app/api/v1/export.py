"""Document export API endpoints."""

from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, status, Path, Query
from fastapi.responses import Response, HTMLResponse, PlainTextResponse
from app.api.v1.auth import get_current_user
from app.domain.models.user import User
from app.api.deps import get_db
from sqlalchemy.ext.asyncio import AsyncSession
try:
    import markdown
    HAS_MARKDOWN = True
except ImportError:
    HAS_MARKDOWN = False
# PDF export requires weasyprint: pip install weasyprint
# For now, we'll use a simpler approach
try:
    from weasyprint import HTML
    HAS_WEASYPRINT = True
except ImportError:
    HAS_WEASYPRINT = False

router = APIRouter()


@router.get("/documents/{document_id}/export")
async def export_document(
    document_id: str = Path(...),
    format: str = Query(..., pattern="^(pdf|html|md)$"),
    current_user: Annotated[User, Depends(get_current_user)] = None,
    db: Annotated[AsyncSession, Depends(get_db)] = None,
):
    """Export document in various formats."""
    from app.infrastructure.database.repositories.document_repository_impl import DocumentRepositoryImpl
    from app.domain.services.document_service import DocumentService
    from app.domain.repositories.project_repository import ProjectRepository
    from app.infrastructure.database.repositories.project_repository_impl import ProjectRepositoryImpl
    
    try:
        document_repo = DocumentRepositoryImpl(db)
        project_repo = ProjectRepositoryImpl(db)
        document_service = DocumentService(document_repo, project_repo)
        document = await document_service.get_document(document_id, current_user.id)
        
        # Extract document fields (Document is a Pydantic model)
        # Access fields directly from the model
        try:
            content = getattr(document, 'content', '') or ''
            title = getattr(document, 'title', 'Document') or 'Document'
            slug = getattr(document, 'slug', 'document') or 'document'
        except AttributeError as e:
            # Fallback: try to access as dict
            if hasattr(document, 'model_dump'):
                doc_dict = document.model_dump()
                content = doc_dict.get('content', '') or ''
                title = doc_dict.get('title', 'Document') or 'Document'
                slug = doc_dict.get('slug', 'document') or 'document'
            else:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Failed to extract document fields: {str(e)}"
                )
        
        if format == "md":
            # Markdown export
            return PlainTextResponse(
                content=content,
                media_type="text/markdown",
                headers={"Content-Disposition": f'attachment; filename="{slug}.md"'}
            )
        
        elif format == "html":
            # HTML export
            if not HAS_MARKDOWN:
                raise HTTPException(
                    status_code=status.HTTP_501_NOT_IMPLEMENTED,
                    detail="HTML export requires markdown library. Install it with: pip install markdown"
                )
            html_content = markdown.markdown(content, extensions=['fenced_code', 'tables'])
            full_html = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="UTF-8">
                <title>{title}</title>
                <style>
                    body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; max-width: 800px; margin: 0 auto; padding: 2rem; }}
                    h1, h2, h3 {{ color: #333; }}
                    code {{ background: #f4f4f4; padding: 0.2em 0.4em; border-radius: 3px; }}
                    pre {{ background: #f4f4f4; padding: 1em; border-radius: 5px; overflow-x: auto; }}
                </style>
            </head>
            <body>
                <h1>{title}</h1>
                {html_content}
            </body>
            </html>
            """
            return HTMLResponse(
                content=full_html,
                headers={"Content-Disposition": f'attachment; filename="{slug}.html"'}
            )
        
        elif format == "pdf":
            # PDF export using WeasyPrint
            if not HAS_WEASYPRINT:
                raise HTTPException(
                    status_code=status.HTTP_501_NOT_IMPLEMENTED,
                    detail="PDF export requires weasyprint library. Install it with: pip install weasyprint"
                )
            
            if not HAS_MARKDOWN:
                raise HTTPException(
                    status_code=status.HTTP_501_NOT_IMPLEMENTED,
                    detail="PDF export requires markdown library. Install it with: pip install markdown"
                )
            
            try:
                html_content = markdown.markdown(content, extensions=['fenced_code', 'tables'])
                full_html = f"""
                <!DOCTYPE html>
                <html>
                <head>
                    <meta charset="UTF-8">
                    <title>{title}</title>
                    <style>
                        @page {{ size: A4; margin: 2cm; }}
                        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; }}
                        h1, h2, h3 {{ color: #333; page-break-after: avoid; }}
                        code {{ background: #f4f4f4; padding: 0.2em 0.4em; border-radius: 3px; }}
                        pre {{ background: #f4f4f4; padding: 1em; border-radius: 5px; page-break-inside: avoid; }}
                    </style>
                </head>
                <body>
                    <h1>{title}</h1>
                    {html_content}
                </body>
                </html>
                """
                pdf_bytes = HTML(string=full_html).write_pdf()
                return Response(
                    content=pdf_bytes,
                    media_type="application/pdf",
                    headers={"Content-Disposition": f'attachment; filename="{slug}.pdf"'}
                )
            except Exception as pdf_error:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"PDF generation failed: {str(pdf_error)}"
                )
        
    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise
    except Exception as e:
        import traceback
        error_detail = str(e)
        # Log full traceback for debugging
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Export error: {error_detail}\n{traceback.format_exc()}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
            detail=f"Export failed: {error_detail}"
        )

