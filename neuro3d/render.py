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
        print("Starting rendering job pool")
        with concurrent.futures.ThreadPoolExecutor(self.workers) as pool:
            futures = [pool.submit(self._bc(self.file).render_portion, i, self.workers) for i in range(self.workers)]
            for future in concurrent.futures.as_completed(futures):
                print("Render worker completed", future.result())

    def render_mpi(self, comm):
        rank = comm.Get_rank()
        size = comm.Get_size()
        print(f"Rendering on worker {rank} of {size}", flush=True)
        res = self._bc(self.file).render_portion(rank, size)
        print(f"Render worker {rank} completed", res, flush=True)
        comm.Barrier()

def render(file, workers, comm=None):
    renderer = Renderer(file, workers)
    if comm:
        renderer.render_mpi(comm)
    else:
        renderer.render_portions()
