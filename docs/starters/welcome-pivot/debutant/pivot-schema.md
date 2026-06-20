# Le schéma SQL du pivot

Objectif : lire et comprendre la table pivot enrichie en SQL.

**Ce que vous allez apprendre :** une table pivot enrichie est une table comme
une autre : deux colonnes de clés (`article_id`, `tag_id`) **plus** les colonnes
d'attributs (`position`, `epingle`). La paire `(article_id, tag_id)` identifie
l'association ; les attributs décrivent la relation.

!!! note "Module opt-in — SQL visible"
    Le module n'invente aucun schéma caché : c'est votre `CREATE TABLE` qui fait foi.

## Le DDL de la table pivot

```sql
CREATE TABLE IF NOT EXISTS article_tag (
    article_id  INT NOT NULL,
    tag_id      INT NOT NULL,
    position    INT NOT NULL DEFAULT 0,
    epingle     TINYINT NOT NULL DEFAULT 0,
    PRIMARY KEY (article_id, tag_id),
    FOREIGN KEY (article_id) REFERENCES article(id),
    FOREIGN KEY (tag_id)     REFERENCES tag(id)
);
```

### Comprendre ce code

- La **clé primaire composite** `(article_id, tag_id)` garantit qu'une paire
  n'apparaît qu'une fois : un tag n'est attaché qu'une seule fois à un article.
- `position` et `epingle` sont les **attributs de la relation** — ce qui fait du
  pivot un pivot *enrichi*.
- Les `FOREIGN KEY` ancrent l'intégrité référentielle côté base.

!!! tip "Unicité de la paire"
    La clé primaire composite est la **vraie** garantie d'unicité. Le service
    propose en complément un contrôle applicatif (`unique_pair`), vu au niveau
    avancé — mais la contrainte SQL reste la défense de fond.

## La correspondance service ↔ table

| Paramètre du service | Colonne SQL |
|----------------------|-------------|
| `source_key="article_id"` | `article_id` |
| `target_key="tag_id"` | `tag_id` |
| `pivot_fields=["position", "epingle"]` | `position`, `epingle` |

Le service écrit et lit **exactement** ces colonnes, jamais d'autres.

## À retenir

- Une table pivot enrichie = clés `(source, target)` + colonnes d'attributs.
- Clé primaire composite = unicité de la paire au niveau base.
- Les `pivot_fields` du service correspondent aux colonnes d'attributs.

## Après ce starter

Vous comprenez le stockage. Faisons le **bilan** du niveau débutant.

[Bilan du niveau débutant](bilan.md)
