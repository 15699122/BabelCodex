from codex_babeldoc.translation.thread_state import ThreadState, ThreadStateStore


def test_thread_state_round_trip_and_rotation(tmp_path):
    store = ThreadStateStore(tmp_path / "threads")
    store.save(ThreadState("paper/one", "thread-a"))
    assert store.load("paper/one") == ThreadState("paper/one", "thread-a")

    rotated = store.rotate("paper/one", "thread-b")
    assert rotated.generation == 1
    assert store.load("paper/one") == rotated
    assert not list((tmp_path / "threads").glob("*.tmp"))
