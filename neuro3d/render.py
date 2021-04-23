import abc, concurrent.futures

class BackendRender(abc.ABC):
    def __init__(self, file):
        self.file = file

    @abc.abstractmethod
    def render_portion(self, rank, size):
        pass

class Renderer:
    def __init__(self, backend, file, workers):
        self.file = file
        self.workers = workers
        self._bc = backend

    def render_portions(self):
        with concurrent.futures.ThreadPoolExecutor(self.workers) as pool:
            futures = [pool.submit(self._bc(self.file).render_portion, i, self.workers) for i in range(self.workers)]
            for future in concurrent.futures.as_completed(futures):
                print("Render worker completed", future.result())
