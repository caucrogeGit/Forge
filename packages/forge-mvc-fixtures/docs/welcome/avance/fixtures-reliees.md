# Relier les fixtures entre elles

Objectif : produire un jeu de données réaliste où les tables se référencent, un `eleve` rattaché à un compte `users`, sans jamais coder d'`Id` en dur.

**Ce que vous allez apprendre :** les colonnes réelles de vos factories, la référence à une autre table par une clé naturelle, et l'ordre de chargement qui respecte les clés étrangères.

## Les colonnes sont celles de la table

Une factory produit un dict dont les clés sont les **colonnes réelles** de la table, pas les noms de champs du contrat.
Un champ `nom` devient la colonne `Nom`, un champ `user_id` la colonne `UserId` ; une clé étrangère déclarée en `foreign_key` garde son nom snake (`user_id`).

C'est exactement ce que `fixtures:make-factory` échafaude pour vous :

```bash
forge fixtures:make-factory eleve
```

Le SQL généré porte donc les bonnes colonnes, et tourne tel quel sur votre backend (MariaDB comme PostgreSQL).

## Référencer une autre table

Un `eleve` pointe un compte `users`. Au moment de générer les fixtures, l'`Id` du compte n'existe pas encore : il sera attribué par la base au chargement.
On référence donc la ligne par une **clé naturelle** (un email, un identifiant unique), pas par son `Id` :

```python
from forge_mvc_fixtures import Factory


class EleveFactory(Factory):
    table = "eleve"

    def rows(self, count: int) -> list[dict]:
        return [{
            "Nom": self.faker.last_name(),
            "Prenom": self.faker.first_name(),
            "UserId": self.reference("users", "Email", "prof.durand@ecole.fr"),
        } for _ in range(count)]
```

`self.reference("users", "Email", "prof.durand@ecole.fr")` ne renvoie pas un nombre : c'est une **référence** que la génération traduit en sous-requête SQL.

## Le SQL reste visible

Générez, puis lisez le `.sql` :

```bash
forge fixtures:generate eleve --rows 3 --seed 1
```

La référence est rendue en sous-requête, résolue au chargement contre le vrai `Id` :

```sql
INSERT INTO eleve (Nom, Prenom, UserId)
VALUES ('Durand', 'Hélène', (SELECT Id FROM users WHERE Email = 'prof.durand@ecole.fr' LIMIT 1));
```

Rien de caché : vous voyez la sous-requête, vous la relisez, vous la comprenez.

## L'ordre de chargement suit les clés étrangères

Un compte `users` doit exister avant l'`eleve` qui le référence.
`fixtures:load` s'en charge : il ordonne les fichiers par **tri topologique** du graphe de clés étrangères déclaré dans `mvc/entities/relations.json`.
La table `users` est chargée avant `eleve`, même si le nom de fichier `eleve.sql` vient avant `users.sql` dans l'alphabet.

```bash
forge fixtures:load --run
```

Si un jeu n'est pas triable (une dépendance circulaire), l'option `--no-fk-checks` désactive les contraintes le temps du chargement, puis les réactive.
À réserver aux cas où l'ordre ne suffit pas : par défaut, l'ordre topologique respecte l'intégrité, ce qui est préférable.

## Ce qu'il faut retenir

- les clés du dict sont les colonnes réelles de la table ;
- `self.reference(table, colonne, valeur)` relie une ligne à une autre par une clé naturelle, sans `Id` en dur ;
- `fixtures:load` charge dans l'ordre des dépendances ; `--no-fk-checks` reste une échappatoire pour les cycles.

## La suite

Voyons quand générer des fixtures et quand écrire une migration de seed.

[Continuer : fixtures ou migration de seed](fixtures-vs-seed.md)
