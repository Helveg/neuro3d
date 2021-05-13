import abc, concurrent.futures
from . import get_backend

class BackendRender(abc.ABC):
    def __init__(self, file):
        self.file = file

    @abc.abstractmethod
    def render_portion(self, rank, size):
        pass

class Renderer:
    def __init__(self, file, workers):
        self.file = file
        self.workers = workers
        self._bc = get_backend().get_renderer()

    def render_portions(self):
        with concurrent.futures.ThreadPoolExecutor(self.workers) as pool:
            futures = [pool.submit(self._bc(self.file).render_portion, i, self.workers) for i in range(self.workers)]
            for future in concurrent.futures.as_completed(futures):
                print("Render worker completed", future.result())

def render(file, workers):
    renderer = Renderer(file, workers)
    renderer.render_portions()
