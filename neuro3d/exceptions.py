from errr.tree import make_tree as _t, exception as _e

_t(
    globals(),
    Neuro3DError=_e(
        BackendError=_e(
            MultiplePriorityError=_e("backends"),
            BackendSetError=_e(),
            UnknownBackendError=_e("name")
        )
    )
)
