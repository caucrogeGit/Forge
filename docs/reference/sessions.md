# Sessions — Concurrence

`MemorySessionStore` protège toutes ses opérations avec un `threading.RLock` (reentrant). Les tests de concurrence (`tests/test_concurrency_session_001.py`) vérifient que création, lecture, écriture, suppression et régénération restent cohérentes sous accès concurrent simple depuis plusieurs threads.

Ce backend est conçu pour un seul processus. Le multi-worker ou le multi-processus n'est pas supporté par le backend mémoire.


