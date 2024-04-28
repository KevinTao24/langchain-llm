from typing import Any, Optional, Type

from embedchain.models.data_type import DataType
from pydantic import BaseModel, Field

from .rag_tool import RagTool


class PDFSearchToolSchema(BaseModel):
    """Schema for input parameters of the PDFSearchTool."""

    pdf: str = Field(..., description="Required file path of the PDF to be searched.")
    query: str = Field(
        ..., description="Required query string to search within the PDF content."
    )


class PDFSearchTool(RagTool):
    name: str = "Search a PDF's content"
    description: str = (
        "This tool performs a semantic search within the content of a specified PDF document."
    )
    args_schema: Type[BaseModel] = PDFSearchToolSchema

    def __init__(self, pdf: Optional[str] = None, **kwargs):
        super().__init__(**kwargs)
        if pdf is not None:
            self.add(pdf)
            self.description = f"Performs semantic searches within the content of the specified PDF file: {pdf}."
            self.args_schema = PDFSearchToolSchema
            self._generate_description()

    def add(
        self,
        *args: Any,
        **kwargs: Any,
    ) -> None:
        kwargs["data_type"] = DataType.PDF_FILE
        super().add(*args, **kwargs)

    def _before_run(
        self,
        query: str,
        **kwargs: Any,
    ) -> Any:
        if "pdf" in kwargs:
            self.add(kwargs["pdf"])
