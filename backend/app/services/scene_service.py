"""Scene service managing active scene state, ring-buffer history, and queries."""

from collections import deque
from typing import Any, Dict, List, Optional
import threading
from app.agent.reasoning import SceneQueryEngine
from app.core.exceptions import ResourceNotFoundError
from app.vision.models import SceneContext


class SceneService:
    """Singleton service maintaining current live scene state and querying capability."""

    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(SceneService, cls).__new__(cls)
                cls._instance._init_service()
            return cls._instance

    def _init_service(self):
        self._current_scene: Optional[SceneContext] = None
        self._history: deque[SceneContext] = deque(maxlen=50)
        self._state_lock = threading.Lock()

    def set_current_scene(self, scene: SceneContext) -> None:
        with self._state_lock:
            self._current_scene = scene
            self._history.appendleft(scene)

    def get_current_scene(self) -> SceneContext:
        with self._state_lock:
            if self._current_scene is None:
                raise ResourceNotFoundError(
                    "No vision frames have been processed yet. The scene buffer is currently empty."
                )
            return self._current_scene

    def has_scene(self) -> bool:
        with self._state_lock:
            return self._current_scene is not None

    def get_history(self, limit: int = 10) -> List[SceneContext]:
        with self._state_lock:
            return list(self._history)[:limit]

    def query_scene(self, query_text: str) -> Dict[str, Any]:
        """Answers queries against the latest scene."""
        scene = self.get_current_scene()
        return SceneQueryEngine.query(scene, query_text)


scene_service = SceneService()

