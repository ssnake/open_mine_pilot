def short_trace(trace_id: str | None) -> str | None:
    if not trace_id:
        return trace_id
    return trace_id.rsplit('-', 1)[-1]


def log(component: str, message: str, trace_id: str | None = None) -> None:
    if trace_id:
        print(f'[{component}][{short_trace(trace_id)}] {message}')
    else:
        print(f'[{component}] {message}')
