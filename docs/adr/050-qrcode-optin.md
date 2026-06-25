# ADR-050 : Opt-in QR Code `forge-mvc-qrcode`

## Statut

Acceptée

S'inscrit dans [ADR-004](004-core-perimeter.md) (périmètre du core minimal) et
[ADR-008-bis / ADR-016](016-opt-in-unification.md) (modèle opt-in) : une brique
générique mais non essentielle relève d'un paquet optionnel, pas du cœur.

---

## Contexte

La génération de QR Codes est un besoin fréquent dans des applications variées :
badges, tickets, liens rapides, inventaire matériel, accès à une activité
pédagogique, lien vers un QCM, usages futurs avec MFA ou Forge Design.

Cette brique **échoue volontairement au test de légitimité d'ADR-004** : « si je
retire cette fonction du core, une application Forge basique tourne-t-elle
encore ? » → oui. Le QR Code n'est pas une primitive du framework. Il ne doit pas
entrer dans Forge Core, ni devenir une dépendance obligatoire du cœur.

## Décision

Créer l'opt-in `forge-mvc-qrcode`, découplé du core, avec une API minimale et
explicite :

- `QrCode.from_text(text)` puis `to_png()` (octets PNG) et `to_svg()` (texte SVG) ;
- `QrCodeResponse.from_text(text, fmt="png"|"svg")` qui renvoie une
  `core.http.Response` servable depuis un contrôleur ;
- `QrCodeError` pour les entrées invalides (texte vide, format inconnu).

La règle de dépendance est unidirectionnelle :

```text
Forge Core ne sait rien des QR Codes.
forge-mvc-qrcode fournit une API simple.
L'application décide ce qu'elle encode.
```

### Bibliothèque retenue

`segno` : génération de QR Codes en **pur Python**, **sans dépendance** (pas de
Pillow), écriture **PNG et SVG natives**, licence BSD, maintenue. Déclarée
uniquement dans le `pyproject.toml` du paquet, jamais dans le cœur.

## Conséquences

- Le cœur reste autonome : aucun import de `forge_mvc_qrcode`, `segno` absent de
  ses dépendances (verrouillé par un test).
- Le paquet suit les conventions opt-in : `py.typed`, `# pyright: strict`, smoke
  test, doc embarquée (ADR-038) agrégée par le plugin monorepo.

## Hors périmètre de ce socle

Commande CLI `forge qrcode:*`, stockage dans `storage/`, génération PDF, scanner
de QR Code, logique métier (badge, ticket, inventaire), intégration MFA/TOTP ou
Forge Design. Ces sujets relèvent de tickets ultérieurs.
