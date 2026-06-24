# ADR-049 — Repositionnement : framework de production auditable

## Statut

Accepté — bêta publique 1.0 (`1.0.0-beta.x`).

---

## Date

2026-06-24

---

## Contexte

Jusqu'ici, l'identité publique de Forge se résumait par le mot « pédagogique »
(`CLAUDE.md` § 1 : « explicite, pédagogique, testable et durable » ; vitrine et
README parlant de « démonstrateurs pédagogiques » et de « prototypes »).

Le but du projet a été explicité : faire de Forge un **produit adopté**, c'est à
dire un framework sur lequel des tiers bâtissent des applications **en
production**, et non seulement un support d'apprentissage.

Or le cadrage « pédagogique / prototype » **disqualifie** Forge auprès de ce
public : un ingénieur qui évalue un framework pour la production lit
« pédagogique » et conclut « pas pour moi ». Le positionnement contredisait donc
l'objectif. Les propriétés techniques de Forge (explicite, sans magie, SQL
visible, sécurisé par défaut, runtime minimal) ne changent pas ; ce sont des
vertus de **production** (auditabilité, absence de surprise, faible surface
d'attaque et de maintenance) autant que d'enseignement.

---

## Décision

L'identité publique de Forge devient : **« le framework web Python que l'on peut
lire en entier », pour des applications de production dont on comprend et audite
chaque ligne**.

- Le caractère **pédagogique** n'est plus l'identité : il devient une
  **conséquence** de la lisibilité (un code que l'on peut lire en entier est, de
  fait, enseignable). Le parcours d'accueil et les starters restent une rampe
  d'apprentissage assumée, c'est à dire une **fonctionnalité**, pas la promesse
  centrale.
- La cible affichée devient : outils internes, applications métier durables,
  sites publics avec administration, et tout contexte (sécurité, conformité) où
  la « magie » d'un gros framework est un risque plutôt qu'un confort.
- Aucune propriété technique ni aucun principe de la charte n'est retiré : ce
  repositionnement réinterprète les mêmes principes (explicite, refus de la
  magie cachée, SQL visible, sécurisé par défaut, noyau minimal) comme des
  atouts de production.

---

## Conséquences

- **Vitrine et README** repositionnés (accroche « lire en entier », cible
  production auditable, retrait de « pédagogique / prototype » comme identité).
- **`CLAUDE.md` § 1** porte encore « pédagogique » dans la phrase d'identité.
  Ce fichier est protégé et refondu aux tags majeurs (§ 10) : la mise à jour de
  la phrase d'identité (« explicite, auditable, testable et durable », le
  pédagogique devenant dérivé) est à intégrer à la prochaine refonte, pas en
  écriture directe.
- Un balayage de la documentation reste à faire pour distinguer les emplois
  légitimes de « pédagogique » (parcours d'accueil, starters, exemples) des
  emplois où il tenait lieu d'identité.
- Ce repositionnement va de pair avec la **promesse de confiance** sur la
  licence (bascule MIT datée et critère vérifiable, `LEGAL-LICENSE-ROADMAP-001`):
  un produit visé pour la production exige clarté du « pourquoi » **et** garantie
  de durée.

---

## Relation avec la charte (ADR-007)

La charte v2 et ses onze principes restent **inchangés et non négociables**.
Le présent ADR ne modifie aucun principe : il fixe le **positionnement** et la
**communication** du projet, qui se situent au-dessus des principes et s'appuient
sur eux. En particulier, « refuser la magie cachée », « garder SQL visible » et
« sécuriser par défaut » sont les fondements directs de l'argument
d'auditabilité en production.

---

## Alternatives écartées

- **Conserver l'identité « pédagogique »** : cohérente avec l'histoire du projet,
  mais incompatible avec l'objectif d'adoption en production (écartée pour cette
  raison).
- **Abandonner toute dimension pédagogique** : la rampe d'apprentissage (parcours
  d'accueil, starters) est un différenciateur réel et un atout d'adoption ;
  écartée. Le pédagogique est conservé comme conséquence et fonctionnalité, pas
  comme promesse centrale.

---

## Liens

- Objectif et plan d'adoption : voir le repositionnement README / vitrine.
- Promesse de confiance : [`LEGAL-LICENSE-ROADMAP-001`](../roadmap/forge-roadmap.md) et [`docs/philosophy/licence.md`](../philosophy/licence.md).
- Charte : [`ADR-007`](007-charter-v2-adoption.md), `CHARTE_DOC.md`.
