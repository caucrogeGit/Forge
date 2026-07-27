# Aide-mémoire Audit

Synthèse de l'API de `forge-mvc-audit`, à garder sous la main.

## Enregistrer une action

| Appel | Résultat |
|-------|----------|
| `record_audit("eleve.cree")` | Insère une trace ; renvoie l'id de la ligne. |
| `record_audit("eleve.cree", actor="prof.dupont")` | Indique l'auteur de l'action. |
| `record_audit("note.modifiee", target_type="eleve", target_id=42)` | Désigne l'objet visé. |
| `record_audit("note.modifiee", details="12 à 14")` | Ajoute un complément libre. |

`action` est obligatoire ; une action vide lève `AuditError`.

## Relire le journal

| Appel | Résultat |
|-------|----------|
| `get_audit_log()` | Les entrées les plus récentes (id décroissant). |
| `get_audit_log(limit=20)` | Borne le nombre de lignes (plafond `MAX_LIMIT`). |
| `get_audit_log(action="note.modifiee")` | Filtre par action. |
| `get_audit_log(actor="prof.dupont")` | Filtre par auteur. |
| `get_audit_log(target_type="eleve", target_id=42)` | Filtre par cible. |

Les filtres se combinent en ET ; `limit < 1` lève `AuditError`.

## L'entrée AuditEntry

| Champ | Contenu |
|-------|---------|
| `id` | Identifiant de la ligne. |
| `actor` | Auteur de l'action (ou `None`). |
| `action` | Libellé de l'événement. |
| `target_type` / `target_id` | Objet visé (ou `None`). |
| `details` | Complément libre (ou `None`). |
| `created_at` | Date et heure (chaîne). |

## Constantes et erreurs

| Nom | Valeur ou rôle |
|-----|----------------|
| `TABLE_NAME` | `audit_log` |
| `MAX_LIMIT` | `1000` |
| `AuditError` | Levée sur action vide ou `limit < 1`. |

## Mise en place de la table

```bash
forge audit:init
forge migration:apply
```

## Rappel

Forge Core ne dépend pas du paquet.
L'audit est applicatif : l'application décide ce qu'elle trace.
