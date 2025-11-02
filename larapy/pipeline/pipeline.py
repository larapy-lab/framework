from typing import Any, Callable, List, Union, Optional


class PipelineException(Exception):
    def __init__(self, result):
        self.result = result
        super().__init__()


class Pipeline:
    def __init__(self, container=None):
        self._container = container
        self._passable = None
        self._pipes = []
        self._method = "handle"
        self._exception_handler: Optional[Callable] = None

    def send(self, passable: Any) -> "Pipeline":
        self._passable = passable
        return self

    def through(self, pipes: Union[List, Any]) -> "Pipeline":
        if not isinstance(pipes, list):
            pipes = [pipes]
        self._pipes = pipes
        return self

    def pipe(self, pipe: Any) -> "Pipeline":
        self._pipes.append(pipe)
        return self

    def via(self, method: str) -> "Pipeline":
        self._method = method
        return self

    def on_exception(self, handler: Callable) -> "Pipeline":
        self._exception_handler = handler
        return self

    def then(self, destination: Callable) -> Any:
        pipeline = self._build_pipeline(destination)

        try:
            return pipeline(self._passable)
        except PipelineException as e:
            return e.result
        except Exception as e:
            if self._exception_handler:
                return self._exception_handler(self._passable, e)
            raise

    def thenReturn(self) -> Any:
        return self.then(lambda passable: passable)

    def _build_pipeline(self, destination: Callable) -> Callable:
        pipeline = destination

        for pipe in reversed(self._pipes):
            pipeline = self._create_slice(pipeline, pipe)

        return pipeline

    def _create_slice(self, destination: Callable, pipe: Any) -> Callable:
        def slice_handler(passable: Any) -> Any:
            try:
                if callable(pipe):
                    return pipe(passable, destination)
                elif hasattr(pipe, self._method):
                    method = getattr(pipe, self._method)
                    return method(passable, destination)
                elif isinstance(pipe, str):
                    name, parameters = self._parse_pipe_string(pipe)
                    pipe_instance = self._container.make(name) if self._container else None
                    if pipe_instance:
                        if parameters:
                            return pipe_instance.handle(passable, destination, *parameters)
                        return pipe_instance.handle(passable, destination)

                return destination(passable)
            except PipelineException:
                raise
            except Exception as e:
                if self._exception_handler:
                    result = self._exception_handler(passable, e)
                    raise PipelineException(result)
                raise

        return slice_handler

    def _parse_pipe_string(self, pipe: str):
        if ":" in pipe:
            name, parameters = pipe.split(":", 1)
            parameters = [p.strip() for p in parameters.split(",")]
            return name, parameters
        return pipe, []
