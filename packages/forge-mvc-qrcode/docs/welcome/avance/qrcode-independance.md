# Indépendance du cœur

Objectif : comprendre pourquoi le QR Code est un opt-in, et non une brique du cœur.

**Ce que vous allez apprendre :** Forge Core ne dépend pas de `forge-mvc-qrcode`.
La dépendance va de l'opt-in vers le cœur, jamais l'inverse.
Une application qui n'installe pas le paquet ne voit aucune référence aux QR Codes.

Troisième palier du **niveau avancé**.

## Ce que ce starter montre

- la règle de dépendance de l'opt-in ;
- ce que cela implique pour votre application.

## La règle

```text
Forge Core ne sait rien des QR Codes.
forge-mvc-qrcode fournit une API simple.
L'application décide ce qu'elle encode.
```

- Le générateur s'appuie sur `segno`, déclaré uniquement par le paquet, jamais par le cœur.
- `QrCodeResponse` importe `core.http.Response` : l'opt-in dépend du cœur, c'est le sens autorisé.
- Aucun fichier du cœur n'importe `forge_mvc_qrcode`, ce qui est verrouillé par un test.

## Ce que cela vous apporte

- Vous n'embarquez la génération de QR Codes que si vous l'installez.
- Le cœur reste minimal et auditable, fidèle au périmètre défini par l'ADR-004.
- Retirer le paquet ne casse pas le cœur : il n'en a jamais dépendu.

## À retenir

- L'opt-in dépend du cœur, le cœur ignore l'opt-in.
- `segno` est une dépendance du seul paquet `forge-mvc-qrcode`.

## Après ce starter

Vous avez fait le tour du socle.
Place au bilan du niveau avancé.

[Bilan avancé](bilan.md)
