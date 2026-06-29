# Aide-mémoire Testing

Synthèse de l'outillage `forge-mvc-testing` (dev-only).

## Installer (développement)

```bash
pip install --pre forge-mvc-testing
```

À déclarer dans `requirements-dev`, jamais dans les dépendances du projet.

## FakeRequest

```python
FakeRequest("GET", "/clients?id=7")
FakeRequest("POST", "/clients", body={"Nom": "Dupont"})
FakeRequest("POST", "/api/sync", json_body={"ids": [1, 2]})
```

Accesseurs : `query`, `form`, `json`, `file`, `header` (comme `Request`).

## Fixtures du plugin (pytest11)

| Fixture | Rôle |
|---|---|
| `configure_forge_kernel` | configure le noyau (session, autouse) |
| `clear_sessions` / `clear_rate_limits` / `clear_upload_rate_limits` | état propre entre tests (autouse) |
| `fake_request` | fabrique une `FakeRequest` |

## À retenir

- `FakeRequest` = une `Request` sans serveur HTTP ;
- plugin pytest auto-activé (point d'entrée `pytest11`) ;
- isolation des tests par fixtures autouse ;
- **dev-only** : jamais une dépendance runtime (ADR-041).

## Voir aussi

- [Référence](../reference.md) : contrat, fixtures, vue d'ensemble.
