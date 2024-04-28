from abc import ABC, abstractmethod
from typing import Any, Callable, Optional, Type

from langchain_core.tools import StructuredTool
from pydantic import BaseModel, Field, validator


class BaseTool(BaseModel, ABC):

    # Placeholder class for arguments schema, used if no schema is provided.
    class _ArgsSchemaPlaceholder(BaseModel):
        pass

    # Unique name of the tool, which clearly communicates its purpose.
    name: str

    # Description of what the tool does and how it should be used. It can include when and why the tool is appropriate.
    description: str

    # Type definition for the arguments schema that the tool accepts. This schema is used for validating the inputs passed to the tool.
    args_schema: Type[BaseModel] = Field(default_factory=_ArgsSchemaPlaceholder)

    # A flag to track whether the description has been updated, which can be useful for dynamic updates and maintenance.
    description_updated: bool = False

    # Optional function that determines whether the results of the tool should be cached.
    # This function should return a boolean value indicating if caching should occur.
    cache_function: Optional[Callable[[Any, Any], bool]] = None

    @validator("args_schema", always=True, pre=True)
    def validate_args_schema(cls, v):
        # Validator to ensure that a proper args schema is provided; raises an error if the default placeholder is used.
        if isinstance(v, cls.ArgsSchemaPlaceholder):
            raise ValueError("Args schema must be defined for the tool.")
        return v

    def model_post_init(self, __context: Any) -> None:
        super().model_post_init(__context)
        self._generate_description()

    def _generate_description(self):
        args = []
        for arg, attribute in self.args_schema.model_json_schema()[
            "properties"
        ].items():
            if "type" in attribute:
                args.append(f"{arg}: '{attribute['type']}'")

        description = self.description.replace("\n", " ")
        self.description = f"{self.name}({', '.join(args)}) - {description}"

    def run(self, *args: Any, **kwargs: Any) -> Any:
        print(f"Using Tool: {self.name}")
        return self._run(*args, **kwargs)

    @abstractmethod
    def _run(
        self,
        *args: Any,
        **kwargs: Any,
    ) -> Any:
        """Here goes the actual implementation of the tool."""

    def to_langchain(self) -> StructuredTool:
        self._set_args_schema()
        return StructuredTool(
            name=self.name,
            description=self.description,
            args_schema=self.args_schema,
            func=self._run,
        )

    def _set_args_schema(self):
        if self.args_schema is None:
            class_name = f"{self.__class__.__name__}Schema"
            self.args_schema = type(
                class_name,
                (BaseModel,),
                {
                    "__annotations__": {
                        k: v
                        for k, v in self._run.__annotations__.items()
                        if k != "return"
                    },
                },
            )
