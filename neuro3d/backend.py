import pkg_resources, functools, abc
from .exceptions import *

__set_backend = False
_backend = None

@functools.lru_cache()
def _get_backends():
    return [entry_point.load()() for entry_point in pkg_resources.iter_entry_points("neuro3d.backends")] + [FallbackBackend()]


def get_backends():
    return [b.name for b in _get_backends()]


def get_backend():
    return _backend


def establish_backends():
    global __set_backend
    backends = _get_backends()
    prio = [b for b in backends if b.priority]
    if len(prio) > 1:
        raise MultipleBackendPriorityError(", ".join(f"'{b.name}'" for b in prio) + " all claim priority as backend.", prio)
    elif len(prio):
        print("What is?", __set_backend)
        return _set_backend(prio[0])
    # Set a fallback backend
    _set_backend(FallbackBackend())
    # Clear the flag that the backend has already been set
    __set_backend = False


def _set_backend(backend):
    import neuro3d

    global __set_backend, _backend
    print("Whyyyyyyyyy", __set_backend)
    # raise Exception("Where is this first set from then?")
    if __set_backend:
        raise BackendSetError(f"The backend has already been set to '{_backend.name}'")
    if not backend.available:
        raise BackendUnavailableError(f"The %backend.name% backend is not available. Available backends: " + ", ".join(f"'{b.name}'" for b in _get_backends() if b.available), backend)
    __set_backend = True
    _backend = backend
    backend.initialize()
    neuro3d.properties = backend.get_properties()


def set_backend(name):
    backends = {b.name: b for b in _get_backends()}
    try:
        backend = backends[name]
    except KeyError:
        raise UnknownBackendError("Unknown backend '%name%'. Known backends: " + ", ".join(f"'{b}'" for b in backends), name) from None
    return _set_backend(backend)


class Backend(abc.ABC):
    @abc.abstractmethod
    def initialize(self):
        pass

    @abc.abstractmethod
    def get_controller(self):
        pass

    @abc.abstractmethod
    def get_properties(self):
        pass


class FallbackBackend:
    priority = False
    name = "fallback"
    available = True

    def initialize(self):
        pass

    @functools.lru_cache()
    def get_properties(self):
        return type("neuro3d.properties", (), {})()

    @functools.lru_cache()
    def get_controller(self):
        return FallbackController()

    def __getattr__(self, attr):
        raise FallbackError("Operation not supported without backend.")


class Controller(abc.ABC):
    def check_support(self):
        pass


class FallbackController(Controller):
    pass


class RequiresSupport:
    def __init_subclass__(cls, requires=None, **kwargs):
        super().__init_subclass__(**kwargs)
        cls._support_requirements = requires

    def __new__(cls, *args, **kwargs):
        backend = get_backend()
        controller = backend.get_controller()
        missing = [r for r in cls._support_requirements if r not in controller.__dict__]
        if missing:
            raise MissingControllerSupport(f"Can't create {cls.__name__} because {backend.name} misses {', '.join(missing)} to support it.")
