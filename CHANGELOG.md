# Changelog

## [Non publié]

### Ajouté

- **La vignette de première image est enfin servable (`VIDEO-POSTER-ROUTE-001`).**
  Le poster est engendré au transcodage et inscrit en base depuis la livraison du paquet. **Aucune route ne le servait**, et la réponse d'état ne le mentionnait pas. Revue du référentiel video.
  `duration_seconds`, `width` et `height` étaient dans la même situation : trois colonnes sondées au transcodage, remplies, et rien pour les lire. Une interface qui sonde `/videos/<uuid>/status` pour savoir quand afficher n'avait donc ni vignette, ni durée, ni dimensions, et devait interroger la base par un chemin qu'un client n'a pas, ou l'application réécrire une route en refaisant la résolution anti-traversal que la lecture porte déjà.
  `GET /videos/{uuid}/poster` sert la vignette, avec **la même garde que la lecture** : le chemin vient de la base, jamais de l'URL, et il est revalidé sous `storage_root`. Une ligne corrompue ou écrite par un autre composant ne permet pas de sortir du dossier de stockage, et le refus ne distingue pas « hors racine » de « absent », les distinguer apprenant à l'appelant ce que contient le disque.
  **`poster_path` n'est pas rendu**, et c'est délibéré : c'est un chemin de stockage, pas une URL, et le rendre publierait l'arborescence du serveur. Cette réponse évite déjà cela avec soin, la sortie d'erreur de ffmpeg en étant absente par construction. Un booléen `has_poster` dit qu'une vignette existe, et la route la sert.
  Une métadonnée absente **n'apparaît pas** dans la réponse : rendre `null` ferait afficher « durée : null » à une interface qui ne teste que la présence de la clé. Une valeur illisible ne lève pas, le contrat de cette vue étant de toujours pouvoir afficher quelque chose.
  Une vidéo sans vignette rend **409**, pas 404 : elle existe, sa vignette non, et un 404 ferait croire à une vidéo inconnue.

### Ajouté

- **Le back-office montre l'état des sessions (`ADMIN-SESSIONS-VIEW-001`).**
  `forge deploy:init` demande de planifier `forge sessions:gc`, et rien ne disait si ce minuteur tournait. `forge-mvc-sessions-db` compte les sessions depuis `SESSIONS-METRICS-001`, réparties par nature, et sait dire si la purge suit : **personne ne regardait ce nombre**, il fallait ouvrir un client SQL. Dernier point ouvert de la revue du référentiel sessions-db.
  Le panneau vit sur `/admin/_sessions`, et le tableau de bord y mène : une page qu'aucun lien n'atteint n'est pas une page. Le chemin porte un tiret bas de tête, `/admin/{slug}` capturant sinon `sessions` comme le slug d'une ressource, et la route est posée **avant** celle à slug, le routeur retenant la première qui correspond.
  Il répond à une question d'exploitation : une table qui grossit pendant que le nombre d'actives stagne signale un `sessions:gc` arrêté. Au delà de la moitié de lignes expirées, la page le dit et nomme la commande, au seuil que `purge_backlog_ratio` documente déjà.
  **Aucun identifiant de session n'est affiché**, et il n'y en a pas à afficher, la mesure rendant des totaux. Le contrat de la donnée l'interdit autant que le gabarit : `SessionsPanel` ne porte aucun champ d'identifiant, si bien qu'un gabarit modifié ne peut rien en faire fuir. Un identifiant lu sur un écran, une capture ou une épaule est une session volée.
  **Le couplage est souple**, comme pour `forge-mvc-rbac` et `forge-mvc-workflow` : `forge-mvc-admin` ne déclare pas `forge-mvc-sessions-db` en dépendance, et un test le vérifie. Son absence rend un panneau qui dit pourquoi il est vide, et une table absente ne fait pas tomber la page. Une page d'administration qui tombe parce qu'un panneau ne répond pas retire l'accès à tout le reste. L'indisponibilité ne rend pas des zéros : « aucune session » et « je ne sais pas » ne se corrigent pas au même endroit.
  Le panneau **ne révoque rien**, et c'est écrit. Fermer une session depuis cet écran demanderait de la désigner, donc de l'identifier, donc de l'exposer ; fermer toutes celles d'un utilisateur est possible sans cela, mais c'est un geste destructeur qui mérite sa décision propre.

### Modifié

- **`forge new` n'installe plus Node par défaut (`FORGE-NEW-NO-NODE-DEFAULT-001`).**
  Il lançait `npm install` puis `npm run build:css` à chaque création. Mesuré : **deux minutes sur cent quarante-quatre**, pour produire un `static/tailwind.css` **identique au bit près** à celui que le squelette versionne. La dépense était entière et son produit nul.
  Elle exigeait en outre une chaîne Node complète, `@parcel/watcher` compilé depuis ses sources compris. Le squelette active `engine-strict` : sous une version de Node antérieure à `.nvmrc`, `npm install` refusait de tourner et `forge new` échouait entièrement.
  **Cesser de reconstruire n'était honnête qu'à une condition** : que le fichier livré ne puisse plus dériver en silence. C'est ce que garantit `SKELETON-TAILWIND-CSS-STALE-001`, livré juste avant. Les deux vont ensemble, et dans cet ordre.
  Mesuré après : `forge new` passe de **144 s à 5,3 s**. Le parcours du guide de prise en main, qui rejoue le tutoriel de bout en bout, passe de 173 s à 10,7 s, et **cesse de se sauter** quand Node manque ou est trop ancien, ce qu'il faisait pour une raison étrangère à ce qu'il vérifie.
  **Rien n'est retiré, seule la dépense l'est.** Le squelette continue de livrer `package.json` et `static/src/input.css`. Node est à un appel de distance, annoncé plutôt que deviné : `forge new <nom> --with-node` à la création, ou `npm install && npm run build:css` plus tard. L'avertissement émis quand npm manque dit désormais que le CSS livré reste en place.
  La phase front quitte `forge.py` pour `cli/project/front_assets.py`, et les options de `new` pour `_options_de_new` : le budget de complexité plafonne `forge.py` et son `main`, et il demande une extraction, pas un plafond relevé. Huit doublures de test figeaient la signature exacte de `cmd_new` et se cassaient sur toute option nouvelle ; elles acceptent désormais ce qu'elles ne regardent pas.

### Ajouté

- **Le quota comptait des fichiers supprimés (`FILES-DELETE-FORGETS-001`).**
  Les suppressions retiraient le fichier du disque sans toucher au registre. La ligne restait, et `owner_usage_bytes` somme les tailles inscrites. Revue du référentiel images.
  Mesuré : trois dépôts d'un mégaoctet, puis trois suppressions par le chemin documenté, et le quota annonçait toujours **trois mégaoctets**, trois lignes restant au registre. Un utilisateur qui dépose et supprime finit refusé pour un espace qu'il n'occupe pas, avec un message « quota dépassé » impossible à diagnostiquer de l'extérieur : son stockage est vide.
  **Trois chemins, un seul défaut.** `delete_upload`, `delete_media_file` et `purge_orphan_variants` suppriment tous des fichiers sous `UPLOAD_ROOT`, et aucun ne désinscrivait. Le dernier est le plus ironique : c'est le nettoyage, et il faisait grossir le quota à chaque passage.
  Le défaut existait déjà pour toute application suivant le chemin documenté, `save_upload` puis `record_file`, puis `delete_upload`. `IMAGES-REGISTRY-RECORD-001` l'a étendu aux images en les faisant inscrire, ce qui est la contrepartie d'avoir fermé la faille de suppression : les deux gestes vont ensemble.
  L'oubli est **au mieux**, la table étant optionnelle : faire échouer une suppression parce qu'un registre n'est pas provisionné empêcherait de supprimer, ce qui est pire que le défaut corrigé. Il a lieu **quel que soit le sort du fichier**, une inscription décrivant un fichier absent étant fausse dans tous les cas.
  Un garde-fou lu sur l'arbre syntaxique refuse qu'une fonction publique supprime un fichier sans le désinscrire.

- **Ce que la purge de fichiers ne fait pas est désormais écrit (`DOC-FILES-RETENTION-SCOPE-001`).**
  `files:orphans` supprime des fichiers que rien ne réclame. Il n'existe pas de purge par ancienneté, et la documentation était **silencieuse** sur cette absence.
  Elle est délibérée : Forge ne sait pas qu'une facture se garde dix ans et une vignette trente jours. La différence avec `audit:gc --days`, `stats:gc --days` et `iot:gc --days` n'est pas de principe, ces commandes suppriment des lignes **dont elles connaissent le sens**, un événement de journal ou une mesure de capteur. Un fichier appartient au domaine de l'application, et supprimer par date sans savoir ce qu'on supprime est le geste qu'il ne faut pas offrir.
  Le chemin est donné plutôt que refusé : le registre porte `created_at`, indexé, et une rétention applicative tient en une requête suivie de `delete_upload` puis `forget_file`. L'écrire soi même force à nommer sa règle, ce qui est le bon endroit pour cette décision.

- **Une notification pouvait être écrite et jamais relue (`NOTIF-STORE-AS-VALIDATED-001`).**
  `notify` validait le destinataire sur sa forme **élaguée** et stockait la forme **brute**. Une notification écrite pour `"  professeur.42  "` était donc invisible à `get_notifications`, `unread_count` et `mark_all_read`, qui interrogent la valeur telle qu'on la leur passe. Revue du référentiel notifications.
  Mesuré : écrit avec `recipient = '  professeur.42  '`, relu avec `'professeur.42'` rendait **zéro notification et zéro non lue**. Aucune erreur nulle part, l'écriture rendant son identifiant comme si tout allait bien. C'est le pire mode de panne, tout paraît avoir marché.
  **Le paquet était incohérent d'une fonction à l'autre, et j'y ai contribué.** `mark_read` élaguait, seule de toutes ; elle a été ajoutée par `NOTIF-HTTP-ROUTES-001`, qui a donc creusé l'écart sans le voir. Une notification au destinataire mal saisi pouvait être listée, par correspondance brute, et pas marquée lue, par correspondance élaguée.
  La normalisation vit désormais à un seul endroit, traversée par l'écriture comme par la lecture, et un garde-fou lu sur l'arbre syntaxique refuse qu'une fonction à destinataire la contourne. Il a d'ailleurs attrapé `mark_read`, qui élaguait en ligne plutôt que d'appeler le normaliseur commun.
  **`type` était le seul champ ni validé ni normalisé**, alors que `recipient`, `message`, `data` et `target_url` le sont tous, et que c'est celui sur lequel un client branche son affichage. Il est désormais élagué, refusé vide, et refusé au delà des soixante-quatre caractères de sa colonne : tronquer donnerait un type sur lequel un gabarit brancherait à tort, et se rabattre en silence sur « info » donnerait un type que personne n'a écrit.
  **Le vocabulaire des types reste ouvert**, et ce n'est pas un oubli : une application réelle observée écrit `type="copie_a_corriger"`, et fermer la liste à « info, alerte, tâche » casserait ce que Forge est censé servir. Le contraste avec `forge-mvc-workflow` et `forge-mvc-sessions-db`, dont les vocabulaires sont fermés, est délibéré : là bas, une nature inventée rendrait la métrique incomparable d'un projet à l'autre.

- **La purge d'orphelins supprimait les images d'un autre opt-in (`IMAGES-REGISTRY-RECORD-001`).**
  `forge-mvc-images` écrit sous `UPLOAD_ROOT`, la racine que `forge-mvc-files` connaît, et n'inscrivait rien à son registre. `forge files:orphans` rapproche le disque et le registre : une image absente du registre y était **un orphelin**, et `--delete` la supprimait. Revue du référentiel files.
  **Le garde-fou du registre vide ne protégeait pas ce cas.** Il ne se déclenche que si le registre est **entièrement** vide. Un projet qui inscrit ses documents, comme la documentation de `forge-mvc-files` l'enseigne, et qui utilise cet opt-in pour ses images, avait un registre peuplé et des images signalées orphelines.
  Mesuré sur un projet portant un document inscrit et une image non inscrite : trois fichiers sur disque, une inscription, et deux orphelins signalés, l'original **et sa vignette**. Deux opt-ins officiels, dont l'un dépend de l'autre, et la purge de l'un supprimait les fichiers de l'autre.
  `save_image` et `generate_image_variants` inscrivent désormais tout ce qu'ils écrivent. **L'inscription est au mieux** : la table `forge_files` est optionnelle (ADR-094), et faire échouer une sauvegarde d'image parce qu'un registre n'est pas provisionné serait disproportionné. Ce n'est pas une dégradation silencieuse pour autant, sans cette table `find_orphans` lève aussi et la purge ne peut pas tourner : les deux cas s'alignent, et il n'y a pas de fenêtre où l'inscription manque pendant que la purge supprime.
  L'échec est journalisé sur une ligne, **sans pile** : ce chemin se déclenche une fois par fichier écrit, et une trace complète par vignette noierait le journal.
  La documentation de `forge-mvc-files` nomme désormais la limite générale : la purge suppose que le registre décrit tout ce qui vit sous `UPLOAD_ROOT`, et cette hypothèse est fausse dès qu'un composant écrit là sans inscrire.

- **Une pièce jointe se perdait en silence au passage par la file (`MAIL-QUEUE-ATTACHMENTS-REFUSED-001`).**
  `MAIL-ATTACHMENTS-001` a livré les pièces jointes, `MAIL-QUEUE-VIA-JOBS-001` la mise en file. Les deux ont été livrés séparément et **ne composaient pas**. Revue du référentiel mail.
  `message_to_payload` recopie huit champs nommés, et `attachments` n'en faisait pas partie. Mesuré : un message avec pièce jointe passait la sérialisation sans erreur, et ressortait de l'aller-retour **sans elle**. L'email partait, le journal inscrivait `sent`, et le destinataire recevait un corps annonçant un document absent. C'est le pire mode de panne, tout paraît réussi.
  La composition est pourtant celle que la documentation recommande, « la file est le point de passage de tout ce qui ne doit pas faire attendre une requête » : envoyer une facture en PDF est exactement ce qu'on met en file.
  **Sérialiser n'était pas viable.** La charge utile est du JSON rangé dans la colonne `payload` de la table `jobs`, de type `text` ; sur MariaDB un `TEXT` tient soixante-cinq mille octets, et une pièce jointe de dix mégaoctets en ferait quatorze millions une fois encodée. Deux cent treize fois la capacité de la colonne, et élargir celle ci ferait de la file une réserve de fichiers.
  `message_to_payload` refuse donc, en nommant les fichiers concernés et en disant quoi faire à la place : ranger le fichier, mettre en file sa référence, l'attacher dans le gestionnaire. **Le refus est uniforme**, et non conditionné à la taille : accepter les petites ferait marcher la chose en développement avec un PDF d'essai et échouer en production sur un vrai document, par une erreur de base opaque. Une fonctionnalité qui marche parfois est la plus difficile à diagnostiquer.
  Un garde-fou refuse qu'un champ de `MailMessage` ajouté demain soit ni recopié, ni refusé, ni dérivé : la cause était une liste de champs muette sur ce qu'elle laissait derrière.

- **`heartbeat` était inutilisable depuis le seul endroit où elle sert (`JOBS-HEARTBEAT-REACHABLE-001`).**
  Elle prolonge le bail d'une tâche longue, pour qu'elle ne soit pas reprise par `jobs:reclaim` alors qu'elle travaille encore, et se garde par le jeton de réservation. Le worker appelait `handler(payload)` : un gestionnaire n'avait **aucun moyen** d'obtenir ce jeton. Revue du référentiel jobs.
  **L'exemple documenté cassait la tâche.** La référence montre `def transcoder(payload, *, claim_token)`. Mesuré, un gestionnaire écrit ainsi levait `TypeError`, repartait en réessai au bout de dix secondes, puis finissait `failed`. Il ne se contentait pas d'être inopérant, et le motif inscrit dans `last_error` parlait d'un argument manquant plutôt que du travail.
  Un gestionnaire qui déclare `claim_token`, en mot-clé ou par `**kwargs`, le reçoit désormais. Celui qui ne déclare rien continue de recevoir la seule charge utile, et **aucun projet existant n'a de geste à faire**. Ce n'est pas de la magie cachée, c'est le gestionnaire qui demande. Un appelable dont la signature ne s'inspecte pas ne reçoit rien : deviner ferait échouer un gestionnaire qui marchait.
  Un test rejoue l'exemple exact de la documentation, l'écart entre les deux étant précisément ce qui a fait le défaut.

- **Le réglage de durée des sessions authentifiées ne servait à rien (`SESSIONS-TTL-AUTHENTICATED-APPLIED-001`).**
  `SESSIONS-TTL-PER-KIND-001` a livré trois durées par nature de session, et la documentation promet trois variables d'environnement pour les régler. Elle argumente même sur le cas qui ne fonctionnait pas : « réglée court, elle déconnecte les utilisateurs authentifiés toutes les heures ». La revue du référentiel sessions-db l'a relevé.
  `ttl_for()` n'était appelée qu'à **un seul endroit**, `create()`, qui crée une session anonyme. La connexion passe par `authenticate()`, qui prenait le `ttl_seconds` de son appelant, et le cœur appelle avec `SESSION_DURATION`, égal au défaut historique de trois mille six cents secondes.
  **Mesuré** : un exploitant réglant `SESSION_TTL_AUTHENTICATED=1800` pour raccourcir ses sessions authentifiées obtenait trois mille six cents secondes quand même, sans un mot. C'est un réglage de **sécurité** : celui qui l'a posé croyait ses sessions raccourcies, et elles ne l'étaient pas. Le module refuse pourtant une valeur illisible, en disant que « retomber en silence sur le défaut donnerait une durée que personne n'a écrite » ; la valeur lisible était ignorée tout aussi silencieusement.
  `authenticate()` suit désormais la règle de `create()` : le `ttl_seconds` de l'appelant l'emporte quand il **diffère** du défaut historique, sinon la durée de la nature s'applique. Un projet qui l'avait réglé à la main garde son réglage, le retirer sous ses pieds serait une rupture silencieuse dans l'autre sens.
  Un garde-fou lu sur l'arbre syntaxique refuse que les deux chemins divergent à nouveau : c'est leur divergence qui avait rendu une des trois durées inerte. La documentation dit par ailleurs que la nature `remembered` s'écrit depuis l'application, le protocole `SessionStore` du cœur n'ayant pas de paramètre de nature et Forge n'implémentant pas de « se souvenir de moi ».

- **`forge-mvc-fixtures` n'était vérifié par aucun typage (`PKG-PYRIGHT-FIXTURES-001`).**
  Le commentaire de `[tool.pyright]` annonce que « le cliquet couvre le cœur, **tous les opt-ins** et les 4 backends BDD ». Il en couvrait **vingt-six sur vingt-sept** : `forge-mvc-fixtures` manquait à `include` comme à `extraPaths`.
  Ses dix fichiers portent pourtant tous `# pyright: strict`. Ils ont donc été écrits pour être vérifiés, et ne l'étaient pas. **Trois erreurs s'y étaient accumulées** sans qu'un seul contrôle proteste : deux fonctions mortes laissées dans `cli/load.py` par le déplacement de l'ordonnancement vers `ordering.py` (`FIXTURES-FK-ORDER-ROBUST-001`), et un type partiellement inconnu que trois `pyright: ignore` masquaient à moitié.
  Le code est corrigé, et le paquet passe à zéro erreur. Le typage de `ordering.py` nomme son type une fois par `cast` plutôt que d'empiler des `ignore` à chaque accès : c'est un `ignore` de trop qui avait rendu l'erreur invisible.
  Une annonce de complétude qui n'en est pas fait cesser de vérifier : on lit la phrase, on conclut que c'est couvert, et on ne compte jamais.
  Le paquet est ajouté aux deux listes du `pyproject.toml` racine, et la vérification est **prouvée active** : une faute injectée dans `ordering.py` fait passer le pyright du projet de zéro à dix erreurs, là où elle serait restée invisible. Un garde-fou refuse désormais qu'un paquet du dépôt manque à `include` ou à `extraPaths`, et que la liste diverge de ce que le dépôt contient.
  **Un garde-fou a résisté, et il figeait le moyen.** Il refusait la chaîne `pyotp` n'importe où dans le `pyproject.toml` du cœur, alors que sa propre docstring énonce la fin visée, « pas dans les **dépendances runtime** du core ». Le fichier ne pouvait donc pas expliquer pourquoi `forge-mvc-mfa` est hors de `all`, alors que nommer ce qu'un opt-in tire avec lui est la seule raison durable de l'en écarter. Il lit maintenant les dépendances déclarées, extras compris, et il a été mis en défaut : une vraie dépendance `pyotp` le fait échouer en la nommant.
  Le commentaire des extras portait au passage quatre mentions « Alpha » pour `images`, `mfa`, `iot` et `video`, contredites par leurs propres classifieurs et sans objet depuis qu'un opt-in suit la version du cœur. Elles sont remplacées par la raison durable de leur exclusion de `all`, ce qu'ils tirent avec eux : Pillow, `cryptography`, `paho-mqtt`, les binaires ffmpeg. Une dépendance ne change pas quand la maturité change. Le même commentaire annonçait « quatre exclus » là où vingt-quatre opt-ins sur vingt-sept sont hors de `all`.

- **Aucun opt-in ne s'attribue plus une maturité propre (`OPTINS-MATURITY-FOLLOWS-CORE-001`).**
  Les vingt-sept opt-ins portent déjà la version du cœur et le même classifieur. Leur **prose** disait autre chose : dix fichiers annonçaient un « Statut : Beta » par paquet, plusieurs adossé à `1.0.0-beta.9` ou `1.0.0-beta.13`, séries closes depuis le renumérotage vers 1.0.
  **Ce n'était pas une coquetterie, la maturité annoncée avait dérivé.** Le README de `forge-mvc-mfa`, module de sécurité, annonçait que « la politique de rotation de la clé Fernet n'est pas encore formalisée » alors que `MFA-KEY-ROTATION-001` l'avait livrée. Il conseillait des **sticky sessions** en multi-worker, là où le paquet livre `DbTotpReplayStore`, magasin partagé par tous les workers, et il ignorait que la parade du rate-limit se pose désormais au proxy (`DEPLOY-NGINX-RATE-LIMIT-001`). Il citait aussi « Forge 2.4.0 » et « Forge 3.0 », numérotation abandonnée.
  La référence MFA portait une liste d'« exigences avant production-ready » dont la rotation, désormais livrée, et deux entrées sans objet, « Publication PyPI » et « Passage en Beta ». Elle ne garde que ce qui relève réellement de l'exploitant, la **sauvegarde de la clé**, dont la perte rend tous les secrets TOTP illisibles, et la revue de son propre déploiement.
  **Trois garde-fous exigeaient le mot « Beta »** dans la documentation MFA, et un quatrième le titre exact d'une sous-section. Ils figeaient le moyen : les satisfaire aurait demandé de réafficher un stade périmé, ce que la règle D interdit. Ils sont réalignés sur la fin qu'ils protégeaient, un bloc de situation en début de page et une page qui dit ce qui est en place. Un cinquième exigeait la trace du ticket de publication PyPI, et lui avait raison : mon édition l'avait fait perdre, elle est remise.
  Le cliquet de style s'est resserré au passage : le retrait des titres « Statut : Beta — … » a fait sortir deux README de sa liste gelée de tirets cadratins, et il refuse qu'on les y laisse.
  Un garde-fou refuse qu'une documentation de paquet prête à un opt-in un cycle de maturité propre. Son détecteur est mis en défaut dans les deux sens, cinq formules attrapées et quatre mentions historiques épargnées.
  Il ne garde **pas** les numéros de version, et c'est délibéré : `tools/check_version_sync.py` le fait depuis `PKG-VERSION-SYNC-CHECK-001`, sur **soixante et un** fichiers et non vingt-sept, `__version__` des modules, pins `forge-mvc>=`, extras du pyproject racine, `core/__init__.py`, `forge.py`, pin du squelette et `package.json` compris. Il est joué par la suite de tests comme par `release-validate.sh`, et mis en défaut il nomme le fichier fautif. Une première rédaction de ce garde-fou doublait ce contrôle sur les vingt-sept `pyproject.toml` : deux gardiens de la même chose, c'est l'assurance que l'un des deux dérive, et le principe 11 refuse deux façons officielles de faire la même chose.

- **Le registre de conditions de transition n'était consulté par personne (`WORKFLOW-CONDITIONS-APPLIED-001`).**
  `WORKFLOW-CONDITIONS-001` a livré un registre, et sa raison d'être est écrite dans son propre module : l'application vérifiait ses règles avant d'appeler, chacune à sa façon, si bien que « deux chemins menant au même état s'oubliaient l'un l'autre, et le second passait sans contrôle ». La revue du référentiel workflow l'a relevé.
  **Le registre ne corrigeait pas cela.** `apply_transition`, la seule fonction du paquet qui sait qu'une transition a lieu, ne le consultait pas. Il fallait appeler `ensure_conditions` à chaque site, donc s'en souvenir à chaque site, donc reproduire exactement le défaut visé.
  Mesuré : une condition enregistrée pour refuser le passage à `validee` n'était jamais appelée, et `apply_transition` rendait `'validee'`.
  Ce n'est pas de la magie cachée, c'est l'inverse. L'application a **explicitement** enregistré ses conditions, et les consulter à l'endroit où une transition a lieu est ce pour quoi le registre existe. Un registre que rien ne lit est une décoration.
  L'ordre est désormais : transition déclarée, conditions, `before`, `commit`, `after`. Les conditions passent **avant tout effet de bord**, `before` pouvant écrire, et une transition non déclarée est refusée **avant** elles, pour ne pas exécuter du code applicatif sur un passage qui n'existe pas. Une application qui appelait déjà `ensure_conditions` les évalue deux fois, sans effet : une condition est un prédicat par contrat.
  Un garde-fou lu par `ast` refuse qu'une réécriture d'`apply_transition` perde cet appel.

- **L'audit des refus RBAC était sourd sur deux gardes, dont la canonique (`RBAC-DENIAL-AUDIT-COMPLETE-001`).**
  `RBAC-DENIAL-AUDIT-001` a livré l'observation des refus, et sa ligne de roadmap le dit honnêtement : « les **3** gardes annoncent ». Le paquet en compte cinq. La revue du référentiel rbac l'a relevé.
  Les deux oubliées sont les deux qui comptent le plus. `require_user_permission` se décrit dans sa propre docstring comme la garde **canonique** (`SEC-RBAC-CANONICAL-GUARD-001`), celle que « les nouveaux projets utilisent ». `require_instance_permission` refuse l'accès à l'objet d'un autre, c'est à dire le refus qu'un exploitant veut précisément voir passer.
  **La conséquence est pire qu'un simple manque.** Une application qui branchait l'observateur sur `forge-mvc-audit` obtenait un journal **qui paraissait complet** : les refus contractuels y figuraient, ceux du préfixe aussi, et ceux de la garde canonique manquaient sans que rien ne le signale. Une énumération de droits menée contre des routes gardées par la garde canonique ne laissait aucune trace, ce que ce module existe précisément pour éviter.
  La docstring de `notify_permission_denied` affirmait par ailleurs « Appelée par les gardes du paquet », faux pour deux d'entre elles, et la référence annonçait « les trois gardes ».
  Les deux gardes annoncent désormais, avec les sources `user-permissions` et `instance`, cette dernière nommant les **deux** permissions demandées, le refus venant de ce qu'aucune ne s'applique. Un 401 reste hors du journal d'accès : il dit « je ne sais pas qui vous êtes », pas « vous n'avez pas le droit », et les confondre noierait les vrais refus sous les visiteurs anonymes.
  Un garde-fou lu par `ast` refuse qu'une fonction `require_*` du paquet refuse sans annoncer. Les `has_*` en sont exclus : ils rendent un booléen, et c'est l'appelant qui décide s'il refuse.

- **Les champs calculés étaient livrés pour un format que les applications n'utilisent pas (`ENTITIES-COMPUTED-CANONICAL-001`).**
  `ENTITIES-COMPUTED-FIELDS-001` les avait livrés, et son test les déclarait au **format interne V1** (`column`, `sql_type`, `python_type`), celui qu'ADR-086 élimine. Le vert du ticket ne disait donc rien du chemin qu'empruntent les applications. La revue du référentiel entities l'a relevé.
  Mesuré sur le chemin canonique, la chaîne était rompue **en trois endroits**. `field.schema.json` porte `additionalProperties: false` et ne déclarait pas `computed` : `forge entity:validate` refusait le contrat. Le résolveur de champs laissait tomber l'expression, si bien que le champ ressortait en colonne ordinaire. `make:crud` engendrait alors un `INSERT` et un `UPDATE` sur une colonne qui devait être en lecture seule.
  **Le deuxième point est le pire des trois** : la perte ne levait rien. Passé dans le normaliseur, un contrat portant `computed: "qte * pu"` ressortait avec `sql_type INTEGER` et aucune trace de l'expression. Qui l'ajoutait à la main obtenait une colonne, pas une erreur.
  `computed` est désormais déclaré dans le contrat, propagé par le résolveur, et le SQL engendré est vérifié de bout en bout depuis un contrat canonique : `SELECT` projette `(qte * pu) AS "Total"`, `INSERT` et `UPDATE` l'ignorent.
  Six combinaisons sont refusées sur le vocabulaire canonique, où `required` et `type` remplacent `nullable` et `sql_type` : `required`, `unique`, `default`, `form`, `source` et le type `foreign_key`. Chacune produirait un SQL faux plutôt qu'une simple maladresse. Le motif du schéma refuse aussi une expression faite d'espaces, que `minLength: 1` laissait passer et qui aurait produit `(   ) AS "Total"`.
  La documentation montrait le même exemple au format interne : elle montre le format canonique, et dit ce qui était rompu.


- **Le CSS livré par le squelette ne couvrait plus ses propres gabarits (`SKELETON-TAILWIND-CSS-STALE-001`).**
  Le squelette versionne `static/tailwind.css`. Il lui manquait **quinze classes** que ses gabarits utilisent, dont `grid`, `grid-cols-2`, `sm:grid-cols-4`, `flex-wrap`, `text-4xl`, `bg-red-600`, `hover:bg-red-700` et `text-white`.
  La dérive était masquée : `forge new` reconstruit le CSS par `npm install && npm run build:css`. Mais **npm peut être absent**, cas que Forge gère explicitement par un avertissement, et le projet part alors avec le fichier versionné. Sa page « charte » perd sa grille, et le bouton `danger` de `components/ui.html` perd son fond rouge et son texte blanc : un geste destructeur qui ne se distingue plus d'un lien ordinaire. L'avertissement dit « Node.js / npm absent », pas « votre mise en page sera fausse », et personne ne relie les deux.
  Le fichier est reconstruit, et un garde-fou fige la fin plutôt que le moyen : toute classe relevée dans un gabarit a une règle dans le CSS livré. Ni la version de Tailwind, ni la taille, ni l'empreinte, qui changent à chaque construction sans rien dire de la couverture.
  **Le relevé lit deux formes, parce qu'une seule ne suffit pas.** Les attributs `class="..."`, exacts mais aveugles là où le risque est le plus grand : les classes qui manquaient vivaient dans une table de variantes Jinja, `{% set styles = {"danger": "text-white bg-red-600 …"} %}`. Et les chaînes dont tous les jetons ont la forme d'un utilitaire Tailwind **et** dont au moins un est déjà dans le CSS. Cette ancre n'est pas décorative : sans elle, la prose française des gabarits fournissait quatre-vingt-dix-huit faux positifs, « avec », « toute », « valeur ».
  **Sa portée est dite plutôt que surestimée.** Vérifié contre le fichier périmé, il retrouve douze des quinze classes ; les trois autres ne vivent dans aucune de ces deux formes. Une couverture complète demanderait de lancer Tailwind, donc npm, donc de sauter le contrôle partout où npm manque. Douze sur quinze toujours joués valent mieux que quinze parfois.

- **Le cliquet des README d'opt-in sautait plus du tiers de sa cible, et sa règle était fausse (`META-README-RATCHET-WIDEN-001`).**
  Il ne reconnaissait une commande que citée entre accents simples **et** précédée de `forge `. Ni un bloc ```bash, qui est précisément l'endroit où un README montre comment installer et provisionner, ni une citation nue comme `mail:doctor`. **Dix paquets sur vingt-sept étaient sautés** faute de citation reconnue : le relevé paraissait large en ne regardant pas les deux tiers de sa cible. Cinq le restent, et ceux là ne citent aucune commande sous aucune forme.
  Sa règle était fausse par ailleurs, et l'élargissement l'a révélé. Il exigeait qu'une commande citée dans un **espace de noms de l'opt-in** figure dans son `COMMANDS`. Or un espace se partage : `db:config` vient de `forge-mvc-entities`, `db:init` et `db:apply` du cœur, dépêchées en dur par `forge.py`. Le README d'entities, qui cite les trois, aurait été accusé de promettre deux commandes qui existent et fonctionnent.
  La règle porte désormais sur ce que Forge accepte, quel qu'en soit le déclarant : l'aide générale, l'aide riche, le dispatch en dur de `forge.py` lu par `ast`, et le `COMMANDS` de chaque opt-in, soit cent quatorze commandes. Aucun README n'annonce de commande inexistante, vérifié avant comme après : le trou était de couverture, pas de correction, et un cliquet sert à attraper la faute suivante.

- **Un garde-fou vérifie les liens absolus, que `mkdocs --strict` laisse passer (`META-DOC-ABSOLUTE-LINKS-001`).**
  Le build strict vérifie les liens **relatifs** et échoue sur une cible absente. Il ne vérifie pas les liens **absolus** : il les signale d'une ligne `INFO ... it was left as is`, et sort en succès quelle que soit la cible.
  Ce n'est pas théorique. `DB-POOL-THREADS-DOC-001` a livré un lien vers `/docs/forge/reference/database/connection/`, page qui n'existe pas, la vraie étant `/docs/forge/core-database/connection/`. Le piège est que le préfixe d'URL d'une documentation embarquée est le `site_name` de son `mkdocs.yml`, et non son chemin de fichier. Vérifié en réintroduisant la faute : `mkdocs build --strict` sort en 0, le garde-fou échoue.
  Le dépôt porte quarante-trois liens absolus, dont **vingt-six vers une seule ancre**. La reformuler casserait vingt-six liens d'un coup, en silence, sur le site publié.
  Les URL sont reconstruites depuis les sources plutôt que lues dans `site/`, avec les mêmes règles que MkDocs, le `docs_dir` de la racine plus le `site_name` de chaque `!include`. Un contrôle qui exigerait `site/` se sauterait quand le dossier n'existe pas, c'est à dire la plupart du temps, et un garde-fou sauté ne garde rien. La fonction de slug est **celle de MkDocs**, importée et non réécrite, une réimplémentation approximative inventant des ancres fausses dans les deux sens.

### Corrigé

- **Le relevé de SQL non portable prenait un gabarit Markdown pour une instruction SQL.**
  `tests/test_optin_dml_dialect_001.py` classe comme SQL toute chaîne d'un opt-in contenant `SELECT`, `INSERT`, `UPDATE`, `VALUES` ou `DELETE`. Cette largeur est voulue, le SQL de Forge s'assemblant par fragments dont beaucoup n'ont pas de verbe.
  Elle a un revers, révélé par `DEPLOY-NGINX-RATE-LIMIT-001` : le gabarit du guide de déploiement, deux cents lignes de Markdown, contient `--delete` dans son tableau des gestes périodiques, ce qui le classait SQL, puis `RATE-LIMIT-001` dans un code de ticket, ce qui le déclarait non portable. Deux mots de prose.
  Renommer la section pour contenter le détecteur aurait été céder au symptôme. Le relevé écarte désormais les chaînes portant un titre Markdown, aucune instruction SQL n'en contenant. **Mesuré avant d'être appliqué** : 387 chaînes classées SQL, 386 après, la seule écartée étant ce gabarit. Un resserrement plus ambitieux, « verbe plus clause », en aurait écarté 261, donc du vrai SQL. Un test fige l'étroitesse de l'exclusion.

- **Ce que fait le pool de connexions quand une requête ouvre des threads n'était écrit nulle part (`DB-POOL-THREADS-DOC-001`).**
  Le runtime de Forge est synchrone, ce qui n'interdit pas de paralléliser des appels sortants dans une requête. Rien ne disait ce que la base y devient.
  Mesuré sur MariaDB, pool de cinq, appels tenant leur connexion trois cents millisecondes : quatre threads en 0,32 s, huit en 0,60 s, vingt en 1,21 s, sans un seul refus. Le parallélisme reste gagnant, vingt appels en série coûteraient six secondes, mais il est **plafonné par `DB_POOL_SIZE`**, cinq par défaut et par processus, non par le nombre de threads.
  **Le fait qui compte est ailleurs**, et c'est celui qu'un développeur ne voit pas venir. Une requête qui parallélise prend les connexions de tout son processus, donc de toutes les requêtes que ce travailleur sert au même moment. Mesuré : pendant qu'une voisine tient le pool avec dix appels d'une seconde, une lecture ordinaire de dix millisecondes a attendu **1,83 s**, cent quatre-vingts fois sa durée, pour un utilisateur qui n'avait rien demandé de particulier.
  Le conseil qui en découle est écrit : ne pas tenir une connexion pendant un appel réseau, faire les appels sortants sans connexion puis écrire une fois les réponses arrivées. Cinq requêtes qui tiennent une connexion pendant l'attente d'une API distante épuisent le pool de leur travailleur, et les suivantes reçoivent un `503` alors que la base n'a rien à se reprocher.
  Forge ne livre pas de client HTTP, ce choix appartenant à l'application, et la documentation le dit plutôt que de le laisser deviner. Un test d'intégration fige désormais la conséquence, qu'une requête qui parallélise prive ses voisines, seul le fait étant figé et non une durée.

- **La parade anti-bruteforce que Forge prescrit n'était pas dans la configuration qu'il engendre (`DEPLOY-NGINX-RATE-LIMIT-001`).**
  Le compteur anti-bruteforce du cœur vit en mémoire du **processus**, et l'unité systemd engendrée lance quatre travailleurs. Les cinq tentatives par minute en deviennent donc jusqu'à vingt, et le verrouillage ne suit pas l'attaquant d'un travailleur à l'autre. Cela vaut pour le contrôleur de connexion engendré par `make:auth` comme pour le challenge MFA.
  **Ce n'était pas une découverte** : `docs/deployment/production-security.md` le disait, prescrivait la parade Nginx et en donnait l'extrait. C'est précisément le défaut. Une ligne de défense qui vit dans une page de documentation est absente de tout projet qui n'a pas lu cette page, et la configuration engendrée n'en portait rien.
  `forge deploy:init` engendre désormais un `location = /login` borné à cinq POST par minute et par IP, avec `limit_req_status 429`, aux valeurs exactes que le guide prescrivait, Forge ne disant qu'une chose d'une seule façon.
  **Seul le POST est compté**, par un `map` sur `$request_method` qui donne une clé vide ailleurs. Limiter aussi le GET ferait répondre 429 à qui recharge la page de connexion six fois, et une limite qui gêne se fait désactiver, donc ne protège plus rien.
  Le nom de la zone est dérivé du dossier du projet. Deux projets Forge derrière le même Nginx déclareraient sinon deux zones homonymes, et Nginx refuserait de démarrer sur « is already bound », message qui ne dit pas quel fichier est en cause.
  Deux limites sont écrites plutôt que tues. Une route de connexion renommée n'est plus bornée, le `location` visant `/login`. Et **le challenge MFA n'est pas couvert** : `forge-mvc-mfa` ne pose aucune route, l'application écrit les siennes, et Forge ne peut pas viser celle du challenge.

- **La documentation du MFA s'appuyait sur un contrôle qui souffre du même défaut qu'elle relativisait.**
  Le bloc `danger` sur l'anti-rejeu par processus, exact par ailleurs, atténuait le risque ainsi : « Le rate-limit du challenge borne par ailleurs le nombre de tentatives. » Ce compteur vit dans la même mémoire de processus. Invoquer en atténuation un contrôle affaibli de la même façon fait sous-estimer les deux à la fois.
  La phrase est retirée, et une note dit ce qu'il en est, avec le geste qui manque : le challenge MFA vit sur une route que Forge ne connaît pas, et demande son propre `location`.

- **Le pré-vol de déploiement ne regardait pas si quelqu'un traitait la file de tâches (`DEPLOY-CHECK-JOBS-WORKER-001`).**
  Les dix-neuf contrôles de `deploy:check` n'en regardaient aucun. Un projet pouvait donc passer le pré-vol au vert avec une file que personne ne draine, et découvrir en production que ses emails ne partent pas.
  Le contrôle ne se déclenche que si le projet **appelle réellement** `enqueue`, lu par `ast` et jamais par grep : une occurrence dans un commentaire, une chaîne ou une docstring ferait accuser un projet qui n'enfile rien, et un détecteur qui accuse à tort se fait désactiver, donc ne garde plus rien. Un projet où `forge-mvc-jobs` est installé sans que rien n'enfile n'est pas inquiété : il n'y a rien à traiter, donc rien à reprocher.
  Trois situations sont refusées : `worker.py` absent, `worker.py` présent avec un `HANDLERS` vide, donc un service qui refusera de démarrer, et aucune unité déclarée. **C'est une erreur, pas un avertissement**, comme pour les sessions multi-travailleurs : les emails ne partiront pas, il n'y a rien à nuancer.
  Un `HANDLERS` construit autrement qu'en littéral, par une fonction ou un registre, n'est pas jugeable statiquement. Le pré-vol se tait alors, plutôt que d'accuser. `--worker` déclare l'emplacement de l'unité, comme `--unite` et `--nginx` le font déjà, pour qu'un projet qui la range ailleurs ne devienne pas invisible du pré-vol.
  Deux tests figeaient au passage le **nombre** d'artefacts de `deploy/`, trois, et non la fin qu'ils visaient, chaque artefact étant annoncé absent avant `deploy:init` et présent après. Ils sont réalignés sur les artefacts nommés.

- **Le guide de déploiement engendrait un minuteur pour les tâches orphelines, et aucun service pour les traiter (`DEPLOY-JOBS-WORKER-UNIT-001`).**
  `enqueue()` écrit une ligne dans une table. **Rien ne la traite tant qu'un worker ne tourne pas.** Le guide de `deploy:init` documentait l'unité `forge-app`, le minuteur `forge-jobs-reclaim`, et aucun service de traitement. Grep sur le générateur : zéro occurrence de `run_worker`. Le squelette ne livrait aucun gabarit non plus, et les 19 contrôles de `deploy:check` n'en regardaient aucun.
  Une application qui enfilait en production et suivait le guide à la lettre obtenait donc une table qui grossit, et un minuteur qui remet consciencieusement en file des tâches que personne ne prend. La panne est silencieuse **et trompeuse** : `systemctl` affiche un `forge-app` parfaitement vert, et le minuteur donne l'impression que quelque chose tourne. C'est le motif d'ADR-092 et ADR-093, la production servant une application désarmée.
  `deploy:init` engendre désormais `worker.py` et `deploy/systemd/forge-jobs-worker.service`, **uniquement quand `forge-mvc-jobs` est installé** : poser un `worker.py` dans un projet sans file de tâches donnerait un fichier à comprendre pour rien. `worker.py` est un fichier applicatif, engendré s'il n'existe pas et jamais réécrit (principe 9), puisqu'il porte les gestionnaires que Forge ne peut pas connaître.
  **Le worker engendré refuse de démarrer si `HANDLERS` est vide, et c'est la propriété la plus importante du gabarit.** Une tâche dont le nom n'a aucun gestionnaire est marquée `failed` : un worker parti sans gestionnaire ne se contenterait pas de ne rien faire, il viderait la file **en la détruisant**, tâche par tâche, en affichant un service vert. Il câble aussi `SIGTERM` sur la condition d'arrêt de `run_worker`, et son gestionnaire de signal ne lève pas, la tâche en cours allant à son terme.
  L'unité pose `Restart=always`, `StartLimitIntervalSec=0` dans `[Unit]` (mal placée, systemd l'ignore avec un simple avertissement), et un `TimeoutStopSec` explicite avec le raisonnement qui va avec, un transcodage vidéo dépassant largement les quatre-vingt-dix secondes par défaut.

- **Le tableau des gestes périodiques du guide en citait trois, alors que les opt-ins en livrent neuf.**
  Manquaient `audit:gc`, `stats:gc`, `iot:gc`, `video:cleanup`, `files:orphans` et `images:orphans`. Un geste d'entretien absent du guide n'est pas planifié, et une table qui grossit sans purge est une panne différée.
  **Six de ces commandes ne suppriment rien sans leur option.** Lancées seules elles affichent ce qu'elles feraient, puis sortent en succès. C'est un bon défaut, il évite une suppression involontaire, mais un minuteur qui planifie la commande nue tourne pour rien, indéfiniment, en affichant un succès à chaque passage. Le tableau cite donc les invocations complètes, `--run`, `--apply` ou `--delete` compris, et un garde-fou refuse qu'une ligne redevienne une commande nue.

- **Un worker de tâches de fond ignorait l'ordre d'arrêt tant que sa file n'était pas vide (`JOBS-WORKER-GRACEFUL-STOP-001`).**
  `run_worker` accepte `stop`, une condition d'arrêt destinée à répondre au `SIGTERM` que systemd envoie pour arrêter un service. Elle n'était consultée qu'entre deux **passes**, c'est à dire une fois la file vidée, ce qui la rendait sans effet précisément quand elle sert.
  Mesuré : un worker recevant l'ordre d'arrêt après trois tâches en traitait **cinquante** avant de le remarquer. Sous systemd, `TimeoutStopSec` expire au bout de quatre-vingt-dix secondes, le worker est alors tué au milieu d'une tâche, et celle ci repart par `jobs:reclaim` après l'expiration de son bail. Un déploiement se fait justement quand la file est pleine, et c'est le seul moment où ce défaut se voyait.
  `drain` accepte désormais `stop` et la consulte **entre deux tâches**, jamais pendant l'une d'elles : interrompre une tâche en cours ne serait qu'un autre nom pour l'interruption brutale, et laisserait la moitié d'un envoi fait. `run_worker` la lui transmet. L'ajout est un mot-clé facultatif, aucun appel existant ne change de comportement.

### Ajouté

- **Les notifications s'exposent en HTTP (`NOTIF-HTTP-ROUTES-001`).**
  Le paquet savait écrire une notification et la relire depuis Python, et n'exposait **aucune route**. `forge-mvc-video` livre `register_video_routes`, `forge-mvc-iot` livre `register_iot_routes`, celui ci ne livrait rien. Chaque application devait donc écrire son contrôleur, sa sérialisation JSON et son compteur de non-lus avant d'afficher quoi que ce soit. Mesuré sur une application réelle : elle appelait `notify()` depuis des mois et n'avait jamais affiché une seule notification, ayant buté sur cette marche manquante.
  `register_notification_routes(router, recipient_of=...)` pose quatre routes JSON, le compteur de non-lus, la liste paginée par curseur, le marquage d'une notification et le marquage global.
  **Le destinataire vient de la session, jamais de la requête**, et c'est le point qui décide de tout le reste. Un destinataire est une chaîne libre, « professeur.42 », dont la convention appartient à l'application. La seule autre façon de le connaître serait de le lire dans la requête, et `?recipient=professeur.7` donnerait alors à quiconque les notifications de n'importe qui. `recipient_of` est donc **obligatoire**, et son absence lève à l'enregistrement plutôt qu'à la première requête : une application qui monte ces routes sans résolveur a fait une erreur de câblage, et la découvrir au démarrage vaut mieux qu'en production. Un résolveur qui lève est journalisé et la requête traitée comme non authentifiée, se rabattre sur « personne » étant acceptable là où se rabattre sur « tout le monde » ne l'est pas.
  **Le marquage est borné au destinataire**, ce qui a demandé d'ajouter `recipient` à `mark_read` **avant** d'exposer la moindre route. Sans cette borne, l'identifiant seul suffisait à faire disparaître l'alerte de quelqu'un d'autre, et les identifiants d'une table se devinent. La réponse ne distingue pas « déjà lue » de « celle d'un autre », les distinguer apprendrait à l'appelant qu'un identifiant existe chez quelqu'un d'autre. `mark_read(id)` sans destinataire reste ce qu'il était, pour l'appel depuis le code de l'application.
  `recipient` est **absent du JSON rendu** : le client ne reçoit que les siennes, le lui répéter n'apprend rien et expose la convention de nommage interne de l'application. Un `limit` ou un `before_id` illisible rend 400 et jamais la page par défaut, la remplacer en silence rendrait une page que l'appelant n'a pas demandée. Le curseur de page suivante vaut `null` quand la page n'est pas pleine, en rendre un ferait demander une page vide.
  Ces routes rendent du JSON et ne poussent rien. Le rafraîchissement s'écrit avec HTMX, que le squelette livre déjà. Une interrogation toutes les dix secondes coûte, pour quarante écrans ouverts, quatre requêtes par seconde ; les tenir ouvertes en SSE coûterait quarante travailleurs immobilisés.

### Corrigé

- **Un motif de retrait du cycle rc8 portait une affirmation fausse.**
  Le retrait de `NOTIF-POLLING-HELPER-001` disait que « la route JSON que l'aide aurait appelée existe déjà côté notifications ». Le paquet n'exposait alors aucune route, et cette affirmation n'avait pas été mesurée.
  Le retrait tient sur son motif principal, le rafraîchissement d'un écran relève de l'application. Mais la marche manquante n'était pas l'assistant, c'était la route, désormais livrée. Un motif de retrait qui s'appuie sur un fait faux fait renoncer à autre chose que ce qu'on croyait écarter.

- **Le README de `forge-mvc-admin` décrivait un état antérieur à son code (`ADMIN-DOC-ETAT-REEL-001`).**
  Il annonçait que « les filtres de liste et les actions en masse restent à venir » alors que les filtres étaient livrés depuis longtemps, et que les actions groupées le sont depuis `ADMIN-BULK-ACTIONS-001`.
  Un README qui décrit un état antérieur à son code est pire qu'un README absent : il fait chercher ailleurs ce qui est déjà là, et personne ne le relit puisqu'il a l'air à jour.

- **Les actions groupées du back-office sont câblées, et couplées au workflow (`ADMIN-BULK-ACTIONS-001`).**
  La première livraison avait posé la fonction de requête `delete_rows` et ses garde-fous, **sans aucun câblage HTTP** : ni méthode de contrôleur, ni route, ni case à cocher. Depuis le back-office, elle était inatteignable, et le ticket était marqué livré à tort. La revue l'a relevé.
  Une ressource déclare désormais `bulk_delete` et `bulk_transitions`, tous deux **fermés par défaut** : une case à cocher offerte sans qu'on l'ait demandée invite à un geste irréversible sur une table qu'on croyait en lecture. Toute action passe par une page de confirmation, comme la suppression unitaire, et cette page montre les lignes concernées ainsi que celles qui ont disparu entre l'affichage et la validation.
  **La transition groupée écrit aussi le statut de départ dans sa clause** : une ligne dont le statut a changé entre l'affichage et la validation n'est pas touchée, là où une mise à jour sur la seule clé primaire écraserait un état que quelqu'un vient de poser. L'écart entre demandé et effectué est dit dans le message de retour.
  Elle **exige `forge-mvc-workflow` installé, et refuse sinon**. Ce refus diffère délibérément de celui de la suppression : appliquer un changement de statut à N lignes sans pouvoir vérifier que la transition est déclarée écrirait un état que le workflow interdit peut-être, sur cinquante lignes d'un coup. Les transitions sont déclarées et jamais déduites, et les conditions du workflow sont consultées avec un contexte portant `bulk`, une règle pouvant refuser en masse ce qu'elle permet à l'unité.

- **La documentation de la garde RBAC de l'admin se contredisait.**
  `_permission_guard` est **fail-closed** depuis toujours, et le dit : sans `forge-mvc-rbac` installé, une route portant une permission déclarée répond 403. La docstring de `register_admin_routes` annonçait « fail-open » deux cents lignes plus bas.
  Une documentation qui annonce une ouverture là où le code ferme fait chercher une faille qui n'existe pas, et inversement. Un test verrouille désormais l'absence de cette contradiction.

### Ajouté

- **Un rôle RBAC peut hériter d'un autre (`RBAC-ROLE-HIERARCHY-001`, ADR-095).**
  Le contrat associait un rôle à une liste plate de permissions. Un projet à trois rôles recopiait donc la liste du lecteur dans l'éditeur, puis les deux dans l'admin. Trois copies de la même règle, qui divergent au premier ajout : on ajoute une permission à l'éditeur, on oublie l'admin, et l'administrateur se retrouve avec **moins** de droits qu'un éditeur, sans que rien ne le signale, puisque personne n'écrit un test vérifiant qu'un administrateur peut faire ce qu'un éditeur peut faire.
  `role_inherits` déclare l'héritage, qui est transitif. La clé est **facultative** : un contrat qui ne la porte pas se résout exactement comme avant, et aucun projet existant n'a de geste à faire.
  **Rien n'est deviné.** « admin » ne domine pas « editeur » parce qu'il s'appelle ainsi, et supposer le contraire accorderait des droits que personne n'a écrits. Une déduction fausse sur un contrôle d'accès ne se répare pas après coup.
  **Une hiérarchie fautive n'accorde rien.** Un cycle et un rôle hérité inconnu sont refusés, et la résolution rend un ensemble vide plutôt que les permissions directes : accorder les droits directs donnerait un contrôle d'accès dégradé en silence, ce qui est pire qu'un refus. Le cycle est nommé, « admin puis editeur puis admin » se corrigeant là où « hiérarchie invalide » ne se corrige pas. La profondeur est bornée à dix niveaux, au delà desquels une revue de sécurité ne peut plus suivre la chaîne.
  `rbac:export` rend les permissions **effectives**, héritages compris : montrer les seules permissions directes ferait croire à un administrateur privé de droits qu'il possède.

### Retiré du périmètre

- **Quatre tickets du lot 5 du cycle rc8 sont retirés par décision écrite** (roadmap `forge-rc8-optins-roadmap.md`, section 8).
  Chacun entrait en tension avec un principe de la charte, et la tension a été tranchée en connaissance de cause plutôt que contournée.
  `MFA-WEBAUTHN-001` : une spécification large et mouvante dont la maintenance ne peut pas être garantie sur la durée, ce que le principe 8 vise exactement.
  `AUDIO-STATEFUL-OPTION-001` : la bonne réponse, si le besoin revient, est d'extraire la machinerie d'état partagée avec `video`, pas de la dupliquer.
  `DEPLOY-CADDY-001` : dire qu'une chose est possible ne coûte rien, maintenir un second gabarit officiel coûte à chaque version.
  `NOTIF-POLLING-HELPER-001` : Forge livre déjà HTMX, et un assistant ne retirerait aucune décision à l'application, il en masquerait une.

- **Un garde-fou refuse qu'un README promette une commande qui n'existe pas (`META-README-COMMANDS-RATCHET-001`).**
  Une phrase de prose ne se vérifie pas en général. Ce qui se vérifie, et qui dérive de la même façon, ce sont les **commandes** : chaque opt-in les déclare dans `COMMANDS`, table que le cœur lit (ADR-059), et son README en annonce dans un tableau.
  Le garde-fou refuse une commande citée au README et absente de `COMMANDS`, promesse que l'utilisateur tape avant de comprendre, et refuse qu'une commande **déclarée** soit annoncée « à venir », ce qui est la dérive exacte que le ticket précédent a corrigée.
  Il **tolère** l'inverse, une commande de `COMMANDS` absente du README : un README n'est pas une référence exhaustive, l'aide riche du CLI porte déjà ce contrat, et exiger la réciproque transformerait chaque README en catalogue.
  Le fichier est exempté du marqueur `docs`, avec sa justification : il compare de la prose à du **code**, et le marquer le retirerait de la boucle où une commande retirée de `COMMANDS` doit être vue.

- **Le contrat RBAC s'exporte (`RBAC-CONTRACT-EXPORT-001`).**
  `rbac:validate` dit si le contrat est valide, `rbac:audit` le compare à la base. Ni l'un ni l'autre ne répond à « qui a le droit de faire quoi », question d'une revue de sécurité, qui demandait de lire `rbac.json` à l'œil.
  `forge rbac:export` rend un tableau Markdown, à versionner à côté du code où une différence montre qu'un rôle a gagné une permission, ou un CSV pour une revue en tableur.
  **L'export rend le contrat, jamais l'état de la base** : confondre les deux ferait prendre une intention pour un état. Un contrat invalide n'est pas exporté, le tableau ne s'appliquant à rien et le lecteur le prenant pour la vérité. Le tri rend deux exports comparables, et les cellules sont échappées.

- **Un rôle peut exiger un second facteur (`MFA-REQUIRED-BY-ROLE-001`).**
  Le paquet savait dire si un utilisateur **a** un facteur actif, jamais s'il **devrait** en avoir un. L'application écrivait donc le contrôle dans chaque écran sensible, le faisait bien la première fois, et l'oubliait au troisième écran ajouté six mois plus tard.
  `MFA_REQUIRED_ROLES` déclare la politique une fois. **Elle n'active rien** : rendre un facteur obligatoire ne peut pas le créer à la place de l'utilisateur, il faut son téléphone et son consentement ; elle dit qu'un accès doit être refusé, et `reason` donne le message qui conduit vers l'inscription.
  Le paquet **n'importe pas `forge-mvc-rbac`** : les rôles sont lus dans la session, où l'authentification les a rangés, et trois emplacements sont acceptés, les applications les employant tous les trois. `check_mfa_requirement` ne lève jamais : un contrôle de sécurité qui échoue en levant priverait d'accès un utilisateur légitime.

- **Le back-office supprime plusieurs lignes en une fois (`ADMIN-BULK-ACTIONS-001`).**
  Il ne savait supprimer qu'une ligne à la fois : nettoyer deux cents inscriptions de test demandait deux cents allers-retours et deux cents confirmations.
  Les identifiants partent en **paramètres liés**, un marqueur par valeur : les concaténer serait une injection, et le fait qu'ils viennent de cases cochées n'y change rien. Une sélection vide est refusée, une suppression groupée sans sélection effaçant la table entière si la clause était omise, et un plafond de deux cents lignes l'est aussi, une sélection de cette taille venant plus souvent d'un « tout cocher » que d'une intention.
  Le nombre réellement supprimé est rendu : une ligne disparue entre l'affichage et la validation n'est pas une erreur.

- **Les minuteries périodiques sont documentées (`DEPLOY-TIMERS-DOC-001`).**
  Purge des sessions, reprise des tâches, sauvegarde : trois gestes qui doivent tourner, et aucun n'est planifié par Forge, embarquer un ordonnanceur faisant du framework autre chose que ce qu'il est.
  Deux unités systemd complètes et quatre pièges nommés : activer le `.timer` et non le `.service`, faute de quoi la commande tourne une fois au démarrage puis plus jamais ; `Persistent=true` qui rattrape les exécutions manquées ; `RandomizedDelaySec` qui étale la charge ; et `EnvironmentFile` en `chmod 600`, ces commandes se connectant à la base.
  La sauvegarde reste hors de Forge, chaque backend ayant son outil. Ce que la documentation dit et qui vaut plus qu'un script générique : **une sauvegarde jamais restaurée n'est pas une sauvegarde**.

- **Les écarts de dialecte sont documentés (`DOC-DIALECT-ECARTS-001`).**
  Bornes de lignes, booléens, insertion conditionnelle, signaux d'erreur, et ce qui reste délibérément hors du contrat. Un écart connu se contourne ; un écart ignoré se découvre en production, sur le seul backend où il mord.
  La documentation nomme les pièges qui ont déjà coûté : `pagination_clause` et `pagination_param_order` se lisent en **paire**, T-SQL inversant l'ordre des deux paramètres ; le SQLSTATE ne discrimine pas sur MariaDB ni SQL Server, qui rendent `23000` pour trois conditions différentes ; et un message d'erreur PostgreSQL est traduit, donc n'est jamais un signal.
  Forge ne fournit **aucune** insertion conditionnelle : les quatre formes n'ont pas la même sémantique de verrouillage, et une abstraction promettrait une équivalence qui n'existe pas.

### Corrigé

- **Une violation de clé étrangère est enfin qualifiée (`DB-ERROR-MESSAGES-HOMOGENES-001`).**
  Le doublon, la table absente, l'indisponibilité et le droit refusé l'étaient. **Pas la clé étrangère**, qui est pourtant l'erreur d'écriture la plus courante après le doublon : supprimer une ligne encore référencée, ou poser une référence qui n'existe pas.
  L'exception du pilote remontait donc telle quelle, ce que l'ADR-054 refuse précisément, une application ne devant jamais avoir à attraper `mariadb.IntegrityError` sous peine de n'être portable nulle part. Six tests du dépôt attrapaient d'ailleurs l'exception brute, et trois importaient le pilote pour cela : ces imports ont disparu avec le correctif.
  Aucun signal n'est portable, et les quatre sont **vérifiés contre des serveurs réels**, jamais contre une exception fabriquée : errno 1451 et 1452 sur MariaDB, message sur SQLite qui n'offre rien d'autre, SQLSTATE 23503 sur PostgreSQL, numéro 547 sur SQL Server. Un test vérifie en outre qu'un doublon ne devient pas une clé étrangère, une erreur mal nommée envoyant chercher au mauvais endroit.

- **Le gabarit Nginx pose HSTS et protège `/static/` (`DEPLOY-NGINX-MEDIA-HEADERS-001`).**
  Le cœur pose déjà cinq en-têtes de sécurité, et **délègue explicitement HSTS au reverse proxy** : derrière un proxy qui termine TLS, `wsgi.url_scheme` vaut `http` côté Forge, et l'émettre à tort bloquerait l'accès. Cette délégation était documentée et personne ne la recevait : le gabarit ne portait pas la directive.
  Le `location /static/` court-circuite par ailleurs l'application, donc **aucun** en-tête de Forge ne l'atteint. `nosniff` y compte le plus, un navigateur devinant sinon le type d'un fichier servi depuis votre domaine.
  Le bloc `internal;` de l'envoi délégué est fourni, commenté, avec le rappel que c'est cette directive et elle seule qui protège : sans elle, la délégation publie tout `UPLOAD_ROOT`.

- **Un champ d'entité peut être dérivé (`ENTITIES-COMPUTED-FIELDS-001`).**
  Un total de ligne, un âge, un nom complet : la valeur se calcule depuis d'autres colonnes, et l'écrire en base la ferait mentir dès qu'une source change. L'application dupliquait l'expression dans chaque requête, ou la recalculait en Python après avoir tout rapatrié.
  `"computed": "qte * pu"` projette le champ en lecture, `(qte * pu) AS "total"`, et l'exclut des écritures : il n'a pas de colonne, et l'inclure dans un `INSERT` ferait échouer la requête sur les quatre backends. L'alias reste entre guillemets, c'est lui qui préserve la casse sur PostgreSQL.
  **L'expression n'est pas paramétrable, et c'est voulu** : le contrat d'entité est du code du projet, relu et versionné, pas une donnée d'utilisateur. Un point-virgule y est néanmoins refusé, l'expression étant projetée dans un `SELECT` et non exécutée. Quatre combinaisons sont refusées, clé primaire, `UNIQUE`, valeur par défaut et présence au formulaire, chacune parce qu'elle produirait un SQL faux plutôt qu'une maladresse.

- **Une règle métier se déclare (`ENTITIES-BUSINESS-VALIDATION-001`).**
  Le contrat décrit des types. Il ne peut rien dire de « la date de fin doit suivre la date de début », qui vivait donc dans les contrôleurs, réécrite à chaque point d'entrée : une entité créée par l'écran passait le contrôle, la même créée par un import CSV ne le passait pas, et rien ne le signalait.
  **Une fonction, et non une expression au contrat.** Une règle a besoin de la base, de l'heure, parfois d'un service ; une mini-langue dans le JSON en couvrirait un dixième et demanderait un interpréteur, c'est à dire du code caché dans de la donnée.
  Toutes les règles sont évaluées, rendre le premier problème seul obligeant l'utilisateur à corriger une erreur à la fois. Une règle qui lève **refuse** l'écriture. Un problème peut n'appartenir à aucun champ, le rattacher arbitrairement ferait pointer le formulaire au mauvais endroit.

- **Une entité à slug gagne sa route publique (`ENTITIES-SLUG-ROUTES-001`).**
  La recherche par slug existait depuis l'ADR-017, et **aucune route ne s'en servait** : une URL publique lisible demandait d'écrire la méthode et la route à la main, dans chaque projet.
  `show_by_slug` et sa route sont engendrées dès que l'entité porte un champ `slug`. Une entité sans slug ne voit aucun changement.
  **La route est déclarée en dernier**, après les segments fixes : un slug valant « new » serait sinon capturé par `/new`, et sa fiche resterait inatteignable. `RESERVED_SLUG_SEGMENTS` nomme ces valeurs pour que l'application les écarte à l'écriture, Forge ne pouvant le faire à sa place puisqu'un slug est une donnée.

### Modifié

- **`migration:diff` se lit, et s'essaie à blanc (`ENTITIES-MIGRATION-DIFF-READABLE-001`).**
  La commande rendait un tableau de lignes sans total : sur une entité de trente colonnes, savoir s'il reste un écart demandait de lire les trente lignes et de compter à la main.
  Un résumé s'ajoute, `--sql` montre la migration que `migration:make --from-diff` produirait **sans rien écrire**, et `--check` rend un code de sortie non nul pour l'intégration continue. Le comportement par défaut reste inchangé, faire échouer la commande d'office aurait cassé les scripts existants.
  Un diff risqué ne se traduit pas en SQL automatiquement, et la commande le dit à cet instant plutôt que de laisser découvrir le refus au moment de créer la migration.

- **Le workflow garde trace de ses transitions (`WORKFLOW-HISTORY-001`).**
  Le paquet appliquait les transitions sans en garder trace : on savait dans quel état une entité se trouve, jamais comment elle y est arrivée, ni quand, ni par qui. « Qui a validé cette commande, et à quelle date » n'avait aucune réponse, et chaque application réinventait sa table.
  **L'enregistrement est explicite, et dans la transaction de l'appelant.** Écrire depuis le paquet imposerait une connexion à un module qui n'en avait pas besoin, et surtout séparerait l'historique de l'écriture qu'il décrit : une transaction annulée laisserait une ligne pour une transition qui n'a pas eu lieu.
  Un acteur absent est une **information** : une transition automatique n'a pas d'auteur, et inventer « system » masquerait la différence. Aucune clé étrangère vers l'entité, le paquet ne sachant pas ce qu'est une entité de l'application, et un historique devant survivre à la suppression de son sujet, c'est justement alors qu'on veut savoir qui avait validé.
  `forge workflow:init` livre la migration. Les transitions et les conditions fonctionnent sans cette table.

- **Une transition peut être conditionnée (`WORKFLOW-CONDITIONS-001`).**
  `can_transition` répond à une seule question, celle de la déclaration. Elle ne peut rien dire de « cette commande a t elle au moins une ligne », qui est pourtant la vraie condition. L'application vérifiait donc avant d'appeler, chacune à sa façon, et deux chemins menant au même état s'oubliaient l'un l'autre.
  **Une condition dit pourquoi elle refuse.** Rendre `False` laisserait l'utilisateur devant « transition impossible », message qui n'indique rien à corriger ; elle rend `None` ou un motif, qui remonte jusqu'à l'écran.
  **Une condition qui échoue refuse la transition.** Traiter son silence comme une autorisation ferait tout passer le jour où le service qu'elle interroge tombe. `check_conditions` ne lève jamais et sert à afficher ce qui bloque, `ensure_conditions` sert à refuser.

- **Chaque nature de session a sa durée de vie (`SESSIONS-TTL-PER-KIND-001`).**
  Le store portait une durée pour tout le monde, ce qui force un arbitrage perdant : réglée court, elle déconnecte les authentifiés toutes les heures ; réglée long, elle laisse traîner des sessions anonymes par milliers, occupant la table pour un jeton CSRF.
  Trois natures fermées, `anonymous`, `authenticated` et `remembered` : une quatrième inventée par une application rendrait la métrique et la purge incomparables d'un projet à l'autre. Une valeur d'environnement illisible **lève**, comme pour les autres paquets qui bornent quelque chose. Un `ttl` passé au constructeur reste prioritaire, le retirer sous les pieds d'un projet étant une rupture silencieuse.

- **Le nombre de sessions actives se mesure (`SESSIONS-ACTIVE-METRIC-001`).**
  `sessions:gc` disait combien il avait purgé ; personne ne pouvait dire combien il en restait. Une table qui grossit sans fin signale une purge qui ne tourne pas, et une chute brutale une déconnexion de masse.
  Le filtre est **en SQL** : compter toutes les lignes puis écarter les expirées en Python rapatrierait une table entière pour rendre un nombre. Une session expirée n'est **pas** active, même si la purge ne l'a pas encore retirée : la compter ferait passer un retard de purge pour de la fréquentation.
  Les trois natures figurent toujours dans la répartition, à zéro le cas échéant, une clé absente se lisant comme une métrique cassée.

- **La purge des sessions a sa minuterie documentée (`SESSIONS-GC-TIMER-DOC-001`).**
  Deux unités systemd complètes. Forge ne fournit pas de planificateur, c'est le rôle du système, et en embarquer un ferait de Forge un ordonnanceur.
  La documentation nomme les trois pièges : `Persistent=true` rattrape les exécutions manquées, sans quoi un serveur redémarré chaque matin ne purgerait jamais ce qui a expiré la nuit ; `RandomizedDelaySec` évite que plusieurs applications frappent la base à la même minute ; et c'est le `.timer` qu'on active, activer le `.service` le ferait tourner une fois au démarrage puis plus jamais.

- **Un client de test qui passe par le vrai chemin WSGI (`TESTING-CLIENT-001`).**
  `FakeRequest` permet d'appeler un contrôleur directement, ce qui est utile et insuffisant : rien n'y passe par le routeur, ni par les middlewares, ni par la construction d'une `Request` depuis un environnement WSGI. Un test qui appelle `Controller.show(fake_request)` ne prouve rien du CSRF, de l'authentification, ni même de l'existence de la route.
  `ForgeTestClient` construit un environnement WSGI et appelle le callable rendu par `create_wsgi_app`, c'est à dire **exactement ce que Gunicorn appelle**. Un client qui reconstruirait sa propre boucle serait un jumeau : il passerait là où la production échoue, et Forge a déjà payé cette erreur une fois, avec un serveur de développement qui répondait là où Gunicorn rendait 404.
  Les cookies sont gardés entre deux requêtes, un scénario réaliste enchaînant connexion, formulaire et envoi. Un cookie effacé par le serveur est **retiré** du client, sans quoi un test de déconnexion passerait sans rien prouver. Une seule redirection est suivie, une boucle étant un défaut à voir et non à absorber.

- **Authentifier un client de test en une ligne (`TESTING-LOGIN-AS-001`).**
  Tester une page protégée demandait de jouer le formulaire de connexion, donc d'avoir un utilisateur en base, un mot de passe haché et un jeton CSRF. Un test de « la page d'administration refuse un visiteur » passait par cinq étapes sans rapport avec ce qu'il vérifie, et cassait dès que le formulaire changeait.
  `login_as` passe par le **vrai magasin de sessions** : fabriquer le cookie soi même produirait un jumeau, et le test passerait avec une session que la production aurait refusée. `logout` **détruit** la session, oublier le cookie sans la détruire laissant un test de déconnexion passer alors qu'elle reste utilisable.
  Aucun utilisateur n'est créé en base : un test de contrôle d'accès vérifie ce que le middleware fait d'une session, pas ce que le dépôt contient.

- **Des assertions qui nomment la cause (`TESTING-ASSERTIONS-001`).**
  Vérifier une authentification, une rotation de session ou la consommation d'un jeton demandait de lire le magasin à la main dans chaque test. Chacun écrivait sa version, et aucune ne disait la même chose en cas d'échec.
  `assert_authenticated` distingue trois échecs qu'un `assert` unique confondrait : pas de cookie, cookie pointant sur une session disparue, session présente mais non authentifiée.
  **`assert_session_rotated` exige que l'ancienne session soit morte.** Vérifier seulement le changement d'identifiant laisserait passer une rotation qui garde l'ancienne vivante, ce qui ne protège de rien contre la fixation de session. `assert_token_consumed` couvre la faille symétrique : un jeton à usage unique encore utilisable après emploi est rejouable, et rien ne le révèle sans le vérifier.

- **Les fixtures du projet se chargent dans un test (`TESTING-FIXTURES-ALIGN-001`).**
  Un projet qui écrit ses données de démonstration avec `forge-mvc-fixtures` les réécrivait une seconde fois pour ses tests. Les deux jeux divergeaient, et un test passait sur des données que l'application ne verrait jamais.
  `load_fixture_scenario` réutilise le code du paquet, les mêmes fichiers et le même ordre topologique : en recalculer un second ici le ferait dériver, ce qui est exactement le défaut corrigé. La connexion appartient au test, qui sait sur quel backend il tourne. La fixture `fixtures_loader` saute proprement quand l'opt-in facultatif est absent.

- **`forge qrcode:make` produit un fichier (`QRCODE-CLI-001`).**
  Le paquet savait produire un QR Code depuis Python et le servir en HTTP. Produire un fichier, pour une affiche ou une étiquette, demandait un script à usage unique.
  Affiche par défaut, écrit sur `--out` (charte §7). **Un fichier existant n'est jamais écrasé** : deux QR Codes se ressemblent à l'œil, ce sont deux carrés noirs et blancs, et l'ancien serait perdu sans que rien ne le signale jusqu'à ce qu'un scan mène au mauvais endroit.
  Une extension qui contredit `--format` est refusée : un SVG nommé `.png` est servi avec le mauvais type et refusé par un imprimeur. Le niveau de correction par défaut est rappelé à l'écriture, au moment où l'information sert.

- **Les clés de traduction employées se listent (`I18N-EXTRACT-CLI-001`).**
  `i18n:check` compare deux catalogues entre eux : il dit quelle clé du français manque à l'anglais, et ne peut rien dire d'une clé employée dans un gabarit et absente **des deux**. C'est pourtant le cas le plus fréquent.
  `forge i18n:extract` balaye `mvc/views/` et compare au catalogue. **Seules les clés littérales sont extraites** : `trans(variable)` n'existe qu'à l'exécution. Ces appels sont comptés et rapportés à part, et la sortie annonce alors que la liste est un minorant, plutôt que de la laisser passer pour exhaustive.
  L'extraction vit dans l'opt-in, qui seul connaît la forme des appels ; la commande l'importe paresseusement, le cœur ne dépendant pas d'un opt-in (ADR-004).

- **Une clé de traduction manquante se voit avant l'utilisateur (`I18N-MISSING-KEYS-DEV-001`).**
  `trans()` rend la clé elle même, ce qui reste le bon comportement : une page ne doit pas casser pour une traduction absente. Mais rien ne le signalait, et « panier_vide » s'affichait à l'utilisateur sans que personne ne s'en aperçoive avant lui.
  La clé est désormais journalisée et collectée **hors production seulement** : journaliser chaque clé manquante à chaque requête noierait le journal, et une traduction absente n'est pas un incident d'exploitation. Une clé n'est signalée qu'une fois, la même sur mille requêtes étant un seul défaut.
  Le signalement ne **lève jamais** : une page qui casse pour une traduction absente serait un remède pire que le mal, y compris en développement, où elle empêcherait de voir le reste de la page.

- **Singulier et pluriel, à deux formes assumées (`I18N-PLURALS-001`).**
  `trans()` rendait une chaîne unique par clé, d'où « 1 articles », ou deux clés avec un `if` dans chaque gabarit. Un catalogue peut maintenant porter `{"one": ..., "other": ...}`, et une clé dont la valeur est une chaîne reste une clé ordinaire.
  **Forge implémente deux formes, CLDR en définit six.** C'est exact pour le français, l'anglais et la plupart des langues d'Europe occidentale, et faux pour le russe, l'arabe, le polonais et le gallois : `plural_form` **lève** pour ces langues plutôt que de rendre une forme qu'elle sait fausse. Une implémentation partielle donnerait l'impression de couvrir une langue qu'elle massacre.
  Le français met zéro au singulier, l'anglais non, et la règle dépend de la langue jamais de la région. Une forme absente du catalogue lève, retomber sur l'autre afficherait « 3 article » sans que rien ne le signale.

### Corrigé

- **La réponse HTTP transmet enfin le niveau de correction d'erreur (`QRCODE-ERROR-LEVEL-001`).**
  Le niveau existait sur `QrCode.from_text`, mais `QrCodeResponse.from_text` appelait `from_text(text)` tout court : un contrôleur, c'est à dire le chemin documenté pour servir un QR Code, ne pouvait pas le choisir.
  Ce n'est pas un réglage de confort. Un code imprimé sur une étiquette ou une affiche, susceptible d'être rayé ou partiellement couvert, demande `h`, qui tolère 30 % de perte ; en `m`, le défaut, qui en tolère 15 %, il devient illisible, et la panne se découvre sur le terrain une fois les étiquettes collées.
  `ERROR_LEVELS` est exporté, une application ne pouvant sinon connaître les valeurs valides sans lire la source du paquet.

- **Compter des visiteurs sans garder d'adresse (`STATS-IP-ANONYMISATION-001`).**
  `forge-mvc-stats` ne stockait **aucune** adresse : sa table n'a pas de colonne pour cela, et ce n'est pas un oubli mais son périmètre, il compte des événements et n'enquête pas.
  `metadata` est pourtant libre, et rien n'empêchait d'y écrire `{"ip": request.remote_addr}`. C'est le geste naturel de qui veut compter des visiteurs uniques, et il transforme une table de statistiques en fichier de données personnelles, soumis à conservation limitée et à droit d'accès, sans que personne ne l'ait décidé.
  **Une adresse brute est désormais refusée à l'écriture**, la ligne ne devant pas exister plutôt qu'être filtrée à chaque lecture. Le contrôle porte sur la **clé** et non sur la valeur : « 1.2.3.4 » est une adresse IPv4 valide et un numéro de version tout aussi valable, et refuser cette forme casserait des métadonnées légitimes.
  `visitor_hash` répond au besoin réel sans rien garder : une empreinte salée valable une journée, identique pour deux visites du même visiteur le même jour, différente le lendemain. Un secret vide est refusé, sans lui l'espace des adresses IPv4 se parcourant en quelques secondes. `anonymize_ip` tronque quand une granularité géographique est vraiment nécessaire, et la documentation dit qu'elle ne rend **pas** une donnée anonyme.
  Le message de refus oriente vers `forge-mvc-audit` pour qui doit conserver une adresse à des fins de sécurité : ce n'est pas une statistique.

- **Une vue de page ne se compte pas comme une action (`STATS-EVENT-KIND-001`).**
  `category` est la taxonomie libre de l'application. Le type est orthogonal : mille pages vues valent moins qu'une commande passée, et les mélanger sous un même total donne un chiffre que personne ne peut interpréter.
  Le vocabulaire est **fermé**, `page_view` et `action` : un troisième type inventé par une application rendrait le champ incomparable d'un projet à l'autre, ce qui est exactement ce qu'il doit permettre. Le défaut est `action`, valeur qui décrit correctement les événements déjà en base, posés par des appels délibérés.
  La colonne arrive par une **migration additive** : une table déjà créée ne se recrée pas, et c'est la seule façon de la faire évoluer sans perdre les événements enregistrés.

- **Les statistiques s'agrègent enfin par jour (`DOC-STATS-AGGREGATES-001`).**
  L'agrégation ne connaissait que `name` et `category`. Grouper par journée demandait de rapatrier tous les horodatages pour les tronquer en Python, ce que la base fait sans rien déplacer.
  `Dialect.date_expression` porte la différence, aucun des quatre backends n'écrivant la troncature d'un horodatage de la même façon. La valeur rendue change aussi de type selon le backend, ce que le contrat annonce plutôt que de le laisser découvrir.
  **Une série temporelle se trie par le temps**, là où les autres dimensions se trient du plus fréquent au moins fréquent : trier une courbe par total décroissant la rendrait illisible.
  La liste des dimensions reste une liste blanche, `group_by` finissant dans un `GROUP BY` où aucun backend n'accepte de paramètre lié. Un `kind` inconnu lève de même, un filtre qui rend zéro sans motif faisant chercher un défaut ailleurs.

### Modifié

- **Un garde-fou cherchait une sous-chaîne là où il visait des noms exacts.**
  `test_stats_generic_events_001` interdisait `"PAGE_VIEW = "` dans `events.py`, moyen qui a fini par déborder sa fin : `KIND_PAGE_VIEW` contient cette sous-chaîne sans être une constante de nom d'événement, les deux vivant sur des axes différents. La lecture se fait maintenant par `ast` sur les affectations de premier niveau.
  Deux tests figeaient par ailleurs le nombre de colonnes et le nombre de paramètres d'insertion. Le second vérifie désormais l'égalité entre marqueurs et valeurs, qui est ce qui compte : un décalage fait échouer l'insertion sur les quatre backends.

- **Les fixtures se rangent en jeux nommés (`FIXTURES-SCENARIOS-001`).**
  `mvc/fixtures/` était plat : tous les fichiers se chargeaient ensemble, et un projet voulant un jeu de démonstration riche **et** un jeu de test minimal devait commenter des fichiers ou les déplacer à la main entre deux exécutions.
  Un sous-dossier par jeu, `forge fixtures:load --scenario demo`. Le jeu commun est chargé d'abord, puis celui du scénario : un scénario complète une base partagée au lieu de la réécrire. Sans `--scenario`, rien ne change.
  **Un scénario inconnu est une erreur, jamais un chargement vide.** `--scenario dmo`, faute de frappe pour `demo`, chargerait zéro fichier et annoncerait un succès : l'exploitant croirait ses données en place, et chercherait ailleurs pourquoi son application est vide. Le message liste les scénarios présents, et un dossier vide est refusé pour la même raison.
  `demo`, `test` et `minimal` sont **suggérés**, jamais imposés : ce ne sont que des noms de dossiers, et une liste fermée obligerait à un ticket pour chaque projet ayant un quatrième besoin.

- **Une fixture peut partir de l'état courant (`FIXTURES-SNAPSHOT-001`).**
  Écrire des fixtures à la main coûte cher et vieillit mal : une colonne ajoutée au contrat, et tous les `INSERT` sont à reprendre. `forge fixtures:snapshot articles` rend l'état d'une table en `INSERT` relisibles.
  **La sortie vient d'une base réelle.** Sur un environnement de recette alimenté depuis la production, ces données sont celles de personnes, et le fichier finit dans un dépôt Git où il ne s'efface plus. L'exécution en `APP_ENV=prod` est refusée sans `--force`, la sortie est **affichée** par défaut, un fichier existant n'est jamais écrasé, et l'en-tête du fichier rappelle d'où il vient.
  Forge ne devine **pas** quelles colonnes masquer : il ne sait pas lesquelles portent une donnée personnelle, et prétendre le deviner donnerait une fausse assurance. C'est pourquoi la relecture précède l'écriture.
  Le plafond vaut 50 lignes, 1000 au maximum : une fixture est une amorce, pas une sauvegarde. Une ligne de plus est lue pour savoir qu'il en restait et le dire, plutôt que de rendre un instantané tronqué qui ressemble à un instantané complet.

### Corrigé

- **L'ordre des fixtures ne se rabat plus en silence (`FIXTURES-FK-ORDER-ROBUST-001`).**
  Le tri topologique existait, et se rabattait sur l'ordre alphabétique sans rien dire dans trois cas : `relations.json` absent, cycle dans le graphe, table sans entité déclarée.
  Le repli est raisonnable, le **silence** ne l'était pas : le chargement échouait ensuite sur une violation de clé étrangère, et rien ne reliait cette erreur à l'ordre qui l'avait causée. L'exploitant cherchait dans ses données un défaut qui était dans son graphe. `fixtures:load` affiche maintenant ce qu'il n'a pas pu déduire, avant de charger, et nomme le cycle : « cycle entre Article, Auteur » se corrige, « ordre non déduit » ne se corrige pas.
  **Un fichier peut écrire dans plusieurs tables**, et l'ordre ne regardait que le premier `INSERT INTO`. Un fichier insérant dans `articles` puis `commentaires` était classé comme s'il ne touchait qu'`articles`, et pouvait passer avant celui dont `commentaires` dépend. Toutes les tables écrites sont lues, et le fichier classé après la plus tardive de leurs dépendances.
  Une table se référençant elle même est signalée : l'ordre doit y être respecté ligne à ligne dans le fichier, ce qu'aucun classement de fichiers ne peut garantir.

- **Une colonne absente donne une erreur, et non dix mille (`IMPEXP-COLUMN-MAPPING-001`).**
  `FieldSpec.name` servait à la fois de clé d'enregistrement et de nom de colonne CSV : un export tableur dont l'en-tête dit « Adresse e-mail » ne pouvait pas alimenter le champ `email`, et il fallait renommer les colonnes à la main avant chaque import. `source` déclare le ou les en-têtes acceptés, essayés dans l'ordre.
  **Le défaut le plus coûteux était ailleurs.** Une colonne absente n'était pas détectée : `row.get(nom, "")` rendait une chaîne vide, et chaque ligne produisait « valeur requise manquante ». Un fichier de dix mille lignes rendait dix mille erreurs pour un seul en-tête mal orthographié, et la vraie cause restait introuvable au milieu. Les en-têtes sont maintenant rapprochés une fois, avant d'examiner la moindre ligne.
  **Rien n'est rapproché par ressemblance.** Ni la casse ni les accents ne sont normalisés : rapprocher « Prix HT » de `prix_ttc` parce que les deux contiennent « prix » ferait importer la mauvaise colonne sans le signaler. Les espaces de bordure sont en revanche tolérées, un export tableur en posant souvent sans intention.

- **Le rapport d'erreurs se télécharge (`IMPEXP-ERROR-REPORT-001`).**
  `ImportReport` portait une liste exploitable en Python et inutilisable par la personne qui a déposé le fichier. Un import de deux mille lignes avec quarante erreurs ne se corrigeait qu'en lisant un écran, une erreur à la fois, sans jamais voir la ligne fautive.
  Le rapport CSV porte la ligne, **le numéro affiché par un tableur** (la ligne 1 des données est la ligne 2 du fichier, et ne donner que l'une des deux fait chercher au mauvais endroit), la colonne, le message et la valeur refusée.
  **Le rapport est lui même échappé** : il contient des données venues du fichier déposé, et sans échappement une cellule commençant par `=` redeviendrait une formule vive à son ouverture. Le rapport d'erreurs deviendrait le vecteur.

- **Un second format, JSONL (`IMPEXP-JSONL-001`).**
  Le CSV ne porte aucun type et ne sait pas représenter une valeur imbriquée : un export destiné à un autre programme y perd la différence entre le nombre `1`, le texte `"1"` et le booléen `true`.
  JSONL plutôt que JSON : un tableau impose de tout charger avant de lire le premier enregistrement, et une virgule manquante le rend entièrement illisible, là où une ligne fautive en JSONL n'empêche pas de lire les autres.
  Une clé absente est écrite à `null` et jamais omise, un consommateur de flux ayant besoin que toutes les lignes aient la même forme. La lecture est stricte par défaut ; le mode tolérant existe pour récupérer ce qui est lisible d'un fichier abîmé, et perd des données en silence, ce que la documentation dit.

### Corrigé

- **L'export CSV du CRUD ne tronque plus en silence (`IMPEXP-FILTERED-EXPORT-001`).**
  **Faux besoin mesuré** : l'export respectait déjà recherche, tri et filtres de la liste. Le manque était ailleurs, et bien plus grave.
  `_EXPORT_LIMIT` valait mille, et **rien ne le disait**. Un utilisateur qui filtrait trois mille lignes en recevait mille, dans un fichier impossible à distinguer d'un export complet jusqu'à ce que quelqu'un compte. Pour un export destiné à un contrôle ou à une reprise de données, c'est une perte silencieuse.
  La fonction d'export demande désormais une ligne de plus que le plafond, seule façon de savoir qu'il en restait sans payer un `COUNT` sur la même requête. La troncature se voit dans le **nom du fichier**, suffixé `-TRONQUE`, ce que la personne lit, et dans les en-têtes `X-Forge-Export-Truncated` et `X-Forge-Export-Limit`, pour un client programmatique.
  Le correctif vit dans le générateur : un contrôleur déjà engendré garde l'ancien comportement jusqu'à un nouveau `forge make:crud`.
  Sept tests de `test_crud_export_csv.py` découpaient un **nombre fixe de caractères** après le début de la fonction engendrée, et l'un avait déjà vu sa fenêtre « étendue » une fois. Ils extraient maintenant la fonction entière, et ne demanderont plus d'extension.

- **L'API IoT ne donne plus tous les sites à qui en veut un (`IOT-DEVICE-AUTH-001`).**
  Elle était protégée par **un** jeton, `FORGE_IOT_API_TOKEN`, qui ouvrait toutes les mesures de tous les sites. Un prestataire chargé des capteurs d'un bâtiment recevait ce jeton, et lisait par là les mesures des autres, sans qu'aucun mécanisme ne l'en empêche ni ne le signale.
  Un jeton porte désormais une portée, globale, un site, ou un seul équipement d'un site. `forge iot:token` les crée, les liste et les révoque. Le filtrage a lieu **en SQL** : rapatrier les mesures des autres sites pour les écarter ensuite les aurait fait passer par un processus qui n'y a pas droit.
  **Le registre s'active en le passant à `register_iot_routes`, jamais d'office.** Le monter par défaut exigerait un jeton là où l'API était ouverte, et casserait sans le dire les déploiements existants. `FORGE_IOT_API_TOKEN` garde la portée globale, le retirer étant une rupture d'API publique que la règle C refuse.
  Le jeton n'est **affiché qu'une fois** et n'est stocké que par son empreinte. Un simple SHA-256 y suffit, sans sel ni étirement : le jeton est engendré avec 256 bits d'entropie, contrairement à un mot de passe humain, et il n'existe donc ni dictionnaire ni table arc-en-ciel à lui opposer. La révocation pose une date et ne supprime pas la ligne.
  Un refus de portée est un **403**, pas un 401 : un 401 ferait croire au porteur que son jeton est faux, et il le remplacerait au lieu d'en demander un dont la portée convient.

- **Les relevés répondent enfin à la question qu'on leur pose (`IOT-AGGREGATES-001`).**
  Le paquet rendait les mesures brutes et les comptait. « Quelle a été la température moyenne de la semaine, et jusqu'où est elle montée » n'avait aucune réponse, et l'application devait rapatrier toutes les mesures pour les additionner en Python, ce qui devient impraticable dès qu'un capteur relève chaque minute.
  Deux routes et deux fonctions rendent moyenne, minimum, maximum et effectif sur une fenêtre, par site ou par équipement, en `AVG`/`MIN`/`MAX` standard écrits une fois pour les quatre backends.
  **Une fenêtre vide ne rend pas zéro** : « le capteur n'a rien envoyé » et « le capteur a relevé zéro » sont deux faits différents, que confondre fausserait toute moyenne. Le comptage porte sur `value` et non sur `*`, une mesure sans valeur ne devant pas gonfler l'effectif d'une moyenne qu'elle n'alimente pas.
  PostgreSQL rend `AVG` en `Decimal` là où MariaDB rend un flottant : la valeur est normalisée, sans quoi la même requête donnerait deux types selon le backend et la sérialisation JSON échouerait sur l'un des deux.

- **Un contrôle d'accès applicatif peut se brancher sur la lecture (`IOT-RBAC-READ-001`).**
  Le jeton dit ce qu'un porteur peut lire ; il ne dit rien de qui le porte ni de ce que cette personne a le droit de faire.
  **Une prise, et non une dépendance à `forge-mvc-rbac`** : aucun opt-in n'importe un autre, et un paquet IoT qui dépendrait du RBAC obligerait à installer le RBAC pour recevoir des mesures MQTT. Un test le vérifie par `ast`.
  **Une vérification qui échoue refuse la lecture.** Un contrôle qui lève ou qui rend autre chose qu'un booléen ne dit pas que l'accès est permis, il ne dit rien ; traiter ce silence comme une autorisation ouvrirait tout le jour où le service de permissions tombe. L'incident est journalisé pour l'exploitant.
  Plusieurs contrôles cohabitent, tous doivent accepter, et le premier refus arrête la série. Sans contrôle branché, rien ne change : le paquet n'invente pas une politique que personne n'a demandée. La liste des actions est fermée, de sorte qu'un contrôle branché sache exactement ce qu'il peut recevoir.

- **Les métadonnées d'un fichier audio sont enfin lisibles (`AUDIO-ID3-001`).**
  `ffprobe` les rendait déjà, le paquet les jetait : le sondage lisait la durée, le codec et le débit, et laissait tomber le titre, l'artiste et l'album. Une application devait rappeler `ffprobe` elle même pour afficher le nom d'un morceau qu'elle venait de recevoir. `probe_audio(...).tags` les porte, et n'est jamais `None`.
  **Le vrai sujet du ticket est le nettoyage.** Une étiquette vient du fichier envoyé, elle est écrite par qui l'a produit, et elle finit affichée dans une page. Les caractères de contrôle sont retirés, y compris `U+2028` que `str.strip` laisse passer et qui casse une chaîne JavaScript ; la longueur est bornée, rien n'empêchant un titre d'un mégaoctet ; et rien n'est interprété, l'échappement appartenant au gabarit.
  Les noms d'étiquettes varient selon le conteneur, ID3 disant `tit2` là où Vorbis dit `TITLE` : les clés sont cherchées en minuscules, par ordre de préférence, et un conteneur sans bloc de format voit ses étiquettes lues sur le flux. Une année implausible ou un « piste 5 sur 2 » sont écartés, afficher une valeur manifestement fausse valant moins que ne rien afficher.
  Le module ne réécrit jamais les étiquettes d'un fichier : lire et écrire sont deux gestes.

- **Un fichier audio peut être découpé (`AUDIO-TRIM-001`).**
  Extraire un extrait, retirer un silence de tête, produire un aperçu : le paquet transcodait un fichier entier et ne savait pas en prendre un morceau. Il fallait rappeler `ffmpeg` à la main, donc réécrire le durcissement des arguments et la gestion du délai.
  `forge audio:trim source.wav extrait.mp3 --from 1:30 --to 2:00`. Les trois écritures d'un instant sont acceptées, `90`, `1:30` et `0:01:30.5`.
  **La sortie ne peut pas être la source** : une découpe sur place n'existe pas côté `ffmpeg`, qui lit et écrit en même temps, et le fichier serait tronqué à zéro. La comparaison porte sur le chemin résolu, `a.mp3` et `./a.mp3` désignant le même fichier. **Un fichier de sortie existant n'est pas écrasé** sans `--force`, mode « Forge génère » de la charte.
  Un intervalle vide ou renversé est refusé plutôt que joué, `ffmpeg` écrivant sinon un fichier de zéro seconde sans se plaindre. `-ss` est placé avant `-i`, ce qui fait sauter directement à l'instant demandé au lieu de décoder tout ce qui précède, et change une découpe de plusieurs minutes en une opération immédiate sur un long fichier.

- **Les deux diagnostics média ne peuvent plus diverger (`AUDIO-DOCTOR-HARMONISE-001`).**
  **Faux besoin mesuré** : `audio:doctor` et `video:doctor` étaient déjà alignés, même dataclass de résultat, mêmes statuts, mêmes contrôles. Le ticket livre donc le garde-fou qui manquait, qui exige l'égalité stricte des deux surfaces à un contrôle près, la migration que l'audio n'a pas puisqu'il est sans état.
  La comparaison a en revanche fait apparaître une divergence réelle ailleurs, corrigée ici.

### Modifié

- **Une valeur de configuration audio illisible lève, au lieu de retomber sur le défaut** (`AUDIO-DOCTOR-HARMONISE-001`).
  `FORGE_AUDIO_MAX_UPLOAD_MB=abc` donnait 200 en silence : les fichiers plus lourds étaient refusés, et rien ne l'expliquait. Les quatre paquets qui bornent quelque chose se comportent désormais pareil, `files`, `images`, `video` et `audio`.
  Un test verrouillait le comportement inverse, c'est à dire le défaut ; il a été réaligné sur la règle.

- **`safe_path_arg` et `default_ffmpeg_runner` deviennent publics dans `forge-mvc-audio.transcode`.**
  La découpe construit sa propre ligne de commande et doit appliquer le même durcissement d'arguments. En garder une seconde copie privée les aurait fait diverger le jour où l'une serait corrigée.

- **L'état de traitement d'une vidéo est enfin montrable (`VIDEO-STATUS-UI-001`).**
  Le paquet enregistrait quatre états sans donner de quoi les afficher : après l'envoi, la page ne savait pas dire où en était le transcodage, et chaque application réécrivait sa correspondance vers un libellé français. `describe_video_status` la fournit, et `GET /videos/{uuid}/status` la rend en JSON pour rafraîchir une page sans la recharger.
  **La sortie d'erreur de ffmpeg ne sort jamais.** `error_message` porte le message de ffmpeg, qui contient les chemins absolus des fichiers du serveur : un gabarit qui affiche « la raison de l'échec » publierait l'arborescence.
  `VideoStatusView` sépare `public_message`, destiné à l'écran, de `technical_detail`, destiné au journal, et `as_public_dict()` ne peut pas rendre le second. La séparation est portée par le type et non par une consigne de documentation : un gabarit ne peut pas afficher par accident un champ qui n'est pas là.
  Un état inconnu ou une ligne absente ne lèvent pas. Une exception ici remplacerait une page dégradée par une page d'erreur, ce qui est pire pour la personne qui regarde.

- **La vidéothèque entière peut être plafonnée (`VIDEO-QUOTA-001`).**
  Les limites **par fichier** existaient déjà et fonctionnaient, taille à l'entrée et durée au sondage. Leur **somme** n'était bornée par rien : cinq cents vidéos d'une heure et de 999 Mo passent chacune le contrôle, et remplissent le disque de cinq cents gigaoctets.
  `FORGE_VIDEO_MAX_TOTAL_MB` et `FORGE_VIDEO_MAX_TOTAL_DURATION_SECONDS` bornent les cumuls. Sans elles rien n'est plafonné, et la base n'est pas même interrogée : un déploiement sans quota ne paye pas une requête par envoi.
  **La durée se vérifie au traitement, pas à l'envoi**, puisqu'elle n'est connue qu'après le sondage. Un dépassement fait échouer le traitement et laisse le fichier source. Sonder avant d'écrire demanderait un fichier temporaire et un appel `ffprobe` de plus par envoi, pour déplacer le problème sans le résoudre. La documentation le dit plutôt que de le laisser découvrir.

- **Une vidéo peut porter des sous-titres (`VIDEO-SUBTITLES-001`).**
  Sans eux, une vidéo est inaccessible aux personnes sourdes ou malentendantes, illisible dans un environnement bruyant, et introuvable par une recherche textuelle.
  Une **table** plutôt qu'une colonne : une vidéo porte souvent plusieurs pistes, une par langue, et une colonne unique aurait forcé à en choisir une ou à sérialiser une liste dans du texte, ce que le principe 5 refuse.
  **WebVTT seul**, le seul format que la balise `track` lit nativement. En accepter d'autres demanderait de convertir à la volée ou de faire porter la conversion au navigateur, qui ne sait pas la faire ; le principe 11 veut une seule façon officielle.
  **Ce qui n'est pas du WebVTT est refusé à l'entrée**, sur la signature que la spécification exige. Sans ce contrôle, n'importe quel fichier serait stocké et servi depuis le domaine de l'application sous un nom rassurant. Le refuser à l'écriture vaut mieux que de le filtrer à chaque lecture.
  Le chemin est bâti depuis l'UUID et l'étiquette de langue, tous deux validés : le nom du fichier envoyé n'y entre pas, et aucune traversée n'est possible. L'étiquette est normalisée en minuscules, `FR` et `fr` créant sinon deux pistes que le lecteur afficherait deux fois. La piste est servie avec la règle d'accès de la vidéo, une piste disant ce que la vidéo raconte.

### Modifié

- **Une valeur de configuration vidéo illisible lève, au lieu de retomber sur le défaut** (`VIDEO-QUOTA-001`).
  `FORGE_VIDEO_MAX_DURATION_SECONDS=7200x` donnait 3600 en silence : les vidéos de deux heures étaient refusées, et rien n'expliquait pourquoi. Le paquet suit désormais `forge-mvc-files` et `forge-mvc-images`, une limite mal écrite se signalant au démarrage.
  Un test verrouillait le comportement inverse, c'est à dire le défaut lui même ; il a été réaligné sur la règle, et non retiré.

- **Les variantes d'image se déclarent, au lieu de vivre en dur (`IMAGES-PRESETS-DECLARATIFS-001`).**
  `medium` et `thumbnail` vivaient dans une constante de module accordée à la main avec deux dictionnaires littéraux : ajouter une taille demandait d'éditer le paquet en trois endroits. L'ADR-018 avait relevé la conséquence sans la corriger, « non extensible sans éditer le code ».
  `IMAGE_VARIANTS=thumbnail:300x300,banniere:1920x1080:crop` déclare les préréglages, et `variant_presets()` les **relit à chaque appel**. La constante était un instantané pris au chargement du module, aveugle à toute configuration posée ensuite : c'était la cause, elle est retirée.
  Le nom devient un dossier sur le disque, donc il est validé. `original` est **réservé**, il désigne le fichier source et une variante de ce nom l'écraserait. Un préréglage déclaré deux fois est refusé, garder la dernière déclaration en silence produisant une taille que personne n'a lue.
  Sans déclaration, les deux préréglages historiques s'appliquent : un projet existant ne change pas de comportement.

- **Une variante peut être rognée autour d'un point d'intérêt (`IMAGES-FOCAL-CROP-001`).**
  Une variante en mode `crop` remplit exactement sa boîte, ce qu'un rognage centré fait mal : sur une photo de groupe cadrée large le centre tombe entre deux personnes, et une bannière taillée dans un portrait coupe la tête.
  Le point est exprimé en fractions, donc valable quelles que soient les dimensions. Une valeur hors de l'intervalle est **ramenée** dedans plutôt que refusée, un clic au bord d'une interface donnant facilement `1.0001` et un téléversement ne devant pas échouer pour un arrondi.
  **La fenêtre est recalée dans l'image.** Un point proche d'un bord donnerait une fenêtre à cheval sur le vide, que Pillow comblerait par du noir.
  **Forge n'invente pas de pixels.** Si la source est plus petite que la boîte, la variante garde le rapport demandé à la taille disponible ; agrandir produirait une image floue se faisant passer pour la taille déclarée. Forge ne détecte pas non plus le point d'intérêt, la saillance demandant un modèle et une surveillance que le paquet n'a pas à porter.

- **Les variantes que plus rien ne sert se voient avant de se supprimer (`IMAGES-ORPHAN-VARIANTS-001`).**
  Deux situations laissent des fichiers derrière elles, et la seconde naît des préréglages déclarables : une variante dont l'original a disparu, et une variante d'un préréglage retiré de `IMAGE_VARIANTS`, dont le dossier garde tout ce qu'il a produit.
  `forge images:orphans` les nomme, affiche par défaut et supprime sur `--delete` (charte §7). Le rapport dit les préréglages en vigueur, sans quoi « préréglage retiré » ne se vérifie pas.
  **Aucune base n'est consultée**, contrairement à `files:orphans` : une variante est orpheline si son original manque sur le disque, ce qui se lit du disque seul, et le garde-fou du registre vide n'a donc pas lieu d'être. La reconnaissance d'un dossier de variantes repose sur la présence d'un fichier homonyme au niveau du dessus, ce qui écarte les dossiers applicatifs.

- **Une entité choisit les variantes dont elle a besoin (`IMAGES-ENTITY-FIELD-001`).**
  Un contrat pouvait dire `variants: true` ou `false`, toutes ou aucune. Une fois les préréglages déclarables ce booléen ne suffit plus : un avatar n'a pas besoin d'une bannière de 1920 sur 1080, dont la génération coûte à chaque envoi.
  `"variants": ["thumbnail"]` nomme les préréglages voulus. Le contrat vérifie la forme de la liste et non l'existence des noms, ceux ci vivant dans la configuration de `forge-mvc-images` qu'un opt-in ne peut pas importer depuis un autre.
  **Un nom non déclaré lève à la génération.** L'ignorer laisserait l'entité réclamer une déclinaison inexistante, et la page finirait avec une image cassée sans que rien n'ait signalé la cause.
  Le dictionnaire de retour ne porte que l'original et ce qui a été **produit** : rendre le chemin d'une variante non générée ferait stocker à l'appelant une adresse qui ne répond pas.

- **Les dimensions et le poids d'une image se bornent (`IMAGES-LIMITS-CONFIG-001`).**
  Le paquet portait une seule limite, la surface en pixels, pensée contre la bombe de décompression. Elle laisse passer une image de 12000 sur 2000, qui tient sous les 24 mégapixels et qui est pourtant impossible à afficher, coûteuse à redimensionner et volumineuse à servir.
  `IMAGE_MAX_WIDTH`, `IMAGE_MAX_HEIGHT` et `IMAGE_MAX_BYTES` complètent la garde de surface, qui reste en place parce qu'elle protégeait contre autre chose. Le poids est distinct d'`upload_max_size` : une application peut accepter un PDF de 20 Mo et refuser une photo de 5 Mo.
  Une valeur illisible **lève**, comme pour le quota de `forge-mvc-files`, et le message dit que retirer la variable est la façon de ne pas borner. Les dimensions sont contrôlées sur l'en-tête avant tout décodage, et le poids avant même l'ouverture.

### Modifié

- **`IMAGE_VARIANT_SIZES` a disparu de l'API publique de `forge-mvc-images`** (`IMAGES-PRESETS-DECLARATIFS-001`).
  Le symbole était la cause du défaut, un instantané figé à l'import : le garder en le dérivant aurait laissé la même surprise. `variant_presets()` le remplace partout, y compris dans les parcours d'accueil, qui affichent désormais ce que le projet produit vraiment plutôt qu'un couple de valeurs écrit d'avance.
  Conformément à la convention pré-1.0, la rupture se fait sans alias déprécié. L'ADR-018 conserve son texte, et note que la conséquence qu'il avait relevée est levée.

- **Un compte ne peut plus remplir le disque un fichier valide à la fois (`FILES-QUOTA-001`).**
  Chaque envoi passait la taille maximale, et rien ne regardait la somme. Le registre de l'ADR-094 la connaissait, personne ne la lisait.
  Le quota porte sur le couple propriétaire, une nature et un identifiant : `user` et `article` ne se règlent donc pas ensemble, ce qui est le sens de « par utilisateur et par ressource ». `FILES_QUOTA_USER_BYTES` l'emporte sur `FILES_QUOTA_BYTES`, et sans aucune des deux rien n'est borné.
  **Une valeur d'environnement illisible lève au lieu d'être ignorée.** `FILES_QUOTA_BYTES=50MB` interrompt la lecture. Retomber en silence sur « aucune limite » à cause d'une faute de frappe irait exactement dans le mauvais sens, et personne ne le verrait avant que le disque soit plein. Le message nomme la variable et donne la valeur en octets.
  **Ce n'est pas une borne infranchissable, et la documentation le dit.** Le contrôle lit la somme puis l'appelant écrit : deux envois simultanés peuvent passer tous les deux, le dépassement restant borné par `upload_max_size`. Fermer cette fenêtre demanderait de sérialiser les envois d'un même compte, pour une garantie que personne n'a demandée.
  `QuotaExceededError` descend d'`UploadError` : une application qui entoure déjà `save_upload` d'un `except UploadError` traite le refus sans changer une ligne.

- **Une analyse antivirus peut se brancher, et sa panne ne vaut pas feu vert (`FILES-SCAN-HOOK-001`).**
  Forge valide l'extension, le type MIME, la taille et les premiers octets. Aucun de ces contrôles ne dit si le contenu est malveillant, un PDF porteur d'une charge active ayant l'extension, le type et la signature d'un PDF.
  Le paquet ne fournit aucune analyse et n'en fournira pas, un moteur antivirus étant un service à installer et à tenir à jour, dont la base de signatures serait périmée le jour de la publication. Il fournit la prise : `register_file_scanner` branche l'analyseur, `save_upload` le consulte.
  **L'analyse précède l'écriture.** Un fichier analysé après avoir touché le disque y est déjà, et l'y laisser quelques millisecondes suffit à ce qu'une sauvegarde ou un indexeur le voie. Un test vérifie qu'un refus ne laisse rien sur le disque.
  **Un analyseur qui lève, qui expire ou qui rend autre chose qu'un verdict refuse le dépôt.** C'est la faute classique de ce genre de branchement : traiter le silence comme un feu vert, et voir tout passer le jour où le service antivirus tombe, sans un signal. `ScannerUnavailableError` reste distincte de `UploadRejectedByScanError`, l'une étant une panne à réparer et l'autre un avis rendu sur un fichier.
  Le motif technique du refus ne parvient jamais au déposant : le nom d'une signature dit ce qui est détecté, donc ce qui ne l'est pas.

- **Les fichiers sans référence se voient avant de se supprimer (`FILES-ORPHAN-PURGE-001`).**
  Un fichier détaché de l'entité qui le portait reste sur le disque, servi par personne et compté dans la sauvegarde. `forge files:orphans` rapproche le dossier d'upload et le registre, et nomme les deux sortes d'orphelins, le fichier que rien n'inscrit et l'inscription dont le fichier a disparu.
  **Un registre vide interrompt la commande.** L'inscription est explicite (ADR-094) : une application qui n'appelle jamais `record_file` a un registre vide et des fichiers parfaitement vivants. Sans ce refus, la première exécution effacerait la totalité des uploads du projet, et c'est le scénario le plus coûteux atteint par la commande la plus banale.
  **Un fichier récent n'est jamais candidat.** Entre l'écriture et l'inscription il s'écoule un instant, davantage si l'application inscrit après validation d'un formulaire ; une purge qui tourne dans cet intervalle supprimerait un dépôt en cours. Le seuil par défaut est d'un jour.
  La commande affiche seulement, `--delete` applique (charte §7). `find_orphans` rend le rapport et `purge_orphans` l'applique tel quel, de sorte qu'un fichier déposé entre les deux gestes n'entre pas dans la fournée. Le rapport dit ce qu'il a écarté, une absence de la liste ne devant pas se lire comme « jugé sain ».

- **L'envoi d'un gros fichier peut être délégué au serveur frontal (`DOC-FILES-XACCEL-001`).**
  `serve_media_file` sert depuis Python, ce qui immobilise un travailleur pendant tout l'envoi : sur 200 Mo et une connexion lente, un travailleur Gunicorn recopie des octets pendant plusieurs minutes.
  Le motif est documenté : le contrôleur décide, `X-Accel-Redirect` fait envoyer nginx, et le contrôle d'accès reste en Python.
  **La moitié qui protège est la directive `internal;`.** Sans elle, le dossier d'upload répond directement par URL, le contrôle du contrôleur ne sert plus à rien, et la délégation devient pire que le service par Python.
  C'est pourquoi Forge ne livre pas d'assistant : il vivrait dans le paquet alors que la garantie vit dans une configuration que Forge ne lit pas, et laisserait croire que l'appeler suffit.

- **Un réglage personnel a sa place, sans collision possible (`SETTINGS-PER-USER-001`).**
  Le thème ou la langue d'un utilisateur n'avaient pas où se ranger, la clé primaire portant la seule clé du paramètre. Une clé composée `user.42.theme` marchait, mais rien n'empêchait la collision : un paramètre global du même nom aurait désigné la même ligne, et l'un aurait écrasé l'autre en silence.
  Le préfixe `user.` est donc **réservé**, et `set_setting` le refuse en nommant la bonne porte. L'identifiant ne peut pas contenir de point, séparateur d'espace de noms, deux utilisateurs pouvant sinon viser la même clé.
  `get_all_settings` ne rend que les paramètres globaux : les mêler ferait grossir la configuration de l'application au rythme de ses comptes, et un écran de réglages afficherait les préférences de tout le monde.
  Un réglage absent **ne retombe pas** sur le paramètre global de même nom. Sinon « cet utilisateur n'a pas de préférence » et « sa préférence vaut le défaut de l'application » ne se distinguent plus, et l'appelant ne peut plus dire lequel il lit ; le repli, s'il le veut, est une ligne de son code.

- **Les paramètres peuvent être servis de mémoire (`SETTINGS-CACHE-001`).**
  Un paramètre est lu à chaque requête, parfois plusieurs fois, et change une fois par mois. Chaque lecture faisait pourtant un aller-retour vers la base.
  Le cache est **éteint par défaut** : il change ce qu'une lecture garantit, la dernière valeur vue au lieu de la valeur en base, et le principe 3 refuse qu'un comportement change dans le dos de l'appelant.
  L'invalidation est explicite, jamais par expiration, qui ferait cohabiter deux valeurs pendant un délai que personne n'a choisi. Une écriture passant par le paquet invalide son entrée ; une écriture faite ailleurs, par une migration, demande un `clear_settings_cache` que l'exploitant décide.
  Une absence est mise en cache comme une valeur, sans quoi un paramètre non posé serait relu à chaque fois, et c'est le cas fréquent. Activer le cache le vide, son contenu pouvant dater d'avant des écritures faites entre temps.
  Ce n'est pas un cache partagé : un déploiement à plusieurs travailleurs en a un par travailleur, ce que la documentation dit plutôt que de le laisser découvrir.

- **Un paramètre n'est pas un endroit pour un secret (`DOC-SETTINGS-NO-SECRETS-001`).**
  Rien ne le disait, et la table s'y prête : un mot de passe SMTP ou un jeton d'API y aurait tenu. Il y serait en clair, lisible par qui accède à la base ou à une sauvegarde, et affiché tel quel par l'écran d'administration.
  La documentation trace la limite avec un tableau de ce qui va ici et de ce qui n'y va pas, et dit où vivent les secrets, l'environnement, que `deploy:check` contrôle déjà.
  Elle explique aussi pourquoi Forge ne chiffre pas cette table : la clé de déchiffrement devrait vivre dans l'environnement, autant y mettre le secret directement, ce qui est plus simple et plus facile à auditer.

- **Un email peut porter une pièce jointe (`MAIL-ATTACHMENTS-001`).**
  Une facture, un export, un justificatif : le paquet ne savait pas en joindre. `with_attachment` rend un message **augmenté** plutôt que de modifier celui qu'on lui donne, un message mis en file puis complété ailleurs partant sinon dans deux états.
  Le nom de fichier est assaini : il voyage dans un en-tête MIME, s'affiche chez le destinataire, et vient souvent d'un fichier déposé par un utilisateur. Un chemin est réduit à son dernier segment, et un saut de ligne retiré, qui couperait l'en-tête en deux.
  Le type MIME est deviné du nom et retombe sur `application/octet-stream` : un type faux serait suivi par le client mail pour ouvrir le fichier. La taille est bornée, un refus à la construction se diagnostiquant mieux qu'un refus du relais après coup.

- **`mail:test` peut vérifier sans écrire à personne (`MAIL-TEST-GUIDED-001`).**
  La commande envoyait toujours : vérifier sa configuration commençait par écrire à quelqu'un, et exigeait un relais joignable. `--dry-run` montre le message qui partirait.
  Le diagnostic **précède** l'envoi, transport, `MAIL_ENABLED`, expéditeur et serveur : un « non envoyé » annoncé après coup se lit comme un échec, alors que c'est une configuration voulue. Un transport local affiche « aucun serveur » plutôt que `None:0`.

- **Les gabarits d'email peuvent partager un en-tête (`MAIL-LAYOUTS-001`).**
  **Faux besoin fonctionnel** : l'héritage Jinja marchait depuis toujours, le moteur montant un chargeur sur le dossier des gabarits. Rien ne le disait, et rien ne le figeait.
  Le ticket livre donc des tests qui verrouillent la capacité, qu'une refonte du renderer pourrait retirer en silence, et la documentation qui manquait. Un en-tête réécrit dans chaque gabarit est oublié quelque part le jour où l'adresse change.

- **Une tâche ne part plus deux fois (`JOBS-IDEMPOTENCY-KEY-001`).**
  Un utilisateur qui double-clique, un webhook rejoué, une requête relancée après un délai d'attente : la tâche partait deux fois, et l'email aussi. `enqueue(..., idempotency_key=...)` ne donne qu'une tâche, la seconde mise en file rendant l'identifiant de la première.
  **Un piège dialectal évité, mesuré contre les serveurs.** Une contrainte `UNIQUE` ordinaire sur colonne nullable n'accepte qu'un seul `NULL` sur SQL Server, là où les trois autres en acceptent autant qu'on veut : la deuxième tâche **sans** clé y aurait été refusée, c'est-à-dire presque toutes, et la file entière serait tombée sur ce backend. `Dialect.unique_nullable_index_sql` porte la différence, filtrée sur SQL Server.
  La course est fermée par la base : deux appels simultanés ne peuvent pas insérer tous les deux, et le perdant relit la ligne gagnante sans lever.

- **Une tâche longue peut prolonger son bail (`JOBS-HEARTBEAT-001`).**
  Une tâche plus longue que le bail se faisait reprendre par `jobs:reclaim`, donc **exécutée une seconde fois** pendant que la première tournait encore. Le remède était d'allonger le bail pour tout le monde, au prix d'une reprise tardive des vraies pannes.
  `heartbeat(claim_token)` recale le bail, et rend `False` quand le jeton ne désigne aucune tâche en cours : le travail est peut-être en train d'être refait ailleurs. La requête est gardée par le jeton, sans quoi n'importe qui retiendrait une tâche qu'il ne traite pas.

- **Les compositions de la file sont documentées (`DOC-JOBS-COMPOSITION-001`).**
  Un tableau unique renvoie vers les motifs de `mail`, `import-export` et `notifications`, en rappelant qu'aucun de ces paquets ne connaît les autres, et ce qu'une tâche doit faire échouer ou non.

- **Une notification porte un lien validé (`NOTIF-TARGET-URL-001`).**
  Le lien pouvait se ranger dans `data`, qui est libre, mais rien ne l'y validait alors qu'il finit dans un `href`. Une notification est écrite par l'application, et son contenu vient souvent d'une saisie.
  `target_url` est une colonne dédiée, validée **à l'écriture** : un schéma qui exécute du code au clic est refusé, y compris coupé par un blanc, certains navigateurs lisant `java<tabulation>script:` comme un schéma. Une URL protocole-relative l'est aussi, qui emmène sur un autre domaine tout en ressemblant à un chemin interne.
  Le refus empêche l'écriture : la ligne ne doit pas exister, plutôt que d'être filtrée à chaque affichage.

- **La liste des notifications se pagine sans sauter de ligne (`NOTIF-PAGINATION-001`).**
  `before_id` remplace ce qu'un `OFFSET` aurait fait de travers : une notification arrivée entre deux pages décale tout ce qui suit, si bien que la page 2 réafficherait la dernière ligne de la page 1 et en cacherait une autre.
  Une liste de notifications est justement celle qui reçoit des écritures pendant qu'on la parcourt.

- **Tracer depuis un contrôleur prend l'acteur dans la requête (`AUDIT-ACTION-HELPER-001`).**
  `record_audit` demande l'acteur en paramètre, et la documentation le montrait écrit à la main. Dans un contrôleur il vient de la session, et chaque appel devait l'en extraire.
  L'oublier une fois donne une ligne sans acteur, c'est-à-dire un journal qui ne répond plus à « qui a fait cela ». Rien ne le signale : la ligne existe, elle est simplement inutile.
  `record_request_audit` fait cette extraction. L'acteur reste `None` quand personne n'est authentifié, ce qui est une **information** et non un manque : une action de visiteur anonyme ou de tâche de fond n'a pas d'auteur, et inventer « system » masquerait la différence.
  Une session illisible donne un acteur absent, jamais une exception : un journal qui interrompt l'opération qu'il devait enregistrer serait pire que l'absence de journal.

- **Un journal d'audit se borne à une période (`AUDIT-FILTERS-001`).**
  Quatre filtres d'égalité existaient déjà, par acteur, action et cible. La question qu'on pose le plus souvent à un journal n'avait aucune réponse : « que s'est-il passé entre telle date et telle autre ».
  `since` et `until` bornent la lecture **et** l'export, et acceptent un `datetime`, un horodatage ou une date seule, un champ de formulaire ne rendant que du texte.
  Une date de fin **inclut la journée entière**. C'est le piège le plus courant d'un filtre de période, et il est silencieux : à minuit, `until="2026-03-05"` exclurait toute la journée du 5, que l'utilisateur qui l'a saisie attend incluse.
  Une période inversée est refusée plutôt que de rendre zéro entrée : un résultat vide sans motif ferait chercher un défaut ailleurs, dans les droits ou dans l'écriture du journal.
  Les bornes partent en paramètres liés, jamais en expression SQL de date.

- **Les sessions d'un compte sont visibles, sans être compromises (`ADMIN-SESSIONS-VIEW-001`).**
  Révoquer était possible, voir ne l'était pas : l'exploitant déconnectait à l'aveugle, sans savoir combien de sessions étaient ouvertes ni depuis quand.
  `list_for_user` rejoint le contrat et les trois stores. `DbSessionStore` filtre l'expiration **en SQL** : une session expirée que la purge n'a pas encore retirée n'a pas à s'afficher comme active.
  Un résumé **ne porte jamais l'identifiant de session**, qui est le jeton d'authentification lui même : l'afficher donnerait à qui lit la page le pouvoir d'usurper la session, et un écran d'administration est lu par quelqu'un d'autre que son titulaire. `SessionSummary` expose un préfixe de huit caractères, assez pour distinguer deux lignes, trop court pour servir de jeton, et qui **ne permet pas de révoquer**.
  Ni adresse ni navigateur : Forge ne les enregistre pas, et prétendre le contraire dans un écran serait mentir. Les sessions gagnent en revanche une date de création, ajoutée délibérément aux champs prévus du garde-fou de durcissement.
  `DbSessionStore` accepte un accesseur `fetch_all`, nommé et posé en dernier pour ne pas déplacer les paramètres positionnels existants.

- **Les paramètres s'éditent depuis un écran, sans casser leur type (`ADMIN-SETTINGS-UI-001`).**
  Un paramètre porte une valeur **et** son type, que `set_setting` déduit de la première. Une page web ne reçoit que du texte, ce qui ouvrait trois pièges.
  Brancher un CRUD générique sur la table ferait saisir `value_type` à la main : une incohérence, `value_type=int` sur une valeur `abc`, casse toute lecture ultérieure du paramètre.
  Convertir avec `int(saisie)` lève une `ValueError` nue, donc une erreur cinq cents là où l'appelant attendait un refus de formulaire.
  Surtout, une valeur booléenne se lisait `text == "1"` : taper **`oui` y enregistrait faux, en silence**. L'exploitant croyait avoir activé une option, et rien ne le détrompait. `parse_setting_value` accepte les écritures usuelles des deux côtés et refuse ce qu'elle ne reconnaît pas.
  `describe_settings` rend la valeur typée **et** sa forme texte : ce que la page affiche, elle peut le renvoyer, là où un `True` produirait une saisie dépendante de la langue de Python.
  `get_settings_with_types` rejoint l'API publique, `get_all_settings` perdant le type qu'un écran doit pourtant renvoyer.

- **Un gros fichier s'importe par la file de tâches (`IMPEXP-ASYNC-JOBS-001`).**
  Importer pendant une requête HTTP la fait attendre autant qu'il y a de lignes. Dix mille lignes, dix mille insertions, et le navigateur abandonne avant la fin : l'utilisateur relance, l'import repart de zéro, et parfois double les lignes déjà écrites.
  Le moteur prend des fonctions de conversion et d'insertion, que JSON ne transporte pas : la tâche porte donc un **nom d'importeur** et un **chemin**, et l'application enregistre ses importeurs des deux côtés.
  `make_import_job_handler(root=...)` **borne les chemins acceptés**. Le chemin vient d'une file que plusieurs processus écrivent : sans racine, un `../../etc/passwd` serait lu et importé ligne à ligne dans la base.
  Un fichier mal rempli **ne fait pas échouer la tâche** : réessayer ne corrigerait pas un CSV, et la tâche rejouerait jusqu'à épuisement de ses tentatives. Le gestionnaire ne lève que sur un importeur inconnu ou un fichier illisible.
  `on_report` rend le rapport à l'application, avec le contexte de la tâche : sans lui, un import différé serait muet, et celui qui a déposé le fichier n'apprendrait jamais ce qui est passé.

- **Le journal d'audit s'exporte en entier (`AUDIT-CSV-EXPORT-001`).**
  `get_audit_log` rend des `AuditEntry` quand un écrivain CSV attend des dictionnaires : les deux ne se composaient pas, et chaque application réinventait la conversion avec son propre ordre de colonnes.
  Surtout, il borne à **mille entrées en silence**. Un export demandé sur cent mille lignes en rendait mille sans rien dire : pour un journal qu'on exporte précisément parce qu'il fait foi, le fichier paraissait complet.
  `iter_audit_rows` parcourt tout le journal par lots, et l'avance se fait **par identifiant, jamais par décalage** : un `OFFSET` sur une table qui reçoit des écritures pendant l'export sauterait ou répéterait des lignes, ce qu'un journal ne peut pas se permettre.
  `get_audit_log` garde sa limite, qui protège un affichage, et gagne un paramètre `before_id` pour le curseur.
  Le module rend des lignes et n'écrit aucun fichier : `forge-mvc-import-export` les écrit, aucun des deux n'importe l'autre, et les cellules héritent de la neutralisation des formules déjà en place.

- **Une notification peut être doublée par un autre canal (`NOTIF-MAIL-BRIDGE-001`).**
  Une notification in-app n'est vue que si son destinataire revient sur le site. Pour une alerte qui compte, une facture impayée ou un incident, c'est trop tard, et l'opt-in n'offrait aucun moyen de doubler le canal.
  Chaque application réécrivait la même chose à côté de `notify`, et l'y oubliait à un endroit sur trois : la notification partait, l'email non, et personne ne s'en apercevait avant la réclamation.
  `notify` annonce désormais ce qu'il écrit, par `on_notification_created`. L'événement porte l'identifiant, le destinataire, le type et le complément de données, souvent nécessaire pour composer le message relayé.
  Le paquet **annonce, il ne parle à personne** : il n'importe aucun autre opt-in, vérifié sur l'arbre syntaxique. Le motif documenté mène à `enqueue` et non à `mailer.send`, un envoi direct faisant attendre la requête qui a créé la notification.
  Un relais ne peut pas annuler une notification : l'annonce suit l'écriture, et faire échouer `notify` après coup laisserait l'appelant croire qu'elle n'existe pas alors qu'elle s'affiche.

- **Les statuts de workflow se lisent du contrat d'entité (`WORKFLOW-ENTITY-STATUS-001`).**
  Une application qui gère un cycle de vie déclarait sa liste de statuts **deux fois** : en `choices` du contrat, pour le formulaire et la base, et en Python pour le workflow.
  Rien ne gardait les deux identiques. Ajouter un statut au contrat sans toucher au workflow donne un choix que le formulaire propose et que la transition refuse ; le retirer donne une transition vers un statut que la base n'accepte plus. Dans les deux cas, la panne n'apparaît qu'à l'usage, sur un seul chemin.
  `statuses_from_entity_field` fait du contrat la source, et `validate_transitions` refuse alors toute transition vers un statut non déclaré, au chargement et non à l'usage.
  Le champ est **nommé, jamais deviné** : une convention de nommage se tromperait sur une entité qui porte deux statuts, publication et paiement par exemple. Le début et la fin du cycle se déclarent aussi, un contrat disant les valeurs permises et jamais laquelle commence.
  Aucune dépendance vers `forge-mvc-entities` : un contrat est un dictionnaire JSON documenté, et un test le vérifie sur l'arbre syntaxique.

- **Les refus d'accès peuvent être tracés (`RBAC-DENIAL-AUDIT-001`).**
  Un refus rendait une 403 et rien de plus. Aucune trace nulle part, si bien qu'une énumération de droits, quelqu'un qui essaie une à une les routes protégées, ne laissait rien derrière elle. L'exploitant n'avait aucun moyen de la voir, ni même de savoir qu'un compte butait sur une permission mal attribuée.
  Les **trois** gardes annoncent désormais leurs refus par `on_permission_denied`, et l'événement porte la permission, l'acteur, la route et la garde qui a refusé. Un visiteur anonyme est rapporté sans acteur, c'est souvent celui qu'on veut voir.
  Le paquet **annonce, il ne journalise pas** : il n'importe aucun autre opt-in, et un test le vérifie sur l'arbre syntaxique. `forge-mvc-audit` est le destinataire évident sans être imposé.
  Un observateur qui lève ne peut pas casser la réponse : l'exception est avalée et journalisée, les suivants sont appelés quand même. Transformer un 403 en 500 parce que la base d'audit est indisponible ferait d'un contrôle d'accès qui fonctionne une panne du site.
  Seuls les refus sont annoncés : annoncer les succès noierait le signal.

- **L'envoi d'email peut être confié à la file de tâches (`MAIL-QUEUE-VIA-JOBS-001`).**
  Envoyer un email pendant une requête HTTP la fait attendre le serveur SMTP. Une seconde de latence est courante, dix le sont aussi quand le relais est lent, et une panne du relais devient une panne du formulaire : l'utilisateur voit une erreur alors que son inscription est enregistrée.
  `message_to_payload` traduit un message en charge utile JSON, `make_mail_job_handler` rend le gestionnaire à enregistrer, et `MAIL_JOB_TASK` nomme la tâche une seule fois pour les deux côtés.
  **Les deux opt-ins ne se connaissent pas** : `forge-mvc-mail` n'importe jamais `forge_mvc_jobs`, et l'application seule les met en présence. Un test le vérifie sur l'arbre syntaxique, le docstring du module montrant justement l'exemple d'import qu'une lecture de texte prendrait pour un vrai.
  Le gestionnaire **lève** quand l'envoi échoue, ce qui déclenche le réessai : rendre `None` ferait marquer la tâche réussie et l'email ne partirait jamais. Un envoi sauté par `NullTransport` n'est pas un échec.
  Le message est validé **à la mise en file**, là où l'utilisateur voit l'erreur, et les champs de journalisation suivent : sans eux, différer un envoi rendrait `mail_log` muet.

- **Le diagnostic de base dit ce que le serveur répond (`DB-DOCTOR-001`).**
  `forge doctor` ne rapportait que « connexion OK », et cela ne suffit pas : une version trop ancienne, un jeu de caractères qui n'est pas de l'UTF-8, ou une connexion établie sous un compte inattendu sont des pannes à venir qu'aucune connexion réussie ne signale.
  Le contrôle rapporte désormais la version, l'encodage ou la collation, la base et le compte. Ce que chaque backend sait dire lui appartient, par `Dialect.server_diagnostics_sql` : un backend qui ne déclare rien reste correct, et le diagnostic se tait plutôt que d'inventer.
  Chaque requête est isolée, et celle qui échoue est omise. Le compte applicatif est volontairement en DML strict (ADR-033) et peut légitimement se voir refuser une lecture de métadonnées : ce refus n'est pas une panne du projet, et un diagnostic ne doit jamais faire échouer `doctor`.
  **Pas de commande `db:doctor`**, contrairement à ce que la roadmap proposait : `forge doctor` portait déjà ce contrôle, et une commande séparée aurait donné deux façons de poser la même question (principe 11).
  Vérifié contre les serveurs, les requêtes étant propres à chaque SGBD : les comparer à des chaînes n'aurait rien prouvé.

- **Les index déclarés au contrat atteignent enfin le SQL (`ENTITIES-UNIQUE-COMPOSITE-001`).**
  Le schéma d'entité **acceptait** une clé `indexes` avec un drapeau `unique`, `entity:validate` vérifiait que leurs champs existent, et le normaliseur les écartait ensuite, avec un commentaire disant que `build:model` ne les supportait pas encore.
  Une contrainte d'unicité composite passait donc la validation sans jamais atteindre la base. Ce n'est pas une fonctionnalité manquante mais une **garantie annoncée et non tenue**, ce qui est pire : l'application croyait ses doublons impossibles.
  Le modèle canonique porte désormais les index, ramenés aux colonnes réelles, et le générateur les rend. Un `unique` multi-champs devient une contrainte nommée dans le `CREATE TABLE`, le nom permettant au serveur de désigner la contrainte violée.
  Vérifié contre les serveurs : le doublon est refusé, le couple différent passe, et un index non unique ne contraint rien. Une comparaison de chaînes n'aurait rien prouvé, une contrainte pouvant être bien écrite et ne rien contraindre.
  Un test figeait le défaut, vérifiant que les index étaient **absents** du modèle. Il vérifie maintenant l'inverse.
  Un projet créé avant la rc8 doit régénérer son SQL et appliquer la migration pour que la contrainte existe réellement.

- **Une permission peut porter sur un objet précis (`RBAC-INSTANCE-PERMISSIONS-001`).**
  Les trois gardes du paquet répondaient toutes à « cet utilisateur peut il modifier des articles ». Aucune ne répondait à « peut il modifier **cet** article, parce qu'il en est l'auteur ».
  Chaque application réécrivait la condition à la main, et souvent de travers : oublier que le modérateur passe outre la propriété, ou vérifier la propriété avant la permission, donne un contrôle qui laisse passer ou qui bloque à tort.
  `has_instance_permission` fixe l'ordre. Le droit global l'emporte **sans regarder la propriété**, c'est le sens de « n'importe lequel » ; le droit de propriétaire ne s'applique qu'ensuite. `is_owner` n'est pas appelée quand le droit manque de toute façon, ce qui évite une requête pour un utilisateur qui n'a aucun droit.
  Forge ne sait pas ce qu'est un propriétaire, et ne le devine pas : déclarer `own_permission` sans `is_owner` est refusé, plutôt que de laisser un droit qui ne serait jamais accordé.
  Ce n'est **pas un quatrième niveau** d'autorisation : la fonction n'a aucune source de permissions et compose au dessus de celle que l'appelant désigne. Un test le vérifie sur la source.

- **Le back-office filtre, cherche et trie ses listes (`ADMIN-LIST-FILTERS-001`).**
  La liste affichait la table entière, page par page, sans autre choix que de tourner les pages. Passé quelques centaines de lignes, retrouver un enregistrement devenait impraticable, et le back-office avec lui.
  Une ressource déclare `filter_fields` et `search_fields`, **vides par défaut et jamais déduits** de `list_fields`. Un filtre porte sur une colonne nommée dans l'URL : accepter n'importe laquelle exposerait une colonne que la liste n'affiche pas, et une recherche sur une telle colonne permettrait d'en deviner le contenu caractère par caractère.
  Les noms sont comparés à la liste déclarée, jamais à la seule forme d'un identifiant SQL ; une colonne inconnue rend `400`, la demande étant fautive et non le serveur. Les valeurs partent en paramètres liés, et le sens du tri est un booléen, aucune chaîne d'URL n'entrant dans la clause `ORDER BY`.
  Les métacaractères `%` et `_` d'une recherche sont neutralisés avec un `ESCAPE '!'` déclaré, le backslash voyant son sens dépendre d'un réglage de serveur sur MariaDB.
  **SQL Server refuse une colonne répétée dans un `ORDER BY`**, ce que les trois autres backends acceptent : le tri secondaire par clé primaire est donc omis quand le tri porte déjà sur elle. Défaut trouvé contre le serveur, pas déduit.
  Les critères suivent la pagination, sans quoi tourner une page les perdrait.

- **Une transition de workflow s'applique dans un ordre garanti (`WORKFLOW-HOOKS-001`).**
  Le paquet savait dire si une transition est **permise**, jamais l'appliquer. Chaque application réécrivait le même enchaînement à la main, et rien n'empêchait d'appeler l'action d'après quand celle d'avant avait refusé.
  `apply_transition` enchaîne la vérification, `before`, l'écriture puis `after`, chaque étape conditionnant la suivante. Un `before` qui lève **empêche** la transition, ce qui donne sa valeur au mécanisme : une règle métier peut refuser, et son refus est visible.
  Un point d'accroche ne rend rien, il lève pour refuser : un booléen obligerait Forge à inventer un message d'erreur à la place de la règle métier. L'exception remonte telle quelle, sans enveloppe.
  `after` ne défait rien, et c'est dit : l'avaler cacherait un état déjà changé. Le paquet ne persiste toujours rien, `commit` étant fourni par l'application, seule à savoir où son statut est rangé.

- **L'état des files de tâches est visible (`JOBS-STATUS-CLI-001`).**
  Le paquet n'offrait aucun moyen de voir sa file. Un exploitant qui se demandait si le travail avançait devait interroger la base à la main, sans que rien ne lui dise quelle requête écrire : une file bloquée ressemblait exactement à une file vide.
  `forge jobs:status` affiche les compteurs par file, et `status_counts` les rend au code, pour une page d'administration par exemple.
  La colonne « prêtes » ne compte que les tâches en attente **et disponibles maintenant**. Une tâche `pending` peut être différée, par `available_in` ou par le délai croissant d'un réessai : confondre les deux ferait chercher un ouvrier en panne là où tout se déroule normalement.
  La commande est en **lecture seule**, `jobs:reclaim` faisant la reprise. Un test le vérifie sur la source : confondre les deux donnerait à un diagnostic un effet de bord que personne n'attend.

- **La file de tâches s'ordonne par priorité (`JOBS-PRIORITY-001`).**
  Elle prenait les tâches par ordre d'insertion, sans exception : une tâche urgente déposée derrière mille envois d'emails attendait mille envois, et rien ne permettait de la faire passer devant.
  `enqueue(..., priority=PRIORITY_HIGH)` ordonne la file en `priority DESC, id`. L'ancienneté départage à égalité, sans quoi deux tâches de même priorité se prendraient dans un ordre que rien ne garantit.
  Un entier plutôt qu'une énumération fermée : le défaut `0` rend « normales » les tâches déjà en file sans migration de données, et une application peut nuancer entre deux niveaux.
  La priorité **ordonne, elle n'interrompt pas** : une tâche déjà réservée va au bout, la file n'ayant aucun moyen d'arrêter un gestionnaire en cours.
  Premier usage de l'`AddColumn` de l'ADR-094, qui a révélé une limite : il ne rendait que les index d'une seule colonne. `AddColumn` accepte désormais `index_names` pour un index composite, et refuse un nom d'index inconnu plutôt que de produire une migration silencieusement incomplète.

- **`forge-mvc-i18n` sait d'où vient la locale (`I18N-LOCALE-DETECTION-001`).**
  Le paquet annonçait « locale et fallback » sans savoir d'où venait la locale : `trans()` retombait sur une valeur **globale** de configuration, la même pour tous les visiteurs. Une application multilingue devait écrire sa propre détection, ce que la documentation ne disait pas.
  `detect_locale` suit un ordre explicite, du plus intentionnel au plus supposé : le choix en session, l'en-tête `Accept-Language`, puis le défaut. `parse_accept_language` respecte les facteurs de qualité de la RFC 9110, `q=0` valant refus.
  `available_locales` sert de liste blanche aux deux sources clientes : sans elle, elles sont refusées et le défaut est rendu, un en-tête forgé ferait sinon chercher un catalogue arbitraire.
  Une variante régionale retombe sur sa base, `fr-FR` étant servi par `fr`, mais jamais l'inverse : servir `fr-CA` à qui demande `fr` serait une supposition, pas une négociation.
  Rien ne se détecte tout seul. `trans()` ne change pas de comportement, et les fonctions prennent des valeurs simples, jamais une requête HTTP, ce qui les rend testables sans monter de serveur.

- **`forge-mvc-files` tient un registre de ce qu'il écrit (`FILES-METADATA-TABLE-001`, ADR-094).**
  Le paquet écrivait des fichiers sans en garder trace, l'ADR-020 ayant exclu tout état de son périmètre. Une conséquence n'avait pas été mesurée : sans registre, aucun quota n'est calculable, aucun orphelin repérable, et le nom d'origine ne survit pas au mode UUID, qui l'efface du chemin par sécurité.
  L'état existait pourtant déjà, dans la table `media` de `forge-mvc-images`, où rien n'est propre à l'image : un projet ne stockant que des PDF aurait dû installer Pillow pour disposer d'une table.
  La table `forge_files` porte ce que le **stockage** sait, jamais une notion métier. Le rôle, la position et le texte alternatif restent à `media`, où une galerie en a besoin. Le propriétaire est un couple libre, une nature et un identifiant, que l'application remplit comme elle l'entend.
  L'inscription est **explicite** : écrire un fichier n'inscrit rien de soi même, et un test le vérifie sur la source de `save_upload`. Le paquet reste utilisable sans base pour qui ne veut que des primitives.
  `forge files:init` écrit la migration. Le registre est exercé contre les serveurs réels, création, quota, agrégation et contrainte d'unicité comprises.
  L'ADR-094 amende l'ADR-020 sur ce seul point, tout le reste de son hors périmètre tenant.

- **L'ajout de colonne était refusé par SQL Server (`SESSIONS-DELETE-FOR-USER-001`, suite).**
  `render_add_column` écrivait `ALTER TABLE t ADD COLUMN`, forme correcte sur trois backends et **erreur de syntaxe sur SQL Server**, qui n'accepte pas le mot-clé. La clause vient désormais du contrat `Dialect`, via `add_column_clause`.
  Le rendu était vérifié par comparaison de chaînes, ce qui ne montre jamais qu'une instruction bien formée est refusée par le serveur. `tests/db/test_add_column_migration_real_server_001.py` joue le scénario réel sur les trois serveurs : table créée sans la colonne, ligne écrite, migration appliquée, ligne d'avant préservée.
  Les trois tests d'intégration des migrations de session nommaient par ailleurs **tous** les index d'une table pareillement, ce qui passait tant qu'elle n'en portait qu'un. MariaDB a refusé le doublon ; PostgreSQL et SQL Server l'ignoraient en silence par leur `IF NOT EXISTS`, et y passaient en ne créant qu'un index sur deux.

- **Le pré-vol refuse un secret laissé à sa valeur d'amorçage (`DEPLOY-CHECK-SECRETS-001`).**
  `deploy:check` vérifiait `DB_HOST`, `DB_NAME` et `DB_APP_LOGIN`, jamais les mots de passe ni les jetons. Un `DB_APP_PWD=change-me` recopié d'un exemple passait donc le contrôle, et la panne n'apparaissait qu'au premier accès à la base, en production, alors que le pré-vol existe précisément pour l'éviter.
  Le repérage porte sur le **nom** de la variable et non sur une liste figée : un nom contenant `PASSWORD`, `PWD`, `SECRET` ou `TOKEN` porte un secret, et un opt-in ajouté demain est couvert sans que le pré-vol change. Les noms de chemin et de drapeau sont écartés, `SSL_KEYFILE` en tête, un contrôle qui crie à tort finissant désactivé.
  Seul le nom de la variable fautive apparaît au rapport, jamais sa valeur : un rapport se colle dans un ticket, où un secret réel fuirait.
  Forge refuse l'évidence, jamais la faiblesse. Mesurer l'entropie d'une chaîne demanderait des règles arbitraires que Forge n'impose pas.
  La liste des valeurs d'amorçage était privée dans `forge-mvc-mfa`, et un opt-in ne peut pas dépendre d'un autre : elle vit désormais dans `core.security.secrets`, avec le repérage des noms sensibles.

- **La table de mesures IoT peut être bornée (`IOT-RETENTION-GC-001`).**
  `iot_events` reçoit une ligne par mesure publiée et rien ne la bornait. Un capteur qui émet toutes les dix secondes y dépose plus de trois millions de lignes par an, et un site en compte rarement un seul : la table grossissait jusqu'à la panne de remplissage, alors que `sessions:gc`, `audit:gc` et `stats:gc` avaient posé le précédent.
  `forge iot:gc --days N` affiche les lignes visées et n'efface qu'avec `--run`. La rétention doit être dite, aucune valeur par défaut n'étant supposée à la place de l'exploitant.
  La commande s'appelle `iot:gc` et non `iot:purge` : trois opt-ins nommaient déjà ce geste ainsi, avec la même option `--days`, et une quatrième forme aurait donné deux façons de dire la même chose (principe 11).
  La purge est indexée, `idx_iot_events_received_at` portant déjà sur la colonne filtrée. Aucune migration n'est requise.

- **Le calcul de la borne de rétention est partagé (`IOT-RETENTION-GC-001`).**
  Il était écrit deux fois à l'identique, dans `forge-mvc-audit` et `forge-mvc-stats`, et le troisième opt-in allait en produire une copie de plus. `core.database.retention` le porte désormais seul, et les deux paquets l'enveloppent pour garder leur type d'erreur public.
  Il emploie `utc_now()`, ce qui a rendu leurs deux exemptions au garde-fou des horodatages conscients sans objet. Elles ont disparu avec leur cause.

- **Activer un second facteur ferme les sessions ouvertes (`MFA-SESSION-INVALIDATION-001`).**
  Activer le MFA ne protégeait rien tant que les sessions ouvertes avant l'activation restaient valides : un accès obtenu avec le seul mot de passe survivait au renforcement.
  `delete_for_user` accepte `except_session_id`, qui épargne la session depuis laquelle le geste est fait. Sans lui, l'utilisateur qui vient d'activer son facteur serait déconnecté par son propre geste, ce qui ne protège de rien.
  L'opt-in ne ferme aucune session lui-même. `confirm_totp_factor` est une fonction pure, et un opt-in qui fermerait des sessions à l'insu de l'appelant serait de la magie cachée (principe 3). La référence de l'opt-in donne le geste à copier, et un test exerce ce code exact pour que la documentation ne puisse pas décrire un parcours qui ne marche pas.

- **Le cœur sait révoquer toutes les sessions d'un compte (`SESSIONS-DELETE-FOR-USER-001`).**
  Le contrat `SessionStore` n'avait que `delete(session_id)`. Rien ne permettait de fermer les sessions déjà ouvertes d'un utilisateur, alors que trois événements l'exigent : l'activation d'un second facteur, le changement de mot de passe et la déconnexion à distance.
  Une session ouverte leur survivait, donc un accès obtenu avant l'événement restait valide après.
  `delete_for_user(user_id)` rejoint le contrat et les trois stores livrés. Les stores mémoire et fichier balaient, leur volume étant borné par une seule instance ; `DbSessionStore` interroge une colonne `user_id` indexée, sa table pouvant être grande et partagée entre processus.
  L'identité comparée est celle que `login_user` pose. Une session anonyme n'est jamais touchée, et `None` ne révoque rien plutôt que de tout révoquer.

- **Un opt-in peut faire évoluer son schéma (`SESSIONS-DELETE-FOR-USER-001`).**
  Le mécanisme de migration des opt-ins (ADR-071) ne savait rendre que des `CREATE TABLE`, si bien qu'aucun opt-in ne pouvait ajouter une colonne sans casser les projets déjà provisionnés, dont la migration de création ne se rejoue pas.
  `AddColumn` et `render_add_column` rejoignent `core.database.table_ddl`, et `MIGRATIONS` accepte les deux formes. La composition d'une colonne est factorisée, si bien qu'un `ALTER` décrit une colonne exactement comme un `CREATE`.
  Une colonne `NOT NULL` sans défaut est refusée au rendu, les lignes existantes ne pouvant pas la satisfaire. Les index de la colonne ajoutée sont toujours rendus séparément, y compris sur les dialectes qui les inlinent dans un `CREATE TABLE`.
  Rendu vérifié sur les quatre backends. Débloque au moins trois autres tickets rc8 qui ajoutent une colonne à une table existante.

### Rupture

- **`SessionStore` gagne une méthode (`SESSIONS-DELETE-FOR-USER-001`).**
  Le contrat est `@runtime_checkable` : un store auquel il manque `delete_for_user` n'est plus reconnu par `isinstance`, et `forge.configure` le refuse.
  Un store tiers écrit avant ce ticket doit l'implémenter pour rester accepté. C'est délibéré, un store qui ne sait pas révoquer ne remplissant pas le contrat de sécurité attendu (principe 10).
  La clé d'identité de session, jusqu'ici dupliquée en dur dans `core/security/session.py`, vit désormais dans `core.sessions.keys`. `core.auth.session.AUTH_USER_ID_SESSION_KEY` en reste l'alias public.


- **La clé de chiffrement MFA peut tourner sans fermer les comptes (`MFA-KEY-ROTATION-001`).**
  `FORGE_MFA_SECRET_KEY` n'avait aucune procédure de rotation : la changer rendait tous les secrets TOTP illisibles au même instant, si bien que chaque porteur d'un facteur perdait son second facteur d'un coup.
  La seule issue était de désactiver le MFA de tout le monde, ce qui transforme une mesure d'hygiène en panne d'authentification.
  `FORGE_MFA_SECRET_KEY_PREVIOUS` déclare les clés retirées, séparées par des virgules, acceptées **au déchiffrement seulement**. Le chiffrement utilise toujours la clé courante, et plusieurs rotations rapprochées restent lisibles.
  `rotate_totp_secret` rechiffre un secret et `uses_current_key` dit ce qu'il reste à traiter, ce qui permet de balayer une table sans tout réécrire. Le rechiffrement passe par `MultiFernet.rotate`, de jeton à jeton : le secret en clair ne transite ni ne se journalise.
  Forge ne balaie pas la base lui-même, la table des facteurs appartenant à l'application dont il ne connaît ni le nom ni les colonnes (principe 1). Il fournit la primitive, l'application décide où elle s'applique.
  Les clés retirées sont validées comme la clé courante, placeholders refusés, et aucun message ne révèle leur valeur. Sans la variable, le comportement est inchangé.

### Corrigé

- **La casse de `APP_ENV` désarmait deux gardes de sécurité (`ENV-APP-ENV-NORMALISATION-001`).**
  Trois normalisations coexistaient pour la même variable : aucune, `.lower()` seul, et `.strip().lower()`.
  Avec `APP_ENV=Prod`, une comparaison brute à `"prod"` est fausse, si bien que deux gardes cessaient de se déclencher sans rien dire.
  L'API IoT s'enregistrait **sans jeton** en production, ce que `SEC-IOT-TOKEN-PROD-001` interdit, et `fixtures:load --run` acceptait de peupler la base de production sans `--force`, ce que l'ADR-074 interdit.
  Les tests de ces deux gardes existaient et passaient : ils n'exerçaient que l'écriture `"prod"` en minuscules. Douze tests de comportement échouent sur le code d'avant et passent sur celui d'après.
  `core.app.env` devient la seule lecture officielle, avec `normalize_app_env`, `read_app_env` et `is_prod`. Le module ne dépend que de la bibliothèque standard, pour rester importable au tout début du démarrage, y compris par la configuration du squelette.
  Le cœur tolère désormais la variante quand le pré-vol `deploy:check`, lui, continue d'exiger la forme canonique : le premier ne doit jamais rater une production, le second impose une écriture unique. Ce partage de rôles est documenté plutôt que subi.
  Le garde-fou `test_app_env_normalisation_001` refuse toute nouvelle lecture brute et toute comparaison non normalisée. Il travaille sur l'arbre syntaxique, parce qu'un `grep` sur « prod » remonte « produire » : c'est ce faux positif qui avait fait conclure à tort que `forge-mvc-fixtures` n'avait aucune garde.

### Documentation

- **Le back-office était décrit comme un paquet vide (`ADMIN-DOC-ETAT-REEL-001`).**
  Le README, le docstring du paquet et le bandeau de la roadmap annonçaient tous les trois qu'aucun code n'existait, alors que `forge-mvc-admin` porte 1259 lignes et un back-office fonctionnel, et que la section 9 de cette même roadmap marquait ses dix-sept tickets « livré ».
  Une affirmation de sécurité était de plus inversée : l'intégration RBAC y était décrite comme `fail-open` quand le code refuse l'accès si une permission est déclarée sans que `forge-mvc-rbac` soit installé.

- **Le cycle rc8 des opt-ins est cadré (`ROADMAP-RC8-OPTINS-001`).**
  Quatre-vingt-cinq tickets en six lots, dont l'ordre est une contrainte de dépendance.
  Quinze améliorations demandées lors de la revue étaient déjà livrées, et sont consignées pour que la prochaine revue ne les redemande pas.



## [1.0.0-rc.7] - 2026-08-17

Vingt et un tickets livrés après le tag `v1.0.0-rc.6`, en deux temps.

Le premier a vérifié la documentation en l'exécutant, plutôt qu'en la relisant.
Le second a cherché les écarts entre ce que Forge annonce et ce qu'il fait, et c'est là que presque tout s'est trouvé.

Un seul défaut de comportement dans le lot, sur les privilèges PostgreSQL.
Les autres étaient des garanties creuses, des contrats rompus ou des promesses que le code ne tenait plus, ce qui est cohérent avec un dépôt qui vient de passer un pré-mortem complet : ce qui reste se cache moins dans le code que dans ce qu'on croit savoir de lui.

Deux ajouts d'API publique en découlent, à prendre en compte pour la prochaine publication.

### Ajouté

- **Un droit refusé par le serveur est reconnu et expliqué (`FIXTURES-PG-FK-PRIVILEGE-001`).**
  `fixtures:load --no-fk-checks` et `fixtures:purge` encadrent leur travail par le levier de contraintes du dialecte.
  Sur PostgreSQL ce levier est `SET session_replication_role`, qui **exige un rôle superutilisateur**, alors que l'ADR-033 fait tourner l'applicatif en compte DML strict.
  Dans la configuration que Forge recommande, l'option était donc refusée par le serveur, et les deux commandes échouaient sans qualifier la cause, en rendant le message brut du moteur, traduit selon sa langue.
  Ni l'ADR-077 ni la référence de l'opt-in ne mentionnaient ce prérequis, que le commentaire du dialecte connaissait pourtant.
  `is_insufficient_privilege_error` rejoint les trois prédicats du contrat de backend, implémenté sur les quatre. Signaux mesurés contre les serveurs avec un compte privé de droits : MariaDB errno 1044, 1142 et 1227, PostgreSQL SQLSTATE 42501, SQL Server numéros natifs 229 et 262, SQLite toujours faux faute de système de droits.
  Le SQLSTATE ne discrimine ni sur MariaDB ni sur SQL Server, tous deux rendant `42000` pour un refus comme pour une faute de syntaxe. L'errno 1045 est volontairement exclu, décrivant un refus de connexion et non un droit manquant sur une opération.
  Le test se connecte avec un rôle ordinaire, jamais en `postgres` : la fixture `real_pg_db` est superutilisateur, et un test écrit dessus serait passé sans rien prouver. C'est ce qui a laissé vivre le défaut.

- **Les attributs d'un pivot se déclarent par l'outillage (`ENTITIES-PIVOT-FIELDS-001`).**
  `make:relation` écrivait toujours `pivot.fields: []` et ne posait jamais la question, **ni en dialogue ni en ligne de commande**, alors que `make:pivot-crud` exige `pivot.fields[]` non vide.
  La commande était donc inatteignable par le seul outillage : la seule voie était d'éditer `mvc/entities/relations.json` à la main, ce que la documentation disait franchement.
  C'était le seul endroit où Forge demandait d'écrire un contrat JSON à la main, et aucun agent ne pouvait modéliser un pivot enrichi alors que Forge écrit lui-même leur guidance (ADR-047).
  L'option `--pivot-field` est répétable et le dialogue pose la même question, un attribut par ligne. Les deux modes reçoivent la capacité ensemble : n'ouvrir que la ligne de commande aurait créé l'asymétrie inverse de celle qu'`ENTITIES-NON-INTERACTIVE-002` a corrigée.
  La grammaire n'est pas inventée, c'est celle de `make:entity --field`, et le parseur est le même. Deux des quatorze types d'entité sont écartés, la clé étrangère étant déjà portée par `from_key` et `to_key`, et un slug désignant une ressource et non un lien.

### Corrigé

- **Le mail refusait deux séparateurs de ligne sur dix (`MAIL-SEPARATEURS-LIGNE-001`).**
  Le contrôle anti-injection d'en-têtes ne cherchait que `[\r\n]`, alors que Python coupe une ligne sur huit autres caractères, dont la tabulation verticale, la nouvelle ligne NEL et les deux séparateurs Unicode.
  Il n'y avait pas de faille, la bibliothèque standard refusant ces valeurs, donc aucune en-tête forgée ne partait. Le défaut est un **contrat rompu** : l'appelant recevait un `ValueError` au lieu du `MailValidationError` annoncé, donc une erreur cinq cents là où il avait prévu un refus de formulaire.
  Le contrôle suit désormais `str.splitlines()`, la définition que la bibliothèque standard applique elle-même, plutôt qu'une liste tenue à la main qui dériverait au premier élargissement de Python.
  La comparaison ne peut pas être « plus d'une ligne » : un séparateur **final** n'en crée pas de seconde, si bien qu'une valeur terminée par un saut passait. C'est le piège de l'ancrage `$` d'une expression rationnelle.

- **Le vingt-septième parcours d'accueil n'allait pas au bout (`WELCOME-ENTITIES-EXECUTION-001`).**
  Joué dans un projet neuf, le parcours du moteur d'entités révèle trois manques, aucun visible à la lecture : chaque commande était juste prise isolément, le manque n'existant qu'entre elles.
  `make:entity` exige un backend BDD, cité seulement au troisième chapitre alors que le besoin est à la première commande.
  Surtout, le parcours ne disait **jamais** d'appliquer le SQL à la base. Mesuré : après tout le parcours, la base ne contenait que `forge_migrations`, ni `article`, ni `tag`, ni la table pivot. Le parcours engendrait des écrans CRUD sur des tables inexistantes et enseignait les migrations sur une base vide.
  Ce dernier manque n'est apparu que par la vérification des **routes**, tous les blocs de commandes passant : sans elle, le parcours aurait été déclaré bon.
  Les vingt-sept parcours sur vingt-sept vont désormais au bout.

- **Deux promesses fausses du tutoriel et neuf signatures d'API périmées (`GUIDE-PRISE-EN-MAIN-EXEC-001`, `DOC-SIGNATURES-REELLES-001`).**
  Trouvées en jouant le tutoriel et en confrontant au code les deux cent cinquante-quatre signatures publiées, plutôt qu'en les relisant.
  Le renommage `--email` vers `--login` avait été appliqué aux exemples, mais ni aux tableaux ni au diagramme de classe.

- **Le prérequis d'installation était inactionnable, et deux parcours ne mettaient rien en base (`WELCOME-PREREQUIS-ACTIONNABLE-001`, `WELCOME-HARNAIS-LIGNE-A-LIGNE-001`, `WELCOME-PARCOURS-COMPLETS-001`).**
  Vingt-six parcours sur vingt-sept menés jusqu'au bout, contre seize au départ.

### Tests

- **Les tests du DDL du socle validaient une copie figée (`AUTH-DDL-TESTS-SOURCE-001`).**
  Le SQL du socle Auth existe en trois copies : la spec déclarative rendue par dialecte, la constante canonique, et la fixture du projet d'exemple. Les deux premières étaient verrouillées par une parité stricte ; la troisième ne l'était qu'à moitié, deux tables sur quatre portant une parité locale.
  `users.sql`, qui n'en avait pas, était restée à l'état d'avant l'ADR-089, où `email` portait l'identité, et d'avant l'ADR-091, qui a retiré `last_login_at`.
  Neuf assertions affirmaient le contrat de la table en lisant cette copie, dont deux affirmaient l'inverse de la règle en vigueur, en restant vertes.
  Aucun défaut de comportement : la fixture n'est jamais appliquée à une base, vérifié par relevé. Le défaut était une garantie creuse.
  Un garde-fou dérivé du système de fichiers tient désormais la parité pour tous les fichiers du dossier, et fait échouer sur un fichier qu'il ne sait ni résoudre ni justifier plutôt que de le sauter en silence.

- **`fixtures:load` et `fixtures:purge` n'étaient exercés que sur MariaDB (`FIXTURES-LOAD-PURGE-TROIS-SERVEURS-001`).**
  Ce sont les deux commandes principales de l'opt-in, et la cause tenait en une ligne : leur table de test était créée par une DDL écrite en dur dans ce dialecte.
  Mesuré par collecte et non d'après les marqueurs, qui trompent : `real_backend_db` porte les siens sur ses paramètres, si bien qu'un marqueur de module s'y ajoute sans restreindre.
  Aucun défaut trouvé, les trois moteurs se comportant identiquement, apostrophe comprise. C'est un résultat en soi, et les docstrings le disent.

### Intégration continue

- **Le SAST est ramené à zéro signalement et devient bloquant (`CI-BANDIT-PERIMETRE-001`).**
  Bandit rendait cent signalements sans qu'aucun n'arrête rien : il était la seule des quatre portes du job en `continue-on-error` **sans** entrée dans le garde final, si bien qu'il sortait en échec à chaque exécution et que son annotation se lisait comme du bruit.
  Mesuré sur les cent, aucun défaut réel. Quatre-vingt-huit relevaient d'une décision d'architecture, le SQL construit par chaîne étant un choix assumé du principe 5, sept venaient de fichiers de test, quatre de comparaisons ou de valeurs par défaut, et un était un faux positif vérifié.
  Le plus parlant des quatre visait la liste des hôtes **refusés** : le scanner signalait comme risque le code qui l'interdit.
  `bandit.yaml` écarte la seule règle structurelle et écrit ce que cela coûte plutôt que de le taire. Les cinq derniers signalements sont annotés à leur site avec leur raison, jamais exclus globalement, pour qu'un vrai bind public ou un `Markup` non échappé reste attrapé.
  C'est le zéro qui rend le prochain signalement utile, et c'est lui qui justifie que la porte devienne bloquante.

- **La CI ignorait le Node épinglé du projet (`CI-NODE-NVMRC-001`).**
  Le fichier `.nvmrc` fixe la version, mais le workflow ne la lisait pas.

- **La couche base n'était éprouvée que sur une version de Python (`CI-DB-PYTHON-VERSION-001`).**
  Forge déclare supporter 3.12, 3.13 et 3.14, et les vingt-sept paquets le déclarent aussi, vérifié sans écart. Mais les 457 tests d'intégration ne s'exécutaient que sur 3.13, choix qui n'était expliqué nulle part.
  Or c'est la couche qui repose sur des extensions C, `mariadb`, `psycopg` et `pyodbc`. Le job matriciel prouve qu'elles **s'installent** sur 3.14 ; seuls les jobs base prouvent qu'elles **fonctionnent** contre un serveur.
  Les trois jobs passent en 3.14, à coût constant, et les trois pilotes tiennent. Le compromis d'une seule version reste assumé, mais il est désormais écrit.

- **Les actions GitHub tournaient sur un runtime Node déprécié (`CI-ACTIONS-NODE24-001`).**
  Chaque exécution posait une annotation, six par run. Ce n'est pas le Node du projet, en 24.17.0 depuis `CI-NODE-NVMRC-001`, mais le moteur interne que chaque action déclare dans son propre `action.yml`, sur lequel Forge n'a de prise qu'en montant de version majeure.
  Dix-sept montées, ruptures vérifiées **avant** de monter et non après : le cache automatique de `setup-node@v5` ne s'applique pas, `package.json` ne portant pas de champ `packageManager`, et le blocage des forks de `checkout@v7` ne concerne aucun des quatre workflows, qui n'emploient ni `pull_request_target` ni `workflow_run`.
  Mesure après fusion : six annotations avant, zéro après.

### Outillage de release

- **Le script de validation rendait trois échecs sur un dépôt sain (`RELEASE-VALIDATE-FAUX-POSITIFS-001`).**
  Deux venaient de lui. `pytest` ne démarrait pas, et le script le rapportait comme un échec des **tests** : `pytest.ini` impose `--dist loadfile`, donc pytest-xdist est obligatoire, et le garde-fou d'interpréteur vérifiait `pytest`, `mkdocs` et `ruff` par un import. Importer pytest ne prouve pas qu'il démarre. La suite n'avait jamais tourné alors que le rapport annonçait un échec.
  Le contrôle lance désormais une collecte réelle, qui lit la configuration et vaut donc pour tout plugin exigé par les addopts, plutôt qu'une liste d'imports qui dériverait au premier changement.
  L'autre était une incohérence : `--ignore-vuln` figurait sur deux relevés et manquait au troisième, si bien que le même avis accepté ailleurs bloquait sur `requirements-dev.txt`.

- **Un commentaire cassait un garde-fou (`RELEASE-VALIDATE-IGNORE-VULN-REGEX-001`).**
  Le relevé des exclusions capturait l'identifiant **avec** la ponctuation qui le suit : une mention entre apostrophes inverses, dans un commentaire, rendait un identifiant inconnu du veilleur et faisait échouer les trois matrices.
  Le garde est rendu insensible à la mise en forme sans rien perdre de sa portée, vérifié par contrôle négatif dans les deux cas, en commande comme en commentaire.

- **Le script donnait un feu vert sur une suite amputée (`RELEASE-VALIDATE-SKIPS-SILENCIEUX-001`).**
  Un test d'intégration qui ne trouve pas son serveur se **saute**, il n'échoue pas. Le dépôt porte 438 tests marqués `db`, `db_pg` ou `db_mssql` : sans les `FORGE_REQUIRE_*`, ils disparaissent de la suite sans que le vert n'en souffre.
  Mesuré sur une validation réelle : **152 tests sautés**, verdict « prêt à releaser » inchangé. C'est le piège du pré-mortem rc3, où l'arrêt d'un serveur avait fait ignorer des milliers de tests sans que rien ne le montre.
  Ces variables ne changent pas ce qui est exécuté, mais ce qui se passe quand la connexion échoue, un saut devenant un échec. Le script les exige avant de lancer les tests, `--sans-serveurs` permettant d'assumer la lacune explicitement. Le nombre de sauts est désormais énoncé même quand tout est vert.
  Effet mesuré au passage suivant : de 20804 tests et 152 sauts, à **20973 tests et aucun saut**.

### Documentation

- **Le changelog annonçait comme à venir ce qui était sorti (`RELEASE-CHANGELOG-POST-RC6-001`).**
  Une section « Non publié » subsistait entre rc6 et rc5, alors que ses quinze tickets étaient tous dans le tag rc6, vérifiés un par un. Elle avait été ouverte pendant le cycle, la release en ayant créé une seconde au-dessus sans refermer celle-ci.
  La roadmap annonçait de son côté la rc5 comme dernière version publiée sur PyPI, alors que la rc6 l'était depuis trois jours.


## [1.0.0-rc.6] - 2026-08-14

Cycle de pré-mortem du cœur et des opt-ins, demandé avant de passer à la rc6.
Vingt-quatre tickets, dont **quinze défauts de comportement** qu'une suite de 17 000 tests verts ne montrait pas.

Trois motifs expliquent presque tout, et ils reviennent d'un bout à l'autre du cycle.

**Un test vérifie la construction, jamais l'effet.** Une requête est comparée à une chaîne attendue, sans être soumise à un moteur ; un script de provisionnement est comparé à un texte, sans être exécuté. La chaîne peut être exactement celle qu'on voulait écrire et rester refusée par le serveur.

**La documentation affirme ce que le code ne fait plus, ou pas partout.** Huit occurrences, dont deux avec une conséquence de sécurité : un exploitant se croyait protégé par une en-tête que son déploiement n'émettait pas.

**Deux jumeaux, un seul exercé.** Le serveur de développement et l'adaptateur WSGI, MariaDB et les trois autres backends. Cinq divergences trouvées, dont une qui rendait une fonctionnalité documentée pour la production **silencieusement inerte** une fois déployée.

### Corrigé

- **Le moteur datait en heure locale sur deux backends (`DIALECT-UTC-DEFAULT-001`).**
  Neuf colonnes réparties dans sept opt-ins laissent le moteur poser leur horodatage. MariaDB et PostgreSQL rendaient l'heure **locale** du serveur, SQLite et SQL Server de l'UTC.
  SQL Server employait déjà `SYSUTCDATETIME()` : l'intention était l'UTC dès l'origine, les deux autres n'avaient jamais été convertis. Une même base portait donc deux référentiels selon le backend.
  Un test existant a rattrapé une régression introduite par ce correctif : `now_expression()` et la clause `DEFAULT` doivent porter la même horloge, sans quoi `forge-mvc-jobs` aurait pris ses travaux deux heures trop tôt.
  Au passage, `settings.updated_at` annonçait la date de **création** sur PostgreSQL et SQL Server, faute d'`ON UPDATE` déclaratif, et un commentaire affirmait que le store écrivait la colonne. Il ne l'écrivait pas ; il le fait désormais.

- **Les nombres négatifs étaient corrompus à l'export CSV (`CSV-NOMBRE-NEGATIF-001`).**
  La protection contre l'injection de formule préfixait d'une apostrophe toute cellule commençant par `=`, `+`, `-` ou `@`. Tout nombre négatif en faisait partie : `-12` sortait `'-12`.
  Dans le tableur, la colonne des montants passait en texte et les sommes cessaient silencieusement de compter les valeurs négatives. Au réimport, la valeur ne se convertissait plus. L'aller-retour exporter, corriger, réimporter est pourtant la raison d'être du module.
  Un nombre ne peut pas être une formule : l'exemption ne retire aucune protection, `-1+1` et `+1+cmd` restant échappés.

- **Une vidéo d'une seconde était rejetée en entier (`VIDEO-AFFICHE-COURTE-001`).**
  L'affiche était prise à une seconde sans regarder la durée. La recherche tombait après la dernière image, ffmpeg échouait, et le pipeline marquait la vidéo entière en échec alors que le transcodage aurait réussi.
  Trouvé en exécutant vraiment `ffmpeg`, que rien n'exerçait : la commande était construite et comparée à une chaîne, jamais lancée, et le parseur de `ffprobe` était nourri d'un JSON écrit à la main.

- **L'aide de trois commandes était masquée (`OPTIN-NATIVE-HELP-001`).**
  `make:entity`, `make:relation` et `migration:make` répondaient « cette commande n'expose pas d'aide détaillée » alors qu'elles en portent une. L'interception d'aide des opt-ins passait devant celles qui traitent `-h` elles-mêmes.
  Le garde-fou censé protéger cette aide était **creux** : il vérifiait l'absence d'un marqueur, que le message de repli satisfaisait aussi. Il passait donc sur l'état exact qu'il devait empêcher.


- **Le nonce CSP n'existait que sur le serveur de développement (`CORE-WSGI-CSP-NONCE-001`).**
  `APP_CSP_NONCE_ENABLED` est documenté comme un réglage de production, avec le helper `csp_nonce()` à poser dans les gabarits. L'adaptateur WSGI n'établissait aucun nonce et servait `script-src 'self'` : le script inline d'un gabarit était **silencieusement bloqué** en production. Pas d'erreur, pas de page cassée, la fonctionnalité ne marchait simplement pas.
  Les tests E2E du nonce existaient et passaient : ils lancent le serveur de développement. C'est la démonstration la plus nette qu'un test passant par le jumeau ne prouve rien sur la production.

- **Le chemin d'erreur 500 pouvait laisser échapper son exception (`CORE-WSGI-ERROR-PATH-001`).**
  Six défauts sur le code qui ne tourne que lorsque tout le reste a déjà échoué, et qu'aucun appel WSGI réel n'exerçait. Un gabarit `errors/500.html` cassé, un journal inécrivable ou un contexte de dev défaillant faisaient ressortir l'exception du callable : le serveur répondait à la place de Forge, sans les en-têtes de sécurité, et **la cause première était perdue** — l'exploitant lisait l'erreur du gabarit d'erreur.
  Le journal consignait par ailleurs la chaîne de requête en clair, là où voyagent les jetons de réinitialisation. Elle suit désormais la règle du POST : les noms restent, les valeurs sont masquées.

- **Le code HTTP des pages d'erreur n'était pas garanti (`CORE-WSGI-CSRF-POST-001`, `TWIN-ERROR-PAGE-PARITY-001`).**
  Les gabarits `errors/*.html` appartiennent à l'utilisateur : un projet peut les casser, ou ne pas les avoir. Un gabarit **absent** faisait rendre un 500 à la place du code voulu, si bien qu'une page manquante se présentait comme une panne. Un gabarit **cassé** faisait de même pour un refus CSRF.
  `error_page` devient la seule façon officielle de rendre une page d'erreur, sur les vingt-trois sites du cœur **et des deux serveurs de développement** : le premier correctif n'avait réparé qu'un jumeau.

- **Deux opt-ins écrivaient des horodatages conscients du fuseau (`OPTIN-AWARE-TIMESTAMP-001`, `OPTIN-TIMESTAMP-WIDEN-001`).**
  Mesuré sur serveurs réels : 7200 s d'écart sur PostgreSQL, zéro sur MariaDB et SQL Server. Deux moteurs sur trois ne montrent rien, ce qui explique la durée de vie du défaut. Un événement IoT reçu à midi UTC était daté de 14 h dans une base où tout le reste est en UTC.
  Trois tests exigeaient explicitement la forme fautive : ils épinglaient le défaut plutôt que la règle.

- **« Table absente » n'était qualifiée que sur MariaDB (`IOT-DOCTOR-MISSING-TABLE-001`).**
  Un exploitant PostgreSQL ou SQL Server qui oubliait sa migration recevait un échec annonçant une base injoignable, avec un message parlant de MariaDB. `is_undefined_table_error` rejoint `is_unique_violation` sur le contrat de backend, implémenté sur les quatre.
  Piège consigné : **le message de PostgreSQL est traduit**. Une détection par le texte dépendrait de la langue du serveur, ce qui n'est pas une propriété du programme.

- **`current_user` se taisait sur un loader incomplet (`CORE-WSGI-AUTH-GATE-001`).**
  Deux branches de refus voisines, une seule journalisée. Un `load_user_by_id` omettant `password_hash` produisait une boucle de redirection vers `/login` que rien n'expliquait, sur un compte existant et une session valide.

### Ajouté

- **Drapeau de route `no_store` (`NO-STORE-ROUTE-FLAG-001`).**
  `Cache-Control: no-store` vivait dans une liste de chemins codée en dur du serveur de développement, que l'adaptateur WSGI ne connaissait pas : la production servait la page de connexion sans l'en-tête.
  Le cœur ne pouvait pas déduire la règle, `/login` étant une route publique. Elle est donc déclarée, et honorée par `Application.dispatch`, donc par les deux serveurs. `forge make:auth` pose le drapeau sur les routes qu'il engendre, et une application marque ses propres pages sensibles de la même façon.

### Documentation

- **HSTS n'est pas émis par les deux serveurs de la même façon (`HSTS-TWIN-DIVERGENCE-001`).**
  Le serveur de développement le pose toujours, l'adaptateur WSGI seulement en HTTPS. Le choix est délibéré et le guide de déploiement confie l'en-tête au proxy inverse, mais deux pages l'annonçaient « sur toutes les réponses » sans réserve : un exploitant croyait disposer d'une protection que son déploiement n'avait pas.

- **`Cache-Control: no-store` n'existe que côté développement (`NO-STORE-TWIN-DIVERGENCE-001`).**
  Trois pages en disaient trois choses différentes. Le code n'est **pas** corrigé, délibérément : `/login` est une route publique, donc indiscernable par le contrat de route, et fermer l'écart demande une décision d'API.

- **La documentation d'authentification suit le contrat login/email (`AUTH-DOC-LOGIN-CONTRACT-001`).**
  Trente passages promettaient `--email` là où la CLI attend `--login` depuis l'ADR-089, y compris des messages d'erreur que la CLI n'émet plus.

### Tests

- **Les surfaces SQL jamais soumises à un moteur sont exercées** (`OPTIN-SQL-SURFACE-EXEC-001`, `DB-INIT-PROVISION-REAL-001`, `DB-INIT-PROVISION-MSSQL-001`, `CORE-WSGI-AUTH-GATE-001`).
  `forge db:init` est la première commande d'un projet : son script est désormais **exécuté** par `psql` et par le pilote SQL Server, sur de vrais rôles et de vraies bases. Un script invalide y bloquerait un projet avant qu'il existe, sans rattrapage.
  La protection d'accès est vérifiée par un témoin d'exécution et non par un code de statut : la propriété qui compte n'est pas « le middleware rend une redirection » mais « le contrôleur protégé ne s'exécute pas ».

- **Le QR Code encode vraiment son texte (`QRCODE-ENCODE-REEL-001`).**
  Les contrôles vérifiaient que la sortie ressemble à une image. Mesure par contrôle négatif : un générateur modifié pour ignorer son argument laissait les 47 tests d'origine verts.
  Les pixels du PNG sont désormais relus et comparés à la matrice, ce qui ferme d'un coup l'image blanche, l'image tronquée, l'échelle non appliquée et la marge absente.

- **Les commandes et options montrées par la documentation existent (`DOC-CLI-INVOCATIONS-001`).**
  823 blocs bash, dont 433 invocations de `forge`, dont aucune n'était vérifiée.

- **Un garde-fou ne juge plus la prose (`SOURCE-SCAN-001`).**
  Cinq fois dans ce cycle, un relevé a échoué sur une docstring qui expliquait précisément ce que le code ne fait pas. `code_sans_prose` porte la règle une seule fois, adopté par huit garde-fous.


## [1.0.0-rc.6] - 2026-08-14 (seconde partie du cycle)

Ces entrées ont porté le titre « Non publié » jusqu'au 2026-08-17, alors que leurs quinze tickets sont tous dans le tag `v1.0.0-rc.6`.
Vérifié un par un contre le tag, aucun n'en était absent.
La section avait été ouverte pendant le cycle, puis la release en a créé une seconde au-dessus sans refermer celle-ci : le changelog annonçait donc comme non publié ce qui l'était depuis trois jours.

### Ajouté

- **Le parcours de connexion est éprouvé du WSGI à la base (`AUTH-WSGI-LOGIN-REAL-001`).**
  Trois changements de ce cycle se rencontrent dans ce parcours, et aucun n'était vérifié **ensemble** : l'identité passée de `email` à `login` (ADR-089), l'émission des événements par le cœur (ADR-091), et les horodatages en UTC naïf.
  Le test entre par une requête WSGI, vérifie un mot de passe contre une vraie base, et lit l'événement qui en sort, sur les trois serveurs.
  Il vérifie ce que le cycle a rendu possible : `2TNE1-01` se connecte, sans arobase et avec ses capitales, sur un compte **sans contact**. Et ce que l'ADR-091 promet : trois tentatives, trois événements, l'échec distinguant le compte trouvé du compte inconnu, et aucun ne portant le mot de passe ni la valeur saisie.
  La leçon qui l'a motivé : un jumeau de test ne prouve rien sur ce que sert la production. Une sonde `/health` au contrat de stabilité a déjà répondu 404 sous WSGI alors que tous ses tests passaient.

- **La surface base non exercée des opt-ins est couverte (`OPTIN-SURFACE-COVERAGE-001`).**
  Le pré-mortem a mesuré, opt-in par opt-in, la part réellement **exécutée** contre un serveur : `rbac` 0 sur 15, `admin` 9 sur 15, `images` 3 sur 8.
  C'est cette mesure qui a mené aux deux défauts corrigés plus haut, tous deux invisibles d'une suite verte parce que les tests des paquets exerçaient la **construction** du SQL et jamais son effet.
  Les trous restants sont fermés : lecture, pagination, comptage et suppression du back-office, rattachement, position, texte alternatif et suppression des médias.
  Aucun défaut trouvé sur ces chemins, et c'est un résultat en soi. Le fichier existe pour que cela le reste.

- **La chaîne de permission RBAC est éprouvée sur les trois serveurs (`RBAC-PERMISSION-CHAIN-REAL-001`).**
  `forge-mvc-rbac` porte quinze fonctions touchant la base, et **aucune n'était exercée contre un serveur réel**. C'est l'opt-in qui décide si un utilisateur a le droit de faire quelque chose, et la question « ce SQL rend-il la bonne réponse sur PostgreSQL » n'avait jamais été posée.
  Le relevé est rassurant, et il faut le dire : les trois requêtes rendent le même résultat partout. Elles étaient écrites avec les précautions qui comptent, colonnes en minuscules et alias explicites, là où d'autres paquets ont payé leur absence.
  Le test couvre la chaîne complète, trois jointures et un `DISTINCT`, plus le cas d'un utilisateur sans rôle : un défaut de jointure y rendrait la liste entière des permissions au lieu d'une liste vide, et personne ne le verrait avant l'incident.

- **Forge annonçait trois événements d'authentification et n'en émettait aucun (`AUTH-EVENTS-EMIT-001`, ADR-091).**
  Un retour terrain relève une table `auth_audit_log` vide après des semaines d'usage, et propose que le cœur l'alimente. **La proposition est écartée** : l'ADR-008 a rangé la persistance du côté applicatif, qualifie cette table de latente, et anticipe même la confusion constatée.
  Le défaut réel est ailleurs, et l'ADR-008 ne le couvre pas. Le générateur du contrôleur d'authentification n'appelle **jamais** `safe_log_auth_event` : aucun événement n'est émis, **pas même vers le logger**. Une application configurant consciencieusement un handler sur `forge.auth.audit`, comme l'ADR-008 le lui demande, ne recevait rien. C'est la brique 2 de cet ADR qui manquait, pas la persistance.
  Le cœur émet désormais `login.success`, `login.failed` et `logout`, et c'est `authenticate_user` qui le fait parce qu'il est **le seul à savoir pourquoi une connexion échoue** : l'appelant ne reçoit qu'un `None` et ne peut distinguer un identifiant inconnu, un compte désactivé, un mot de passe faux ou un loader qui a levé. L'échec porte donc la raison, et c'est le cas qui intéresse une enquête.
  Le mot de passe n'entre jamais dans un événement, ni la valeur saisie quand elle a échoué : une faute de frappe sur un mot de passe ressemble trop à un mot de passe. L'émission passe par `safe_log_auth_event`, si bien qu'une table saturée ou un verrou ne peut jamais empêcher quelqu'un d'entrer.
  **`last_login_at` est retirée.** Créée par le cœur et écrite par personne depuis toujours, elle est un horodatage géré dont l'ADR-081 confierait l'autorité à Python, ce qui suppose un écrivain que le cœur n'a pas ; il n'écrit nulle part ailleurs dans `users`. Le journal répond déjà à la même question, avec la raison en prime.
  Un test existant affirmait qu'un échec d'auth normal n'est pas journalisé. Il visait le logger d'**infrastructure**, et cette distinction est rétablie explicitement plutôt que perdue.

- **Un garde-fou documentaire lisait le cache de pytest, et devenait intermittent (`TESTS-DOCS-SCAN-CACHE-001`).**
  `.pytest_cache` manquait à la liste d'exclusions du balayage, où figurent pourtant `.venv`, `site` et `build`.
  En série le cache est écrit une fois puis stable ; sous `-n`, quatre workers le réécrivent pendant que le balayage le lit.
  Le défaut s'est manifesté deux fois sans se reproduire à la demande, et j'ai eu tort de le laisser passer la première fois en le disant « à surveiller » : c'était un défaut explicable, pas un aléa.

- **Un fichier engendré dit par quel contrat il l'a été, et `forge doctor` le compare (`GENERATED-CONTRACT-MARKER-001`, ADR-090).**
  Forge engendre du code puis ne le retouche plus, et c'est le principe 9. La conséquence est qu'un correctif livré dans un générateur **n'atteint aucune application déjà engendrée**, et que son auteur ne l'apprend pas.
  Le cycle en cours le démontre au lieu de le supposer : deux tickets viennent de corriger `make:auth`, dont un qui rouvre la connexion sur SQLite, et la seule application Forge existante porte une copie du contrôleur d'avant.
  L'empreinte porte le **numéro de contrat du générateur**, et c'est la décision qui fait tenir le reste. Pas un condensat du contenu, un fichier engendré étant fait pour être édité, si bien qu'un condensat serait faux dès la première ligne ajoutée et l'avertissement permanent, donc invisible. Pas la version du framework, qui ferait crier à chaque montée et s'apprendrait à être ignorée.
  Un registre par générateur dit ce qui a changé à chaque montée, et signale celles qui touchent la sécurité. Sans lui, l'avertissement dit « en retard » sans dire de quoi, et ne se traduit pas en geste.
  Trois issues, la troisième comptant autant que les autres. Contrat identique : **silence**. Contrat inférieur : le fichier est nommé, la montée décrite, le geste donné. Empreinte absente : le contrôle **dit qu'il ne sait pas**, ce qui est vrai des applications antérieures comme d'un fichier dont l'auteur a effacé l'en-tête, et il n'accuse pas.
  Éprouvé sur le cas réel, un contrôleur extrait de l'historique du dépôt : sans empreinte il obtient un avertissement qui ne l'accuse pas, avec l'empreinte du contrat 1 il obtient un échec nommant le changement de sécurité, regénéré il obtient le silence.
  Neuf autres générateurs restent sans empreinte, **inscrits en dette listée** avec un cliquet, plutôt qu'exclus en silence.
  Forge ne réécrit toujours rien : le contrôle avertit, l'auteur décide.

### Modifié

- **Les défauts SQL d'horodatage sont retirés du socle, seconde moitié (`AUTH-TIMESTAMPS-REMOVE-DEFAULTS-001`, ADR-081).**
  Les sept tables du socle d'authentification portaient `DEFAULT CURRENT_TIMESTAMP`, et quatre `ON UPDATE CURRENT_TIMESTAMP`. Elles étaient les seules de Forge à déléguer leur horodatage au moteur, alors que l'ADR-081 avait **examiné puis refusé** ce mécanisme au motif qu'il introduit une double horloge.
  Le retrait ne vient qu'après que les écritures du framework ont été rendues explicites, et l'ordre était le ticket lui-même : l'inverse aurait rendu `NOT NULL` sans valeur et empêché toute création de compte, partout à la fois.
  Le DDL est désormais `DATETIME NOT NULL`, conforme à ce que Forge impose à toute entité engendrée.
  **La recette documentée de persistance d'audit est corrigée au passage, sur deux points.** Elle ne nommait pas `created_at`, donc s'appuyait sur le défaut retiré. Et elle employait des marqueurs `%s` là où Forge écrit `?` : le cœur traduit `?` vers le format de chaque pilote et **double** tout `%` littéral, si bien que ce code recopié rendait « 0 marqueurs pour 6 paramètres » sur PostgreSQL comme sur SQL Server. C'est le défaut même corrigé dans `forge-mvc-video` ce cycle, présent dans une documentation que l'ADR-008 invite à recopier.
  Sept tests figeaient l'ancienne DDL, dont deux qui **exigeaient explicitement** le défaut, plus quatre fixtures SQL sur disque.
  Le cliquet d'inventaire est vidé, et conservé pour faire échouer un retour du mécanisme.

- **Les horodatages du socle sont posés par Python, première moitié (`AUTH-TIMESTAMPS-EXPLICIT-001`, ADR-081).**
  L'ADR-081 a tranché que l'autorité sur les horodatages est Python, jamais le moteur, après avoir **examiné et refusé** les défauts SQL au motif qu'ils introduisent une double horloge.
  Les entités engendrées suivent cette règle. **Les sept tables du socle d'authentification, non** : elles sont les seules de Forge à s'en écarter, et quatre portent aussi `ON UPDATE CURRENT_TIMESTAMP`. Le relevé initial ne nommait que `users` ; l'inventaire a montré que les sept sont concernées.
  C'est là que la double horloge coûte le plus, `users` étant la seule table que toute application Forge possède.
  **Cette livraison rend les écritures explicites et ne retire aucun défaut**, et l'ordre est le ticket lui-même. Aucune écriture ne nommait ces colonnes, ni la CLI ni les applications : retirer les `DEFAULT` d'abord aurait rendu `NOT NULL` sans valeur et empêché toute création de compte, partout à la fois.
  Le framework ne compte que deux écritures dans ce socle, `INSERT INTO users` et `INSERT INTO user_roles`. Les cinq autres tables n'ont **aucun écrivain** dans Forge, ce qui rend le retrait de leurs défauts dépendant des applications, angle mort que l'ADR-090 vient précisément d'outiller.
  Un cliquet inventorie l'écart restant et échoue dans les deux sens, pour que la seconde livraison ait sa liste et qu'elle ne dérive pas.

  **Aveu de méthode.** Mes premiers tests passaient aussi sur le code d'avant : SQLite remplissait la colonne par son défaut, si bien qu'une assertion « `created_at` non vide » était vraie des deux côtés. Refaits sur une DDL privée de ses défauts, donc conforme à l'ADR-081, et sur la requête elle-même. Le contrôle négatif fait alors tomber quatre tests sur six, là où il n'en faisait tomber aucun.

- **L'identité et le contact sont deux colonnes distinctes (`AUTH-IDENTITY-CONTACT-001`, ADR-089).**
  La table `users` n'avait qu'une colonne d'identité, `email`, et **rien ne vérifiait qu'elle contienne une adresse** : le cœur n'exige qu'une chaîne non vide. Poser son adresse changeait donc son identifiant de connexion, et une application y inscrivait légitimement `2TNE1-01`.
  Le vocabulaire avait produit du comportement, deux fois. Une fonction nommée `_normalize_email` abaissait la casse, fermant la connexion sur SQLite. Et la CLI refusait tout argument sans `@`, si bien que `forge auth:user:show 2TNE1-01` rejetait la saisie au lieu de chercher le compte, alors que le cœur l'acceptait sans réserve.
  `login` porte désormais l'identité : unique, obligatoire, sans contrainte de forme, casse conservée. `email` porte le contact, facultatif et **non unique**, normalisé en minuscules, et `email_verified_at` le suit.
  Un compte sans contact est un compte valide, ce qui est le cas d'un élève mineur, et `PasswordResetRequest.email` vaut alors `None` : l'application sait qu'elle n'a rien à poster, au lieu d'envoyer à un identifiant qui n'est pas une adresse.
  La CLI distingue `--login` et `--email`, et le contrôle de forme suit le contact, où il a un sens.
  `AuthJinjaUser` expose `login` : un gabarit qui affiche « connecté en tant que » désigne la session, pas une adresse que deux comptes peuvent partager.
  **Rupture d'API publique**, assumée et prise avant le tag 1.0.0 précisément pour éviter la migration en trois temps qu'elle imposerait après. Aucune migration : la convention pré-1.0 l'autorise et la seule application existante peut reconstruire sa base.
  Le compteur des deux mois sans changement d'API publique repart. Ce coût est imputable au défaut, non à sa correction : un socle dont le champ d'identité est mal nommé et refuse par la CLI ce que le cœur accepte n'est pas taggable en 1.0.0.

### Corrigé

- **`tables_temporaires` jetait les tables dans le mauvais ordre (`TESTING-DROP-ORDER-FK-001`).**
  Les tables étaient créées parent avant enfant, ce qui est nécessaire, mais **jetées dans le même ordre** : une table référencée par une clé étrangère partait donc avant celle qui la référence. Les trois moteurs le refusent, chacun avec son message, et le démontage échouait sans que le test lui-même ait rien à se reprocher.
  Le défaut ne s'était pas vu parce qu'aucun test n'avait encore employé ce helper avec des tables liées ; il est apparu au premier, celui de la chaîne de permission RBAC.

- **Tout ce que Forge horodate était décalé de deux heures sur PostgreSQL (`TIMESTAMPS-NAIVE-UTC-001`, ADR-081).**
  L'ADR-081 avait tranché que l'autorité sur les horodatages est Python, sans dire sous quelle **forme** la valeur devait être passée. L'omission a coûté deux heures.
  Les colonnes de Forge sont des `DATETIME` sans fuseau. Un `datetime` conscient du fuseau y laisse le pilote décider, et chaque pilote décide autrement. Mesuré sur serveurs réels, serveur en UTC+2 : PostgreSQL convertit vers l'heure locale, soit **7200 secondes d'écart** ; MariaDB et SQL Server n'y touchent pas.
  Le piège est que la forme consciente **paraît plus juste**, puisqu'elle porte l'information de fuseau. Elle l'est en Python, pas au passage du pilote.
  Tous les écrivains de Forge la posaient : le socle d'authentification, le back-office, le dépôt de médias, et le modèle engendré par `make:crud`. Le défaut précède ce cycle pour le dernier.
  `core.database.timestamps.utc_now()` devient la seule façon officielle d'en produire un, et un relevé par analyse syntaxique refuse tout `datetime.now(...)` chez les quatre écrivains.
  L'ADR-081 gagne la section qui lui manquait, avec la mesure.

- **Le CRUD engendré affichait des cellules vides sur PostgreSQL (`CRUD-PG-COLUMN-CASE-001`).**
  PostgreSQL replie tout identifiant non protégé en minuscules : une colonne déclarée `Nom` s'y relit `nom`. MariaDB et SQL Server conservent la casse.
  `make:crud` engendrait `SELECT * FROM contact`, sans alias, et les vues qu'il engendre lisent `{{ contact.Nom }}`, par **nom de colonne**. Sur PostgreSQL, l'attribut n'existait donc pas, et **Jinja ne lève pas sur un attribut absent** : le tableau s'affichait entièrement vide, lignes et boutons présents, contenu manquant, sans une ligne de journal. Les liens `/contact/show/{{ contact.Id }}` pointaient tous vers `/contact/show/`.
  Silencieux, sur un backend que l'ADR-084 donne au niveau plein depuis juillet, et pour toute application dont les colonnes sont en PascalCase.
  La projection est désormais **nommée et aliasée entre guillemets**, forme acceptée par les quatre backends et vérifiée sur serveurs réels. Les vues sont inchangées, et le SQL y gagne en lisibilité (principe 5).

- **L'horodatage des médias venait du moteur, en heure locale (`IMAGES-MEDIA-TIMESTAMP-UTC-001`).**
  `forge-mvc-images` écrivait `CreatedAt` avec `CURRENT_TIMESTAMP`. Sur MariaDB, cette expression rend l'heure **locale du serveur** : un média enregistré à midi UTC était daté de 14 h, dans une base où tout le reste est en UTC.
  C'est aussi la première épreuve de ce paquet contre un serveur réel : il écrivait en base sans qu'aucun test ne l'exerce ailleurs qu'en mémoire.

- **Le back-office ne savait créer aucun enregistrement dans une entité à horodatages gérés (`ADMIN-MANAGED-TIMESTAMPS-001`).**
  L'ADR-081 a retiré les `DEFAULT CURRENT_TIMESTAMP` des tables d'entités : `created_at` et `updated_at` y sont `NOT NULL` **sans défaut**, Python posant la valeur.
  `forge-mvc-admin` ignorait ce mécanisme, sans une seule mention dans tout le paquet.
  Mesuré sur les trois serveurs avant correctif : `Field 'CreatedAt' doesn't have a default value` sur MariaDB, violation de `NOT NULL` sur PostgreSQL, `Cannot insert the value NULL` sur SQL Server. **Créer un enregistrement était impossible** dans toute entité engendrée avec `options.timestamps`, sur les quatre backends.
  La modification, elle, passait sans erreur en laissant `updated_at` figé, ce qui est plus discret et plus durable : l'horodatage mentait alors sur la dernière modification.
  Le défaut date de l'ADR-081, le 13 juillet, et traverse les rc4 et rc5. Aucun test ne l'a vu parce que ceux d'`admin` exercent la **construction** du SQL et jamais son exécution contre une table à horodatages gérés. C'est la forme même des cinq défauts trouvés avant la rc5.
  `AdminResource` gagne un champ `timestamps`, déclaré et non deviné (principe 3), à `False` par défaut : une ressource existante ne change pas de comportement. Déclaré, le back-office pose les deux valeurs à la création et rafraîchit `updated_at` à la modification, sans jamais réécrire `created_at`. Le contrat refuse ces colonnes dans `form_fields`, un champ géré n'étant pas éditable.
  Neuf cas vérifiés sur les trois serveurs, six tombant sur le code d'avant.
  Trouvé par le pré-mortem d'avant rc6, au premier angle.

- **Un compte créé par la CLI ne pouvait pas se connecter sur SQLite (`AUTH-CASE-ASYMMETRY-001`).**
  Forge écrit dans la table `users` par deux chemins, et ils ne suivaient pas la même convention.
  La CLI `forge auth:user:*` abaissait la casse, à l'écriture comme à la lecture : prise seule, elle était cohérente. Le contrôleur et le modèle engendrés par `forge make:auth` ne normalisent rien, ils passent la saisie du formulaire telle quelle à `WHERE email = ?`.
  Sur MariaDB, la collation `utf8mb4_unicode_ci` compare sans égard à la casse et l'écart n'a aucun effet observable. Sur SQLite, où `TEXT` compare en binaire, il **ferme une porte** : un compte créé par `forge auth:user:create`, donc stocké en minuscules, ne peut pas se connecter dès que l'utilisateur tape une majuscule. Dans l'autre sens, un compte créé par l'application est introuvable depuis la CLI.
  Les deux moteurs sont au niveau plein depuis l'ADR-084, et le défaut a été expédié jusqu'à la 1.0.0-rc.5 incluse.
  La normalisation quitte l'identité, qui conserve désormais la casse saisie. Ce n'est pas seulement le correctif le plus court, c'est le seul qui aille dans le sens du contrat : **rien dans Forge ne vérifie que cette colonne contient une adresse**, le cœur n'exigeant qu'une chaîne non vide (`core/auth/user.py`). Une application y met légitimement un identifiant de classe ou un nom de compte, et abaisser la casse d'une identité la déforme. La sensibilité à la casse relève de la collation du moteur, que Forge n'a pas à contredire.
  Le nom `_normalize_email` est retiré au passage : il donnait à croire que cette colonne est une adresse, et c'est cette croyance qui a produit la ligne fautive.
  Trois tests figeaient l'ancien comportement, dont un dans un fichier que le relevé initial n'avait pas ouvert.
  Vérifié contre un **vrai SQLite** monté depuis la DDL dialectale, les deux chemins exercés : quatre tests, tous en échec sur le code d'avant.

  **Limite connue, laissée à un ticket dédié.** La CLI impose par ailleurs une **forme** : `if "@" not in value` refuse l'argument avant toute requête. `forge auth:user:show 2TNE1-01` ne cherche donc pas le compte, il rejette la saisie, et `auth:user:create` ne peut pas créer un tel compte. C'est une seconde divergence entre la CLI et le cœur, de la même famille que celle-ci, mais son correctif est une décision de conception : elle appartient à l'ADR qui séparera l'identité du contact.


## [1.0.0-rc.5] - 2026-08-10

### Ajouté

- **Une seule fabrique de réponse d'erreur JSON (`CORE-API-ERROR-CANONICAL-001`, ADR-088).**
  Forge portait deux formes d'erreur JSON qui s'étaient développées séparément, et un client recevait l'une ou l'autre selon la route touchée.
  D'un côté une enveloppe déclarée dans `core/http/helpers.py`, documentée sur quatre cent onze lignes dans `docs/reference/api-json.md` et câblée dans le cœur ; de l'autre une forme plate qu'aucun document ne décrivait, mais que les trois opt-ins exposant réellement du JSON avaient adoptée seuls.
  Mesuré : l'enveloppe comptait trois sites d'appel, tous dans un module qu'aucun opt-in n'emploie, et son pendant `api_success` n'en comptait aucun.
  L'ADR-088 a tranché pour la forme pratiquée, et ce ticket l'établit : `core.http.json_error(code, status, message=...)` devient la seule fabrique, et `application.py` comme `forge-mvc-iot`, `forge-mvc-video` et `forge-mvc-audio` y convergent.
  Le format en sortie ne bouge pas, les tests d'API des trois opt-ins passent sans modification, ce qui était le critère de validation du ticket.
  Le champ `message` reste **facultatif et réservé aux erreurs de validation**, seul cas où le client a besoin de savoir quoi corriger ; un refus qui explique à quelle étape il a eu lieu renseigne l'attaquant.
  Un garde-fou par analyse syntaxique refuse désormais tout corps d'erreur JSON composé hors de cette fabrique. Sans lui la divergence recommencerait, puisqu'elle est née exactement de l'absence d'un endroit unique où la forme soit écrite.
  L'enveloppe `api_success` et `api_error` est marquée sortante mais **encore exportée** : son retrait, celui de `core/security/api_auth.py` et la réécriture de la référence forment des tickets distincts, pour ne pas laisser le dépôt cassé entre deux commits.


- **La table d'événements statistiques gagne une politique de rétention (`STATS-RETENTION-001`).**
  `forge_stats_events` reçoit une ligne par événement suivi et rien ne la bornait.
  Une application qui trace consciencieusement y accumule des millions de lignes, et les agrégats ralentissent d'autant sans que rien ne prévienne.
  `forge stats:gc --days N` compte les événements antérieurs à la borne et les affiche ; `--run` supprime.
  Même forme que `audit:gc`, rétention à dire explicitement par l'option ou par `STATS_KEEP_DAYS`, refus d'une valeur nulle ou négative.
  Le module de rétention suit la convention **du paquet** et non celle de `forge-mvc-audit` : il n'accède jamais à la base de lui-même, l'appelant fournit l'exécuteur, exactement comme `track_event` et `count_stats_events`.
  La commande fait seule la jonction avec `core.database`.
  La borne part en paramètre lié, aucune expression de date n'entrant dans le SQL, et `idx_forge_stats_events_created_at` rend la suppression indexée sans migration.
  Purger détruit de l'information et aucun agrégat de remplacement n'est calculé, ce que la page de référence dit sans détour.
  Le paquet reçoit au passage son **premier test d'intégration** : il rendait jusqu'ici un DDL que rien n'exécutait jamais, si bien qu'une erreur de rendu ne se serait vue qu'en production.

- **`forge-mvc-stats` rejoint la convention de provisioning des opt-ins BDD (`STATS-OPTIN-CONFORM-001`).**
  Le paquet était en retrait des neuf autres opt-ins adossés à la base.
  Il décrivait bien sa table en `TableDefinition`, mais il n'avait ni `MIGRATIONS`, ni entry point `forge_mvc.commands`, ni dossier `cli/`, ni commande d'amorçage.
  `forge_stats_events` n'était donc créée par aucune commande Forge, alors que l'ADR-071 fixe une convention unique de provisioning, et sa page de référence affirmait « cet opt-in n'apporte aucune table », ce qui était faux.
  L'écart n'a été trouvé qu'en vérifiant un avis extérieur qui, lui, pointait autre chose.
  `forge stats:init` rend désormais la migration pour le backend installé et l'écrit dans `mvc/migrations/`, sans exécuter de SQL.
  La déclaration de la table déménage dans `tables.py`, emplacement conventionnel où le provisioning partagé va la chercher ; `schema.py` la réexporte, ces noms appartenant à l'API publique du paquet depuis son origine.
  Un test vérifie que les deux modules désignent le même objet, deux `TableDefinition` pour une même table divergeant en silence.
  Un projet antérieur avait créé `forge_stats_events` à la main, faute de commande. Vérifié en conditions réelles, les deux cas se passent bien.
  Si sa table est conforme, la migration ne fait rien et s'enregistre, le DDL étant rendu en `CREATE TABLE IF NOT EXISTS` sur les quatre backends.
  Si elle diverge, la migration **échoue franchement** en nommant la colonne absente, et **n'est pas enregistrée comme appliquée**, ce qui laisse le projet réparer puis rejouer.

- **Les tâches de fond orphelines sont reprises au lieu de rester bloquées (`JOBS-STALE-RECLAIM-001`).**
  Un worker réserve une tâche en la passant à `running`, puis rend son verdict.
  Tué entre les deux, il ne rendait aucun verdict et personne ne le rendait à sa place : la tâche restait `running` indéfiniment, et la file se remplissait de lignes mortes que rien ne signalait.
  La limite était assumée en toutes lettres dans le module, ce qui la rendait visible sans la rendre supportable.
  `forge jobs:reclaim` remet en file les tâches dont le **bail** de réservation a expiré, et marque en échec celles qui ont épuisé leurs tentatives.
  Aucune migration n'était nécessaire, `started_at` et `claim_token` existaient déjà dans la table.
  L'échec de reprise porte un message distinct de celui d'une exception du gestionnaire : confondre les deux ferait chercher un bogue applicatif là où il y a eu une panne de processus.
  Le réessai après échec attend désormais un **délai croissant**, 10, 20, 40, 80, 160, 320 puis 600 secondes, au lieu de repartir aussitôt.
  Sans lui, une tâche qui échouait vite consommait toutes ses tentatives en une fraction de seconde et ne laissait aucune chance à une panne passagère de se résorber.
  C'est un changement de comportement pour les files réglées à plus d'une tentative, et les tests qui encodaient le réessai immédiat disent maintenant le délai.
  Détail de portabilité qui valait le détour : l'inégalité du bail est écrite `started_at + bail < maintenant` et non `started_at < maintenant - bail`.
  Les deux sont équivalentes en mathématiques, pas en SQL portable.
  Mesuré, le dialecte SQLite compose son modificateur par concaténation et rend **`NULL`** pour un intervalle négatif, si bien que la seconde forme n'aurait rien repris du tout sur SQLite, sans lever la moindre erreur.
  Un garde-fou relit le SQL engendré pour empêcher la forme négative de revenir.
  Deux limites écrites plutôt que découvertes : le bail est une durée fixe, donc une tâche légitimement plus longue que lui sera reprise alors qu'elle tourne encore et exécutée deux fois, ce qui impose des gestionnaires idempotents ; et le worker ne prolonge pas son bail pendant qu'il travaille.

- **Le journal d'audit gagne une politique de rétention (`AUDIT-RETENTION-001`).**
  `audit_log` grossissait à chaque action tracée et rien ne la bornait.
  C'était la seule table d'opt-in adossé à la base sans purge, alors que `sessions:gc` avait posé le précédent, si bien que l'exploitant devait écrire lui-même son ménage en SQL.
  `forge audit:gc --days N` compte les entrées antérieures à la borne et les affiche ; `--run` supprime.
  La rétention doit être **dite**, par l'option ou par la variable `AUDIT_KEEP_DAYS`, l'option l'emportant sur la variable.
  Aucune valeur par défaut n'est supposée, et une rétention nulle ou négative est refusée, car elle viderait le journal entier sans que rien ne distingue l'intention de l'étourderie.
  Contrairement à `sessions:gc` qui supprime directement, la commande affiche d'abord (charte §7, motif déjà suivi par `fixtures:purge` et `db:init`).
  La raison de cette asymétrie est écrite dans le module : une session expirée n'est plus rien pour personne, son expiration étant portée par la ligne elle-même, tandis qu'une entrée d'audit est un enregistrement délibéré dont aucune date ne dit qu'il a cessé de valoir.
  La borne est calculée en Python et part en **paramètre lié**, sur le modèle de `forge-mvc-sessions-db` : aucune expression de date n'entre dans le SQL, ce qui évite d'emblée le piège mesuré par `OPTIN-DML-DIALECT-001`.
  Aucune migration n'est requise, `idx_audit_created` portant déjà sur `created_at`, donc la suppression est indexée.
  Deux limites écrites noir sur blanc : aucune archive n'est produite avant suppression, et la suppression tient en une instruction, donc sur une très grosse table le verrou peut être long.

### Modifié

- **Le routeur énonce enfin sa règle de résolution, et indexe ses routes statiques (`ROUTER-STATIC-INDEX-001`).**
  Forge n'avait **aucune règle de résolution écrite**. Le résultat découlait de l'ordre d'itération d'une liste, si bien que déclarer `/client/{id}` avant `/client/index` faisait résoudre `/client/index` vers `show(id="index")`.
  Le contrôleur recevait un identifiant nommé « index », et le développeur y lisait une erreur de base de données, jamais une erreur de routage.
  Une règle qui dépend de l'ordre des lignes d'un fichier et que personne n'a énoncée est de la magie cachée (principe 3), et c'est **le motif principal de ce ticket** ; la vitesse n'en est que l'effet secondaire.
  La règle est désormais écrite, documentée et gardée : une route **statique** l'emporte sur une route **dynamique**, quel que soit l'ordre de déclaration ; entre deux routes de même nature, la première déclarée gagne.
  **C'est une rupture de contrat**, assumée avant le tag 1.0.0 stable. Les générateurs de Forge ne produisent pas la situation, le paramètre occupant le troisième segment sous l'ADR-029 tandis que les formes statiques en ont deux ; seule une route écrite à la main peut la déclencher.
  Le test qui figeait l'ancien comportement a fait ce pour quoi il avait été écrit : il a échoué **seul**, obligeant ce ticket à énoncer la rupture au lieu de la glisser.
  Techniquement, les routes sont partitionnées à l'enregistrement, un dictionnaire pour les chemins statiques et une liste pour les dynamiques, `_entries` restant la seule source d'ordre pour `iter_routes()` dont `routes:list` dépend.
  Le classement est décidé par le compilateur de motif lui-même, seul endroit où le critère existe : `/a/{id-x}` n'est **pas** une route dynamique, le tiret n'appartenant pas aux caractères de mot, et un classement naïf par présence d'accolade l'aurait rendue introuvable. Un test paramétré fixe ce piège.
  Mesuré sur le chemin applicatif complet à mille routes : succès statique de 57,0 à **0,3 µs**, succès dynamique de 56,5 à 26,5 µs, 405 de 176,1 à 84,7 µs, 404 de 260,0 à 115,8 µs.
  Cumulé avec le ticket précédent depuis l'état d'origine : une route statique passe de 99,4 à 0,3 µs.

- **La résolution de routes gagne 41 à 47 % sur le chemin nominal (`ROUTER-METHOD-HOIST-001`).**
  Un avis extérieur affirmait que le parcours linéaire du routeur devenait « une latence CPU réelle » à cinq cents routes.
  Le parcours linéaire est bien réel, mais aucune des deux analyses n'avait de chiffre, et j'avais moi-même écarté le point en avançant des ordres de grandeur faux des deux côtés de la comparaison.
  La mesure a tranché, et elle a désigné une cause que personne n'avait nommée : à cette granularité, le coût dominant n'est ni l'expression rationnelle ni la normalisation de méthode, c'est **l'appel de fonction Python**, exécuté une à deux fois par entrée parcourue.
  Les méthodes d'une route sont désormais rangées en `frozenset` à l'enregistrement, la méthode demandée est normalisée **une fois** par résolution au lieu d'une fois par entrée, et les boucles de `match`, `allowed_methods` et `is_public` ne font plus aucun appel de fonction par entrée.
  Mesuré sur le chemin applicatif complet, celui qui enchaîne `match()` puis `allowed_methods()` sur un échec : succès de 99,4 à 57,0 µs à mille routes, 405 de 263,0 à 176,1 µs, 404 de 351,2 à 260,0 µs.
  **Aucune sémantique ne change**, et une quinzaine de tests le verrouillent, dont les deux pièges du remaniement : `method_label` doit continuer de lire la déclaration ordonnée et non l'ensemble, et l'en-tête `Allow` d'un 405 doit rester exhaustif.
  Le banc de mesure est versé dans `tools/bench_router.py`, afin que ces chiffres soient contredisables en une commande plutôt que crus sur parole.
  Réserve à garder en tête : tout ceci reste sous la milliseconde, et à cent routes, taille d'une application Forge courante, le gain va de 10,2 à 5,8 µs, soit un dixième d'un aller-retour SQL.

### Corrigé

- **Six tests d'empaquetage ne s'exécutaient nulle part (`CI-WHEEL-TESTS-NEVER-RAN-001`).**
  Ils vérifient que les cinq schémas JSON canoniques (ADR-058) sont bien **dans** le wheel et le sdist publiés. Un schéma absent d'une distribution ne se voit qu'après publication, chez l'utilisateur, sous la forme d'une commande qui échoue.
  En CI, le job construit les distributions **après** avoir lancé la suite : `dist/` était vide au moment où ils passaient, et ils se sautaient. En local, ils tournaient contre un `dist/` résiduel d'une construction ancienne, donc contre une distribution ne correspondant plus au code.
  Une étape les relance désormais après la construction, distributions fraîches en main, avec `FORGE_REQUIRE_DIST=1` : distribution absente devient un **échec**, sur le modèle de `FORGE_REQUIRE_DB`. La garantie d'empaquetage ne doit jamais être verte par défaut.
  Étape séparée plutôt que déplacement du build avant la suite : le job veille à ce que rien ne masque l'exécution de pytest (`CI-AUDIT-BLOCKING-001`), et un build en échec le ferait.
  Vérification faite, les schémas **sont** correctement empaquetés : aucun défaut, seulement une garantie qui ne garantissait rien.
  Un garde-fou fige les deux propriétés, l'existence de l'étape et son ordre après la construction.

  Ces six-là ont été trouvés par le passage de `-rs` en CI, décidé au ticket précédent. C'est le premier bénéfice de rendre les sauts lisibles, et il est arrivé au premier passage.

- **Une paramétrisation vide rendait un test invisible, et mon relevé en avait manqué une (`TESTS-EMPTY-PARAMETRIZE-GUARD-001`).**
  `@pytest.mark.parametrize` sur une liste vide ne produit pas zéro test : pytest en produit **un**, marqué `skip`, avec le motif « got empty parameter set ».
  C'est exactement là que le contrôle compte le plus. Les cliquets de dette de Forge se vident à mesure qu'elle est payée, et la liste vide est justement l'état qu'on veut voir tenir.
  J'en avais corrigé deux à la main dans ce cycle. Une troisième restait, dans le contrôle de cohérence de la feuille de route, et mon relevé ne l'avait pas vue : je l'avais mené sur `-m "not docs"`, sélection où ce fichier n'apparaît pas. **Corriger à la main ce qui doit l'être par un garde-fou, c'est se donner rendez-vous avec le même défaut.**
  Un garde de session les refuse désormais toutes, présentes et futures, sans coûter de collecte séparée. Éprouvé sur une sonde : la session s'arrête avec le nom du test fautif.

- **Les motifs de saut sont imprimés partout, `-rs` par défaut.**
  Un saut est invisible par construction. Ce cycle a montré ce que cela coûte : vingt-cinq tests dormaient depuis deux ADR, l'un cachant une dérive réelle des générateurs, l'autre une métadonnée publiée manquante.
  La CI ne les imprimait pas, si bien qu'un écart de huit sauts entre elle et le poste de développement restait indéchiffrable. Il ne le sera plus.

- **Vingt-cinq tests se sautaient en silence, dont un cachait une dérive réelle (`TESTS-DEAD-SKIPS-REVIVE-001`).**
  Chacun visait un chemin disparu et se sautait plutôt que d'échouer. Vingt et un pointaient vers `cli/starters/`, retiré par l'ADR-035, ou vers `mvc/`, sorti du dépôt par l'ADR-044.
  Ils sont repointés vers ce qui a pris la place, jamais supprimés : le générateur `make:auth` pour les quinze contrôles d'authentification, le squelette pour les routes et contrôleurs publics, les cinq racines productives réelles pour le balayage PBKDF2, les onze pages de la référence pour le contrôle de `cmd/`.
  Chaque cible neuve fait **échouer** le contrôle si elle disparaît à son tour, au lieu de le rendre muet. C'est le vrai correctif : un garde-fou qui saute quand sa cible manque finit toujours par dormir.
  Deux autres sautaient parce qu'une `parametrize` sur une liste vide rend un test sauté. Les deux cliquets de dette concernés sont réécrits en boucle. La liste vide est justement l'état qu'on veut voir tenir, c'est là que le contrôle a le plus de sens.
  Deux enfin cherchaient `def <nom>` dans un fichier, et ne trouvaient plus `get_session` ni `get_session_id`, déplacées puis réexportées. La source est maintenant résolue par l'objet fonction, ce qui suit la réexportation.
  **Le vingt-cinquième cachait une omission réelle** : `forge-mvc-testing` ne déclarait pas d'URL de documentation quand les vingt-six autres paquets le faisaient, donc sa page PyPI n'offrait aucun lien vers la doc. La clé est déclarée, et le contrôle l'exige désormais au lieu de sauter.
  Un vingt-sixième défaut a été trouvé par le réveil d'un de ces tests, et fait l'objet du ticket `PUBLIC-GEN-CANONICAL-DB-001` ci-dessous.
  Reste zéro saut sur la suite entière, serveurs présents.

- **La suite d'intégration ne tenait pas en parallèle (`TEST-DB-WORKER-ISOLATION-001`).**
  Deux défauts distincts, découverts parce qu'un passage de la suite complète a échoué là où deux autres passaient.
  Le premier est **de ce cycle** : `TEST-PACKAGE-INTEGRATION-REAL-LAYER-001` a remplacé la base jetable par test par des tables dans une base commune, et `tables_temporaires` les crée puis les jette par leur nom réel. Deux workers exerçant deux paquets qui partagent une table se détruisaient mutuellement leurs données. Mesuré sous `-n 4` : **7 à 26 échecs sur 135, à chaque passage**. Chaque worker travaille désormais dans sa propre base, créée au besoin.
  Le second **préexistait**, vérifié en rejouant les fichiers d'avant le cycle : plusieurs fichiers d'intégration sont des scénarios dont une étape crée la table et une autre la lit, et la répartition par défaut de pytest-xdist les éparpille. Mesuré sur les deux scénarios E2E MariaDB : **2 à 4 échecs sur 19**, aucun en `--dist loadfile`, désormais posé par défaut. Le drapeau est sans effet sans `-n`, donc sans effet en CI.
  Trois fichiers interrogeaient `information_schema` sur une base écrite en dur, donc regardaient ailleurs que là où leurs tables vivaient.
  **La CI ne pouvait rien voir** : elle ne parallélise pas ses jobs d'intégration. Seule la boucle locale rencontrait ces échecs, et pouvait les prendre pour un aléa, ce qui est la forme la plus coûteuse d'un défaut.
  Aveu utile : le premier correctif PostgreSQL a été écrit en `%s` sur une connexion qui traduit `?`, et a fait échouer les 98 cas PostgreSQL d'un coup. C'est le défaut même que `VIDEO-DML-PORTABLE-001` venait de corriger ailleurs. Un garde-fou le fige maintenant.

- **Forge avait deux façons officielles d'accéder à la base dans le code qu'il engendre (`PUBLIC-GEN-CANONICAL-DB-001`).**
  `make:crud` engendrait un modèle employant l'API canonique, `from core.database.db import fetch_one, fetch_all, execute, insert`.
  `make:public-list`, `make:public-show` et `make:public-form` engendraient, eux, des connexions brutes : `get_connection()`, `connection.cursor(dictionary=True)`, `cursor.fetchall()`, `connection.commit()`, le tout dans un `try/finally` de dix lignes que l'utilisateur devait relire.
  Deux façons de faire la même chose dans du code livré à l'utilisateur, contre le principe 11.
  Les trois générateurs emploient désormais l'API canonique. Le contrôleur de liste passe de onze lignes à une.
  **Le défaut n'était pas une régression de portabilité** : le motif brut fonctionne sur les trois serveurs, vérifié plutôt que supposé, et `cursor(dictionary=True)` est accepté partout parce que les backends normalisent le curseur. Ce que je soupçonnais d'abord était faux.
  Quatre tests figeaient l'ancienne forme, donc l'écart. L'un d'eux s'appelait `test_form_controller_importe_get_connection` : son nom même consacrait le défaut qu'il verrouillait.
  Le code engendré a été exécuté pour de vrai sur MariaDB, PostgreSQL et SQL Server, lecture, détail et insertion.
  **La documentation décrivait le générateur d'avant** : `docs/features/crud.md` montrait le modèle `make:crud` sous sa forme à connexion brute, que le générateur n'émet plus. Le bloc est remplacé par la sortie réelle du générateur, engendrée pour l'occasion et non recopiée de mémoire.

  Ce défaut a été trouvé en réveillant un test mort. `test_sql_examples_canonical_001.py` interdisait exactement cela, mais visait `mvc/models/`, dossier disparu depuis l'ADR-044 : il se sautait en silence depuis, pendant que les générateurs dérivaient.

- **Le job d'intégration MariaDB payait quatre minutes pour des tests qu'il ne pouvait pas exécuter (`CI-DB-JOB-SELECTOR-001`).**
  Il sélectionnait `-m db`. Or un cas PostgreSQL ou SQL Server porte **aussi** `db`, si bien qu'il les collectait tous, et que leur fixture tentait une connexion vers un serveur absent avant de les sauter.
  Mesuré, fixture `real_pg_db` avec un hôte injoignable : **quinze secondes par cas**, contre deux et demie quand l'hôte refuse, ce qui est le cas d'un runner. Le job sélectionnait 312 tests pour 116 exécutables.
  Le défaut préexistait, mais restait discret. Il est devenu voyant avec la paramétrisation des tests de paquet sur les trois serveurs (`TEST-PACKAGE-INTEGRATION-REAL-LAYER-001`), qui a fait passer ce job de 4 min 47 à 8 min 45.
  Le correctif porte sur la **sélection**, pas sur les marqueurs : `-m "db and not db_pg and not db_mssql"`.
  La combinaison `db` + `db_pg` reste en place, et c'est délibéré. Elle est **porteuse** : elle dit au garde de collecte qu'un cas PostgreSQL n'est pas exigé du job MariaDB, et elle permet au job sans base d'exclure les trois serveurs d'un seul terme, `-m "not db"`. La retirer aurait cassé le premier et obligé le second à énumérer chaque backend, donc à en oublier un au prochain ajout.
  Aucune couverture n'est perdue : 116 sur MariaDB, 98 sur PostgreSQL, 98 sur SQL Server, soit les 312 d'avant.
  Un garde-fou fige la sélection de chacun des trois jobs, et vérifie que le job sans base garde son terme unique. Éprouvé en remettant `-m db` : il échoue.

- **Le dépôt de `forge-mvc-video` était inutilisable sur PostgreSQL et SQL Server (`VIDEO-DML-PORTABLE-001`).**
  Il écrivait ses marqueurs de paramètre en `%s`, le format natif du connecteur MariaDB, quand Forge écrit `?`.
  Le cœur traduit `?` vers le format de chaque pilote et **double tout `%` littéral** au passage, si bien qu'un `%s` déjà écrit devenait `%%s`, un texte et non un marqueur.
  Douze marqueurs, plus deux `LIMIT` écrits en dur qui auraient de toute façon cassé SQL Server.
  Mesuré avant correctif, sur les deux moteurs promus au niveau plein par l'ADR-084 : `psycopg` répond « the query has 0 placeholders but 8 parameters were passed », `pyodbc` répond « The SQL contains 0 parameter markers, but 8 parameters were supplied ».
  Le paquet avait pourtant un test d'intégration, mais marqué `db` seul, donc exécuté contre MariaDB uniquement, où `%s` passe par coïncidence. Il porte maintenant sur les trois serveurs, et deux tests s'y ajoutent, l'un pour les métadonnées `ffprobe`, l'autre pour vérifier que la borne des listes s'applique réellement.
  Un test unitaire figeait `WHERE status = %s`, donc verrouillait le bug ; il affirme la forme portable et dit pourquoi.
  **La dette listée du cliquet DML est vidée**, et elle décrivait le défaut de travers : elle affirmait que PostgreSQL accepte `%s` nativement. C'est faux à cause du doublement des `%`, et je ne l'ai su qu'en interrogeant les serveurs plutôt que le pilote.
  Le cliquet lui-même passait d'ailleurs en test **sauté** une fois la liste vide, donc invisible : il est réécrit en boucle. Un saut n'est pas un succès, y compris pour le garde-fou qui surveille les sauts des autres.

- **Six tests d'intégration de paquet passaient à côté de la couche qu'ils prétendaient éprouver (`TEST-PACKAGE-INTEGRATION-REAL-LAYER-001`).**
  `audit`, `jobs`, `mfa`, `notifications`, `settings` et `stats` ouvraient chacun sa propre connexion MariaDB et l'enveloppaient dans un petit objet exposant `execute`, `fetch_one` et `fetch_all`.
  Deux conséquences, aucune voulue. Ils ne tournaient que sur **MariaDB**, alors que l'ADR-084 donne les quatre backends au niveau plein. Et ils court-circuitaient `core.database.db`, donc la **qualification d'erreur** de Forge : une violation d'unicité y remontait sous sa forme pilote, jamais sous la forme portable `UniqueViolationError`.
  C'est cet écart qui a caché les deux défauts du magasin anti-rejeu MFA, dont un interblocage InnoDB, pendant tout un cycle. Le pré-mortem les a trouvés seulement en mettant le magasin en course réelle, hors de ces tests.
  Les six passent désormais par `real_backend_db`, donc par la couche réelle, et chacun s'exécute **trois fois**, une par serveur. La suite gagne 103 cas d'exécution sans qu'une seule assertion soit dupliquée.
  Les helpers de `jobs` écrivaient eux-mêmes `NOW()` et `INTERVAL ? SECOND`, les constructions que le relevé de portabilité bannit : ils auraient fait échouer le fichier dès son premier passage sur un autre moteur. Le vieillissement d'une réservation lit maintenant l'heure **au serveur** et soustrait en Python, ce qui évite l'arithmétique dialectale et le piège de l'intervalle négatif, que SQLite rend en `NULL` sans rien signaler.
  Deux lectures entrent au relevé au passage, `jobs.get_job` et la liste d'administration de `stats`, toutes deux fautives et toutes deux jamais exercées ici.
  Le garde-fou a d'abord été écrit trop étroit, de deux façons : il jugeait la prose des docstrings comme du SQL, et il ne visait que les fichiers employant une fixture serveur, donc **aucun des six fichiers d'origine**. Corrigé sur les deux points, puis vérifié en le relançant sur les versions d'avant : six sur six.

- **Les fixtures de serveur réel n'étaient visibles que d'un seul dossier (`TESTING-REAL-DB-FIXTURES-001`).**
  `real_db`, `real_pg_db` et `real_mssql_db` vivaient dans `tests/db/conftest.py`, donc n'existaient que pour ce dossier.
  Les tests des paquets opt-in sont sous `packages/*/tests/` : ils n'y avaient pas accès, et six d'entre eux avaient répondu en réécrivant chacun son propre adaptateur de connexion à la main.
  Deux façons officielles de monter une base de test contredisaient le principe 11, et la seconde court-circuitait la vraie couche d'accès, donc la qualification d'erreur de Forge. C'est ce qui a caché les deux défauts du magasin anti-rejeu MFA pendant tout un cycle.
  Les quatre fixtures vivent désormais dans `forge-mvc-testing`, l'emplacement prévu pour l'infrastructure de test partagée (ADR-041), et son plugin pytest les expose à toute la suite. `tests/db/conftest.py` ne définit plus rien, il réutilise.
  Nouveauté : `real_backend_db` est **paramétrée sur les trois serveurs**, et chaque paramètre porte ses propres marqueurs. Un test d'intégration écrit **une seule fois** produit donc trois cas, que les trois jobs de CI sélectionnent chacun le sien. C'est ce qui rend abordable la couverture des trois backends, jusqu'ici payée en triplant le code.
  Le garde-fou a immédiatement révélé un piège que personne n'avait encore rencontré : les trois fixtures directes n'apportent **aucun** marqueur, si bien qu'un test qui les demande sans déclarer `db` est collecté dans le job sans serveur, où la fixture le saute en silence, et où il compte comme vert sans rien avoir vérifié. Un relevé sur analyse syntaxique refuse désormais ce cas.
  Les deux propriétés qui comptent sont vérifiées par **collecte réelle** dans un pytest lancé sur un fichier sonde écrit hors du dépôt, plutôt que par introspection : l'attribut privé de pytest qui porte les paramètres d'une fixture a déjà changé de nom d'une version à l'autre.

- **Le back-office ne savait ni modifier ni supprimer un enregistrement sur PostgreSQL et SQL Server (`ADMIN-JOBS-LIMIT-PORTABLE-001`).**
  Quatre `LIMIT` écrits en dur, trois dans `forge-mvc-admin` et un dans `forge-mvc-jobs`.
  `UPDATE ... LIMIT` et `DELETE ... LIMIT` sont des **extensions MySQL et MariaDB** que PostgreSQL et SQL Server refusent tous les deux : les deux actions les plus visibles d'un back-office étaient donc inutilisables sur la moitié des backends, alors que l'ADR-084 les donne au niveau plein.
  `jobs.get_job` portait le même défaut sur un `SELECT`, ce qui le cassait sur SQL Server.
  Un cinquième cas est apparu en élargissant le relevé : `forge-mvc-stats` engendrait un `LIMIT ?` en dur pour sa liste, là où `forge-mvc-audit` employait déjà `limit_clause()` au même endroit.
  Le correctif est un **retrait**, pas un rendu dialectal : les quatre clauses portent sur une clé primaire, donc au plus une ligne, et le `LIMIT` n'apportait rien. Seul celui de `stats` passe par le dialecte, sa borne étant réelle.
  Trois tests d'`admin` figeaient le SQL fautif, donc verrouillaient le bug ; ils affirment désormais la forme portable et disent pourquoi.
  Vérifié pour de vrai sur MariaDB, PostgreSQL et SQL Server : les quatre opérations passent partout.
  Ces défauts existaient à l'identique dans la rc4, aucun n'est introduit par ce cycle.

  **Huit emplacements de documentation affichaient le SQL fautif**, dont trois pages du parcours welcome d'`admin` qui donnaient à lire, mot pour mot, une requête que PostgreSQL et SQL Server rejettent.
  Deux autres décrivaient la réservation de `jobs` comme un `UPDATE ... ORDER BY id LIMIT 1`, forme abandonnée au cycle précédent, et le README d'`admin` annonçait encore « pas de reprise automatique » comme limite V1, alors que `reclaim_stale()` la lève depuis ce cycle.
  Deux pages enfin présentaient la borne de pagination comme fixe : elles disent maintenant qu'elle vient du backend actif, et le rendu annoncé pour chacun des quatre a été lu sur les dialectes réels, non supposé.
  C'est la sixième fois de ce cycle qu'une documentation affirme un comportement que le code n'a pas ou n'a plus.

- **Le relevé de portabilité DML ne couvrait qu'un tiers des paquets, et un échantillon d'opérations (`OPTIN-DML-PORTABILITY-WIDEN-001`).**
  `OPTIN-DML-DIALECT-001` avait rendu la DML de trois opt-ins portable, et s'était arrêté là.
  Deux restrictions se cumulaient. Il couvrait `jobs`, `notifications` et `settings`, donc ni `admin`, ni `audit`, ni `stats`, ni `mfa`. Et pour `jobs`, il exerçait treize opérations choisies, parmi lesquelles `get_job` ne figurait pas, c'est-à-dire précisément la fautive.
  Le garde-fou statique, lui, cherchait `ORDER BY <col> LIMIT <chiffre>`, motif trop étroit sur trois points à la fois : il exigeait un `ORDER BY`, une seule colonne de tri, et un chiffre. Aucun des cinq défauts ne lui correspondait.
  Le relevé porte désormais sur la **surface publique** de sept paquets, et non sur un échantillon jugé représentatif.
  Le garde-fou statique est refait sur **analyse syntaxique** : il ne juge que de vraies chaînes littérales, docstrings exclues, ce qui permet de bannir `LIMIT` en entier sans les faux positifs qui obligeaient à garder un motif étroit. `DELETE` rejoint les mots-clés reconnus, il manquait.
  Le relevé élargi a immédiatement trouvé le défaut de `stats`, puis un sixième cas dans `forge-mvc-video`, dont le dépôt emploie douze marqueurs `%s` au lieu de `?`.
  Ce dernier dépasse le périmètre du ticket : il est **inscrit en dette listée**, avec son motif, et un cliquet échoue dès qu'il devient propre, sur le modèle du cliquet DDL. Une exclusion muette aurait rendu le relevé rassurant et faux.
  Vérifié : le relevé élargi échoue sur le code d'avant, sur PostgreSQL comme sur SQL Server, et passe après correctif.
- **L'anti-rejeu TOTP partagé s'effondrait sous concurrence, exactement le cas qu'il vise (`PREMORTEM-RC5-003`).**
  `MFA-TOTP-REPLAY-SHARED-001` promettait que deux requêtes concurrentes portant le même code ne pouvaient pas être acceptées toutes les deux.
  Ses tests vérifiaient la propriété **en séquence**, et par un adaptateur de connexion écrit à la main. Mis en concurrence réelle par le pré-mortem, le magasin a révélé deux défauts que cette approche ne pouvait pas voir.
  **Un interblocage InnoDB.** L'ordre d'origine tentait l'`INSERT` puis, sur doublon, l'`UPDATE`. Or un `INSERT` qui échoue prend un verrou partagé sur la ligne, et l'`UPDATE` suivant en réclame un exclusif : sur douze requêtes simultanées, **dix mouraient** sur un `Deadlock found when trying to get lock`. L'ordre est inversé, l'`UPDATE` d'abord et l'`INSERT` en repli terminal, ce qui est aussi le plus rapide passé la première authentification.
  **Un doublon non reconnu.** `core.database.db` qualifie déjà ses erreurs et lève `UniqueViolationError` ; le module ne testait que `is_unique_violation()`, qui interroge le backend sur une erreur **de pilote** et rend donc `False` face à la forme portable. Chaque rejeu remontait une erreur au client au lieu d'un refus propre. Le CRUD engendré et `forge-mvc-settings` attrapaient déjà `UniqueViolationError` : ce module était le seul du dépôt à s'en écarter.
  La propriété de sécurité n'avait jamais cédé, une seule acceptation dans tous les cas, mais **par accident** : les requêtes tuées n'avaient pas l'occasion d'accepter.
  Le test de non-régression passe par **`core.database.db`**, la couche de production, et non par un adaptateur. Vérifié : il échoue sur le code d'avant, il passe sur le code corrigé.
  Mesuré après correctif, jusqu'à vingt requêtes simultanées, sur facteur neuf comme sur ligne préexistante : exactement une acceptation, aucune erreur.


- **Le drapeau `api` d'une route ne faisait rien, alors que la documentation lui prêtait un comportement (`CORE-ROUTE-API-FLAG-001`).**
  Il était déclaré dans `RouteEntry`, propagé par `RouteGroup`, affiché par `routes:list`, et **lu par aucun code applicatif**.
  Ses seules lectures dans tout le dépôt étaient celle de `forge.py`, pour l'afficher, et des tests vérifiant qu'il valait ce qu'on lui avait passé.
  La documentation du routeur en promettait pourtant « réponses JSON, pas de redirection login » : une route marquée `api=True` recevant une requête non authentifiée renvoyait une redirection 302 vers une page HTML de connexion, et son client JSON échouait loin de la cause en tentant de désérialiser du HTML.
  C'est le troisième cas de ce cycle où une documentation affirme un comportement que le code n'a pas, après la mise en service de `forge-mvc-stats` et le motif de saut des tests d'intégration.
  Le drapeau tient désormais sa promesse pour tout ce que le framework rend **après** avoir trouvé la route : 401 sur défaut d'authentification, 403 sur jeton CSRF invalide, 503 sur base indisponible, 500 sur erreur non gérée, tous en JSON.
  Un refus déjà explicite garde son statut, seule sa forme change : un middleware applicatif qui rend 403 continue de rendre 403.
  Les en-têtes du refus sont conservés, **cookies compris**, et c'est le point délicat : `AuthMiddleware` ferme la session quand il détecte une session orpheline (ADR-080), et reconstruire la réponse sans ce cookie aurait laissé la session ouverte, transformant une correction de forme en régression de sécurité.
  La cause d'une erreur non gérée n'est **jamais** exposée, même en `APP_ENV=dev`, contrairement à la page HTML : celle-ci est lue par un humain devant son navigateur, tandis qu'une réponse d'API part vers un client qui la journalise, la stocke ou la réexpose. La cause reste dans les journaux du serveur.
  La forme `{"error": "<code>"}` n'est pas inventée ici : `forge-mvc-iot`, `forge-mvc-video`, `forge-mvc-audio` et `forge-mvc-admin` avaient déjà convergé seuls dessus, `video` et `audio` portant même la ligne à l'identique. Ce ticket la reprend, il ne la décrète pas, et ne touche pas encore aux quatre paquets.
  **Limite assumée et écrite** : les 404 et 405 restent en HTML. Le drapeau appartient à une route, et dans ces deux cas aucune route n'a été trouvée, donc rien ne dit que le chemin visait une API.

- **Le motif de saut des tests d'intégration désignait la mauvaise cause (`TEST-DB-SKIP-REASON-001`).**
  Les douze fixtures d'intégration rangeaient toute erreur de connexion sous un mot unique, « injoignable », et le commentaire de `tests/db/conftest.py` assumait la confusion en toutes lettres.
  Or « pas de serveur » et « serveur qui refuse mes identifiants » appellent des gestes opposés, démarrer un service dans un cas, corriger une variable d'environnement dans l'autre.
  Le coût n'est pas théorique : un serveur MariaDB actif, à l'écoute, qui refusait seulement le mot de passe, a été lu comme un serveur arrêté, et le diagnostic s'est fourvoyé jusqu'à ce que l'erreur réelle soit relue.
  En CI le point était masqué, `FORGE_REQUIRE_DB=1` transformant le saut en échec ; en local il produisait un faux diagnostic sans le moindre signal.
  Un classificateur partagé vit désormais dans `forge-mvc-testing` (ADR-041), et les douze sites l'appellent au lieu de recopier le message.
  Le motif nomme le geste attendu, « le serveur tourne, inutile de le démarrer, posez `FORGE_TEST_DB_PASSWORD` », ou « démarrez le serveur, ou vérifiez `FORGE_TEST_DB_HOST` et `FORGE_TEST_DB_PORT` ».
  Une cause non reconnue n'est jamais rangée d'office dans l'une des deux autres : mieux vaut ne rien affirmer que d'affirmer faux avec l'aplomb du vrai.
  Le classificateur est éprouvé sur des messages **réels** des trois pilotes, relevés en condition, et non sur des chaînes inventées.
  Les deux scénarios ont été rejoués de bout en bout, mauvais mot de passe puis port sans serveur, pour vérifier que chacun produit bien son motif.

### Sécurité

- **L'anti-rejeu TOTP peut désormais être partagé par tous les processus (`MFA-TOTP-REPLAY-SHARED-001`).**
  Le registre des codes déjà consommés vivait dans la mémoire d'un processus, donc chaque worker gunicorn avait le sien.
  Or `deploy:init` génère précisément du gunicorn multi-worker, si bien que le chemin de déploiement officiel de Forge affaiblissait sa propre protection.
  Un code intercepté pouvait être présenté à chaque worker tour à tour, et accepté autant de fois qu'il y a de workers.
  La limite était connue, écrite et gardée par un test (`MFA-REPLAY-SCOPE-DOC-001`), qui laissait le remède au choix de l'exploitant ; ce ticket lui en donne un qui fonctionne, sans lui retirer le choix.
  Le registre passe derrière un contrat, `TotpReplayStore`, et Forge en livre deux mises en œuvre.
  Le **défaut ne change pas**, c'est toujours le registre en mémoire, si bien qu'aucun projet existant ne voit son comportement bouger.
  `DbTotpReplayStore` s'adosse au backend BDD du projet et vaut alors pour tous les processus ; l'application le pose au démarrage par `set_replay_store()`, en une ligne visible (principe 3).
  Aucune dépendance nouvelle, ni Redis ni broker, `core.database` venant de `forge-mvc` que le paquet exigeait déjà, et l'import restant paresseux pour que `forge-mvc-mfa` demeure utilisable sans backend.
  Le contrat est reproduit **exactement**, y compris sa partie la moins visible.
  Il refuse toute fenêtre antérieure ou égale à la dernière vue, et pas seulement le doublon exact, sans quoi un code plus ancien resterait rejouable tant que la tolérance de `verify_totp_code` l'accepte.
  D'où une ligne par facteur portant sa dernière fenêtre, et non une ligne par code consommé, ce qui borne aussi la table au nombre de facteurs actifs.
  L'atomicité est obtenue sans transaction applicative, par un `INSERT` dont l'échec en doublon bascule vers un `UPDATE` gardé par `last_step < ?`, le doublon étant reconnu par `is_unique_violation()` du contrat `DatabaseBackend`.
  La purge compare des numéros de fenêtre et jamais des dates, ce qui la rend portable sans effort sur les quatre backends.
  La table est **optionnelle**, `forge mfa:init` ne servant qu'aux projets qui installent le registre partagé ; le paquet reste une bibliothèque sans persistance pour tous les autres.
  Le test central ouvre deux connexions distinctes et vérifie qu'un code accepté par la première est refusé par la seconde, propriété que le registre en mémoire ne peut pas offrir.

- **Les listes blanches ancrées acceptaient la valeur suffixée d'un saut de ligne (`VALIDATION-ANCHOR-FULLMATCH-001`).**
  En Python, `$` n'ancre pas tout à fait la fin de la chaîne, il accepte aussi la position qui précède un saut de ligne final.
  Un validateur écrit `^...$` puis consulté par `match()` laissait donc passer ce qu'il prétendait interdire.
  Mesuré, `_ident("titre\n")` rendait la chaîne intacte, et cette valeur est ensuite interpolée dans le `SELECT` de `forge-mvc-admin`.
  Aucun cas exploitable n'a été trouvé, rien ne peut suivre ce saut de ligne, `"titre\nDROP TABLE x"` étant bien rejeté.
  Mais plusieurs de ces valeurs composent ensuite un chemin de fichier, l'identifiant de session devenant `<dossier>/<identifiant>.json` et la locale `<dossier>/<locale>.json`, or un saut de ligne est un caractère légal dans un nom de fichier POSIX.
  Une défense en profondeur ne se juge pas à son exploitabilité du jour.
  Le critère de tri n'est pas la forme de l'expression mais la méthode d'appel, `fullmatch()` immunisant déjà même en gardant les ancres.
  Le dépôt employait les deux formes, `core/forms/fields.py`, `forge_mvc_files` et `forge_mvc_entities` appelant déjà `fullmatch()`.
  Le ticket retient `fullmatch()` partout, forme unique (principe 11), sur **29 sites répartis dans 18 fichiers**.
  Quatre sites étaient couverts par accident, un `.strip()` en amont retirant le saut avant la validation ; **six laissaient réellement passer**.
  Le garde-fou ne porte aucune liste de sites et détecte l'idiome par analyse syntaxique, si bien qu'un site futur le fera échouer sans que personne ait à l'y inscrire.
  Il a d'ailleurs trouvé cinq sites qu'une recherche textuelle avait manqués, leurs variables ne suivant pas la convention de nommage attendue.

### Retiré

- **L'enveloppe `api_success` et `api_error` (`CORE-API-ENVELOPE-REMOVE-001`, ADR-088).**
  Ces deux fonctions enveloppaient toute réponse dans `{"success": ..., "data": ...}` ou `{"success": false, "error": {"code", "message"}}`.
  Elles étaient exportées par `core.http`, documentées dans deux pages de référence, couvertes par un fichier de tests de trois cent soixante-cinq lignes, et **appelées par aucun code de production** : leurs seuls sites vivaient dans `core/security/api_auth.py`, retiré par le ticket précédent, et l'unique occurrence d'`api_success` hors tests était dans une docstring.
  Le code HTTP porte déjà l'information de succès, et Forge le traite comme tel avec soin, 405 accompagné de son en-tête `Allow`, 503 distinct du 500, 401 distinct d'une redirection ; un champ `success` la redoublait.
  **Remplacement** : une réponse de succès rend la ressource par `json_response(data, status)`, une erreur passe par `json_error(code, status, message=...)`.
  Les trois pages qui enseignaient l'enveloppe sont réécrites, et elles disent désormais **pourquoi** la forme est plate plutôt que de la présenter comme allant de soi.
  La contradiction laissée par `CORE-ROUTE-API-FLAG-001` est corrigée au passage : `docs/reference/api-json.md` affirmait encore que le drapeau `api=True` « est déclaratif, sans modifier leur comportement », ce que ce ticket avait rendu faux deux jours plus tôt.
  Le fichier de tests de l'enveloppe est supprimé, ses propriétés génériques étant déjà couvertes par `test_core_json_response_unify_001.py` ; ses **conventions de contrôleur** sont en revanche reprises sous la forme retenue, car elles n'ont pas disparu avec l'enveloppe, elles ont changé de forme.
  Trois garde-fous documentaires exigeaient l'enveloppe dans la page de référence. Ils ont échoué, comme prévu, et vérifient désormais la forme plate **et l'absence** de l'ancienne, sans quoi la page enseignerait deux contrats à la fois.

- **`core.security.api_auth`, seconde implémentation Bearer du cœur (`CORE-API-AUTH-REMOVE-001`, ADR-088).**
  Le cœur portait **deux** implémentations de l'authentification par jeton Bearer, divergentes jusque dans la lecture du préfixe, `"Bearer "` avec espace contre `"bearer"` comparé en minuscules.
  Le ticket `CORE-HTTP-BEARER-PRIMITIVE-001` avait extrait `core/http/bearer.py` au motif qu'« un correctif de sécurité appliqué à une seule copie laisse les autres vulnérables » ; il a consolidé les trois opt-ins et laissé ce module de côté.
  Le verdict d'usage était sans appel : quand `forge-mvc-iot`, `forge-mvc-video` puis `forge-mvc-audio` ont eu ce besoin exact, les trois ont importé `core.http.bearer` et écrit autre chose.
  Sa posture de sécurité était par ailleurs en retrait : il distinguait trois causes de refus, `unauthorized`, `invalid_authorization_header` et `invalid_token`, donc renseignait un attaquant sur l'étape qu'il avait franchie, là où les opt-ins rendent délibérément un refus opaque.
  Le module portait un correctif de sécurité issu d'un audit (`SECURITY-API-AUTH-COMPARE-DIGEST-001`, comparaison en temps constant). Sa suppression n'a été retenue qu'après avoir vérifié que `tests/test_core_http_bearer_001.py` verrouille la même garantie sur `core/http/bearer.py`, en lisant le source pour exiger `secrets.compare_digest`.
  **Remplacement**, à écrire dans le contrôleur plutôt qu'en décorateur :

  ```python
  import os
  from core.http import json_error, json_response
  from core.http.bearer import is_bearer_authorized

  def status(request):
      if not is_bearer_authorized(request, os.getenv("API_TOKEN") or None):
          return json_error("unauthorized", 401)
      return json_response({"status": "ok"})
  ```

  Aucun décorateur n'est recréé. Si un besoin réel apparaît, sa place est `core/security/decorators.py`, auprès de `require_auth`, `require_csrf` et `require_role`, bâti sur la primitive et avec un code d'erreur unique.
  `core/http/bearer.py` **gagne au passage sa page de documentation**, qu'il n'avait pas : supprimer l'implémentation documentée pour promouvoir l'indocumentée aurait été une régression.
  La section d'authentification de `docs/reference/api-json.md` est réécrite, et elle dit désormais le piège que l'ancienne taisait : un jeton attendu à `None` ouvre l'API à tout le monde, et il faut refuser de démarrer en production plutôt que de servir sans le savoir.

## [1.0.0-rc.4] - 2026-08-04

### Ajouté

- **Un garde qui vérifie que la documentation nomme du code existant (`DOC-CODE-ADEQUATION-001`).**
  Une page qui montre `from forge_mvc_x import Y` promet que `Y` s'importe, et une qui écrit `forge machin:truc` promet que la commande existe.
  Rien ne le vérifiait, et le seul retour possible était celui d'un lecteur qui essaie.
  Forge a pourtant beaucoup renommé, extrait et supprimé depuis la 0.x, et la documentation suit à la main.
  `tools/check_docs_symbols.py` lit les blocs de code de toute la documentation embarquée, en extrait les imports visant Forge et les appels au CLI, puis demande à l'interpréteur et au CLI eux-mêmes si cela existe.
  Il ne juge pas le sens, seulement l'existence, seule chose vérifiable sans ambiguïté.
  État mesuré du dépôt : **1192 imports et 619 appels de commande, tous valides**, dont 635 imports et 180 commandes dans les seuls parcours d'accueil.
  Trois exclusions, toutes motivées. Les archives de `docs/history/` conservent à dessein du code supprimé.
  Un ADR qui déclare son remplacement décrit un état passé et doit continuer de montrer ce qu'il a fait adopter, sans quoi on réécrirait la décision qu'il enregistre.
  Une page peut enfin se déclarer hors contrôle par un marqueur explicite, ce qui vaut mieux qu'une liste de répertoires exclus se remplissant en silence (principe 3).
  Le garde appartient à la boucle **code** et non à la boucle documentaire, la dérive naissant le plus souvent d'un symbole renommé ou d'une commande retirée.
  Deux péremptions trouvées à la première exécution. L'ADR-023 se déclarait « Accepté » alors que l'ADR-035 a retiré `forge starter:build`, si bien qu'un lecteur y trouvait la façon canonique de faire une chose impossible ; son statut annonce désormais son remplacement.
  Une page d'architecture conservait un nom d'époque en le disant dans son texte, mais sans que rien ne le rende lisible par la machine.

- **Un harnais qui joue un parcours d'accueil au lieu de le relire (`WELCOME-EXECUTION-001`).**
  Lire un parcours ne dit pas s'il marche.
  `tools/run_welcome_parcours.py` suit les paliers dans l'ordre du `nav` de `mkdocs.yml`, celui que le lecteur voit dans le menu, et exécute les blocs `bash` dans un projet Forge réel jusqu'au premier qui refuse.
  L'ordre ne pouvait pas venir de la convention « Palier suivant », qui ne couvre que 21 des 316 pages de parcours.
  Trois raisons de ne pas exécuter un bloc, toutes déclarées et comptées, un `<nom>` à remplacer par le lecteur, une commande qui ne rend jamais la main, un geste hors du terminal.
  Un bloc sauté est annoncé, jamais tu, un harnais silencieux se lisant comme une couverture complète (principe 3).
  Éprouvé sur le plus simple des vingt-sept parcours, SQLite, il a trouvé **trois manques dans les deux premiers paliers**.
  Le moteur d'entités n'était pas cité, alors que `db:init` en vient ; `db:config` manquait, si bien que le backend ignorait quel fichier ouvrir ; `make:crud` était donné seul, alors qu'il consomme une entité que seul `make:entity` crée.
  Chaque commande était juste prise isolément, et le manque n'existait qu'entre elles.
  Le parcours corrigé se déroule désormais de bout en bout, dix blocs sur dix, sur un projet neuf.

- **Un garde interdit à la documentation d'affirmer ce que l'aide contredit (`DOC-COMMAND-BEHAVIOUR-001`).**
  Trois ADR récents ont changé le comportement de commandes centrales, et la documentation a décrit l'ancien pendant des mois : le tutoriel de première application, le guide de migration, la page d'installation MariaDB, les chapitres des quatre backends, le parcours welcome-forge.
  Le garde compare la documentation à **l'aide de la commande**, pas à une liste écrite dans le test : si l'aide dit que `db:init` affiche par défaut et n'exécute qu'avec `--run`, aucune page ne peut affirmer qu'il crée sans nommer `--run`.
  Il est volontairement **étroit**. Sa première version relevait dix phrases dont la moitié étaient justes, une négation, une comparaison, et le cas SQLite où `db:init` crée réellement le fichier faute de serveur.
  Les exemptions sont explicites et motivées, et un test vérifie qu'elles le restent : une exemption sans motif écrit devient un trou silencieux.
  Les ADR sont hors de portée, comme les archives : ils énoncent ce qui était vrai à leur date, et les corriger réécrirait la décision qu'ils enregistrent.
  L'ADR-033, qui décrivait un `db:init` se connectant, reçoit à la place un renvoi vers l'ADR-067 qui a changé ce comportement, sa propre décision restant en vigueur.
  Trois pages de `welcome-forge` affirmaient enfin que `db:init` « crée la base, l'utilisateur applicatif » : c'est vrai sur SQLite, sans serveur ni comptes, et faux sur les trois autres backends. Elles distinguent désormais les deux cas.

- **La page d'installation de MariaDB décrivait un `db:init` d'avant l'ADR-067 (`DOC-INSTALL-MARIADB-STALE-001`).**
  Elle affirmait que `forge db:init` « se connecte en tant que `forge_admin` », et citait un message d'erreur, `Connexion MariaDB admin impossible`, qui **n'existe plus dans le code**.
  Depuis l'ADR-067, `db:init` ne se connecte pas : il affiche le SQL de provisioning, et seul `--run` l'exécute.
  Un lecteur y cherchait donc la cause d'une erreur que la commande ne peut plus produire.
  Elle employait par ailleurs `db:apply` pour « appliquer les migrations », rôle de `migration:apply` : `db:apply` applique le schéma des entités, et la page confondait les deux à trois endroits.
  Enfin, elle faisait lancer neuf fois `db:init` et quatre fois `db:apply` **sans jamais nommer les deux opt-ins d'où ces commandes viennent**, `forge-mvc-mariadb` (ADR-060) et `forge-mvc-entities` (ADR-070).

- **Le tutoriel de première application ne fonctionnait pas (`DOC-TUTORIAL-PREREQUIS-001`).**
  C'est le guide qu'un débutant suit pour construire son premier CRUD, et il échouait à sa **première commande de génération**.
  Il ne mentionnait ni `forge-mvc-entities`, dont viennent `make:entity`, `make:relation`, `build:model` et `make:crud` depuis l'ADR-070, ni aucun backend de base de données, le squelette étant livré sans depuis l'ADR-060.
  Le mot `pip install` n'apparaissait nulle part dans ses 426 lignes.
  Sa section base de données était périmée de la même façon : elle annonçait que `forge db:init` « crée la base, l'utilisateur applicatif et les tables », alors qu'il **affiche** le SQL de provisioning depuis l'ADR-067, et que ce sont les tables que `db:apply` crée — commande absente du tutoriel.
  Un lecteur arrivait donc au bout avec des fichiers générés, aucune table, et une application incapable de démarrer.
  Les prérequis sont posés au premier chapitre, la section base distingue provisionner de créer les tables, et le récapitulatif final suit.

  Vérifié sans défaut dans la même zone : `getting-started` s'arrête à `forge run` et renvoie aux parcours, sans promettre de génération ; `bases-de-donnees` présente correctement les quatre backends.

- **Le guide de migration décrivait trois commandes de travers et une version inexistante (`DOC-MIGRATION-GUIDE-STALE-001`).**
  Son bloc « commandes concernées » annonçait que `forge db:init` « crée la base et applique les entités », alors que depuis l'ADR-067 il **affiche** le SQL de provisioning et n'exécute qu'avec `--run`, et qu'il n'applique aucune entité.
  `forge db:apply` y « appliquait les migrations », rôle de `migration:apply` ; le bloc citait le premier et omettait le second.
  Un lecteur qui suivait ce guide pour migrer croyait donc sa base provisionnée alors que rien n'avait été exécuté.
  La procédure de retour arrière proposait par ailleurs `pipx install forge-mvc==2.2.0`, version qui **n'a jamais été publiée** : PyPI ne porte que des `1.0.0b*` et `1.0.0rc*`, la trajectoire publique ayant été renumérotée vers 1.0.
  Elle cite désormais une version réellement publiée, et l'exemple de numérotation PATCH passe de `2.2.0` à `1.2.0`, comme les exemples MINOR et MAJEUR : illustrer avec une série 2 laissait croire à une version 2 de Forge.

  Vérifié sans défaut dans la même zone : la page sur les événements documente correctement une **absence assumée** (ADR-052) et non un paquet disparu, et les seules mentions d'une version 3.x vivent dans `docs/history/`, qui décrit son époque.

- **La documentation de déploiement figeait encore l'unité systemd sur MariaDB (`DOC-DEPLOYMENT-BACKEND-001`).**
  Deux pages montraient `After=network.target mariadb.service` comme unité de service, alors que `deploy:init` la fait suivre le backend résolu depuis `DEPLOY-BACKEND-AGNOSTIC-001`.
  C'est mon propre correctif qui avait créé l'écart : le code a changé, la documentation qui le décrit non.
  Un lecteur sur PostgreSQL, SQL Server ou SQLite qui recopiait l'exemple obtenait une unité attendant un service inexistant.
  Les deux pages disent désormais que la ligne suit le backend, et invitent à préférer le fichier produit par `deploy:init` à une recopie, lui seul connaissant le backend du projet.

- **`DB_POOL_TIMEOUT` manquait à la documentation de production (`DOC-DEPLOYMENT-POOL-TIMEOUT-001`).**
  Les quatre backends la déclarent dans leur gabarit d'environnement, et la page de sécurité en production ne citait que `DB_POOL_SIZE`.
  C'est pourtant elle qui borne l'attente d'une connexion, donc qui fait rendre un `503` avec `Retry-After` au lieu de laisser la requête pendre.
  Sans borne, mesuré lors du chantier des pools, une transaction coincée fait patienter les requêtes cinquante secondes sur MariaDB et indéfiniment sur PostgreSQL et SQL Server.

  Vérifié sans défaut dans la même zone : les variables citées correspondent toutes au contrat réel des backends, et la configuration Nginx documentée est identique, ligne à ligne, à celle que `deploy:init` produit.

- **« Poser sa base » ne parlait que de tables, et quatre opt-ins sont tombés dans le trou (`WELCOME-OPTIN-INIT-001`).**
  Le troisième point de la procédure canonique d'installation cadrait l'étape sur les migrations seules.
  Ses vingt-sept dérivations en ont hérité, et quatre références concluaient donc « Rien à faire : cet opt-in n'apporte aucune table ».
  C'est vrai des tables et faux de l'opt-in. `upload:init` crée `storage/uploads/` et ses sous-dossiers, `mail:init` crée `storage/mail/`, `admin:init` génère la structure du back-office, `deploy:init` produit les fichiers Nginx et systemd.
  Sans eux, l'opt-in est installé, inscrit, et ne fonctionne pas.
  La cause était en amont, pas dans les quatre pages : le point canonique devient « Poser ce dont il a besoin », dit ce que la commande pose selon l'opt-in, et écrit noir sur blanc que **ne pas avoir de tables ne veut pas dire n'avoir rien à faire**.
  Les vingt-deux références qui portaient l'ancien intitulé suivent, et les quatre incomplètes reçoivent leur commande.
  Un garde-fou confronte désormais les commandes `:init` publiées en entry points au chapitre de mise en service de chaque opt-in.
  Trouvé en balayant les 508 blocs `bash` de `docs/`, en partant de la procédure dont les 27 références déclarent dériver.

- **Deux vérifications de plus sur les 508 blocs, sans défaut (`DOC-BASH-SWEEP-001`).**
  La validité shell de chaque bloc, par `bash -n` : **484 sur 493 se collent tels quels**, les 9 autres étant des gabarits à trous que `<VERSION>` ou `<nom>` rendent volontairement non exécutables.
  Et les paquets que la documentation fait installer : les 10 distributions Forge citées existent, les 15 paquets système aussi.

- **Une page du cœur échappait au contrôle documentaire (`DOC-SWEEP-PERIMETER-001`).**
  Le motif de balayage était `core/*/docs`, à une seule étoile : il attrapait les treize `core/<module>/docs` et manquait `core/docs`, situé un niveau au-dessus.
  `core/docs/forge_config.md` n'a donc jamais été confrontée au code, sans que rien ne le signale.
  Un garde n'est fiable que sur le périmètre qu'on lui a donné, et ce périmètre doit se mesurer comme le reste : un test compare désormais les pages balayées à toutes celles qui existent, sous `core/`, `cli/` et `packages/`.
  Couverture vérifiée : 66 pages du cœur, 35 du CLI, 475 des opt-ins, aucune manquante.
  C'est le quatrième angle mort trouvé dans mes propres outils, après les fences indentées, l'oubli de `cli/*/docs` et la règle trop large sur les diagnostics.

- **Douze gabarits ne disaient qu'en prose où les poser (`WELCOME-TEMPLATE-DESTINATION-001`).**
  Les parcours nomment la destination d'un bloc en première ligne, `# chemin.py` ou `{# chemin.html #}`, convention suivie par 49 blocs `html` sur 62.
  Les treize autres, dans `rbac`, `mail`, `admin` et `entities`, ne l'indiquaient que dans la phrase précédente, « Créez la vue `mvc/views/rbac_permission/index.html` ».
  Un lecteur s'en sort ; rien d'automatique ne le peut, et surtout la destination se perd dès qu'on copie le bloc seul.
  Douze reçoivent la destination que leur prose nommait déjà, reprise telle quelle et non devinée.
  Le treizième est un **extrait** que sa page annonce comme tel, et n'a donc pas de destination.
  Trouvé en faisant répondre les routes : les pages de `rbac` rendaient `TemplateNotFound` faute de gabarit posé.

- **Une configuration d'upload retirée du cœur était encore lue par un parcours (`WELCOME-FILES-CONFIG-001`).**
  Le parcours `files` appelait `get_config("upload_allowed_extensions")`, clé que l'ADR-032 a sortie du registre du cœur, où seul `upload_max_size` demeure.
  Sa page `/files-welcome/inspect` rendait donc 500 sur `Clé de configuration inconnue`.
  L'exemple lit désormais l'environnement, comme `forge-mvc-files` lui-même, et le dit.
  La sonde HTTP distingue par ailleurs un `4xx` d'un `5xx` : un refus prouve que la route est câblée et que le contrôleur fait son travail, un plantage non.

- **Les parcours qui se vérifiaient au navigateur répondent enfin (`WELCOME-HTTP-ROUTES-001`).**
  Douze parcours n'ont aucun bloc `bash` : ils font écrire du code, puis se vérifient en ouvrant une page.
  Leur code était posé et compilé depuis `WELCOME-CODE-PLACEMENT-001`, mais rien ne disait s'il **fonctionnait**.
  Le harnais fusionne désormais les fragments de câblage dans `mvc/routes/__init__.py`, ce que le lecteur fait à la main puisque Forge n'injecte jamais de route (ADR-085), puis appelle les routes que le parcours vient de déclarer.
  L'appel passe par `create_configured_wsgi_app()`, le point d'entrée WSGI **de production**, celui que Gunicorn utilise : pas de serveur à démarrer, pas de port à réserver, et l'on éprouve la même pile que le lecteur.
  Les routes visées sont celles que le parcours déclare lui-même, plus sûr que de deviner des URL dans la prose. Seuls les `GET` sont appelés, un `POST` sans jeton CSRF étant refusé à juste titre (principe 7).
  Deux défauts trouvés du premier coup, invisibles à tout ce qui précédait.
  Le parcours i18n ne citait **nulle part** `forge i18n:init`, si bien que ses neuf pages rendaient 500 sur `Catalogue introuvable : translations/fr.json`.
  Et **cinq gabarits** de `i18n` et `mail` étendaient `layouts/app.html`, que le squelette ne livre pas : il livre `layouts/base.html`. Copiés tels quels, ils rendaient `TemplateNotFound`.
  Le guide portait la même référence.
  Une troisième convention de nommage de destination est reconnue, le commentaire **Jinja** `{# … #}`, seul correct pour un gabarit puisqu'un commentaire HTML serait envoyé au client.
  L'ignorer laissait les gabarits non posés.
  État mesuré : `i18n` répond sur ses 8 routes, `iot` sur 6, `mail` sur 5. `import-export` reste le seul parcours dont rien n'est mécaniquement vérifiable.

- **Quatre exemples de documentation levaient `TypeError` si on les copiait (`DOC-CODE-SIGNATURES-001`).**
  Le contrôle d'adéquation vérifiait que le symbole documenté **existe**. Un symbole peut exister et sa **signature** avoir changé : l'exemple passait alors le contrôle et échouait chez le lecteur.
  La vérification descend d'un cran et lie chaque appel documenté à la signature réelle, par `inspect.signature`.
  Mesuré sur **770 appels**, quatre étaient fautifs, dans trois paquets.
  `forge-mvc-rbac` employait `require_contract_permission` **en décorateur**, alors que c'est une fonction de garde rendant `None` ou une `Response` 403 ; l'exemple enseignait donc un usage qui n'existe pas.
  `forge-mvc-mfa` passait `user_id=` à `start_mfa_challenge`, un mot-clé absent de la signature, et omettait `factors` dans `verify_mfa_challenge` et `is_mfa_enabled`.
  `forge-mvc-images` appelait `attach_media_to_entity` avec trois positionnels, alors que `entity_name` et `entity_id` sont réservés aux mots-clés.
  Le garde ne juge que ce qui est sans ambiguïté, un mot-clé inconnu, un argument requis manquant, trop de positionnels, et se tait sur les appels à `*args` ou `**kwargs` qui ne se lient pas.
  Chaque cas mesuré a son test, avec la contre-épreuve : un garde qui passerait aussi sans le correctif ne garderait rien.

- **La doc embarquée du CLI échappait au contrôle d'adéquation, et `forge --help` s'y contredisait (`CLI-HELP-SUMMARY-COHERENCE-001`).**
  `tools/check_docs_symbols.py` balayait `packages/*/docs`, `core/*/docs` et `docs/`, mais pas `cli/*/docs` (ADR-043), qui porte pourtant 60 blocs de commandes qu'un lecteur tape.
  Balayage élargi : **1220 imports et 700 appels de commande**, tous valides.
  Le premier passage y a trouvé une contradiction. `forge --help` annonçait `media:init` comme un « alias de upload:init », quand son aide détaillée, dans le même fichier, disait justement « surensemble de upload:init pour le sous-système média ».
  La conséquence n'est pas cosmétique : `init_media_storage()` appelle `init_upload_storage()` **puis** crée les sous-dossiers de variantes d'image.
  Un lecteur qui croit les deux commandes équivalentes lance `upload:init`, n'obtient ni `thumbnail` ni `medium`, et le découvre au premier traitement d'image.
  Le sommaire dit désormais ce que fait la commande, et un garde-fou refuse toute description courte annonçant un alias que l'aide longue ne confirme pas.
  Une sur quatre-vingts le faisait.

- **Les fixtures reliées ne chargeaient pas sur SQL Server (`FIXTURES-REFERENCE-DIALECT-001`).**
  `fixtures:generate` traduit `self.reference(table, colonne, valeur)` en sous-requête, écrite telle quelle dans un `.sql`.
  Le littéral passait bien par `dialect.render_literal()`, mais la borne était écrite en dur, `LIMIT 1`.
  Mesuré contre un serveur réel, SQL Server refuse ce fichier avec `Incorrect syntax near '1'`, alors qu'il est au niveau plein depuis l'ADR-084.
  Le chantier de portabilité de la DML avait manqué ce cas parce qu'il balayait la **couche de requêtes** : ici le SQL n'est pas exécuté, il est écrit comme texte dans un fichier, et n'a donc jamais traversé cette couche.
  Un audit qui suit les chemins d'exécution ne voit pas le SQL qu'on imprime.
  `limit_clause()` ne pouvait pas servir, étant paramétrée là où l'on écrit du SQL sans paramètre, et sa forme T-SQL exigeant un `ORDER BY` en suffixe quand l'équivalent littéral de SQL Server est `TOP 1`, en tête du `SELECT`.
  Le contrat `Dialect` reçoit donc `single_row_subquery()`, qui rend la **sous-requête entière** plutôt que deux morceaux à recoller.
  Deux primitives à lire en paire auraient reproduit le piège de `pagination_clause()` et `pagination_param_order()`, dont l'ordre des marqueurs s'inverse en T-SQL.
  Les quatre backends l'implémentent, et un test joue la sous-requête de chacun **contre son serveur**, par le chemin de requêtes de Forge : c'est ce pendant qui manquait pour que le défaut se voie.

- **Les quatre chapitres « Mise en service » des backends divergeaient (`REFERENCE-BACKENDS-SETUP-001`).**
  Constaté en jouant les 26 chapitres des pages de référence, ceux que 22 opt-ins font suivre à leur lecteur.
  `sqlite` s'arrêtait à `db:config` et ne créait jamais sa base : ses commandes `db:init` et `doctor` vivaient dans la prose, jamais dans un bloc, si bien qu'un lecteur qui copie les blocs repartait sans base de données.
  `postgres` et `mssql` mentionnaient `doctor` de la même façon, en prose seulement, et n'exécutaient jamais le SQL de provisioning que `db:init` se contente d'afficher (ADR-067).
  `mariadb`, le plus complet, allait jusqu'à `forge db:apply`, qui échoue sur `mvc/entities/relations.sql` introuvable tant qu'aucune entité n'est déclarée, ce qui est toujours le cas à ce stade.
  Les quatre suivent désormais la même séquence, amorcer, provisionner, vérifier, et se terminent sur `forge doctor` dont la ligne `Base de données` atteste que la mise en service est faite.
  Aucun n'applique de schéma, cette étape venant avec les entités.
  Un garde-fou fige les trois points sur les quatre backends à la fois.
  **Les 26 chapitres se déroulent désormais de bout en bout**, les trois backends serveur vérifiés contre MariaDB 11.8, PostgreSQL 17.10 et SQL Server 2022.

- **Le câblage généré par `opt-in:enable` ne passait pas la porte qualité du projet (`OPTINS-GENERATED-TYPING-001`).**
  Second défaut de la même famille, révélé en débloquant le premier.
  `opt-in:enable` écrivait `optins/<nom>/routes.py` avec `def register(router) -> None:`, paramètre non annoté.
  Le squelette livrant un pyright strict (ADR-063), `make typage` refusait donc le code que Forge venait d'écrire.
  La forme retenue n'est pas inventée : c'est celle que le `optins/registry.py` du squelette emploie déjà, un import gardé par `TYPE_CHECKING`.
  Deux générateurs de la même couche écrivaient deux conventions différentes.
  Les trois parcours de `audio`, `video` et `iot` se déroulent désormais de bout en bout, ce qui achève de les débloquer.

- **`optins/__init__.py` vivait en double, et les trois opt-ins routiers en pâtissaient (`OPTINS-INIT-SOURCE-UNIQUE-001`).**
  Le squelette en livrait une version, `cli/optins/enable.py` en portait une autre dans une constante.
  Les deux disaient la même chose, écrite différemment, 319 caractères contre 349, et elles avaient dérivé.
  La conséquence se voyait au premier geste sur un projet neuf. `forge new` posait sa version, puis `forge opt-in:enable <route> --apply` trouvait un fichier « existant avec un contenu différent », refusait d'écraser et sortait en erreur.
  `audio`, `video` et `iot`, les seuls opt-ins à recevoir la couche `optins/`, étaient donc inutilisables sur un projet neuf.
  Le refus d'écraser était **juste**, Forge ne réécrivant pas un fichier applicatif (principe 9) ; c'est la duplication qui était fautive.
  Une règle écrite deux fois finit écrite de deux façons, exactement comme la primitive CSV recopiée dans chaque contrôleur généré.
  La commande lit désormais le fichier du squelette au lieu de le redéfinir (principe 11), et le garde-fou interdit à la constante littérale de revenir.
  Constaté en jouant les chapitres « Mise en service » des références, qui échouaient tous les trois au même endroit.

- **Un projet neuf échouait à son propre `make check` (`SKELETON-PYTEST-PYTHONPATH-001`).**
  Constaté en jouant les chapitres « Mise en service » des références, dont 22 sur 26 font lancer `make check`.
  Sur un projet à peine créé par `forge new`, sans que rien n'y soit fait, la collecte s'arrêtait sur `ModuleNotFoundError: No module named 'mvc'`.
  La cause tenait à une différence que rien n'annonçait. `python -m pytest` insère le répertoire courant dans `sys.path`, le script console `pytest` ne le fait pas, et c'est ce dernier que le `Makefile` lance.
  Les tests passaient donc sous une forme et échouaient sous l'autre, ce qui rendait le défaut difficile à voir et facile à croire résolu.
  `pythonpath = .` dans le `pytest.ini` du squelette fait tenir les deux formes.
  Le motif est écrit à côté de la ligne, sans quoi elle passerait pour superflue au prochain nettoyage.
  Un garde-fou existait pourtant, mais il vérifiait que le `Makefile` **contient** ses cibles, sans jamais rien lancer.
  Le nouveau **exécute** pytest sur un projet reconstitué, dans les deux modes d'invocation, et vérifie en outre que le défaut revient si la ligne est retirée : un garde qui passerait aussi sans le correctif ne garderait rien.
  `lint`, `typage` et `docs` passaient déjà ; seule `test` échouait, c'est-à-dire la cible qui donne son sens à l'apparat qualité que l'ADR-063 fait livrer.
  **Les projets déjà créés ne sont pas rattrapés.** `forge skeleton:upgrade` ajoute les fichiers manquants mais ne réécrit jamais les vôtres (principe 9), et `pytest.ini` vous appartient dès qu'il existe.
  Il faut donc y ajouter `pythonpath = .` à la main ; la [FAQ](guide/faq.md) le rappelle avec le symptôme qui met sur la piste.

- **Un garde de fraîcheur pour les diagrammes UML des références (`DOC-UML-FRESHNESS-001`).**
  Chaque page de référence porte un chapitre « Schémas UML », soit 27 diagrammes de classe et 27 de séquence.
  Dessinés à la main, ils vieillissent en silence, et un schéma périmé garde l'autorité que donne un dessin.
  `tools/check_uml_diagrams.py` lit les diagrammes de classe et confronte au code, lu par AST et jamais importé, les classes et les méthodes qu'ils déclarent.
  Une périmption trouvée à la première exécution : le diagramme de `forge-mvc-sessions-db` attribuait `cleanup_expired()` au **protocole** `SessionStore` du cœur, qui ne le déclare pas.
  La méthode existe, mais sur `DbSessionStore` seulement, et c'est cohérent, purger des sessions périmées n'ayant de sens que pour un store persistant.
  Le diagramme montre désormais le contrat réel, et la page dit pourquoi la méthode le déborde.
  Le garde est **silencieux plutôt que criard**, et c'est un choix mesuré. Sa première version refusait douze acteurs conceptuels que les diagrammes ont le droit de dessiner, l'exécuteur injecté, la bibliothèque externe, le contrôleur du lecteur, la factory d'exemple.
  Un garde qui crie à tort finit désactivé, et ne garde alors plus rien.
  La limite est écrite dans l'outil : une classe **renommée** sort du contrôle au lieu d'être signalée, faute de pouvoir la distinguer d'un acteur conceptuel.

- **Le palier des fixtures reliées se déroule enfin (`WELCOME-FIXTURES-RELIEES-001`).**
  Il relie un `eleve` à un compte `users` sans coder d'`Id` en dur, mais ne préparait aucune des deux tables.
  Il était le dernier arrêt du parcours des fixtures, et il l'est resté tant que déclarer une entité avec ses champs exigeait un terminal ; les modes non interactifs livrés juste avant l'ont débloqué.
  La page pose désormais `make:auth`, `auth:init`, l'entité `Eleve` et `db:apply` avant d'échafauder sa factory.
  Elle précise aussi que `user_id` est ici un **entier ordinaire** et non un champ `foreign_key`, distinction dont dépend le nom de colonne que la factory doit employer, `UserId` contre `user_id`.
  Le parcours des fixtures passe de bout en bout, **dix-sept blocs, aucun saut, aucune substitution**.
  Vérifié au passage, exact au mot près : `self.reference()` produit bien la sous-requête que la page montre.

- **Le harnais pose le code des parcours et le compile (`WELCOME-CODE-PLACEMENT-001`).**
  Douze parcours sur vingt-sept n'ont **aucun** bloc `bash` : ils font écrire du code, puis se vérifient au navigateur.
  Leur code n'était donc soumis à rien, alors qu'il est précisément ce que le lecteur recopie.
  Le harnais lit désormais tous les blocs dans l'ordre du document, et non les seuls `bash`, ce qui revenait à jouer la moitié d'un dialogue, la commande lançant un fichier échouant faute de ce fichier.
  Un bloc qui nomme sa destination en première ligne est posé à sa place, convention déjà suivie par **187 des 279 blocs `python`** des parcours.
  Le nom peut être suivi d'une précision utile au lecteur, mais doit venir en premier, sans quoi toute phrase citant un module passerait pour un ordre d'écriture.
  Un fichier existant n'est **jamais** écrasé, et pas seulement par prudence : `mvc/routes/__init__.py` est nommé 92 fois dans les parcours, toujours pour un fragment à fusionner, et l'écrire entier détruirait le câblage posé par `forge new` (principe 9).
  Le code posé est ensuite compilé avec l'interpréteur du projet, ce qui ne prouve pas qu'il fonctionne mais prouve qu'il n'est pas périmé au point de ne plus se lire.
  État mesuré : **dix des douze parcours** voient leur code posé et compilé, de 1 à 10 fichiers chacun.
  Les deux autres restent sans couverture, `import-export` n'offrant que des extraits d'API sans fichier de destination, et `mail` aucun bloc de code dans son parcours.

- **Dix parcours d'opt-in joués, deux blocs qui piégeaient leur lecteur (`WELCOME-OPTINS-STEPS-001`).**
  Le parcours de `sessions-db` étiquetait `bash` une ligne de **crontab**, que le shell lit comme un appel à une commande nommée `0`.
  Celui de `testing` proposait `grep -r "forge_mvc_testing" mvc/   # ne doit rien retourner`, dont le succès est un **code retour 1**, `grep` sortant ainsi quand il ne trouve rien.
  Posé tel quel dans une intégration continue, ce bloc signalait un échec au moment précis où tout allait bien ; il prend désormais une forme qui sort en zéro quand la vérification passe.
  Neuf parcours sur dix se déroulent de bout en bout, le dixième, `iot`, n'ayant **aucun** bloc exécutable sans broker MQTT ni serveur lancé.
  Le harnais gagne quatre motifs de saut, tous constatés et non anticipés : un serveur local que le harnais n'a pas démarré, un service externe, un fichier que le lecteur écrit lui-même depuis un bloc `python`, et un diagnostic dont le code retour **est** le rapport.
  Ce dernier vise `deploy:check`, qui documente lui-même sortir en 1 dès qu'il trouve une erreur bloquante, comportement juste qu'il ne fallait pas prendre pour un parcours cassé.
  Le harnais annonce enfin **« rien joué »** au lieu de « de bout en bout » quand aucun bloc n'a tourné, un contrôle qui n'a rien contrôlé devant le dire.

- **Le déploiement supposait MariaDB sur les quatre backends (`DEPLOY-BACKEND-AGNOSTIC-001`).**
  Constaté en jouant le parcours de l'opt-in sur un projet SQLite.
  `forge deploy:check` cherchait le module `mariadb` et rendait une **erreur** quand il manquait, en conseillant de l'installer.
  Sur trois des quatre backends officiels, ce refus était donc faux, et il envoyait installer le pilote d'un SGBD que le projet n'emploie pas.
  L'unité systemd générée portait le même défaut avec `After=network.target mariadb.service`, soit un service inexistant sur PostgreSQL et SQL Server, et un service attendu là où SQLite n'a aucun serveur.
  Le cœur est agnostique et résout son backend par entry point (ADR-054) : la vérification pose désormais la même question que lui, ce qui la rend juste pour les quatre backends et pour tout backend tiers à venir.
  Elle distingue trois refus utiles, aucun backend, plusieurs backends, et un backend installé dont le pilote ne se charge pas, ce dernier étant le vrai cas que l'ancien contrôle visait sans savoir le nommer.
  L'unité systemd attend le service du backend résolu, et n'en attend aucun quand il n'y en a pas.

- **Les quatre parcours de backend supposaient trois états jamais établis (`WELCOME-BACKENDS-STEPS-001`).**
  Le même défaut, aux mêmes endroits, sur SQLite, MariaDB, PostgreSQL et SQL Server.
  Le moteur d'entités n'était cité nulle part, alors que `db:init`, `db:apply` et `migration:*` en viennent depuis l'ADR-070.
  `forge db:config` manquait, si bien que le backend ignorait où se connecter et que `db:init` refusait, à juste titre et avec un message excellent.
  Enfin `make:crud` était donné seul, alors qu'il consomme un contrat que seul `make:entity` crée.
  Chaque commande était juste prise isolément, et le manque n'existait qu'entre elles, ce qu'aucune relecture ne pouvait montrer.
  Les quatre parcours se déroulent désormais de bout en bout, **vérifiés contre des serveurs réels**, MariaDB 11.8, PostgreSQL 17.10 et SQL Server 2022.
  Un garde-fou fige les trois points sur les quatre backends à la fois, la répétition du défaut valant avertissement.
  Le harnais gagne au passage deux motifs de saut déclarés, `sudo` pour la session d'administration où le lecteur colle le SQL affiché par `db:init` (ADR-067), et `docker run` pour l'instance jetable que proposent les paliers avancés.

- **`forge make:relation` déclare une relation sans terminal (`ENTITIES-NON-INTERACTIVE-002`).**
  La commande était entièrement interactive, sans la moindre option.
  Or la contrainte de clé étrangère vient de `relations.json` (ADR-069), si bien qu'un modèle relationnel complet restait hors d'atteinte d'un script, de l'intégration continue et d'un agent, même après l'ouverture de `make:entity`.
  Donner `--from` et `--to` suffit à passer en mode non interactif, exiger un drapeau de plus ferait échouer la forme évidente sur un détail.
  Les deux cardinalités sont couvertes, avec `--name`, `--inverse-name`, `--on-delete`, puis `--foreign-key`, `--not-null` et `--no-index` en `many_to_one`, `--pivot-table`, `--from-key` et `--to-key` en `many_to_many`.
  Les défauts sont ceux du dialogue jusque dans leurs différences, `restrict` pour une clé étrangère et `cascade` sur un pivot.
  La ligne de commande vaut confirmation, redemander sans terminal rendrait le mode inutilisable ; le dialogue reste intact pour qui l'emploie.
  Vérifié de bout en bout sur un projet neuf, jusqu'aux contraintes réelles du pivot en base.

- **`forge make:entity` décrit enfin une entité entière sans terminal (`ENTITIES-NON-INTERACTIVE-001`).**
  `--no-input` ne posait qu'une entité minimale, aux champs imposés.
  Décrire ses propres champs exigeait donc un humain devant un dialogue, ce qui mettait la modélisation hors d'atteinte d'un script, de l'intégration continue et d'un agent, alors que Forge écrit lui-même la guidance des agents (ADR-047).
  Constaté en jouant le parcours des fixtures, dont le palier des fixtures reliées suppose une entité portant une clé étrangère.
  `--field "nom:type:attributs"` décrit les champs un à un, avec `--table`, `--timestamps` et `--soft-delete` pour le reste.
  Les attributs sont ceux du dialogue, `required` ou `optional`, `nullable`, `unique`, `max_length=N`, `precision=N` et `scale=N`, et **les défauts aussi**, sans quoi les deux modes produiraient des entités différentes pour la même intention.
  Ce que le dialogue exige, la ligne de commande l'exige de même, un `decimal` sans précision étant refusé des deux côtés.
  Deux types manquaient au générateur, tous deux adossés à un ADR. `slug` est canonique depuis l'ADR-017, `foreign_key` est un champ de première classe depuis l'ADR-069.
  La liste des types vivait en dur dans le générateur et avait dérivé, douze contre quatorze au schéma, si bien qu'aucun générateur ne savait produire ces deux types.
  Elle est désormais **lue du schéma canonique** (ADR-058), seule façon de ne plus diverger.
  Le champ déclare la colonne, au type de la clé primaire visée ; la contrainte reste portée par `relations.json`, conformément à l'ADR-069.

### Corrigé

- **`cryptography` n'est plus plafonné (`DEPS-CRYPTOGRAPHY-NO-CEILING-001`).**
  Quatre changements de borne depuis la bêta, aucun motivé par une rupture d'API : tous venaient d'un avis de sécurité, sur les majeures 42 à 50. Le plafond n'a jamais servi à ce pour quoi il existait.
  Il nuisait en revanche. Cette bibliothèque livre ses correctifs de sécurité dans une **nouvelle majeure**, jamais dans un correctif de la précédente, si bien qu'un plafond `<majeure+1` exclut le correctif au moment même de sa parution. Le plafond `<49` a été posé le 2026-06-24, alors que la 49.0.0 était sortie douze jours plus tôt : la borne naissait périmée.
  Tant qu'un plafond tient, un utilisateur de `forge-mvc-mfa` ne peut pas prendre le correctif amont même en le voulant, et attend une release de Forge. La fenêtre de vulnérabilité passe de l'amont à Forge, ce qui est le contraire du but recherché sur une bibliothèque de sécurité.
  `forge-mvc-mfa` étant une bibliothèque, son plafond cassait de surcroît la résolution de toute application ayant besoin d'une majeure plus récente pour une autre dépendance, sans recours possible.
  Ce que le plafond protégeait est tenu autrement. Une rupture d'API dans Fernet, seul usage de Forge, fait rougir l'aller-retour de `tests/test_mfa_secret_crypto.py` ; l'abandon d'un vieux Python par une majeure relève de `requires-python`, que pip respecte sans plafond ; et l'audit hebdomadaire a relevé les trois derniers avis en moins de vingt-quatre heures.
  La décision ne vise que cette dépendance, seule sans borne haute de `requirements-audit.txt`. L'étendre aux autres serait une décision distincte.

- **Trois avis de sécurité sur `cryptography` 48.0.1 (`DEPS-CRYPTOGRAPHY-50-001`).**
  Publiés le 2026-08-04, ils ont fait passer la CI de `main` au rouge en quelques heures, sans qu'aucun changement du dépôt en soit la cause.
  `CVE-2026-69248` permet de contourner les contraintes de noms X.509 : une autorité intermédiaire limitée à `foo.example.com` accepte une feuille portant le joker `*.example.com`.
  `CVE-2026-69249` provoque une explosion exponentielle sur une chaîne invalide contenant des copies d'un même certificat auto-signé.
  `CVE-2026-69247` est un oracle de déchiffrement PKCS#7 : l'issue du déchiffrement d'un `encryptedKey` était distinguable et révélait la longueur récupérée de l'opération RSA. C'est le seul des trois à exiger la 50.0.0, les deux autres étant corrigés en 49.0.0.
  Aucun ne touche le chemin de Forge, qui n'utilise que `cryptography.fernet.Fernet`, du chiffrement symétrique, sans X.509 ni PKCS#7.
  La borne monte quand même, de `>=48.0.1,<49` à `>=50.0.0,<51` : la dépendance est **expédiée** avec `forge-mvc-mfa`, et une application peut s'en servir pour tout autre chose que ce que Forge en fait.

- **Un projet mis à jour gardait une unité systemd figée sur MariaDB, sans le savoir (`DEPLOY-SYSTEMD-STALE-AFTER-001`).**
  `DEPLOY-BACKEND-AGNOSTIC-001` a rendu l'unité systemd dialectale, mais `deploy:init` écrit en write-if-new, et c'est juste : Forge ne réécrit pas un fichier du projet (principe 9).
  Un projet provisionné avant ce correctif garde donc son `After=network.target mariadb.service`, quel que soit son backend, et rien ne le lui disait.
  La panne qui en découle est discrète. Sous PostgreSQL, cet `After=` désigne un service inexistant, donc systemd ne retarde rien : au démarrage de la machine, l'application part avant sa base et rate ses premières connexions. Cela ne se produit qu'au boot, jamais en test, et ressemble à un défaut de Forge.
  `deploy:check` compare désormais la ligne `After=` de l'unité déjà écrite au service du backend résolu, et dit quoi éditer.
  C'est un avertissement, jamais une erreur, et Forge ne touche pas au fichier : l'unité appartient au projet.
  Il n'affirme rien quand aucun backend n'est résolu, la commande signalant déjà cette cause ailleurs. Deux messages pour une seule anomalie brouilleraient le diagnostic, et le second serait faux.
  SQLite est traité à part, n'ayant aucun service à attendre : une unité qui en nomme un y retarde le démarrage pour rien.

- **Le contrat de stabilité garantissait deux classes qui n'existent pas (`DOC-CITED-PATHS-001`).**
  `docs/release/stability-contract.md` engageait Forge sur des « backends de session FileStore / MariaDbStore ». Aucun des deux noms n'existe dans le code, où les stores s'appellent `FileSessionStore` et `DbSessionStore`.
  Le même document se contredisait sur leur statut. Il les déclarait « Disponible, API stable » dans son tableau du public, puis les rangeait plus bas parmi ce qui n'est **pas** garanti, comme « expérimentaux ». `release-policy.md`, que le contrat désigne lui-même comme source unique de la maturité, les classe en expérimental. Le contrat suit désormais sa propre source.
  Découvert en balayant le contrat plutôt qu'en corrigeant les deux lignes déjà repérées.
  Dans la même famille, dix-huit autres chemins cités en prose ne désignaient plus rien, dont sept dans les trois documents les plus engageants du projet, tous hérités de la refonte de l'ADR-039 et du découpage de `docs/reference.md` en onze fichiers. Un lecteur cherchant où sont documentées les clés d'environnement ou les commandes CLI garanties tombait sur un fichier absent.
  Ces mentions survivaient parce que `mkdocs build --strict` vérifie les liens Markdown et ne voit pas un chemin écrit entre dos-de-chat.
  Un garde-fou vérifie maintenant que tout chemin cité en prose désigne un fichier réel, hors archives : un ADR, une entrée de roadmap ou un ticket de campagne enregistrent ce qui était vrai à leur date, et corriger leurs chemins réécrirait le compte rendu qu'ils conservent.
  Il a aussitôt révélé qu'un garde plus ancien passait grâce au chemin mort lui-même. Il exigeait la sous-chaîne `reference.md` dans la page d'authentification, que seule satisfaisait la mention obsolète ; le vrai lien de « Voir aussi » ne la contient pas, si bien que le garde serait resté vert si ce lien avait disparu.

- **Soixante-cinq tests, dont les trente-trois d'en-têtes de sécurité, ne s'exécutaient plus depuis six versions (`E2E-LAUNCHER-APP-PATH-001`).**
  L'ADR-044 a relocalisé l'application de dogfooding hors de la racine du dépôt le 2026-06-23. `tests/_e2e_launcher.py` a continué de la chercher à la racine.
  Trois causes se sont additionnées pour rendre la panne muette. Le lanceur visait un fichier disparu. Son `stderr` partait dans `subprocess.DEVNULL`, si bien que le `FileNotFoundError` n'atteignait personne. Et l'absence du signal `READY:` se traduisait en `pytest.skip("Serveur Forge non disponible")`, formule qui décrit un poste local mal équipé plutôt qu'un défaut.
  Les trois fichiers concernés sautaient donc intégralement, en local comme en CI, sans que rien ne distingue leur silence d'une suite verte.
  Découvert en inspectant les motifs de saut lors du pré-mortem précédant la rc4, et non par un test rouge.
  Un `skip` est légitime quand l'environnement manque vraiment de quelque chose, une base par exemple. Ici l'application servie est dans le dépôt, donc son absence est toujours un défaut du harnais.
  Le chemin est résolu en un seul endroit, le `stderr` du lanceur est capturé et rendu, et les quatre fixtures échouent au lieu de se sauter.
  Les soixante-cinq tests passent tous, sans qu'aucun code de production n'ait eu à changer : ils étaient corrects, seulement inertes.
  Un garde-fou tient les trois causes et prouve par exécution que le harnais sert. Sa contre-épreuve a été mesurée en cassant volontairement le chemin, ce qui le fait bien rougir.

- **La sonde `GET /health` répondait 404 en production (`CORE-WSGI-HEALTH-PARITY-001`).**
  `GET /health` → `200 {"status": "ok"}` figure au contrat de stabilité comme surface publique garantie.
  Elle n'était pourtant servie que par le serveur de développement, qui la traitait par un littéral inscrit dans son `do_GET`.
  Le chemin WSGI, seul chemin de production supporté, ne la connaissait pas.
  Un opérateur qui branchait la sonde de son superviseur sur `/health` derrière Gunicorn obtenait une application déclarée morte alors qu'elle servait, et un redémarrage en boucle du seul composant qui allait bien.
  Trouvé en vérifiant par exécution le `curl` que la page de mise en production donne comme étape de validation, laquelle échouait donc depuis toujours.
  Le défaut a tenu parce que ses deux tests exercent le même serveur, l'un en appelant `do_GET`, l'autre en lançant `python app.py` en sous-processus.
  Aucun ne traversait le callable WSGI, si bien qu'une surface du contrat de stabilité était absente de la production sans qu'aucun garde ne puisse le voir.
  La réponse vit désormais dans `core/http/health.py`, source unique que tous les serveurs consomment (règle A) : il n'y a plus qu'un contenu, donc plus d'écart possible.
  Ils étaient trois, et non deux comme annoncé d'abord. L'application de dogfooding servie par les tests E2E gardait sa propre copie du littéral, restée invisible tant que ces tests étaient inertes. Réveillés par `E2E-LAUNCHER-APP-PATH-001`, ils valident ce fichier, si bien qu'une divergence y aurait fait passer au vert une sonde différente de celle qui est expédiée.
  Sept tests passent par le callable WSGI et par lui seul, dont un qui refuse qu'un littéral `{"status": "ok"}` revienne dans le squelette.
  La sonde reste sans effet de bord, ne touchant ni la base ni les sessions : une sonde qui interroge la base transforme une base lente en application déclarée morte.

- **`forge migration:make` sans nom rendait un `IndexError` (`ENTITIES-MIGRATION-MAKE-USAGE-001`).**
  Constaté en jouant le parcours du moteur d'entités, dont la page écrivait `forge migration:make` sans argument alors que le nom est obligatoire.
  Le code lisait `args[1]` sans vérifier, si bien qu'un argument oublié produisait `IndexError: list index out of range` en trace brute.
  Un argument manquant est une erreur d'usage, et appelle donc le rappel de l'usage avec un exemple.
  La page du parcours donne désormais un nom réel, et explique que ce nom devient celui du fichier de migration, à choisir comme un message de commit.

- **Une erreur d'environnement sortait en trace Python, pas en message (`CLI-ERROR-BOUNDARY-001`).**
  Mesuré en exécutant le parcours d'accueil SQLite dans un projet neuf, tel qu'un débutant le suit.
  `forge db:init` sans `DB_NAME` déroulait vingt lignes de trace avant d'arriver à la phrase utile, qui disait pourtant exactement quoi faire.
  Le message était juste, et `forge doctor` affichait déjà le même diagnostic proprement en `[WARN]`.
  Seule la frontière du CLI manquait, celle-ci ne rattrapant que `KeyboardInterrupt`.
  Une trace répond à « où Forge s'est-il trompé », et n'a rien à dire à qui a oublié un renseignement dans son env.
  Elle enterre au passage la seule ligne qui compte.
  La règle retenue tient en deux phrases.
  Les erreurs qui décrivent l'environnement de l'utilisateur sortent en message, sans trace ; tout le reste garde la sienne, parce qu'un `AttributeError` est un bug de Forge et que la trace en est le diagnostic.
  Deux familles seulement sont triées, les erreurs de base de données et de configuration de projet, et cette liste ne s'élargira que sur constat (règle B).
  Escamoter une trace sans recours serait de la magie cachée (principe 3), d'où `FORGE_TRACEBACK=1` qui la rend à qui la demande.
  Le contrat portable reçoit `DatabaseConfigurationError`, distincte de `DatabaseUnavailableError` puisque attendre résout l'une et jamais l'autre.
  Le backend SQLite levait un `RuntimeError` à deux endroits, indiscernable d'un bug ; le garde-fou écrit pour le premier a trouvé le second.
  Le même parcours a livré un second constat, traité ici aussi. `forge make:entity` interroge l'utilisateur, et l'entrée standard fermée rendait une trace finissant sur `EOF when reading a line`, sans que rien n'annonce que la commande était interactive.
  Elle dit désormais ce qu'elle attend, et oriente vers l'option non interactive que son aide expose.

- **La reprise de publication ne servait qu'une release, et le garde de complétude posait une question trop large (`RELEASE-PUBLISH-RESUME-GENERALIZE-001`).**
  PyPI limite la création de nouveaux projets, si bien qu'une release qui en introduit plusieurs se heurte à un 429 en cours de route et doit être relancée toutes les demi-heures.
  Un script posé en cron faisait ce guet, mais il portait `rc2` dans son nom, son journal, ses messages et sa ligne d'auto-retrait.
  Il aurait donc fallu le réécrire au moment précis où le 429 frappe, c'est-à-dire au plus mauvais moment pour écrire un script.
  La version se lit désormais dans `pyproject.toml`, seule source de vérité, et `tools/publish-resume.sh` sert toutes les releases à venir sans édition.
  Généraliser a révélé un trou dans `tools/check_pypi_completeness.py`.
  Celui-ci demandait « cette distribution a-t-elle été publiée un jour », alors que la question d'une release est « la version qu'on publie est-elle servie partout ».
  Une distribution restée en rc2 pendant que les vingt-sept autres passent en rc3 le satisfaisait donc, alors que la release est partielle et que personne ne peut épingler la nouvelle version.
  Le script de reprise posait bien cette question, mais dans son coin, avec sa propre lecture de PyPI, forcément divergente.
  Mesuré : elle comptait une version retirée comme installable, et déduisait les noms de distribution des noms de dossier.
  La question rejoint le garde sous `--version`, qui accepte les deux écritures d'une même version, SemVer pour les tags et PEP 440 pour les distributions.
  Le script de reprise l'appelle au lieu de relire PyPI (principe 11).
  Enfin, `tools/publish.sh` vérifie lui-même, après avoir publié, que PyPI sert bien la version pour les 28 distributions.
  Sans cet appel, la vérification dépendait de la mémoire de qui publie, aucune documentation ne portant la séquence.
  Un délai de réindexation ne doit pas faire crier le garde sur un envoi réussi, d'où trois tentatives espacées.

## [1.0.0-rc.3] - 2026-07-30

Troisième release candidate.
Elle porte trois cycles de pré-mortem sur la couche d'accès aux données et sur les opt-ins, une chaîne de publication qui vérifie enfin ce qu'elle publie, et le dernier scénario connu où un projet restait bloqué sans outil.
Les quatre backends de base de données sont éprouvés contre de vrais serveurs sous panne, saturation, concurrence et verrou, et la DML des opt-ins adossés à la base cesse de supposer MariaDB.

### Sécurité

- **Un saut de ligne dans un en-tête de réponse découpait la réponse (`CORE-HEADER-CRLF-001`).**
  Les valeurs d'en-tête partaient telles quelles vers le client.
  Or un `CR` ou un `LF` termine la ligne pour lui, qui lit la suite comme un nouvel en-tête, voire comme le début du corps.
  Il suffisait qu'une application reprenne une donnée utilisateur dans un en-tête, un nom de fichier en `Content-Disposition` ou une cible en `Location`, pour qu'un attaquant pose l'en-tête de son choix, `Set-Cookie` compris, ou fasse servir son propre corps de réponse.
  Mesuré sur la pile WSGI réelle, quatre charges sur quatre sortaient avec leur saut intact, sur les deux chemins de sortie.
  Forge **refuse** désormais la réponse plutôt que de retirer le caractère en silence, car retirer modifierait une donnée applicative sans le dire, et la norme HTTP n'admet aucun saut de ligne dans une valeur.
  La règle vit dans `core.security.headers`, source unique partagée par les deux émetteurs, et s'exécute avant la première ligne envoyée.
  Le serveur de développement émet ses en-têtes un par un, si bien que refuser après coup n'aurait servi à rien ; les cookies accumulés hors du dictionnaire d'en-têtes sont couverts aussi.

### Ajouté

- **Un ADR canonique pour le style rédactionnel de la documentation (`ADR-087`).**
  Forge imposait ces règles à sa documentation depuis longtemps, mais elles vivaient dans `CLAUDE.md` §2.1, une directive refondue à chaque version majeure, sans date ni motivation.
  Or l'ADR-082 fait poser dans **chaque projet** un `docs/adr/002-style-documentation.md` : Forge prescrivait donc à ses utilisateurs un ADR pour une règle qu'il s'appliquait sans ADR, et les deux énoncés avaient déjà divergé.
  L'ADR-087 devient la source unique de sept règles, dont une nouvelle, **au plus un deux-points par phrase**, qui attrape l'empilement de propositions dans une phrase à rallonge.
  `CLAUDE.md` y renvoie et cesse de les énoncer en double ; le gabarit projet déclare en dériver et reçoit la règle manquante.
  Deux règles se contrôlant sans ambiguïté, l'absence de tiret cadratin et l'unicité du deux-points, un **cliquet** les fige : le fonds existant est gelé en l'état, 67 et 71 fichiers, et ces listes ne peuvent que décroître. Aucune campagne de réécriture n'est imposée, aucune nouvelle infraction n'est admise.
  Les cinq autres règles relèvent du jugement : un contrôle approximatif produirait des faux positifs qui feraient désactiver l'ensemble.

### Corrigé

- **La validation de release portait sur le mauvais interpréteur (`RELEASE-VALIDATE-INTERPRETER-001`).**
  `tools/release-validate.sh` résolvait `python3` depuis le `PATH` et se contentait de vérifier qu'il existe.
  Or il en existe un sur toute machine, si bien que le script lancé sans venv actif validait l'interpréteur du système, où ni Forge ni l'outillage ne sont installés.
  Mesuré sur une validation réelle de la rc3, deux échecs sur trois étaient des faux positifs de cette nature.
  Le sens inverse est plus grave et n'avait pas encore été rencontré, un interpréteur portant une version ancienne de Forge donnant un feu vert sur autre chose que ce qu'on s'apprête à publier.
  Le script vérifie désormais que la **distribution** `forge-mvc` est installée, et non qu'un `import core` réussit, ce dernier passant depuis la racine du dépôt avec n'importe quel interpréteur.
  Il compare ensuite la version installée à celle du `pyproject.toml`, puis contrôle la présence de l'outillage qu'il appelle.
  Le garde s'exécute avant les étapes coûteuses, découvrir l'erreur après vingt minutes de tests étant sans intérêt.

- **La documentation d'installation des opt-ins donnait une commande qui ne fait rien (`DOC-OPTIN-INSTALL-PROCEDURE-001`).**
  Les pages de référence écrivaient `forge opt-in:enable <nom>`, or cette commande est en **dry-run par défaut** : sans `--apply`, rien n'est écrit. **19 références sur 22** donnaient donc une instruction qui laisse croire l'opt-in activé alors que `optins/registry.py` reste inchangé. Corrigé partout.
  Deux des cinq gestes de mise en service n'étaient documentés **nulle part** : l'épinglage dans `requirements.txt`, sans lequel l'opt-in n'existe que sur la machine qui l'a installé, et la preuve par un premier usage réel. La procédure canonique en cinq points vit désormais dans `docs/install/opt-ins.md`, et les 22 références y renvoient au lieu de la redire.
  La référence RBAC faisait par ailleurs **copier trente lignes de `CREATE TABLE ... ENGINE=InnoDB`** à la main, syntaxe propre à MariaDB, alors que `rbac:init` existe depuis le chantier du DDL dialectal et produit un DDL portable sur les quatre backends. Elle donne maintenant la commande.
  **Les quatre backends de base de données ne mentionnaient pas non plus l'épinglage**, alors que c'est chez eux qu'il est le plus vital : sans pilote épinglé, un collègue ou un serveur qui installe depuis `requirements.txt` démarre sans backend et l'application n'atteint aucune base. Les quatre pages le documentent désormais, à leur étape 1.
  Enfin, les **26 références concernées** reçoivent un **chapitre « Mise en service » distinct de l'installation**. Le chapitre d'installation répond à « comment obtenir le paquet » ; il ne répondait pas à « que me reste-t-il à faire pour que ça marche ». Le nouveau chapitre décline les cinq points avec les commandes **propres à chaque opt-in**, dérivées du catalogue et du code : son type, sa commande `:init` s'il a des tables, son mode de branchement.
  Les quatre backends de base de données sont concernés au même titre : leur séquence propre, `db:config`, accès, `db:init`, `doctor`, **est** une mise en service, et elle était noyée dans le chapitre d'installation. Elle en a été **déplacée**, pas dupliquée. Seul `forge-mvc-testing` reste sans ce chapitre, une infrastructure de développement n'ayant rien à mettre en service.
  Le cycle de vie occupe désormais **trois chapitres distincts** au lieu de deux : « Installation » ne porte plus que l'obtention du paquet, « Mise en service » ce qui le rend opérationnel, et un nouveau chapitre « Désinstallation » son retrait, placé après la mise en service. `forge-mvc-entities`, qui ne documentait pas du tout sa désinstallation, en reçoit une, avec la précision qui compte : retirer le moteur laisse en place vos contrats d'entités, le code généré et les migrations appliquées, qui vous appartiennent (principe 4).
  L'avertissement sur `externally-managed-environment` (PEP 668) était enfermé dans le seul onglet « Depuis Git », sur les **27** références. Or le verrou ne dépend pas du canal d'installation mais de l'endroit où `pip` s'exécute : la commande de l'onglet PyPI le heurte tout autant, et c'est l'onglet affiché par défaut. L'avertissement sort des onglets, passe **avant** eux et devient un **prérequis** donnant la commande d'activation du venv, plutôt qu'un dépannage lu après l'échec.
  **Les blocs à onglets d'installation sont remplacés par des sous-titres.** Lu dans le code du thème : chaque étiquette d'onglet voit son contenu remplacé par un lien `<a href="#__tabbed_1_2">`, et le fragment d'URL sélectionne l'onglet en retour. Cliquer un onglet écrit donc ce fragment dans l'URL ; comme il désigne un élément situé dans un bloc repliable, le navigateur déplie et fait défiler pour le révéler. Le chapitre d'installation s'ouvrait ainsi tout seul, à chaque changement d'onglet.
  Deux sous-titres, « Depuis PyPI » et « Depuis Git », suppriment le mécanisme au lieu d'en contourner les effets. Ils montrent en outre les deux canaux d'un coup, se trouvent au `Ctrl+F` et s'impriment, ce qu'un onglet ne permet pas.
  Les deux canaux sont lettrés **A** et **B**, précédés de « Deux canaux, au choix » placé **après** le prérequis, qui vaut pour les deux. Cette annonce ne figurait auparavant que dans **une** référence sur 27 : les 26 autres enchaînaient sur le premier canal sans dire qu'il en existait un second.
  La conversion a révélé un doublon : 22 chapitres d'installation reprenaient `opt-in:enable` et les commandes `:init`, désormais portées par la mise en service. Placés après le canal Git, ils se lisaient de surcroît comme s'ils lui étaient propres. Retirés du chapitre 2, où seule reste l'obtention du paquet.
  Un garde-fou fige l'ensemble, dont l'interdiction de documenter `opt-in:enable` sans `--apply`, celle de faire copier du DDL à la main, l'obligation pour **les 27 paquets** d'indiquer leur épinglage, la présence du chapitre de mise en service et la continuité de la numérotation des chapitres.

- **La neutralisation de l'injection CSV rejoint le cœur (`CRUD-CSV-ESCAPE-CORE-001`).**
  `make:crud` **recopiait** dans chaque contrôleur sa défense contre l'injection de formule CSV. Mesuré sur une application réelle de 50 entités : **36 exemplaires identiques**.
  Deux défauts en un. La règle était **incomplète** : elle n'examinait que le premier caractère, alors qu'un tableur ignore une tabulation ou un retour chariot de tête, si bien que `"\t=1+1"` s'ouvrait comme la formule `=1+1`. Et elle était **incorrigible** : Forge ne réécrit jamais le code utilisateur (principe 9), donc aucune correction n'atteignait les fichiers déjà générés.
  La règle vit désormais dans `core.security.csv_export.escape_csv_field`, que le contrôleur généré **appelle**. Un `pip install --upgrade` corrige toutes les applications. Un garde-fou interdit désormais à tout générateur de recopier une primitive de sécurité.

- **`make:auth` ne met plus de SQL dans le contrôleur (`MAKE-AUTH-MODEL-LAYER-001`).**
  Le scaffold d'authentification portait sa requête `SELECT ... FROM users` directement dans le contrôleur généré, en contradiction avec la séparation que `make:crud` produit et que la documentation Forge enseigne. Un générateur ne peut pas prescrire une doctrine qu'il enfreint.
  `make:auth` génère désormais `mvc/models/user_model.py`, qui porte `load_user_by_email` ; le contrôleur l'importe. Le SQL y reste visible et paramétré (principe 5).

- **Plus aucune référence au défunt `mvc/routes.py` (`DOC-ROUTES-PACKAGE-REFS-001`).**
  L'ADR-068 a remplacé ce fichier par le package `mvc/routes/`, mais **194 références** au chemin disparu ont survécu dans 107 fichiers. Trois d'entre elles étaient des **messages affichés à l'utilisateur** par `forge module:routes`, l'invitant à éditer un fichier inexistant ; les autres vivaient dans le squelette, sa suite de tests, la documentation du routeur et les parcours d'apprentissage de quinze opt-ins.
  L'exemple minimal du README était doublement périmé : il citait le chemin disparu **et** enseignait la forme `routes = [...]` que le cœur ne connaît plus ; il montre désormais `Router()` et ses groupes.
  Les archives sont préservées : `docs/history/`, les ADR et `docs/roadmap/` décrivent l'état de leur époque.

- **Le garde de release audite enfin ce que Forge livre (`RELEASE-AUDIT-SHIPPED-SURFACE-001`).**
  `tools/release-validate.sh` auditait `requirements.txt`, soit les **quatre** dépendances du cœur, en ignorant `requirements-audit.txt` qui agrège la surface réellement expédiée (Pillow, cryptography, psycopg, pyodbc...) — précisément celles qui portent des CVE. Le fichier existait pour cela, mais le garde ne le lisait pas.
  Son verdict pytest se lisait par ailleurs dans le **texte** de sortie. Mesuré : une suite ne collectant aucun test affiche « no tests ran », que l'ancien motif comptait comme réussi, alors que pytest sort en **code 5**. Une erreur de configuration pouvait donc laisser passer une release **sans qu'un seul test ait tourné**. Le verdict vient désormais du code retour, avec un message propre au cas « aucun test collecté ».

- **Bornes de dépendances : Pillow relevé, mariadb en plage (`DEPS-PILLOW-FLOOR-001`, `DEPS-MARIADB-PIN-RANGE-001`).**
  La borne `Pillow>=10.3` autorisait des versions vulnérables sans que l'audit s'en aperçoive, celui-ci résolvant vers la borne haute. Mesuré avec `pip-audit` : 10.3, 11.0, 11.3, 12.0 et 12.2 portent des avis, **tous corrigés en 12.3.0**, première version propre. La borne devient `Pillow>=12.3,<13`, ce qui tranche l'arbitrage par la mesure plutôt que par estimation.
  `mariadb==1.1.14` figeait une version portant `PYSEC-2026-217`, avis sans correctif amont, exclu de l'audit. La dépendance devient `mariadb>=1.1.14,<1.2` pour accueillir le correctif sans changer le contrat.
  Surtout, une exclusion `--ignore-vuln` est une **dette** : sans surveillance, elle survit à la publication du correctif et masque une vulnérabilité réparable. Le nouveau `tools/check_ignored_vulns.py` relit l'audit **sans** les exclusions et échoue dès qu'un avis ignoré annonce une version corrective. C'est la **seule étape bloquante** de l'audit hebdomadaire, par ailleurs informatif, et elle est rejouée à chaque validation de release. Un garde-fou vérifie qu'aucun `--ignore-vuln` posé ailleurs n'échappe à cette surveillance.

- **Le serveur de développement honore les réponses en flux (`SKELETON-DEVSERVER-STREAM-001`).**
  `Response.file()` (HTTP Range, `CORE-HTTP-FILE-RANGE-001`) laisse `body` vide et pose `stream` plus `content_length`. Le chemin WSGI le gérait depuis l'origine ; `_send_response` du serveur de développement annonçait `len(body)`, soit **0**, et n'écrivait jamais le flux.
  Mesuré sur un fichier de 5000 octets : `Content-Length: 0` et **zéro octet écrit**. Tout téléchargement, toute lecture vidéo ou audio et tout `/media/` étaient donc servis **vides** en développement, sans la moindre erreur. Le contrat Range du cœur était correct mais inobservable par un développeur.
  Le serveur suit désormais le contrat du chemin WSGI, et une déconnexion du client en cours d'envoi est tracée plutôt que remontée : les en-têtes sont déjà partis, il n'y a plus de réponse d'erreur possible.
  Test de bout en bout sur une socket réelle, requête `Range` comprise : `200` complet, `206` avec `Content-Range`, `416` hors limites.

- **Un jeu de caractères inconnu ne fait plus tomber une requête multipart (`CORE-MULTIPART-CHARSET-001`).**
  Le décodage d'un champ multipart utilise le jeu de caractères **déclaré par le client**. `bytes.decode()` lève `UnicodeDecodeError` sur des octets invalides, mais `LookupError` sur un encodage inconnu, et seule la première était interceptée.
  N'importe quel client pouvait donc provoquer une **500** en envoyant `charset=charset-bidon` dans une part de formulaire, sans authentification. Le champ indécodable vaut désormais la chaîne vide, comme toute valeur illisible. Un jeu de caractères légitime non UTF-8 continue de se décoder : le correctif n'est pas un repli systématique.

- **`fixtures:load` charge dans une transaction unique (`FIXTURES-LOAD-SINGLE-TX-001`).**
  Chaque instruction s'exécutait sur sa propre connexion. Deux conséquences, mesurées : un échec à mi-parcours laissait la base **à moitié peuplée**, sans rien pour revenir en arrière ; et `--no-fk-checks` était **sans effet**, la désactivation des contraintes étant une variable de session, donc propre à une connexion aussitôt rendue au pool, quand les insertions suivantes repartaient sur d'autres connexions. Rien ne le signalait.
  Le chargement suit désormais le modèle de la purge (F52-bis) : une transaction, une connexion, `tx` propagé jusqu'aux fixtures Python.
  **Rupture d'API dans `forge-mvc-fixtures`** : `Fixture.load()` prend `tx`, comme `purge()` depuis F52-bis. L'asymétrie était l'anomalie. Écrivez `def load(self, *, tx=None)` et propagez `tx` à vos `db.execute`. Une fixture qui ne l'accepte pas est **refusée avec un message qui indique la correction**, plutôt que d'être appelée sans `tx` : un repli silencieux sortirait ses écritures de la transaction sans le dire.

- **Trois accrocs du parcours d'utilisation (`USAGE-JOURNEY-GAPS-001`).**
  Trouvés en déroulant le parcours documenté de bout en bout sur un vrai serveur, avec de vrais comptes séparés.
  **`build:model` exigeait `relations.json`**, alors qu'`entity:validate` le déclarait « optionnel », que le squelette ne le livre pas et que seul `make:relation` l'écrit. Un projet à une entité **sans relation**, le cas le plus courant au premier jour, ne pouvait pas franchir cette étape. L'absence vaut désormais « aucune relation », et `sync:relations` s'aligne.
  **`db:config` écrivait hors d'un projet Forge**, posant ses fichiers dans n'importe quel dossier, quand `db:init` refuse ensuite d'y travailler faute de `config.py`. Il exige maintenant le même projet, et n'écrit rien sinon.
  **`forge doctor` rassurait à tort** : son contrôle de base était codé en dur en avertissement, avec le message « normal avant configuration ou db:init », même sur un projet configuré et migré. Seul avertissement, il laissait `doctor` **sortir en 0**, donc un contrôle de déploiement passer avec une base morte. Sur un projet dont les accès sont renseignés, l'échec devient une **erreur** et le message oriente le diagnostic ; un projet non configuré garde son avertissement.

- **Injection SQL par antislash dans les littéraux MariaDB (`MARIADB-LITERAL-BACKSLASH-001`).**
  MariaDB est le **seul** des quatre backends où l'antislash échappe dans un littéral : `NO_BACKSLASH_ESCAPES` y est désactivé par défaut. Le rendu ne doublait que l'apostrophe, ce que prescrit la norme SQL et qui suffit à PostgreSQL, SQLite et SQL Server.
  Deux trous, mesurés sur serveur réel. Une valeur terminée par un antislash échappait le guillemet fermant et cassait l'instruction. Et `a\' OR 1=1 -- ` refermait la chaîne : **la suite devenait exécutable**, le serveur évaluait la condition et rendait `1`.
  **Surface** : le SQL écrit dans des **artefacts** (ADR-075), fixtures générées et valeurs par défaut de DDL, à partir de données contenant un antislash. Le chemin de requête ordinaire n'est pas concerné, il passe par des paramètres liés.
  Le correctif vit dans le dialecte MariaDB, non dans le cœur, qui implémente correctement la norme pour les trois autres backends. Vérifié sur les trois serveurs : eux rendaient la charge intacte.

- **Une file d'attente devant le pool de connexions MariaDB (`MARIADB-POOL-QUEUE-001`).**
  Le pilote MariaDB n'offre **aucune** file : son `get_connection()` lève dès que toutes les connexions sont prises. Mesuré avec le pool par défaut de cinq et une lecture indexée de 0,26 ms, **145 requêtes sur 200 arrivées au même instant échouaient**, alors qu'attendre une fraction de milliseconde suffisait.
  Ce n'était pas un problème de capacité : cinq connexions servent près de 19 000 requêtes par seconde. C'était l'absence de file.
  Un sémaphore aux jetons du pool la rétablit. Il en fallait un vrai : mesuré, une simple boucle de réessais **aggrave** la situation, 200 emprunteurs interrogeant le pool en boucle se disputant son verrou (170 échecs contre 146 sans attente). Après correctif, **500 requêtes simultanées sont toutes servies**, en 0,17 seconde.
  L'attente est bornée par `DB_POOL_TIMEOUT` (5 s). Au delà, la nouvelle `DatabaseUnavailableError` du cœur est levée et traduite en **`503` avec `Retry-After`**, non en `500` : une saturation est passagère, et un 500 enverrait chercher un bug dans le code là où le remède est d'élargir `DB_POOL_SIZE`.
  Le 503 ne dépend pas d'un gabarit : `errors/503.html` rejoint le squelette, mais aucun projet existant ne le recevra (principe 9), et `_html` **rend une 500** quand un gabarit manque au lieu de lever. La réponse teste donc le statut obtenu et retombe sur un corps en texte brut.
  `DB_POOL_SIZE` et `DB_POOL_TIMEOUT` sont enfin documentés, avec leur règle de dimensionnement : la référence du paquet n'en disait pas un mot.

- **Le diff de schéma était faux sur tout booléen MariaDB (`MARIADB-BOOLEAN-FAMILIES-001`).**
  MariaDB accepte `BOOLEAN` à la déclaration et **stocke** `TINYINT(1)`, que l'introspection rapporte. Le dialecte rangeait `TINYINT` dans les entiers avant de tester les booléens : les deux faces d'un même type physique rendaient donc des familles différentes.
  `forge migration:diff` signalait en conséquence une différence sur **chaque colonne booléenne** d'une base MariaDB, et `migration:make --from-diff` refusait alors de produire quoi que ce soit en criant au « diff risqué ».
  Le dialecte rend désormais `("int", "bool")` pour `BOOLEAN` comme pour `TINYINT(1)`, sur le modèle de `forge-mvc-sqlite` dont l'`INTEGER` le faisait déjà. Un `TINYINT` sans largeur reste un entier.
  Le défaut avait échappé à la livraison du diff par familles parce que le serveur MariaDB n'était pas joignable : la validation avait porté sur SQLite, PostgreSQL et SQL Server seulement. **MariaDB rejoint le test d'or sur serveur réel**, dont l'échantillon gagne une colonne booléenne ; vérifié qu'il échoue sans le correctif.
  Effet de bord assumé : un contrôle de validation refusait `TINYINT(1)` avec `python_type='bool'`, pour pousser vers l'alias `BOOLEAN`. Ce refus était propre à MariaDB, SQLite acceptant déjà `INTEGER`. Un contrôle de compatibilité doit dire ce qui est **possible**, pas ce qui est préféré ; la préférence reste portée par le générateur et la documentation.

- **Le diff de schéma compare des familles de types, plus des chaînes (`ENTITIES-DIFF-TYPE-FAMILIES-001`).**
  `forge migration:diff` confrontait deux **chaînes** de types. Hors MariaDB elles ne coïncident jamais : l'introspection de PostgreSQL rend `character varying` là où le générateur écrit `VARCHAR(255)`, et SQL Server `NVARCHAR` sans longueur. La commande déclarait donc **chaque colonne modifiée** sur une table pourtant conforme, et `migration:make --from-diff` refusait de produire quoi que ce soit en criant au « diff risqué ».
  Trois défauts distincts, corrigés ensemble : la comparaison porte désormais sur la **famille** du type, que le contrat `Dialect` exposait déjà, puis sur ses arguments ; l'introspection de PostgreSQL et de SQL Server recompose la **longueur**, publiée par `information_schema` dans une colonne séparée ; SQLite ne rapporte plus sa clé primaire comme nullable, `PRAGMA table_info` annonçant `notnull = 0` sur un `INTEGER PRIMARY KEY` dont il refuse pourtant les NULL.
  Deux arguments ne départagent que si les **deux** côtés en portent : un type sans parenthèses n'apprend rien sur la longueur de l'autre, et le signaler créerait une différence là où il n'y en a pas.
  Test d'or sur serveurs réels : une table créée depuis le DDL généré donne un diff **vide** sur SQLite, PostgreSQL et SQL Server. Contrôle négatif au même endroit, tout aussi important : une longueur, une famille ou une nullabilité qui diffèrent restent détectées, le correctif ne rendant pas le diff aveugle.

- **L'introspection de PostgreSQL et de SQL Server se borne au schéma courant (`DB-INTROSPECTION-SCHEMA-FILTER-001`).**
  `introspect_columns` ne filtrait que sur le **nom** de la table. `information_schema` exposant toutes les tables visibles de la base, une homonyme dans un autre schéma faisait remonter ses colonnes en plus des bonnes, **entrelacées** par la position ordinale.
  Mesuré sur serveurs réels, pour une table de deux colonnes et une homonyme de trois : l'introspection rendait `['id', 'autre_a', 'autre_b', 'titre', 'autre_c']`. Le diff de migration voyait donc des colonnes fantômes et proposait de les supprimer.
  PostgreSQL filtre désormais par `table_schema = current_schema()`, SQL Server par `TABLE_SCHEMA = SCHEMA_NAME()`, celui-là même que résout `OBJECT_ID` sur un nom non qualifié. MariaDB filtrait déjà par `TABLE_SCHEMA` ; SQLite n'a pas de schémas.

- **Les cinq opt-ins qui bornaient leurs lectures en MySQL suivent le dialecte (`OPTIN-RUNTIME-PAGINATION-DIALECT-001`).**
  Suite immédiate du ticket ci-dessous, sur le SQL que les opt-ins **exécutent** et non sur du code généré : `forge-mvc-admin`, `forge-mvc-audit`, `forge-mvc-iot`, `forge-mvc-mail` et `forge-mvc-notifications` écrivaient `LIMIT ?`, donc échouaient sur SQL Server à chaque lecture bornée.
  Le contrat `Dialect` reçoit `limit_clause()`, distincte de `pagination_clause()` : elle ne porte qu'un paramètre, donc aucun ordre à consulter. SQL Server reçoit `OFFSET 0 ROWS FETCH NEXT ? ROWS ONLY`, les trois autres gardent `LIMIT ?`.
  **Rupture d'API publique dans `forge-mvc-iot`** : les constantes `SELECT_IOT_EVENTS_RECENT_SQL` et `SELECT_IOT_EVENTS_BY_DEVICE_SQL` deviennent les fonctions `select_iot_events_recent_sql()` et `select_iot_events_by_device_sql()`. Même raison que la suppression des `CREATE_TABLE_SQL` : une constante figée à l'import ne peut plus être correcte quand le SQL dépend d'un backend résolu à l'exécution. Ces lectures restent publiques et lisibles, conformément au principe 5. `COUNT_IOT_EVENTS_BY_DEVICE_SQL` reste une constante : ne bornant rien, elle ne dépend d'aucun dialecte.
  Vérifié sur un serveur SQL Server réel : les six requêtes réellement produites par les cinq opt-ins s'exécutent, là où l'ancienne forme est rejetée avec « Incorrect syntax near 'LIMIT' ».

- **La pagination du CRUD généré suit le dialecte (`ENTITIES-CRUD-PAGINATION-DIALECT-001`).**
  Le modèle généré assemblait sa pagination en `LIMIT ? OFFSET ?`, syntaxe MySQL codée en dur. **T-SQL ne connaît pas `LIMIT`** : tout CRUD généré sur SQL Server échouait dès qu'il listait des enregistrements, alors que l'ADR-084 promeut ce backend au niveau plein. Mesuré sur un serveur réel, l'ancienne forme est rejetée avec « Incorrect syntax near 'LIMIT' ».
  La clause rejoint le contrat `Dialect`, avec `pagination_clause()` et `pagination_param_order()`. SQL Server reçoit `OFFSET ? ROWS FETCH NEXT ? ROWS ONLY` ; MariaDB, SQLite et PostgreSQL gardent `LIMIT ? OFFSET ?`, au caractère près.
  **Les deux méthodes vont par paire** : T-SQL annonce le décalage **avant** le nombre de lignes, donc une clause lue sans son ordre produirait une pagination inversée, silencieuse et fausse. Le générateur les lit ensemble, sur le même dialecte.
  Vérifié de bout en bout sur SQL Server et SQLite : à `offset=3, limit=3`, la requête générée rend bien les lignes 4 à 6. Le garde-fou contrôle le **comportement** de la requête, pas seulement le texte émis.

  À signaler, découvert au balayage et **volontairement laissé hors périmètre** : cinq opt-ins écrivent la même syntaxe MySQL dans leur SQL d'exécution, `forge-mvc-admin`, `forge-mvc-audit`, `forge-mvc-iot`, `forge-mvc-mail` et `forge-mvc-notifications`. La plupart utilisent `LIMIT ?` sans décalage, cas que le trait posé ici ne couvre pas encore. Suivi par `OPTIN-RUNTIME-PAGINATION-DIALECT-001`.

### Ajouté

- **Les générateurs décident d'après la nature du champ, plus d'après un nom de type SQL (`OPTIN-SQL-TYPE-BRANCHING-001`).**
  Correctif de l'audit `OPTIN-SQL-TYPE-BRANCHING-AUDIT-001`, voie « décider à partir du type Forge ».
  Le code testait des préfixes de types (`VARCHAR`, `TEXT`, `LONGTEXT`, `DATE`), qui appartiennent au dialecte. Sur SQL Server, dont les types commencent par `NVARCHAR`, aucune condition n'était vraie et **la fonctionnalité disparaissait sans la moindre erreur**.
  Effets corrigés, mesurés : le CRUD généré retrouve sa recherche `LIKE`, ses `textarea` et ses libellés de relation sur SQL Server ; les filtres de liste sont de nouveau acceptés sur SQLite et SQL Server.
  **Deux défauts de plus que l'audit n'avait listés** ont été trouvés en corrigeant : un champ de formulaire `date` était refusé sur SQLite, et `datetime` sur SQLite comme sur SQL Server.
  Le résolveur propage désormais `forge_type`, la nature Forge du champ, et expose trois prédicats consommés par les générateurs : `is_long_text`, `is_text_like`, `is_list_filterable`. Cela va dans le sens de l'ADR-086, dont le ticket 2 prévoit exactement des accesseurs canoniques à la place des clés du dict interne.
  Le repli `"BIGINT UNSIGNED"` de `make_crud` devient `dialect.identity_storage_type()`.
  **Les fichiers d'entité au format legacy V1 gardent leur comportement d'origine** : n'ayant pas de nature déclarée, ils continuent d'être jugés sur leur type SQL, ce qui est exact pour eux puisqu'ils datent de l'époque mono-backend. Le double régime est explicite dans le code.

- **`mail` et `stats` passent au DDL dialectal (`OPTIN-DDL-MAIL-STATS-001`) : le chantier de portabilité du DDL est terminé.**
  Les deux derniers `CREATE TABLE` MariaDB écrits en dur, jamais repérés par l'audit initial qui ne scannait que les fichiers `.sql`, sont remplacés par une déclaration rendue pour le backend installé.
  Le champ `status` de `mail_log` portait un `ENUM('sent', 'failed', 'skipped')`, type que ni SQLite ni SQL Server ne connaissent et que PostgreSQL n'offre qu'au prix d'un `CREATE TYPE` séparé. Il devient une chaîne courte, comme le `status` de `forge-mvc-jobs` : la valeur est produite par le code, pas saisie par un utilisateur.
  Sur MariaDB et pour les nouveaux projets, la colonne `metadata` de `forge_stats_events` passe de `JSON` à `LONGTEXT`, mapping propre au dialecte ; elle devient `JSONB` sur PostgreSQL, ce qui est meilleur.
  **Le garde-fou de portabilité n'a plus aucune entrée** : il cesse d'être un cliquet pour devenir un invariant absolu, aucun paquet ne livrant plus de SQL propre à MariaDB.

  À signaler, découvert en élargissant le scan et **volontairement laissé hors périmètre** : cinq modules branchent sur des noms de types MariaDB (`LONGTEXT`, `UNSIGNED`) pour décider d'un comportement, par exemple choisir un widget de formulaire. Sur PostgreSQL ces noms n'apparaissent jamais, donc la branche ne se déclenche pas. C'est une famille de défaut distincte de l'émission de DDL, qui mérite son propre audit ; elle est documentée dans le garde-fou.

### Retiré

- **Suppression des constantes `CREATE_TABLE_SQL` (`OPTIN-DDL-CONSTANTS-001`), rupture d'API publique.**
  `forge-mvc-jobs`, `forge-mvc-audit`, `forge-mvc-settings` et `forge-mvc-notifications` exposaient chacun une constante portant le DDL de leur table, écrit en MariaDB.
  Leur documentation présentait explicitement **deux** chemins pour créer la même table, « `CREATE_TABLE_SQL` **ou** `forge <opt-in>:init` », ce que le principe 11 proscrit. Aucun code applicatif ne les exécutait.
  Une constante ne pouvait par ailleurs plus être correcte : le DDL dépend du backend, résolu à l'exécution.
  **Chemin unique désormais** : `forge <opt-in>:init` écrit la migration rendue pour le backend installé, puis `forge migration:apply` l'applique.
  Le SQL reste visible, et il l'est même mieux : il est relu dans `mvc/migrations/` **avant** d'être appliqué, au lieu d'être imprimé depuis une constante.
  Les quatre parcours welcome gardent leur section sur la visibilité du schéma, recentrée sur la migration rendue.
  Rupture assumée sans alias déprécié, conformément à la convention pré-1.0 du dépôt, et avant publication : rc2 reste la dernière version publiée.

### Corrigé (suite)

- **Le moteur d'entités ne pose plus de SQL MariaDB en dur (`OPTIN-DDL-ENTITIES-001`).**
  `db_init.py` portait une constante `FORGE_MIGRATIONS_TABLE_SQL` doublon **caractère pour caractère** de `Dialect.forge_migrations_ddl()`, que le contrat rendait déjà : `forge db:init` produisait donc un registre de migrations inexécutable sur trois backends, alors que le rendu correct était à portée d'appel. Remplacée par `forge_migrations_table_sql()`, fonction et non constante puisque le DDL dépend du backend résolu à l'exécution.
  `migrations.py` ajoutait le mot-clé `AUTO_INCREMENT` sans condition dans le chemin de diff (`migration:make --from-diff`), produisant du SQL invalide sur PostgreSQL et SQL Server où l'auto-incrément est porté **par le type**. Le contrat gagne `Dialect.auto_increment_clause()`, qui rend le mot-clé sur MariaDB et une chaîne vide ailleurs.
  Le gabarit de migration vierge montrait en exemple une colonne à la syntaxe MariaDB : il enseignait du SQL invalide à un projet PostgreSQL. Il est rendu pour le backend actif.

- **Cliquet de portabilité rendu précis (`OPTIN-DDL-GUARD-RATCHET-001`, suite).**
  Le scan Python passait le fichier en majuscules, si bien que l'identifiant ordinaire `auto_increment` (nom de champ, clé de dictionnaire) déclenchait le garde-fou : un faux positif sur du code parfaitement portable.
  Seules les **chaînes littérales** sont désormais inspectées, à la casse exacte. Le SQL de ce dépôt écrit ses mots-clés en majuscules, les identifiants Python en minuscules : la casse suffit à discriminer. Vérifié dans les deux sens, y compris qu'un vrai `CREATE TABLE` MariaDB déposé dans un paquet fait toujours échouer la suite.

- **`forge iot:doctor` diagnostique enfin les quatre backends (`OPTIN-DDL-IOT-DOCTOR-001`).**
  Son contrôle de schéma interrogeait `INFORMATION_SCHEMA` par une requête écrite en dur, que SQLite ne possède pas, et comparait le résultat à des types MariaDB figés (`BIGINT UNSIGNED`, `DATETIME(6)`).
  Il signalait donc comme « type inattendu » un schéma PostgreSQL pourtant correct : un outil de diagnostic qui se trompait sur trois backends sur quatre.
  L'introspection passe désormais par `Dialect.introspect_columns`, et les attentes sont dérivées de la déclaration `forge_mvc_iot.tables` plus le dialecte actif. Vérifié sur MariaDB, PostgreSQL et SQL Server : `conforme` sur les trois.
  La comparaison de type porte sur la **famille** (`int`, `str`, `datetime`), seul niveau portable : l'introspection ne normalise pas les types entre SGBD et perd la longueur, mesuré sur serveurs réels (`varchar(64)` sur MariaDB, `character varying` sur PostgreSQL, `NVARCHAR` sur SQL Server). La longueur reste vérifiée quand les deux côtés la portent.
  Perte assumée : l'attribut `UNSIGNED` n'est plus vérifié, étant propre à MariaDB.
  Le cœur expose `core.database.table_ddl.column_sql_type()` pour les outils qui comparent un schéma observé à un schéma attendu sans reconstruire le DDL entier.

- **`iot` et `video` passent au DDL dialectal (`OPTIN-DDL-IOT-001`, `OPTIN-DDL-VIDEO-001`) : plus aucun fichier SQL figé dans `packages/`.**
  Ces deux paquets demandaient un changement de code : leur commande `doctor` lisait le fichier de migration à l'exécution, via `importlib.resources`, pour vérifier l'installation.
  `check_migration_present()` interroge désormais la déclaration. Le contrôle garde son rôle et gagne en robustesse : il ne dépend plus de `[tool.setuptools.package-data]`, dont l'oubli était précisément le risque que l'ancienne lecture cherchait à couvrir. Les entrées `migrations/*.sql` des deux `pyproject.toml` sont retirées, devenues sans objet.
  Le rendu gagne `UniqueConstraint`, contrainte d'unicité nommée, qui préserve à l'identique le `UNIQUE KEY uq_videos_uuid (uuid)` de `videos` sur MariaDB tout en rendant `CONSTRAINT ... UNIQUE` ailleurs. Aucune page de documentation à réécrire.
  Deux tests d'intégration qui montaient leur schéma depuis le fichier `.sql` le rendent maintenant par le dialecte : ils ne pouvaient tourner que sur MariaDB, ils sont désormais corrects sur les quatre backends.
  Précision : `received_at` (IoT) et les horodatages vidéo passent de `DATETIME(6)` au type datetime du dialecte, ce qui perd la microseconde **sur MariaDB seul** ; PostgreSQL et SQL Server la conservent. L'ordre des événements IoT d'une même seconde reste départagé par la clé primaire croissante.

- **Cinq opt-ins de plus passent au DDL dialectal (`OPTIN-DDL-BATCH-001`).**
  `audit`, `jobs`, `settings`, `notifications` et `images` déclarent leur table dans `tables.py` au lieu de livrer un `.sql` figé ; leur `<opt-in>:init` rend le DDL du backend installé.
  Plus aucun fichier SQL figé n'est livré par ces paquets.
  **Le cliquet est étendu au code Python.** Supprimer un `.sql` en laissant la même table écrite en dur dans une constante Python aurait rendu le garde-fou vert sans rien corriger.
  Cette extension a révélé que l'audit initial **sous-comptait** : il ne scannait que le `.sql` et avait manqué du DDL MariaDB dans `mail`, `stats`, `entities` et le `doctor` d'`iot`.
  **`iot` et `video` sont reportés** à leurs propres tickets : contrairement aux autres, leur commande `doctor` lit le fichier de migration à l'exécution pour vérifier l'installation du paquet ; les supprimer casse la commande, leur bascule demande donc un changement de code.
  À noter : `iot` et `video` déclaraient `DATETIME(6)` ; leur conversion fera perdre la microseconde sur MariaDB seul, PostgreSQL et SQL Server la conservant.

- **Nouvelle commande `forge rbac:init` (`OPTIN-DDL-RBAC-INIT-001`).**
  Les tables `roles`, `permissions` et `role_permissions` n'avaient **aucun chemin de provisioning utilisable** : le paquet n'exposait pas de commande d'initialisation, son `sql/rbac.sql` n'était pas livré dans le wheel, et le README renvoyait vers `docs/features/rbac.md`, document inexistant.
  Un utilisateur installant `forge-mvc-rbac` depuis PyPI ne pouvait donc pas créer ses tables, alors que `forge auth:init` lui écrivait un `user_roles.sql` portant une clé étrangère vers `roles`.
  `forge rbac:init` écrit désormais les trois migrations dans `mvc/migrations/`, dans l'ordre des dépendances, rendues pour le backend installé.
  Vérifié sur MariaDB, PostgreSQL et SQL Server : les tables s'installent, l'unicité du slug est active et la cascade depuis `roles` fonctionne.
  À noter : les clés primaires passent de `INT` à l'identité du dialecte (`BIGINT UNSIGNED` sur MariaDB), alignement sur le reste du provisioning Forge.

- **Suppression de quatre fichiers SQL morts (`OPTIN-DDL-DEAD-SQL-CLEANUP-001`).**
  `packages/forge-mvc-mfa/sql/auth_mfa_factors.sql`, `auth_mfa_recovery_codes.sql` et `packages/forge-mvc-rbac/sql/user_roles.sql` doublonnaient, en MariaDB seul, la spécification **déjà dialectale** de `cli/security/auth_sql.py` que `forge auth:init` rend pour le backend actif ; plus aucun code ne les lisait.
  `packages/forge-mvc-rbac/sql/rbac.sql` est remplacé par la déclaration `forge_mvc_rbac.tables`.
  Les garde-fous correspondants sont **généralisés plutôt que supprimés** : ils vérifient désormais le rendu réel, et pour les quatre backends au lieu du seul MariaDB.
  Un test exigeait jusqu'ici la présence d'`AUTO_INCREMENT` : il verrouillait le défaut mesuré par l'audit, il vérifie maintenant la portabilité.

- **`forge-mvc-sessions-db` passe au DDL dialectal (`OPTIN-DDL-SESSIONS-DB-001`), pilote du chantier.**
  Le paquet ne livre plus de `.sql` figé : il déclare sa table une fois (`forge_mvc_sessions_db.tables`) et `forge sessions:init` rend le DDL du backend installé.
  Le fichier remplacé portait lui-même l'aveu de sa limite, « DDL MariaDB, adaptez les types au backend actif si nécessaire » : l'adaptation n'est plus reportée sur l'auteur du projet.
  La table de session s'installe et fonctionne désormais sur MariaDB, PostgreSQL et SQL Server, concurrence optimiste par la colonne `version` comprise, vérifié sur les trois serveurs.
  Le mécanisme de rendu est porté par le helper partagé `cli/_support/optin_migrations.py` : les neuf opt-ins restants basculeront en déclarant leur table, sans autre changement.
  `sessions:init` reste sans amorçage de config : rendre exige l'identité du backend (entry point, ADR-054), pas les identifiants de connexion, et aucune connexion n'est ouverte.
  À noter sur MariaDB, pour les **nouveaux** projets : la colonne `data` devient `TEXT` au lieu de `LONGTEXT` (les tables existantes ne sont pas modifiées, la migration reste un `CREATE TABLE IF NOT EXISTS`).

- **Rendu dialectal des tables d'infrastructure (`DB-TABLE-DDL-RENDERER-001`).**
  Nouveau module `core/database/table_ddl.py` : un paquet décrit sa table une fois (`TableDefinition`, `Column`, `Index`, `ForeignKey`) et `render_create_table()` produit le DDL correct pour le backend actif, en passant par le contrat `Dialect`.
  Le rendu retourne la liste des instructions : le `CREATE TABLE`, puis les `CREATE INDEX` séparés que PostgreSQL, SQLite et SQL Server exigent là où MariaDB les porte en ligne.
  Le SQL reste visible : `<opt-in>:init` écrit le texte produit dans `mvc/migrations/`, où l'auteur le relit avant application (ADR-071 inchangé, seule la production du fichier change).
  Vérifié en exécution sur MariaDB, PostgreSQL 17.10 et SQL Server 2022, table sans identité comme table avec identité, horodatages et clé étrangère.
  `ON DELETE RESTRICT` est normalisé en `NO ACTION`, que SQL Server est seul à ne pas comprendre.
  Documentation embarquée : `core/database/docs/table_ddl.md`.

- **Cliquet de portabilité du DDL des opt-ins (`OPTIN-DDL-GUARD-RATCHET-001`).**
  L'audit `OPTIN-DDL-DIALECT-AUDIT-001` a mesuré que 12 fichiers SQL livrés par 10 opt-ins étaient inexécutables ailleurs que sur MariaDB.
  Le garde-fou fige cette liste et interdit qu'elle grandisse : un paquet neuf livrant du SQL propre à MariaDB fait échouer la suite.
  Il se resserre aussi tout seul, un fichier corrigé mais laissé dans la liste faisant également échouer le test, avec le message qui demande de l'en retirer.
  La dérive s'arrête donc avant même que les dix paquets soient repris.

- **Le CRUD généré traite les doublons (`CRUD-DUP-HANDLING-001`).**
  Une entité pouvait déclarer un champ `unique` et le DDL créait bien la contrainte, mais le contrôleur généré n'entourait l'INSERT pour aucun champ unique : un doublon soumis remontait l'exception brute du pilote et produisait une 500, sur les quatre backends.
  `create` et `update` attrapent désormais `UniqueViolationError` et réaffichent le formulaire avec l'erreur.
  Avec un seul champ unique, l'erreur se pose sur ce champ et s'affiche sous lui ; avec plusieurs, l'exception ne dit pas laquelle des contraintes a sauté, une erreur globale est donc posée plutôt que d'en désigner une au hasard.
  **Une entité sans champ unique produit exactement le même contrôleur qu'avant** : ni import, ni garde inutile.
  Lacune ouverte depuis la bêta 13, rendue traitable de façon portable par `DB-UNIQUE-VIOLATION-CONTRACT-001`.

### Ajouté (contrat)

- **Détection portable des violations d'unicité (`DB-UNIQUE-VIOLATION-CONTRACT-001`).**
  Une application ne pouvait pas distinguer « ce courriel existe déjà » d'une panne sans attraper l'exception de son pilote, ce qui la rendait non portable et contredisait l'ADR-054.
  Le contrat `DatabaseBackend` gagne `is_unique_violation(error)`, implémentée par les quatre backends ; `core.database.db` lève désormais `UniqueViolationError` (nouveau module `core/database/errors.py`), l'exception du pilote restant accessible via `__cause__`.
  Toute exception que le backend ne confirme pas remonte **inchangée** : le cœur n'enveloppe pas ce qu'il ne sait pas qualifier.
  Les quatre signaux ont été mesurés sur serveur réel, aucun n'est portable : MariaDB errno 1062, SQLite message « UNIQUE constraint failed », PostgreSQL SQLSTATE 23505, SQL Server numéro natif 2627.
  Le SQLSTATE seul ne convient pas : MariaDB et SQL Server renvoient `23000` aussi bien pour un doublon que pour un `NOT NULL` ou une clé étrangère, si bien qu'une détection par SQLSTATE serait fausse sur la moitié des backends.
  La méthode est portée par le backend et non par `Dialect`, car reconnaître une exception relève du pilote là où `Dialect` ne décrit que du SQL.
  Documentation embarquée : `core/database/docs/errors.md`.

- **Suppression de `DoublonError`** (même ticket).
  Cette exception du cœur n'était ni levée, ni attrapée, ni générée nulle part ; sa seule documentation recommandait `except mariadb.IntegrityError`, propre à un backend, dans un cœur agnostique ; et son nom francophone contrevenait à l'ADR-003.
  Elle est remplacée par `UniqueViolationError`, qui est, elle, réellement utilisable.
  Le CRUD généré ne traite toujours pas la violation d'unicité : c'est l'objet du ticket `CRUD-DUP-HANDLING-001`, déjà inscrit à la roadmap, que ce contrat rend enfin réalisable de façon portable.

### Corrigé

- **Clés étrangères corrompues sur PostgreSQL et SQL Server (`FK-IDENTITY-STORAGE-TYPE-001`, révision de l'ADR-069).**
  Un champ `foreign_key` recevait le type de la clé primaire auto-incrémentée (`dialect.identity_type()`), en s'appuyant sur une prémisse de l'ADR-069 vraie sur MariaDB et SQLite seulement.
  Sur PostgreSQL, la colonne référençante était déclarée `BIGSERIAL` : elle recevait sa propre séquence et un `DEFAULT nextval()`, si bien qu'un `INSERT` omettant la clé étrangère, pourtant `NOT NULL`, était accepté et se voyait attribuer une valeur fabriquée pointant vers une ligne arbitraire de la table cible (vérifié sur PostgreSQL 17.10).
  Sur SQL Server, la colonne était déclarée `BIGINT IDENTITY(1,1)`, ce qui rend le `CREATE TABLE` invalide : une table n'admet qu'une seule colonne IDENTITY, déjà prise par la clé primaire.
  Le contrat `Dialect` gagne `identity_storage_type()` (`BIGINT UNSIGNED` sur MariaDB, `INTEGER` sur SQLite, `BIGINT` sur PostgreSQL et SQL Server), que les champs `foreign_key` consomment désormais ; la clé primaire continue d'employer `identity_type()`.
  **MariaDB et SQLite ne changent pas de comportement** : les valeurs renvoyées sont identiques, aucun schéma existant n'est affecté.
  **Schémas PostgreSQL et SQL Server déjà générés** : ils ne sont pas réparés automatiquement.
  Pour les repérer sur PostgreSQL, chercher les colonnes de clé étrangère portant un `DEFAULT nextval()` :
  `SELECT table_name, column_name, column_default FROM information_schema.columns WHERE column_default LIKE 'nextval%' AND column_name <> 'id';`
  Chaque colonne listée doit être passée en `BIGINT` nu, avec suppression de la séquence associée.

### Ajouté

- **PostgreSQL et SQL Server promus au niveau plein (révision ADR-084 du 2026-07-19).**
  Les quatre backends BDD sont désormais au même niveau de support.
  Ce qui a été livré pour la promotion :
  identité d'insertion fiabilisée (`PG-INSERT-IDENTITY-001` : `lastval()` sous garde savepoint ; `MSSQL-INSERT-IDENTITY-001` : `SCOPE_IDENTITY()` exécuté dans le lot de l'INSERT, corrige un `lastrowid` toujours NULL) ;
  `forge db:init` génère et exécute (`--run`) le provisioning PostgreSQL (rôles, base, droits DML présents et futurs, registre des migrations) et SQL Server (logins, users, `GRANT ON SCHEMA::dbo`, lots `GO`), l'escape hatch `DB_APP_PRIVILEGES` au-delà du DML restant propre à MariaDB (refus explicite, règle B) (`PG-DB-INIT-PROVISIONING-001`, `MSSQL-DB-INIT-PROVISIONING-001`) ;
  deux jobs CI exécutent les suites d'intégration `-m db_pg` / `-m db_mssql` contre de vrais serveurs (PostgreSQL 16, SQL Server 2022), avec le même garde anti « vert avec 0 test » que MariaDB (`CI-DB-POSTGRES-001`, `CI-DB-MSSQL-001`) ;
  les chemins de génération (entités, `auth:init`, relations `many_to_one`) et le runner de migrations (application, idempotence, dry-run, refus CHANGED, rollback réel, introspection) sont validés dialectalement et face aux vrais serveurs (`PG/MSSQL-DIALECT-PARITY-TESTS-001`, `PG/MSSQL-MIGRATIONS-INTEGRATION-001`).
  Classifieurs PyPI des deux paquets : `3 - Alpha` vers `4 - Beta` ; mentions Alpha retirées des docs, parcours welcome, landing et briefing agent.

- **Moteur d'entités extrait du cœur : opt-in `forge-mvc-entities` (ADR-070).** Toute la
  génération et la modélisation de la couche de données quitte le cœur (`cli/entities`) pour un
  paquet opt-in : `make:entity`, `make:relation` (`many_to_one` et `many_to_many`), le normaliseur
  canonique, la validation, `build:model` / `sync:entity`, la génération de migrations, `make:crud`,
  `entity:validate`, `entity:doc`, le provisioning `db:config` / `db:init` / `db:apply`, plus le
  pivot enrichi (`PivotAdvancedService`, `make:pivot-crud`) qui absorbe l'ancien `forge-mvc-pivot`.
  Le cœur ne garde que la couture runtime d'accès base (`core/database`, contrat `Dialect`,
  ADR-054) ; le nouvel opt-in dépend de ce contrat, pas d'un backend concret. Ses commandes sont
  gatées sur son installation (entry point `forge_mvc.commands`, échec gracieux si absent). Le
  squelette est livré **sans** moteur d'entités (comme sans backend, ADR-060) : on installe
  l'opt-in explicitement (`pip install forge-mvc-entities`) pour une application qui modélise des
  données, le `requirements.txt` du projet le documente. Les schémas d'entités/relations restent
  des contrats du cœur (`cli/schemas`, ADR-058).
- **Clé étrangère de première classe : type de champ `foreign_key` (ADR-069, retour terrain).**
  Une clé étrangère se déclare désormais comme un champ d'entité : `{ "name": "annee_scolaire_id",
  "type": "foreign_key", "references": "AnneeScolaire", "required": true }`. Le normaliseur le
  résout au type de la clé primaire visée (`BIGINT UNSIGNED` sur MariaDB, backend-agnostique) avec
  une colonne snake_case fidèle au dictionnaire. `make:relation` **injecte** ce champ dans le JSON
  de l'entité source (chirurgical, annoncé `[MODIFIE]`, idempotent) en plus d'écrire la relation ;
  la FK est alors visible dans le contrat, `relations.sql` ne pose plus que la contrainte, et
  `make:crud` la gère naturellement (plus besoin d'injection synthétique). Une relation écrite sans
  champ FK déclaré reste supportée (repli `ADD COLUMN` de `relations.sql`).
- **Page de référence de la charte graphique dans le squelette (`/charte`).** Le squelette
  livre `mvc/views/pages/charte.html`, une page servable (câblée sur `/charte`) qui montre le thème
  « Accessible chaleureux » livré par défaut : palette, typographie, boutons, badges, alertes
  et champs de formulaire. Elle sert de référence visible et rappelle que les tokens (couleurs,
  polices, rayons) s'éditent dans `static/src/input.css` (source unique, `@theme` Tailwind) pour
  reskinner toute l'application. Seules la landing (`/`) et cette page restent pré-câblées.
- **`forge entity:doc`** : vue globale des entités et de leurs relations, produite à
  partir des contrats du projet (`mvc/entities/*.json` et `relations.json`). Sortie
  Markdown : un tableau par entité (champs, colonnes, types, nullable, PK, unicité),
  la liste des relations avec leur cardinalité (`N:1`, `N:N`) et un diagramme Mermaid
  `erDiagram` qui se rend dans GitHub et MkDocs. Affiche sur stdout par défaut (mode
  « Forge affiche ») ; `--output <fichier>` écrit le résultat. Lecture seule des
  contrats, sans backend BDD ni connexion : documente le modèle déclaré, pas la base.
- **`forge skeleton:upgrade`** (retour terrain, FORGE-9) : ajoute au projet courant
  les fichiers du squelette qui lui manquent, en **write-if-new** strict (aucun
  fichier existant modifié ou écrasé). Utile quand Forge enrichit le squelette
  (outillage, config qualité) après la création du projet. `--check` liste ce qui
  serait ajouté sans écrire ; `--bare` ignore l'apparat qualité (ADR-063). S'arrête
  proprement hors d'un projet Forge.
- **`forge make:auth`** (retour terrain, FORGE-5) : scaffolde le flux de connexion
  qui manquait. Le cœur redirige les routes protégées vers `/login` (codé en dur) et
  fournit le backend (`core.auth.session`), mais aucune route, aucun contrôleur ni
  aucune vue de login n'étaient générés. `make:auth` crée (write-if-new)
  `mvc/controllers/auth_controller.py` (`login_form`, `login`, `logout` ; flux
  `authenticate_user` + `login_user` + régénération de session anti-fixation + cookie),
  `mvc/views/auth/login.html` et `mvc/routes/auth_routes.py` (ADR-068), puis
  **affiche** le branchement à coller dans `mvc/routes/__init__.py` (Forge n'écrit pas
  dans ce fichier utilisateur). Cible le socle standard `users` (`forge auth:init`).
  Version 1 sans MFA / rate-limit / audit.

- **Journal de reprise des migrations (`MIGRATION-RESUME-JOURNAL-001`).**
  Sur MariaDB, seul backend qui ne sait pas annuler la DDL, une migration cassée en cours de route laissait les instructions déjà passées en base, hors journal, et la relance butait sur « already exists ».
  L'état était révélé depuis le cycle précédent, mais aucune commande ne permettait d'en sortir : c'était le dernier scénario connu où un projet Forge restait bloqué sans outil.
  Chaque instruction est désormais retenue dans `forge_migration_steps` et validée sitôt exécutée, et `migration:apply` **reprend** à la première instruction non appliquée, l'annonce, puis efface le journal quand la migration aboutit.
  Le préfixe déjà en base ne se réécrit pas : la base l'a exécuté tel quel, et la reprise refuse toute divergence en nommant l'instruction.
  Une migration purement DML n'est pas journalisée, même sur MariaDB : sans DDL le rollback l'annule entièrement, et l'atomicité qui existe vraiment ne se sacrifie pas.

- **Un pool de connexions devant PostgreSQL (`POSTGRES-POOL-001`).**
  Le backend ouvrait puis fermait une connexion à chaque requête : mesuré, 12,12 ms contre 0,16 ms sur une connexion tenue, soit une page à dix requêtes qui payait 120 ms de connexion pure.
  MariaDB avait son pool et SQL Server bénéficie de celui du gestionnaire ODBC ; PostgreSQL était le seul à repartir de zéro, et `DB_POOL_SIZE` comme `DB_POOL_TIMEOUT` y étaient ignorés en silence.
  Le pool est celui de `psycopg_pool`, écrit par les auteurs du pilote, né au premier emprunt pour appartenir au processus fils de gunicorn.
  Après : 0,91 ms par requête, et 200 requêtes simultanées en 0,17 s contre 0,86 s.

- **L'attente d'un verrou est bornée au runtime (`DB-LOCK-WAIT-BOUND-001`).**
  Une transaction coincée, bug applicatif ou requête d'administration oubliée, faisait patienter les requêtes HTTP 50 secondes sur MariaDB et **indéfiniment** sur PostgreSQL et SQL Server.
  Les workers s'épuisaient un à un et le site figeait sans un 503 ni une ligne de journal.
  Les connexions du runtime reçoivent désormais `DB_POOL_TIMEOUT` comme borne, la variable qui nomme déjà le temps qu'on accepte de patienter, quelle que soit la ressource attendue.
  Les connexions d'administration restent sans borne, une migration ayant le droit d'attendre.

- **Garde de complétude de la publication (`RELEASE-PYPI-COMPLETENESS-GUARD-001`).**
  La rc2 a été publiée avec vingt-quatre distributions sur vingt-sept, sans que rien ne le signale : les trois absentes étaient nées après la publication précédente.
  Le garde croise le dépôt, la construction et PyPI, et refuse une release dont une distribution du dépôt n'a jamais été publiée.
  Rien n'y est écrit en dur, le relevé venant des `pyproject.toml`.
  Un PyPI injoignable fait échouer par défaut : un garde qui se tait quand il ne peut pas vérifier ne garde rien.


### Modifié

- **Vues d'application sous un namespace `mvc/views/app/` (ADR-073, retour terrain 018 F41).**
  À l'échelle (banc d'essai à ~40 entités), la racine de `mvc/views/` mélangeait les dossiers
  du cadre et un dossier par entité, devenant illisible. Les vues de l'application (à la main ou
  générées) vivent désormais sous `app/`, à côté de `public/` ; les 6 dossiers du cadre restent à
  la racine. `forge make:crud` écrit sous `mvc/views/app/<snake>/` et génère des
  `render("app/<snake>/...")` / `{% include %}` cohérents ; `render()` et le loader Jinja sont
  inchangés (chemins littéraux). Le dossier est réglé par `APP_VIEWS_NAMESPACE` dans `config.py`
  (défaut `"app"` ; `""` rétablit la disposition plate historique). Projet existant : ajouter
  `APP_VIEWS_NAMESPACE = ""` à `config.py` pour rester à plat. `make:auth` range de même sa
  vue de connexion sous `app/auth/login.html` (le helper de namespace vit dans le cœur,
  `cli.project.views_namespace`, ré-exporté par l'opt-in entités sans dépendance inverse,
  ADR-070). `make:public-*` (déjà sous `public/`) est inchangé.
- **`make:auth` génère un bouton Connexion / Déconnexion pour la barre de navigation (retour terrain).**
  En plus du contrôleur, de la vue de login et des routes, `make:auth` génère désormais
  un bouton conditionnel « Connexion » (lien vers `/login` pour un visiteur) ou « Déconnexion »
  (POST vers `/logout` pour un utilisateur connecté), stylé via la macro `button`. Le bouton est
  **injecté** dans la barre de navigation `partials/nav.html` (incluse par le `{% block nav %}`
  de `layouts/base.html`), de façon **chirurgicale et idempotente** : le squelette livre `nav.html`
  avec un ancrage `{# forge:auth-nav #}` où `make:auth` insère le bloc sans toucher aux liens
  ajoutés par le développeur (même mécanisme qu'`opt-in:enable`). Pour rendre l'état
  d'authentification disponible partout, `BaseController.render` injecte désormais
  `is_authenticated` dans le contexte de tout template (comme `csrf_token`).
- **Scaffold cohérent : les vues générées s'appuient sur le layout partagé `layouts/base.html` (retour terrain).**
  Le squelette livre un `base.html` complet (header, navigation, footer, charte « Accessible
  chaleureux »), mais les générateurs le contournaient : `make:crud` produisait son propre
  `app.html` (sans footer), `make:auth` une page de login autonome, et `public:*` étendaient un
  `layouts/public.html` jamais livré (`TemplateNotFound` latent). Désormais toutes les vues
  générées (`make:crud`, `make:auth`, `public:*`) étendent `layouts/base.html` : header, nav,
  footer et charte partout, et le trou `public.html` disparaît. `make:crud` ne génère plus de
  layout. De plus, les formulaires générés (`form.html` et la vue de login) utilisent les macros
  de `components/forms.html` (`field`, `textarea_field`, `select_field`, `checkbox`, `submit`) :
  champs homogènes, libellés (le select de relation retire le suffixe `_id`), états d'erreur et
  style de la charte. Même esprit que les correctifs FORGE-1 (flash) et FORGE-11 (button) :
  utiliser ce que le squelette fournit au lieu de le réinventer.
- **Les routes applicatives deviennent un paquet `mvc/routes/` (ADR-068).** Le fichier
  monolithique `mvc/routes.py` est remplacé par un paquet `mvc/routes/` : `__init__.py`
  est la racine de composition (crée `router`, câble la route d'accueil, appelle
  `register_optins(router)` puis, explicitement, un `register_<contrôleur>_routes(router)`
  par contrôleur), et chaque contrôleur porte son propre `mvc/routes/<contrôleur>_routes.py`.
  `make:crud` et `make:auth` **génèrent** le fichier de routes du contrôleur (write-if-new)
  et **affichent** la ligne de branchement à coller dans `__init__.py` ; `make:public-page`
  injecte sa route dans `__init__.py`. Aucune découverte automatique (charte principe 3,
  ADR-030) : chaque branchement reste explicite et lisible. L'import
  `importlib.import_module("mvc.routes").router` reste inchangé (un paquet expose le même
  attribut qu'un module). Migration d'un projet existant : créer `mvc/routes/__init__.py`
  avec le contenu de l'ancien `mvc/routes.py`, puis extraire progressivement les routes
  par contrôleur.
- **`forge db:init` génère le SQL de provisioning par défaut (ADR-067).** Au lieu de
  se connecter avec un compte d'administration serveur lu dans `env/`, `db:init`
  **affiche** désormais le script SQL de provisioning dérivé de `env/` (création de la
  base et des deux comptes, scellés à `DB_NAME`), à exécuter dans une session
  d'administration (ex. `sudo mariadb`). `forge db:init --run` conserve l'exécution
  automatique (opt-in), pour les contextes disposant d'un compte serveur (CI,
  conteneurs, serveur auto-géré). Les deux modes vérifient d'abord que les variables
  requises sont renseignées et que `DB_NAME` est un nom de base valide. Forge n'exige
  ainsi plus jamais le root du serveur dans `env/` ; `DB_ADMIN_*` désigne le
  propriétaire de la base du projet, pas l'administrateur du serveur.
- **Contrat d'environnement des backends BDD unifié (ADR-066).** L'adresse du
  serveur est désormais décrite par un seul couple `DB_HOST`/`DB_PORT`, partagé par
  les connexions applicative et d'administration ; seuls les identifiants restent
  distingués (`DB_APP_LOGIN`/`DB_APP_PWD` pour le runtime, `DB_ADMIN_LOGIN`/`DB_ADMIN_PWD`
  pour le provisioning). `DB_APP_HOST`, `DB_APP_PORT`, `DB_ADMIN_HOST` et `DB_ADMIN_PORT`
  disparaissent du contrat. Concerne `forge-mvc-mariadb`, `forge-mvc-postgres` et
  `forge-mvc-mssql`, `forge db:config` (`env_template`), `forge db:init`, l'audit projet,
  `forge-mvc-deploy` et la documentation. Rupture interne assumée en phase bêta : un
  projet existant remplace `DB_APP_HOST`/`DB_ADMIN_HOST` par `DB_HOST` et les ports
  correspondants par `DB_PORT`.

- **La DML des opt-ins adossés à la base devient portable (`OPTIN-DML-DIALECT-001`).**
  Un audit précédent avait rendu leur **DDL** dialectale et s'était arrêté là.
  Mesuré sur serveurs réels, `jobs`, `notifications` et `settings` cassaient sur trois backends sur quatre, alors que la documentation de `settings` promettait les quatre : `NOW()` est inconnu de SQL Server et de SQLite, `NOW() + INTERVAL ? SECOND` et `ON DUPLICATE KEY UPDATE` sont propres à MariaDB.
  Deux traits rejoignent le contrat `Dialect`, ceux qui n'ont aucune écriture commune : `now_expression()` et `interval_seconds_expression()`.
  L'upsert et la réservation d'une ligne s'expriment sans lui, par des motifs portables bâtis sur l'existant, un noyau minimal ne gagnant pas à porter ce qu'on peut dire sans lui.

- **Le contrat de backend demande la famille, plus une cause (`DB-UNAVAILABLE-FAMILY-001`).**
  `is_connection_lost` nommait une cause alors que le cœur ne se sert que de la famille : quelle que soit la réponse, il lève `DatabaseUnavailableError`, donc un 503 avec `Retry-After`.
  La question devient `is_unavailable`, ce qui rétablit la symétrie d'une question du contrat pour une erreur du cœur, et permet d'y ranger le verrou de fichier SQLite, jumeau exact de la saturation du pool.
  Les interblocages restent dehors sur les trois serveurs : le critère est « attendre suffit », or attendre n'y change rien.

- **SQLite applique enfin ses clés étrangères (`SQLITE-FOREIGN-KEYS-ON-001`).**
  Le pragma restait inactif, réglage propre à la connexion que Forge n'armait nulle part : les contraintes écrites par `make:relation` ne contraignaient rien, un enfant orphelin entrait et `ON DELETE CASCADE` ne cascadait pas.
  Le sens de la dérive commandait de corriger : SQLite sert en développement, les SGBD serveur en production, donc le défaut ne se voyait jamais chez le développeur et toujours chez l'utilisateur, sur des données déjà incohérentes.
  Une base SQLite créée avant cette version peut porter des lignes orphelines ; toute écriture qui les toucherait sera désormais refusée.


### Corrigé

- **`make:public-list/show/form` échouent proprement sans le moteur d'entités (audit, ADR-070).**
  Ces commandes du cœur lisent le contrat JSON de l'entité via `forge-mvc-entities` ; sans l'opt-in,
  elles produisaient une traceback brute d'import au lieu d'un message d'installation. Elles gatent
  désormais sur `find_spec` et rendent le même message que `db:init` (principes 8 et 10). Au passage,
  `forge-mvc-entities` et `forge-mvc-rbac` déclarent `jsonschema` comme dépendance directe (elles
  l'utilisent, mais ne la tiraient que transitivement via le cœur).
- **Upload multi-fichiers (galeries) : plus de perte de données silencieuse (audit).**
  `Request.files` était un `dict[str, UploadedFile]` qui écrasait à chaque part de même nom :
  un `<input type="file" ... multiple>` (galerie `make:crud`) n'enregistrait qu'**un seul** fichier
  sur N, sans erreur. Le parsing multipart accumule désormais tous les fichiers ; un nouvel accesseur
  `request.files_list("champ")` renvoie la liste complète (le CRUD généré l'utilise pour les
  galeries), tandis que `request.files` / `request.file(...)` restent focalisés sur le cas mono
  (premier fichier, rétro-compatible). Garde-fou de parsing HTTP réel (3 fichiers de même nom → 3 conservés).
- **Commandes CLI des opt-ins : aide et config projet (retour terrain 016, F39 / F40 ; ADR-072).**
  Deux frictions sur les commandes livrées par les opt-ins, corrigées dans le dispatch commun
  (`dispatch_optin`). **F40** : `forge sessions:gc --help` (et `sessions:init --help`) exécutait
  l'effet au lieu d'afficher l'aide ; `-h`/`--help` est désormais **intercepté avant tout effet**
  pour toute commande d'opt-in (les commandes Forge documentées l'étaient déjà via
  `format_command_help`, ce filet couvre aussi les opt-ins tiers). **F39** : `forge sessions:gc`
  ouvrait une connexion BDD sans avoir chargé la config du projet (`env/dev`), le pool se rabattant
  sur l'utilisateur système sans mot de passe (`Access denied`) et rendant la purge inutilisable en
  cron/systemd. La table `COMMANDS` d'un opt-in peut maintenant marquer une commande adossée à la
  base avec `config: True` : le dispatch **amorce alors `load_project_config()`** (comme le cœur le
  fait pour `migration:apply`) avant le handler. Un audit transverse a posé le drapeau sur toutes
  les commandes d'opt-in adossées à la base : `sessions:gc`, `iot:listen` (INSERT `iot_events`),
  `video:upload` / `video:process` / `video:cleanup` (table vidéo). Les commandes qui ne connectent
  pas (copie de migration `*:init`, diagnostics statiques `*:doctor`, `iot:simulate`) ne le posent
  pas. Clé additive, rétro-compatible ; garde-fou verrouillant l'audit.
- **`forge iot:doctor --db` charge la config projet si présente (IOT-DOCTOR-DB-CONFIG-BOOTSTRAP-001).**
  Le check `--db` connectait avec l'environnement ambiant : en projet, sans `env/dev` chargé, il
  signalait à tort la base injoignable. Il charge désormais `env/dev` **si un projet est présent**,
  pour se connecter avec les identifiants applicatifs, tout en restant utilisable **hors projet**
  (checks statiques) : contrairement aux commandes fonctionnelles adossées à la base (`config: True`,
  qui exigent la config), un diagnostic charge la config sans la réclamer. Le chemin statique et les
  tests (fetch injecté) ne sont pas affectés.
- **Unicité des relations scopée à l'entité source (retour terrain, F24 / F25).** `make:relation`
  et le validateur partagé (`validate_relations_definition`, donc aussi `entity:validate`,
  `sync:relations`, `project:check`) traitaient le **nom de relation** et le **nom de colonne FK**
  comme des identifiants **globaux** sur tout `relations.json`, rendant inexprimables les schémas
  où plusieurs entités (cas standard des pivots) référencent la même cible. L'unicité porte
  désormais sur le couple `(from, name)` pour l'accesseur et `(from, foreign_key)` pour la colonne :
  `Classe.annee_scolaire` et `InscriptionEleve.annee_scolaire` (colonnes `annee_scolaire_id` dans
  deux tables distinctes) coexistent. Les tables pivot restent globalement uniques. Les messages
  d'erreur sont qualifiés par la source (« ... existe déjà sur Classe »).
- **Chaîne applicative des relations : migration et affichage (retour terrain, FORGE-15 / FORGE-16).**
  `migration:make` reçoit une option `--with-relations` (valide avec `--from-entity` ou
  `--from-entities`) : après les `CREATE TABLE`, la migration inclut le SQL des relations
  (`ADD COLUMN` + `FOREIGN KEY` + `INDEX`) régénéré depuis `relations.json`, dans l'ordre
  tables puis contraintes (FORGE-15). Côté `make:crud`, la fiche détail (`show.html`) affiche
  désormais le **libellé** de l'entité liée au lieu de l'identifiant brut : `SELECT_BY_ID`
  joint la table cible comme la liste (FORGE-16). Le reste de FORGE-16 (select dans le
  formulaire, FK persistée dans `INSERT`/`UPDATE`, libellé en liste) était déjà couvert par
  l'intégration CRUD des relations.
- **Login impossible sur MariaDB/SQLite : `is_active` (int 0/1) refusé (retour terrain, FORGE-10).**
  Les backends SQL renvoient la colonne `BOOLEAN` / `tinyint(1)` en entier `0/1` ; le
  contrat `normalize_auth_user` exigeait un `bool` strict et levait avant la vérification
  du mot de passe, si bien que `authenticate_user` renvoyait `None` (login toujours refusé,
  même avec le bon mot de passe). La normalisation accepte désormais `0/1` et les coerce en
  `bool` ; les autres types restent refusés.
- **`make:crud` : `500` au rendu (`TemplateNotFound: components/button.html`) (retour terrain, FORGE-11).**
  Les vues générées incluaient `components/button.html`, absent du squelette : le bouton est
  la macro `button` de `components/ui.html`. Les vues importent et appellent désormais la macro,
  ce qui corrige aussi le lien de modification (concaténation Jinja `'/x/edit/' ~ obj.pk`). La
  variante `danger` est ajoutée à la macro. Un garde-fou vérifie que tout composant Jinja
  référencé par les vues générées existe bien dans le squelette livré par `forge new`.
- **Relation `many_to_one` inapplicable sur MariaDB (retour terrain, FORGE-12 / FORGE-13 / FORGE-14).**
  `generate_relations_sql` n'émettait que la contrainte `ADD CONSTRAINT ... FOREIGN KEY`, jamais
  la colonne FK (FORGE-12), avec un nom incohérent entre l'entité (PascalCase) et la contrainte
  (snake_case, FORGE-13) et un type incompatible avec la PK visée `BIGINT UNSIGNED` (FORGE-14) :
  MariaDB refusait la contrainte (errno 150). Désormais, quand la colonne FK n'est pas déclarée
  comme champ d'entité, `relations.sql` la crée lui-même (`ADD COLUMN`) au type exact de la PK
  visée, avec le même nom dans la colonne et la contrainte, puis un index, avant la contrainte.
  Le schéma d'une relation `many_to_one` est ainsi applicable de bout en bout sans SQL manuel.
  Côté CRUD, `make:crud` injecte un champ synthétique pour cette FK portée par la relation :
  le formulaire généré propose un `<select>` de l'entité liée (libellé dérivé de l'entité, sans
  le suffixe `_id` : « Annee scolaire » plutôt que « Annee scolaire id ») et le modèle persiste
  la valeur choisie (colonne présente dans `INSERT` et `UPDATE`), sans qu'il faille déclarer la
  FK comme champ d'entité.

- **Un bloc `transaction()` ne rend plus l'exception du pilote (`CORE-TX-LOST-CONNECTION-001`).**
  L'annulation du chemin d'erreur échoue elle aussi sur une connexion coupée, et remplaçait alors la cause par la sienne.
  Mesuré en tuant la session pendant le bloc, les trois backends serveur rendaient chacun l'exception de leur pilote, c'est-à-dire exactement ce que l'ADR-054 promet de ne jamais laisser atteindre l'application, et un 500 là où la requête simple rendait un 503.
  La qualification devient un service du cœur partagé par les deux chemins, et trois sorties qui pouvaient retenir la connexion, donc perdre son jeton de file d'attente, sont fermées.

- **SQL Server perdait l'identité de quatre formes d'INSERT sur sept (`MSSQL-INSERT-IDENTITY-SCOPE-001`).**
  La reconnaissance de l'INSERT était textuelle : la ligne était bien écrite, mais `db.insert()` rendait `None` dès qu'un commentaire précédait ou suivait l'instruction, ou que le mot « output » figurait dans un littéral.
  Le CRUD généré redirige vers `/show/{id}` avec cette valeur, et le défaut pénalisait justement le SQL commenté que le principe 5 encourage.
  La reconnaissance porte désormais sur un squelette de mots-clés bâti sur le découpeur canonique du cœur, qui connaît déjà littéraux et commentaires.

- **Une base SQLite absente n'est plus créée en silence (`SQLITE-RUNTIME-NO-CREATE-001`).**
  Un `DB_NAME` erroné, une faute de frappe suffisait, faisait fabriquer une base vide : l'application démarrait puis répondait « table inconnue » page après page, là où la vérité était « base absente ».
  L'exécution ouvre désormais sans droit de création, et le refus nomme le chemin **absolu** réellement tenté, ce qui règle du même coup la dépendance au répertoire de lancement.
  La création appartient au provisionnement.

- **Le verrou de fichier SQLite rend 503 (`SQLITE-BUSY-503-001`).**
  Un écrivain long, sauvegarde ou `fixtures:load`, faisait attendre cinq secondes puis échouer sur une erreur non qualifiée, donc une page 500.
  En mode journal par défaut, le verrou exclusif tient aussi les lecteurs à distance : ce n'était pas une page sur deux qui tombait, c'était le site entier.

- **L'export CSV ne produit plus de formule vive (`IMPORT-EXPORT-CSV-ESCAPE-001`).**
  `to_csv` écrivait ses cellules telles quelles : une cellule commençant par `=`, `+`, `-` ou `@` redevenait une formule à l'ouverture dans un tableur, et la donnée vient le plus souvent d'un utilisateur.
  Il se branche désormais sur la primitive du cœur, en-têtes compris, un nom de colonne pouvant venir d'une entité donc d'une saisie.

- **Le smoke d'installation ne fumait plus rien (`RELEASE-SMOKE-INSTALL-PATH-001`).**
  Il pointait un chemin de squelette disparu avec l'ADR-065 et échouait dès sa première vérification.
  Réparé, il a révélé ce qu'il existait pour révéler : il installait la wheel par son nom, donc pouvait fumer la version déjà publiée au lieu de celle en préparation, et le projet généré naissait avec un backend BDD épinglé que l'ADR-060 interdit.

- **Le cliquet de style rendait un verdict différent selon la machine (`META-RATCHET-TRACKED-FILES-001`).**
  Il parcourait le disque, donc aussi les journaux d'erreur que Git ignore et qui n'existent que chez le développeur.
  L'intégration continue est restée rouge deux jours pour cette seule raison.
  Il ne lit plus que les fichiers suivis par Git.

- **Les tests d'intégration ne déclaraient pas le serveur qu'ils exigent (`TEST-DB-BACKEND-MARKERS-001`).**
  Trente et un tests visant PostgreSQL ou SQL Server ne portaient que le marqueur générique, et le job MariaDB échouait de les avoir sautés, par un message de fin de session qui ne produit aucune ligne d'échec.
  Le lien entre la fixture et le marqueur est désormais figé par un garde-fou.

- **Les distributions absorbées sont retirées de PyPI (`PKG-ORPHAN-YANK-001`).**
  `forge-mvc-pivot` et `forge-mvc-media` restaient installables alors que le dépôt ne les porte plus, servant un code que personne ne maintient.
  Toutes leurs versions sont remisées, ce qui les sort de toute résolution nouvelle sans casser les projets qui les épinglent.
  La marche à suivre est documentée pour la prochaine absorption.

## [1.0.0-rc.2] - 2026-07-01

Deuxième release candidate. Consolidation post-rc.1 : refonte de la navigation et
de plusieurs pages de documentation, page d'accueil du squelette, correctifs issus
d'un audit multi-axes, une passe d'industrialisation (smoke d'installation vierge,
budget de complexité, smoke des profils, couches de test) et une refonte de
l'architecture de dispatch CLI (ADR-059 : `forge.py` devient un lanceur mince, les
commandes opt-in sont découvertes par entry points).

### Ajouté

- **Garde-fou anti-tiret cadratin** : `tests/meta/test_no_em_dash_in_live_docs_001.py`
  échoue si un U+2014 réapparaît dans la doc vivante (DOC-EMDASH-SWEEP-001).
- **`py.typed` sur `forge-mvc-testing`** : le paquet expose désormais ses types
  (PEP 561), comme les 24 autres (PKG-TESTING-PYTYPED-001).
- **Smoke co-localisé pour `forge-mvc-testing`** dans son propre dossier `tests/`
  (ADR-040, TEST-TESTING-SMOKE-001).
- **Registre de dispatch des commandes CLI** (ADR-059) : les commandes du cœur
  passent par des tables (`CORE_COMMANDS`) et les commandes des opt-ins sont
  découvertes par entry points (`forge_mvc.commands`), le cœur ne les liste plus.
  Chaque opt-in déclare ses commandes dans son `pyproject.toml` via une table
  `<pkg>.commands:COMMANDS`.
- **Smoke d'installation vierge** : `tools/smoke-install.sh` construit les wheels
  localement, installe `forge-mvc` dans un venv jetable, lance `forge new` avec
  résolution `--find-links` et vérifie le projet généré, indépendamment de PyPI ;
  garde-fou rapide anti-paquet-fantôme et flag `--with-smoke` de
  `release-validate.sh` (SMOKE-INSTALL-VIERGE-001).
- **Budget de complexité du lanceur** : plafond de taille de `forge.py`, `main()`
  et fonctions borné en AST (CLI-COMPLEXITY-BUDGET-001).
- **Smoke des profils de `forge new`** : les 5 profils génèrent un projet dont tout
  le Python compile (PROFILES-STARTER-SMOKE-001).
- **Carte des couches de test** dans `conventions.md` (pattern B.7) et garde-fou de
  cohérence avec `pytest.ini` (TEST-LAYERS-DOC-001).
- **Documentation contributeur du dispatch opt-in** : `contributing/optin-cli-commands.md`
  (OPTIN-CLI-COMMANDS-DOC-001).

### Modifié

- **Documentation** : barre de navigation universelle (réplique de la landing) sur
  toutes les pages, sommaire de page déplacé dans la barre de gauche, menu
  « Documentation » réorganisé (Commandes CLI, API Core, Packages, Starters).
- **Pages repensées** : « Démarrer » (quick-start et onglets par système), « Référence
  CLI » (catalogue), « API du cœur » (catalogue par usage), « Starters » (catégorisée
  par fonctionnalité, comme les Packages).
- **Parcours d'apprentissage des opt-ins** renommés « Welcome <X> » (au lieu de
  « Bonjour Forge <X> », réservé au parcours cœur).
- **Tiret cadratin U+2014 supprimé** de 87 fichiers de doc vivante, remplacé par le
  trait d'union court (directive de style FR, DOC-EMDASH-SWEEP-001).
- **Page d'accueil du squelette** : barre de navigation retirée, logo Forge centré
  en tête du hero (SKEL-HOME-LOGO-001).
- **Cliquet pyright** étendu aux 4 backends BDD (ADR-054) et à `forge-mvc-testing`
  (PKG-PYRIGHT-INCLUDE-001).
- **Statuts ADR formalisés** : 031 et 032 « Acceptée et mise en œuvre » ; 054 et 056
  « Acceptée » (ADR-STATUS-FORMALIZE-001).
- **`forge.py` ramené à un lanceur mince** : `main()` passe d'une chaîne de 46
  branches à un dispatch par tables + entry points (ADR-059).
- **`forge new` refuse les options inconnues** au lieu de les ignorer
  silencieusement (CLI-NEW-UNKNOWN-ARGS-001).

### Corrigé

- **Cohérence documentation ↔ tests méta** après la refonte de la référence en
  catalogue : contenu de référence restauré depuis l'historique (politique de
  stockage des secrets MFA, distinction RBAC cœur/opt-in, référence des filtres
  CRUD, commandes CLI `auth:user:*`/`check:model`/`sync:relations` manquantes) et
  garde-fous obsolètes repointés.
- **Mention de version périmée** « Forge 2.10.0 » de `core/security/docs/hashing.md`
  rendue agnostique.

### Retiré

- **Page de référence générale `docs/reference/reference.md`**, devenue superflue ;
  chaque option du menu Documentation a sa propre page de présentation.


## [1.0.0-rc.1] — 2026-06-26

Première release candidate avant la 1.0.0 stable : API publique gelée, tous les
opt-ins officiels en statut Beta, nouvelles briques opt-in (ADR-052) et
extraction du déploiement (ADR-053).

### Modifié

- **Tous les opt-ins officiels passent en statut Beta** (`Development Status :: 4 - Beta`).
  `forge-mvc-mfa` inclus : il reste hors de `forge-mvc[all]` par choix de sécurité
  explicite, plus par maturité Alpha.
- **Version `1.0.0rc1`** (PEP 440), affichée `1.0.0-rc.1` (SemVer). API publique
  gelée pour la 1.0.

### Retiré

- **Dossier `deploy/` à la racine du dépôt** : artefact régénérable par
  `forge deploy:init`, retiré et ignoré (ADR-044, le dépôt framework ne porte pas
  d'application déployée).
- **Support pédagogique temporaire welcome-reseau** (2TNE CIEL, sans lien avec le
  framework) : retiré de la documentation, de la nav et de la landing.

### Sécurité

- **`cryptography` relevé à `>=48.0.1,<49` dans `forge-mvc-mfa`.** Réponse à
  `GHSA-537c-gmf6-5ccf` (OpenSSL lié statiquement dans les wheels `cryptography`
  antérieures à 48.0.1). MFA n'utilise que Fernet (API stable) ; l'ancien plafond
  `<47` qui bloquait le correctif est levé. Garde-fou `test_security_cryptography_mfa_001`
  mis à jour.
- **`mariadb` 1.1.14 / `PYSEC-2026-217` documenté** dans `SECURITY.md`
  (vulnérabilités connues suivies) : avis sur le chemin `mysql_real_escape_string()`
  + big5 + protocole texte, non emprunté par Forge (requêtes paramétrées, protocole
  binaire) ; aucune version corrigée disponible en amont (1.1.14 est la dernière).

### Ajouté

- **Opt-in `forge-mvc-deploy`** (ADR-053, `DEPLOY-EXTRACT-001`). Outillage de
  déploiement extrait du cœur : commandes `forge deploy:init` (gabarits Nginx,
  systemd, `wsgi.py`) et `forge deploy:check`. Premier opt-in à CLI seule, sans
  API runtime. `forge.py` dispatche `deploy:*` vers le paquet avec repli explicite
  si le module n'est pas installé.
- **Opt-ins applicatifs ADR-052** : `forge-mvc-settings` (paramètres `app_settings`,
  `get_setting`/`set_setting`), `forge-mvc-audit` (journal `audit_log`,
  `record_audit`/`get_audit_log`), `forge-mvc-jobs` (file de tâches `jobs`,
  `enqueue` + worker `drain`/`run_worker`), `forge-mvc-notifications`
  (`notify`/`get_notifications`/`mark_read`) et `forge-mvc-import-export` (échange
  CSV : import validé par champ et export `to_csv`). Chacun dépend uniquement du
  cœur, avec sa commande `*:init`, sa doc embarquée et son parcours welcome.
- **Opt-in `forge-mvc-qrcode`** (ADR-050, `QRCODE-OPTIN-SCAFFOLD-001`). Socle de
  génération de QR Codes découplé du cœur : `QrCode.from_text(...).to_png()` /
  `.to_svg()` (octets PNG, document SVG) et `QrCodeResponse.from_text(...)` qui
  renvoie une `core.http.Response` servable depuis un contrôleur (PNG par défaut,
  `fmt="svg"` possible). `QrCodeError` sur entrée vide ou format inconnu. Dépend
  de `segno` (pur Python, sans Pillow), déclaré uniquement dans le paquet. Forge
  Core reste indépendant (aucun import, `segno` absent de ses dépendances,
  verrouillé par test). Non publié sur PyPI (statut Beta).
- **Parcours d'accueil `welcome-projet` dans le squelette** (ADR-048,
  `WELCOME-PROJET-CONTENT-001`, `WELCOME-PROJET-NAV-001`). `forge new` embarque un
  parcours pédagogique court dans `docs/welcome/` du projet : mise en route, puis
  trois niveaux (débutant : entité, CRUD ; intermédiaire : page publique,
  contrôleur/template ; avancé : opt-in, valider/livrer), chaînés par des bilans
  et un récapitulatif. Orienté « votre projet », chaque page renvoie à
  forgemvc.com pour approfondir (sans dupliquer `welcome-forge`). Contenu statique
  sous `skeleton/data/docs/welcome/`, garde-fou de chaînage
  `test_skeleton_welcome_projet_nav_001`. Troisième couche « expérience » d'un
  projet généré, avec la guidance agent (ADR-047), sans code métier (ADR-024).

- **Couche de guidance agent IA dans les applications** (ADR-047,
  `AGENTS-BRIEFING-TEMPLATE-001`, `AGENTS-SEED-ADR-001`, `AGENTS-SKELETON-EMIT-001`,
  `AGENTS-INIT-COMMAND-001`).
  `forge new` écrit désormais, en write-if-new, un briefing agent distillé
  (`CLAUDE.md` et `AGENTS.md`, même contenu : conventions Forge, générateurs CLI,
  règle write-if-new, discipline ADR, validations) et un ADR d'amorçage
  `docs/adr/001-adopter-forge.md` (acte l'adoption de Forge, sert d'exemple de
  format, date tamponnée). Gabarits canoniques versionnés dans le paquet
  (`cli/agents/`). Le projet généré gagne ainsi un cadre de travail pour les
  agents IA, sans cesser d'être nu côté code métier (précision d'ADR-024).
  La commande `forge agents:init` apporte cette couche aux applications
  existantes : `--check` signale un briefing absent ou divergé, `--force`
  rafraîchit `CLAUDE.md` / `AGENTS.md` depuis la version de Forge installée
  (sans toucher l'ADR-001 du projet).

- **Registre de loaders de templates Jinja pour les opt-ins** (ADR-046,
  `CORE-JINJA-OPTIN-LOADERS-001`). Le cœur expose
  `register_jinja_template_loader()` / `iter_jinja_template_loaders()`
  (`core/mvc/controller/registry.py`), symétrique au registre de fournisseurs de
  contexte. Le renderer (`integrations/jinja2/renderer.py`) compose le dossier
  `mvc/views/` du projet puis les loaders d'opt-in, résolus dynamiquement à
  chaque rendu : un opt-in peut servir ses templates embarqués, et un template du
  projet de même chemin les surcharge (ordre projet-puis-paquet). Infrastructure
  générale du cœur, prérequis du rendu de Forge Admin ; aucun opt-in n'est nommé
  par le cœur.

- **Paquet opt-in `forge-mvc-admin` (scaffold)** (`ADMIN-OPTIN-PACKAGE-001`).
  Premier pas de la roadmap Forge Admin : un paquet installable mais
  volontairement vide, qui pose le contrat de version (`__version__`), le
  marqueur de typage `py.typed` (PEP 561) et un smoke test. Aucune API
  fonctionnelle n'est encore exposée ; le châssis d'administration, le registre
  de ressources et les vues viendront par les tickets `ADMIN-*` suivants.
  Le paquet est ajouté au cliquet pyright (`[tool.pyright]`, ADR-036). Forge
  Core n'en dépend pas. Voir `docs/roadmap/forge-admin-roadmap.md`.
- **Documentation embarquée de Forge Admin** (`ADMIN-OPTIN-DOCS-001`).
  Page de positionnement `packages/forge-mvc-admin/docs/index.md` (convention
  ADR-038), montée sous `/admin/` dans la nav « Opt-ins officiels ». Sans lien
  transversal vers le cœur (ADR-042).
- **Contrat de ressource admin** (`ADMIN-RESOURCE-CONTRACT-001`). Première
  couche du châssis Forge Admin : `AdminResource` (dataclass immuable décrivant
  l'entité, le slug, les libellés, les champs liste/formulaire ; validée à la
  construction) et `AdminRegistry` (registre explicite, sans découverte
  automatique — charte principe 3). Déclaration Python, pas de nouveau schéma
  JSON : l'entité reste son contrat JSON, la ressource admin est une couche de
  présentation au-dessus. Aucune vue ni route fournie à ce stade. Doc embarquée
  `packages/forge-mvc-admin/docs/resources.md`.
- **Commande `forge admin:init`** (`ADMIN-INIT-COMMAND-001`). Prépare la
  structure `mvc/admin/` d'un projet (`__init__.py` + `resources.py` où
  l'application déclare ses ressources). Write-if-new, idempotente, sans
  écrasement (charte §9) ; dispatch dans `forge.py` derrière un import optionnel
  (échoue proprement si le paquet n'est pas installé) ; aide riche `--help`.
  Documentée dans l'espace de l'opt-in (ADR-042), pas dans la référence CLI du
  cœur. Aucune vue ni template à ce stade.
- **Dashboard minimal Forge Admin** (`ADMIN-DASHBOARD-MINIMAL-001`).
  `register_admin_routes(router)` (branchement explicite, ADR-030) ajoute la
  route `GET /admin` (nommée `admin-dashboard`, **non publique** + `@require_auth`
  en défense en profondeur). `AdminController.dashboard` rend le template
  embarqué `admin/dashboard.html` listant les ressources du registre ; le paquet
  enregistre son `PackageLoader` auprès du cœur (ADR-046), et un projet peut
  surcharger le template via `mvc/views/admin/dashboard.html`.
- **Vue liste Forge Admin** (`ADMIN-LIST-VIEW-001`). Route `GET /admin/<slug>`
  (nommée `admin-resource-list`, non publique) affichant une liste paginée des
  lignes d'une entité. `AdminResource` gagne `table` (table physique) et
  `order_by` (tri par défaut). La requête est un `SELECT` contraint construit
  dans le châssis (`query.py`) : table, colonnes et tri sont des identifiants
  validés en liste blanche (jamais paramétrables), seules les bornes de
  pagination passent en paramètres `?` ; pagination via `core` `Pagination` ;
  `fetch_all`/`fetch_one` injectables (résolus paresseusement vers
  `core.database.db`). Template embarqué `admin/list.html` (surchargeable). Ni
  ORM ni introspection ; le rapprochement avec le contrat d'entité réel reste du
  ressort de `admin:doctor`.
- **Vue détail Forge Admin** (`ADMIN-DETAIL-VIEW-001`). Route
  `GET /admin/<slug>/<id>` (nommée `admin-resource-detail`, non publique)
  affichant une ligne. `AdminResource` gagne `pk` (colonne de clé primaire,
  défaut `id`). La requête est un `SELECT` contraint `WHERE <pk> = ? LIMIT 1`
  (identifiants en liste blanche, clé en paramètre) ; les colonnes affichées
  sont `pk` puis `list_fields` puis `form_fields` (uniques). 404 si la ligne est
  absente. Template embarqué `admin/detail.html` (surchargeable).
- **Création depuis Forge Admin** (`ADMIN-FORM-NEW-001`). Routes
  `GET /admin/<slug>/new` (formulaire) et `POST /admin/<slug>/new` (création),
  nommées, non publiques. Seules les colonnes `form_fields` sont écrites (liste
  blanche, valeurs paramétrées via `core.database.db.insert`) ; une valeur vide
  devient `NULL` ; le jeton CSRF est vérifié par le middleware ; succès →
  POST-Redirect-GET vers la fiche créée avec flash. Template embarqué
  `admin/form.html` (surchargeable). La route littérale `/new` est enregistrée
  avant `/{id}` (le routeur retient la première correspondance). Pas de
  validation par champ à ce stade (pas de contrat au runtime) : les contraintes
  restent celles de la base.
- **Édition depuis Forge Admin** (`ADMIN-FORM-EDIT-001`). Routes
  `GET /admin/<slug>/<id>/edit` (formulaire pré-rempli depuis la ligne) et
  `POST /admin/<slug>/<id>/edit` (mise à jour), nommées, non publiques. L'`UPDATE`
  écrit les colonnes `form_fields` (liste blanche, valeurs paramétrées via
  `core.database.db.execute`) `WHERE <pk> = ? LIMIT 1` ; CSRF vérifié ; succès →
  redirection vers la fiche avec flash. La fiche détail propose un lien
  « Modifier ». Template `admin/form.html` réutilisé.
- **Suppression contrôlée depuis Forge Admin** (`ADMIN-DELETE-ACTION-001`).
  `GET /admin/<slug>/<id>/delete` affiche une page de confirmation en lecture
  seule ; seul `POST /admin/<slug>/<id>/delete` exécute
  `DELETE … WHERE <pk> = ? LIMIT 1` (jamais en GET, CSRF vérifié, via
  `core.database.db.execute`), puis redirige vers la liste avec flash. Routes
  nommées, non publiques. Template embarqué `admin/delete.html` ; la fiche détail
  propose un lien « Supprimer ».
- **Garde-fou de sécurité Forge Admin** (`ADMIN-CSRF-SECURITY-001`). Test
  verrouillant les invariants des routes du back-office : aucune route `/admin`
  n'est publique ; toute mutation (méthode non sûre) exige le CSRF ; les routes
  GET ne le demandent pas ; toutes redirigent un visiteur non authentifié vers
  `/login` (`@require_auth`, vérifié avec `FakeRequest`). Empêche l'ajout futur
  d'une route admin publique, sans CSRF ou sans authentification.
- **Intégration RBAC optionnelle de Forge Admin** (`ADMIN-RBAC-INTEGRATION-001`).
  `register_admin_routes(router, permission="admin.access")` exige une permission
  sur toutes les routes admin (gate global). Opt-in explicite : sans le paramètre,
  l'admin reste en authentification seule (aucun changement). Vérification via
  `forge_mvc_rbac.require_contract_permission_for_request` importée en
  `try/except ImportError` : 403 si la permission manque (rbac installé),
  fail-open + avertissement `forge doctor` si `forge-mvc-rbac` est absent. Aucune
  dépendance dure ; la garde s'ajoute par-dessus `@require_auth`.
- **Surcharge des templates Forge Admin** (`ADMIN-TEMPLATE-OVERRIDE-001`).
  Documente et verrouille (test) la surcharge des templates embarqués : un projet
  remplace n'importe quel `admin/*.html` (layout, dashboard, list, detail, form,
  delete) en plaçant un fichier de même chemin sous `mvc/views/admin/`. Propriété
  acquise par l'ordre des loaders (projet d'abord, paquet ensuite, ADR-046),
  désormais couverte par un test et la doc embarquée.
- **Commande `forge admin:doctor`** (`ADMIN-DOCTOR-001`). Rapproche les ressources
  admin déclarées (`mvc/admin/resources.py`, importé pour peupler le registre)
  des contrats d'entité du projet (`mvc/entities/*/*.json`, lus directement) :
  signale entité introuvable, table ou colonnes divergentes. Lecture seule,
  aucune connexion base. Sévérité : `fail` si la déclaration ne charge pas,
  `warn` pour tout écart au contrat (qui peut être en retard sur la base),
  `skip` si `mvc/admin/resources.py` est absent. Code de sortie 1 seulement sur
  `fail`. Ferme la boucle de l'accès aux données par mapping déclaré.
- **Parcours pédagogique `welcome-admin`** (`ADMIN-WELCOME-001`). Progression
  embarquée réalisée à la main (ADR-028/035/038) sous
  `packages/forge-mvc-admin/docs/welcome/` : installation, puis trois niveaux de
  trois étapes (débutant : dashboard, ressource, liste ; intermédiaire : fiche,
  création, édition ; avancé : suppression, surcharge de template, RBAC +
  `admin:doctor`), chaînés par des bilans et un récapitulatif. Nav du paquet et
  garde-fou de chaînage `test_starter_welcome_admin_nav_001`. Aucun code de
  production touché.
- **Clôture du chantier Forge Admin** (`ADMIN-CLOSING-AUDIT-001`). Tous les
  tickets `ADMIN-*` (plus `CORE-JINJA-OPTIN-LOADERS-001` et `ADMIN-WELCOME-001`)
  sont livrés : le back-office couvre le CRUD complet, la sécurité par défaut, le
  RBAC optionnel, la surcharge de templates, `admin:init` / `admin:doctor` et le
  parcours `welcome-admin`. Suite complète verte (16 298 tests) hormis un échec
  pré-existant et hors périmètre (`test_no_old_owner_name`, identité
  `official-site`). Bilan dans `docs/roadmap/forge-admin-roadmap.md` §14.


## [1.0.0-beta.17] — 2026-06-18

### Modifié

- **Tutoriel welcome-forge strict-clean** (`WELCOME-FORGE-STRICT-CLEAN-001`).
  Le squelette démarrant désormais en `typeCheckingMode: strict`, le code des
  3 paliers de welcome-forge est rendu propre en mode strict (16 fichiers).
  Corrections : le helper `_start_session` ne relit plus une session
  `dict | None` (`session_id = get_session_id(request) or create()`,
  `get_session(...) or {}`, `session.get("csrf_token", "")`) ; `int(request.route("id"))`
  reçoit `default="0"` (sûr grâce au nouvel overload) ; `fetch_one(...)["total"]`
  passe par une garde `… if row else 0` ; la méthode `json` de
  `WelcomeController` (qui masquait `BaseController.json`) est renommée
  `json_demo` (URL `/welcome/json` inchangée). Vérifié : `pyright --strict` à
  0 erreur sur les 3 bilans. L'opt-in `forge-mvc-files` utilisé par le palier
  avancé expose `py.typed` dès cette release ; son usage est donc typé en mode
  strict.
- **Accesseurs `Request` précis en typage strict (`@overload`)**
  (`HTTP-REQUEST-ACCESSOR-OVERLOAD-001`). `request.query()`, `request.form()`,
  `request.header()` et `request.route()` exposent désormais deux surcharges :
  avec un `default` de type `str`, le retour est `str` (jamais `None`) ; sans
  `default` (ou `default=None`), le retour reste `str | None`. Conséquence : le
  code idiomatique d'un débutant — `request.form("name", default="").strip()` ou
  `int(request.route("id", default="0"))` — est **sûr en mode strict** sans
  garde manuelle. Changement purement typage (implémentation runtime inchangée,
  rétro-compatible). Bénéficie à tout code applicatif, dont le tutoriel
  welcome-forge.
- **Squelette `forge new` en mode strict par défaut (payoff ADR-036)**
  (`SKELETON-VSCODE-STRICT-DEFAULT-001`, `SKELETON-VSCODE-STRICT-NOISE-REMOVE-001`).
  Le cliquet `# pyright: strict` étant terminé sur tout le cœur (`pyright core/`
  à 0 erreur), le cœur n'émet plus de `reportUnknown*` sur ses symboles via
  `py.typed`. Trois changements dans `skeleton/data` :
  1. l'override `python.analysis.diagnosticSeverityOverrides` (qui neutralisait
     les cinq règles `reportUnknown*`) est **retiré** du `.vscode/settings.json` —
     la mitigation provisoire `SKELETON-VSCODE-STRICT-NOISE-001` est remplacée
     par le traitement de la cause (règle A) ;
  2. le `.vscode/settings.json` active désormais
     `python.analysis.typeCheckingMode: "strict"` : un projet généré démarre en
     mode strict complet ;
  3. le code généré `app.py` est rendu strict-clean (annotations de
     `_error_context`, `_dev_error`, `_dispatch`, `log_message`, `get_request`,
     `process_request_thread` ; l'import lazy de l'opt-in `forge-mvc-files` porte
     un ignore ciblé, absent d'un squelette nu). `app.py` racine est synchronisé
     à l'identique (anti-dérive ADR-024). Vérifié : `pyright --strict` à 0 erreur
     sur le squelette. Les garde-fous du squelette deviennent des tests
     d'absence (override) et de présence (`typeCheckingMode`).

### Ajouté

- **Typage statique du cœur vérifié en CI (pyright) + `py.typed`**
  (`ADR-036`, `CORE-TYPING-PYRIGHT-BASELINE-001`). `core/` passe désormais
  **pyright en mode basic à 0 erreur** (41 corrigées : annotations correctes —
  `Response.__init__`, `html()`, `core.forge.get -> Any`, `db.fetch_one/execute`,
  `is_valid_slug` — et gardes de type — `get_session`, `sql_loader`, parsing
  multipart). Le gate est en mode **`standard`** (0 erreur). Le cœur **expose ses
  types** via `core/py.typed` (PEP 561, inclus
  au wheel) : un projet `forge new` bénéficie de l'autocomplétion et de la
  vérification du cœur. Une étape `pyright` est ajoutée à la CI. Cliquet à venir
  (ADR-036) : `integrations` et les opt-ins, puis passage `strict` module par
  module ; à terme, l'override `reportUnknown*` du squelette devient inutile.
- **Cliquet strict sur `core/http` (`# pyright: strict`)**
  (`CORE-TYPING-STRICT-HTTP-001`). Passé en strict :
  tout le paquet `core/http` : `response.py`, `helpers.py`, `slug.py`,
  `byte_range.py`, `router.py`, `request.py` et `__init__.py` (annotations de
  paramètres et de conteneurs ; au passage `template_manager.render` et
  `log_runtime_error` sont typés à la source ; suppressions ciblées
  `reportUnnecessaryIsInstance` sur les gardes runtime volontaires ; `router.py`
  et `request.py` adoptent `from __future__ import annotations`, un alias
  `Handler` et un contrat d'attributs explicite pour `Request`). Seul
  `debug_dumper.py` reste hors strict, à dessein (introspection d'objets
  arbitraires, `Any` par nature). L'override `reportUnknown*` du squelette est
  conservé tant que le reste du cœur (database, forms, security, templating,
  auth) n'est pas strict : `py.typed` couvrant tout le paquet `core`, ces
  modules génèreraient sinon du bruit en mode strict. Il sera retiré quand le
  cliquet aura couvert le cœur entier.
- **Garde-fou d'absence du cliquet strict** (`CORE-TYPING-STRICT-GUARD-001`).
  `tests/test_core_typing_strict_guard_001.py` verrouille l'acquis : tout fichier
  `.py` non vide de `core/` doit porter `# pyright: strict`, à la seule exception
  documentée de `core/http/debug_dumper.py`. Empêche une régression silencieuse
  (nouveau fichier du cœur sans marqueur, ou exemption non maîtrisée).
- **Cliquet strict sur `core/forge.py` + clôture du cœur (`# pyright: strict`)**
  (`CORE-TYPING-STRICT-FORGE-001`). `core/forge.py` annote son registre
  hétérogène `_cfg: dict[str, Any]` (frontière de config dynamique assumée, déjà
  documentée sur `get()`). Les `__init__` racine (`core/__init__.py`) et
  `core/sessions/__init__.py` reçoivent aussi le marqueur. **Le cliquet ADR-036
  est terminé : `pyright core/` passe à 0 erreur en mode strict sur l'ensemble
  du cœur**, seul `core/http/debug_dumper.py` reste hors strict à dessein
  (introspection d'objets arbitraires, `Any` par nature). L'override
  `reportUnknown*` du squelette peut désormais être retiré (ticket de suivi).
- **Cliquet strict sur `core/app` (`# pyright: strict`)**
  (`CORE-TYPING-STRICT-APP-001`). Passés en strict : `application.py`,
  `app_factory.py`, `wsgi.py`, `dev_server.py`, `prod_warnings.py`,
  `api_routes_loader.py`, `__init__.py`. `Application.dispatch` type
  `request: Request -> Response` ; l'adaptateur WSGI type ses callables
  (`environ: dict[str, Any]`, `start_response: Callable[..., Any]`, retours
  `Iterable[bytes]`). `load_api_routes` appelle `register_api_routes` via
  `getattr` (le `ModuleType` n'expose pas l'attribut statiquement) ;
  `build_application` annote son retour `Application` (importé sous
  `TYPE_CHECKING`). Le check d'idempotence `template_manager._renderer is None`
  porte un `# pyright: ignore[reportPrivateUsage]`. La comparaison morte
  `response.body is not None` est retirée (`Response.body` est toujours
  `bytes` — règle A). **À ce stade, `pyright core/` passe à 0 erreur sur
  l'ensemble du cœur** ; seul `core/http/debug_dumper.py` reste hors strict à
  dessein (introspection d'objets arbitraires).
- **Cliquet strict sur `core/modules` (`# pyright: strict`)**
  (`CORE-TYPING-STRICT-MODULES-001`). Passés en strict : `manifest.py`,
  `discovery.py`, `registry.py`, `files.py`, `routes.py`, `remove.py`,
  `__init__.py`. Les `dict` nus du registre deviennent `dict[str, Any]` ; les
  frontières de validation (`validate_module_manifest`, `_validate_provides`,
  `_validate_paths`, `load_installed_modules_registry`) `cast` après la garde
  `isinstance`. Le `default_factory=dict` du champ `ModuleManifest.paths`
  devient `dict[str, str]` (factory typée). `_safe_relative_path` prend `Any`
  (validateur d'entrée). `files.py` déclare un `__all__` officialisant son
  helper `_planned_file_pairs`, réutilisé par `remove.py` (`reportPrivateUsage`).
  Pyright reste à 0 erreur sur le paquet.
- **Cliquet strict sur `core/errors` (`# pyright: strict`)**
  (`CORE-TYPING-STRICT-ERRORS-001`). Passés en strict : `runtime_errors.py`,
  `runtime_error_logger.py`, `runtime_error_markdown.py`, `__init__.py`. Les
  `dict` nus deviennent `dict[str, Any]` (événements d'erreur, requête sûre,
  contexte page 500), `_extract_traceback` type son `exc_info: Any`. La variable
  d'override de répertoire de logs `_JSONL_DIR_OVERRIDE` est renommée
  `_jsonl_dir_override` : elle est mutable, donc son nom majuscule trompait
  pyright (`reportConstantRedefinition`) — règle A. Le helper de test
  `_sensitive_keys_exposed` (consommé par `tests/meta`) porte un
  `# pyright: ignore[reportUnusedFunction]` commenté. Pyright reste à 0 erreur
  sur le paquet.
- **Cliquet strict sur `core/mvc` (`# pyright: strict`)**
  (`CORE-TYPING-STRICT-MVC-001`). Passés en strict : `controller/base_controller.py`,
  `controller/registry.py`, `controller/__init__.py`, `model/validator.py`,
  `model/exceptions.py`, `view/pagination.py`. `BaseController` type toutes ses
  méthodes statiques (`request: Request` sous `TYPE_CHECKING`, `context`,
  retours `Response`/`str`/`dict[str, Any]`). `Validator` et `Pagination`
  reçoivent leurs annotations (`list[str]`, `dict[str, Any]`, retours fluent
  `-> "Validator"`). `registry.py` déclare un `__all__` qui officialise son
  helper de test `_clear_for_tests` (réexporté), corrigeant `reportPrivateUsage`
  et `reportUnusedFunction`. Pyright reste à 0 erreur sur le paquet.
- **Cliquet strict sur `core/validation` (`# pyright: strict`)**
  (`CORE-TYPING-STRICT-VALIDATION-001`). Passés en strict : `decorators.py`,
  `exceptions.py`, `__init__.py`. Le module était déjà entièrement annoté
  (`Setter = Callable[..., Any]`) ; seule la garde runtime volontaire de
  `typed()` (validation de l'argument `expected_type`) porte un
  `# pyright: ignore[reportUnnecessaryIsInstance]`. Pyright reste à 0 erreur sur
  le paquet.
- **Cliquet strict sur `core/forms` (`# pyright: strict`)**
  (`CORE-TYPING-STRICT-FORMS-001`). Passés en strict : `exceptions.py`,
  `upload_exceptions.py`, `upload_validation.py`, `fields.py` (454 l.,
  hiérarchie de champs), `form.py`, `__init__.py`. Les surfaces dynamiques des
  champs (`value`, `raw_value`, `default`, `validators`, `choices`, `coerce`,
  `form`) sont annotées (`Any`, `Callable[[Any], Any]`, `Form` sous
  `TYPE_CHECKING` pour casser le cycle `form` ↔ `fields`) ; les conteneurs
  reçoivent leur type (`list[Any]`, `dict[str, Any]`, `set[int]`). Les `cast`
  ciblés couvrent les narrowings `isinstance` qui retombaient en
  `list[Unknown]`/`dict[Unknown]` (messages de validateurs, `_first`,
  `_choice_values`, `_values`, aplatissement de `Form`, collecte de
  `FormMeta`). La validation d'upload pure (`upload_validation`) type ses
  itérables (`Iterable[Any] | None`). Pyright reste à 0 erreur sur le paquet.
- **Cliquet strict sur `core/auth` (`# pyright: strict`)**
  (`CORE-TYPING-STRICT-AUTH-001`). Passés en strict : les 10 modules du paquet
  (`exceptions.py`, `password.py`, `user.py`, `email.py`, `tokens.py`,
  `session.py`, `reset.py`, `audit.py`, `rate_limit.py`, `__init__.py`). Les
  frontières de validation (`normalize_*`, `validate_*_contract`,
  `sanitize_auth_audit_metadata`) `cast` en `dict[str, Any]` après la garde
  `isinstance` ; les dicts littéraux de branche sont annotés `dict[str, Any]`
  pour ne pas faire fuiter un type de valeur précis dans les constructions de
  dataclasses. Les validateurs privés (`_validate_password*`) prennent `Any`
  (leur rôle est justement de valider l'entrée). Les gardes runtime volontaires
  sur les API publiques typées (entrées non fiables : `user_id`, `token`,
  `email`, `password`) portent des `# pyright: ignore[reportUnnecessaryIsInstance]`
  ciblés (même précédent que `core/http`). `login_required` type ses
  `Callable[..., Any]`. Pyright reste à 0 erreur sur le paquet.
- **Cliquet strict sur `core/security` (`# pyright: strict`)**
  (`CORE-TYPING-STRICT-SECURITY-001`). Passés en strict : `api_auth.py`,
  `cookies.py`, `csp.py`, `decorators.py`, `hashing.py`, `headers.py`,
  `middleware.py`, `session.py`. Les paramètres `request`, `response` et `func`
  sont typés (`Request`, `Response`, alias `Handler` de `core/http/router`,
  importés sous `TYPE_CHECKING` pour éviter tout cycle) ; les `dict` nus
  deviennent `dict[str, Any]` / `dict[str, str]`. `csp.request_nonce` adopte
  `Generator[str | None, None, None]` (l'annotation `Iterator` est dépréciée
  avec `@contextmanager`). `hashing.py` déclare un `__all__` explicite pour ses
  réexports de `core.auth.rate_limit`. `middleware._extract_token` retire une
  garde `isinstance` morte (le contrat `Request.body: dict[str, list[str]]`
  garantit déjà une liste — règle A : retirer la cause). Pyright reste à
  0 erreur sur le paquet.
- **Cliquet strict sur `core/sessions` (`# pyright: strict`)**
  (`CORE-TYPING-STRICT-SESSIONS-001`). Passés en strict : `contract.py`,
  `manager.py`, `keys.py`, `memory_store.py`, `file_store.py`,
  `mariadb_store.py`. Les `dict` nus des signatures (contrat `SessionStore`,
  données de session, `user_data`, flash) deviennent `dict[str, Any]`. Le
  backend MariaDB type ses accesseurs injectables (`_FetchOne`, `_Execute` :
  `Callable[[str, tuple[Any, ...]], …]`). Les lectures JSON de session
  (`file_store._load`, `cleanup_expired`, `mariadb_store._load`) `cast` le
  résultat de `json.loads` en `dict[str, Any]` après la garde `isinstance`
  (objet de frontière `Any` par nature). Pyright reste à 0 erreur sur le paquet.
- **Cliquet strict sur `core/templating` (`# pyright: strict`)**
  (`CORE-TYPING-STRICT-TEMPLATING-001`). Passés en strict : `contracts.py`,
  `manager.py`, `errors.py`. Le protocole `Renderer.render` et
  `TemplateManager.render` typent désormais leur contexte en `dict[str, Any]`
  (au lieu du `dict` nu). `__init__.py` est vide, donc sans marqueur. Pyright
  reste à 0 erreur sur le paquet `core/templating`.
- **Cliquet strict sur `core/database` (`# pyright: strict`)**
  (`CORE-TYPING-STRICT-DB-001`). Passés en strict : `connection.py`, `db.py`,
  `transaction.py`, `sql_loader.py`. Le pilote `mariadb` ne fournit pas de stubs
  de types : `connection.py` accepte explicitement cette absence
  (`reportMissingTypeStubs=false`, dépendance externe) et aliase le module en
  `Any` localement pour ses accès membres (`ConnectionPool`, `PoolError`) ; les
  connexions et curseurs sont typés `Any` (objets de frontière du pilote). Les
  helpers `fetch_one`/`fetch_all`/`execute`/`insert` exposent des signatures
  complètes (`params: Sequence[Any]`, `tx: Transaction | None`, retours
  `dict[str, Any] | None` / `list[dict[str, Any]]` / `int`).
- **DX VS Code dès `forge new` : schémas JSON cœur et auto-import des classes**
  (`SKELETON-VSCODE-DX-001`). Le squelette embarque désormais les schémas
  **cœur** (`schemas/` : entity, field, common, relations, pivot) et un
  `.vscode/settings.json` qui associe les schémas aux fichiers de contrat cœur
  (`mvc/entities/*/*.json`, `mvc/entities/relations.json`) et active l'auto-import
  des classes Pylance (`python.analysis.autoImportCompletions`, indexation du
  paquet `core`). Un projet généré bénéficie ainsi de la validation/autocomplétion
  JSON et des imports automatiques sans configuration manuelle. Conformément au
  principe 8, les schémas opt-in (ex. `rbac.json` → `forge-mvc-rbac`) ne sont
  **pas** dans le squelette nu. L'association `env/*` au langage `properties`
  est conservée.
- **Le câble de l'opt-in RBAC explique la validation VS Code de `rbac.json`**
  (`OPTIN-RBAC-SCHEMA-GUIDANCE-001`). `forge opt-in:enable rbac` affiche désormais
  comment valider `mvc/security/rbac.json` dans VS Code : copier le schéma
  `rbac.schema.json` (fourni par forge-mvc) dans `schemas/`, puis ajouter
  l'association `json.schemas` à `.vscode/settings.json`. Conformément au
  principe 9, Forge **n'édite pas** le `settings.json` du projet : la guidance
  montre le bloc à coller (mode « Forge affiche »).
- **Pages d'erreur 404 et 413 du squelette : détail en développement**
  (`SKELETON-ERROR-PAGES-DEV-DETAIL-001`). Dans la même logique que la 500, le
  `app.py` du squelette passe désormais un contexte aux pages 404 (chemin
  demandé) et 413 (taille reçue), affiché **uniquement en `dev`** via le helper
  `_dev_error()` (None en production, aucune information interne exposée). Les
  templates `errors/404.html` et `errors/413.html` portent le bloc `{% if error %}`
  correspondant. Appliqué au squelette et au `app.py` racine (anti-dérive ADR-024).
- **Les 12 opt-ins en pyright strict + `py.typed`** (`FILES-TYPING-STRICT-001`,
  `IMAGES-TYPING-STRICT-001`, `MAIL-TYPING-STRICT-001`, `PIVOT-TYPING-STRICT-001`,
  `I18N-TYPING-STRICT-001`, `AUDIO-TYPING-STRICT-001`, `VIDEO-TYPING-STRICT-001`,
  `IOT-TYPING-STRICT-001`, `WORKFLOW-TYPING-STRICT-001`, `STATS-TYPING-STRICT-001`,
  `MFA-TYPING-STRICT-001`, `RBAC-TYPING-STRICT-001`). Le cliquet ADR-036 s'étend
  du cœur aux 12 paquets `forge-mvc-*` : chaque module porte `# pyright: strict`
  et chaque paquet expose `py.typed` (PEP 561, inclus au wheel via
  `[tool.setuptools.package-data]`). Conséquence concrète : un projet qui
  installe un opt-in bénéficie de l'autocomplétion et de la vérification de
  types de ce module ; le palier avancé de welcome-forge, qui utilise
  `forge-mvc-files`, devient pleinement strict-clean. Recette appliquée :
  `dict[str, Any]` aux frontières, `Protocol` pour l'adapter base de données
  (`core.database.db`), helpers `_as_dict`/`_as_list` pour isoler le typage du
  JSON, `cast` et `# pyright: ignore` ciblés sur les gardes runtime volontaires
  et les dépendances optionnelles mal typées (Pillow, paho-mqtt, referencing).
  Chaque paquet porte un garde-fou d'absence
  `tests/test_<pkg>_typing_strict_guard_001.py` (marqueur strict + `py.typed`).
- **Scan pyright CI étendu aux 12 opt-ins** (`TYPING-CI-OPTINS-001`). Le bloc
  `[tool.pyright]` du dépôt couvre désormais le cœur **et** les 12 paquets
  `forge-mvc-*` (170 fichiers, 0 erreur en mode `standard` complété des marqueurs
  stricts). `extraPaths` liste les sources de chaque paquet pour résoudre les
  imports inter-paquets (images→files, video→files…), pyright ne suivant pas les
  installs éditables PEP 660. Un vrai bug de type introduit dans un opt-in est
  désormais attrapé en CI, en complément des garde-fous pytest.

### Corrigé

- **Guidance MFA : retrait de la référence à `forge starter:build`**
  (`OPTIN-MFA-GUIDANCE-STARTER-BUILD-001`). `forge opt-in:enable mfa` renvoyait à
  `forge starter:build mfa-welcome` (commande retirée, ADR-035) ; il renvoie
  désormais au parcours manuel welcome-mfa de la documentation.
- **Page 500 du squelette : détail de l'exception affiché en développement**
  (`SKELETON-500-ERROR-CONTEXT-001`). Le `app.py` du squelette rendait
  `errors/500.html` **sans contexte**, donc le bloc `{% if error %}` restait
  toujours faux et le détail (type, message, traceback) n'apparaissait jamais,
  même en `dev`. Ajout d'un helper `_error_context()` qui ne fournit le détail
  qu'en `dev` (`APP_ENV == "dev"`, via `sys.exc_info()` et `traceback`) et `None`
  en production (aucune fuite de traceback) ; les deux rendus de la 500 (GET et
  requêtes dynamiques) passent désormais ce contexte. Aligné aussi sur le `app.py`
  racine (anti-dérive ADR-024).
- **`Response` valide le type du `status` à la construction**
  (`CORE-RESPONSE-STATUS-TYPE-001`). `Response("du texte")` plaçait silencieusement
  une chaîne dans `status` (le 1er argument positionnel est le STATUS), puis
  provoquait une erreur **différée** et cryptique à l'envoi
  (`%d format: a real number is required, not str`) sans jamais pointer le
  contrôleur fautif. `Response.__init__` lève désormais un `TypeError` explicite
  **au moment de la construction** — donc dans le frame du contrôleur, qui
  apparaît dans le traceback — avec un message orientant vers `Response.text(...)`.
  Couvre tous les chemins d'envoi (serveur de dev et WSGI). Durcissement interne
  pré-1.0.
- **Le handler d'une route est validé comme appelable à l'enregistrement**
  (`CORE-ROUTE-HANDLER-CALLABLE-001`). Même classe d'erreur différée :
  `router.add("GET", "/", X)` avec `X` non appelable ne cassait qu'au dispatch
  (`route.handler(request)`), traceback pointant le routeur et non la ligne de
  `mvc/routes.py` fautive. La route lève désormais un `TypeError` explicite **à
  l'enregistrement** (import de `routes.py`), avec un exemple correct
  (`router.add("GET", "/", HomeController.index)`). Durcissement interne pré-1.0.
- **`html()` / `render()` valident le `status` (2e argument positionnel)**
  (`CORE-RENDER-STATUS-TYPE-001`). `render("tpl", {...})` (réflexe d'autres
  frameworks où le 2e argument est le contexte) plaçait un dict dans `status` et
  provoquait une erreur différée. Le funnel `core.http.helpers.html()` — utilisé
  par `BaseController.render()` et les helpers d'erreur — lève désormais un
  `TypeError` explicite orientant vers `context=...`. Durcissement interne pré-1.0.
- **Squelette : bruit Pylance en mode strict neutralisé**
  (`SKELETON-VSCODE-STRICT-NOISE-001`). Le cœur Forge étant partiellement typé,
  le mode strict de Pylance/Pyright noyait l'utilisateur sous des
  `reportUnknown*` sur les symboles du framework (ex. `Response.text`). Le
  `.vscode/settings.json` du squelette passe désormais la famille `reportUnknown*`
  (`MemberType`, `VariableType`, `ArgumentType`, `ParameterType`, `LambdaType`) à
  `none` via `diagnosticSeverityOverrides` : le mode strict reste utile sur le
  code de l'utilisateur, sans le bruit du framework.

### Documentation

- **Convention « validation précoce des arguments critiques » + registre**
  (`CORE-EARLY-VALIDATION-CONTRACT-001`). Pattern `C.6` ajouté à
  `docs/contributing/conventions.md` : les entrées publiques du cœur appelées par
  le code applicatif valident tôt leurs arguments positionnels critiques
  (anti-erreur-différée), sans sur-valider (principe 8). Le contrat est verrouillé
  par un test méta `tests/meta/test_core_early_validation_contract_001.py` qui
  recense les entrées couvertes (Response, html/render, route) — registre à
  étendre à chaque nouvelle entrée.


## [1.0.0-beta.16] — 2026-06-16

### Ajouté

- **Chemin de production Gunicorn / WSGI généré par `forge deploy:init`**
  (`DEPLOY-GUNICORN-UNIT-001`). `forge deploy:init` matérialise le chemin de
  mise en production officiel : un `wsgi.py` à la racine du projet (exposant
  `application = create_configured_wsgi_app()`, même configuration que
  `python app.py`) et une unité `systemd/forge-app.service` lançant Gunicorn
  (`gunicorn wsgi:application --workers 4 --bind 127.0.0.1:8000`,
  `After=mariadb.service`). Doctrine : `python app.py` en développement,
  Gunicorn derrière systemd en production. La documentation est complétée d'un
  parcours de mise en production et de la réconciliation des pages
  `docs/deployment/` (`DEPLOY-PARCOURS-DOC-001`).
- **Association `env/*` au langage `properties` dans VS Code**
  (`SKELETON-VSCODE-ENV-ASSOCIATION-001`). Le squelette associe les fichiers
  `env/dev`, `env/prod`, `env/test` (motif `**/env/*`) au langage `properties`
  pour la coloration et l'édition dans VS Code ; les fichiers des dossiers dot
  du squelette (`.vscode/…`) sont désormais inclus dans le wheel.
- **Rendu HTML de `Response.debug` en grille repliable**
  (`DX-DEBUG-DUMP-RENDER-002`). La sortie de `Response.debug(...)` s'affiche en
  grille avec des sections repliables, plus lisible pour inspecter une requête.

### Modifié

- **Identifiants DB générés sans suffixes** (`NEW-DB-NAMING-NO-SUFFIX-001`,
  ADR-034). `forge new <nom>` génère `DB_NAME` et `DB_APP_LOGIN` à partir du nom
  **normalisé** du projet, sans suffixe `_db` / `_app` (ex. `forge new blog` →
  `DB_NAME=blog`, `DB_APP_LOGIN=blog` ; `forge new welcome-forge` →
  `DB_NAME=welcome_forge`). `APP_NAME` garde le nom humain (tirets, casse),
  `DB_ADMIN_LOGIN` reste `forge_admin`.
- **Les migrations s'appliquent avec le compte d'administration** (`DB-APPLY-ADMIN-CREDS-001`,
  ADR-033). `forge db:apply` et `forge migration:status` modifient la structure
  de la base : ils se connectent désormais en `DB_ADMIN_*` (`forge_admin`), et
  non plus avec le compte applicatif `DB_APP_*`. Cela corrige un défaut
  fonctionnel (en suivant `mariadb-comptes.md`, qui n'accorde que le DML à
  `forge_app`, `forge db:apply` échouait sur `CREATE command denied`) et aligne
  le code sur la doctrine : `forge_admin` pour le provisioning et les migrations,
  `forge_app` pour le runtime en DML strict. En conséquence, `forge db:init`
  n'accorde plus `CREATE/ALTER/DROP/INDEX/REFERENCES` à `forge_app` par défaut
  (un override `DB_APP_PRIVILEGES` reste possible).
- **Périmètre de la configuration upload resserré sur le core**
  (`UPLOAD-CONFIG-DECOUPLE-001`, ADR-032). Seul `upload_max_size` reste un
  réglage du noyau (il borne le corps des requêtes multipart dans
  `core/http/request.py`, avant tout opt-in). Les quatre autres clés quittent
  `core.forge` et le squelette nu : `upload_root`, `upload_allowed_extensions`,
  `upload_allowed_mime_types` sont lues depuis l'environnement par
  `forge-mvc-files`, et `upload_max_image_pixels` par `forge-mvc-images` (qui
  devient ainsi réellement configurable via `UPLOAD_MAX_IMAGE_PIXELS`). Le
  `FileField` du core prenait déjà ses listes en paramètres, il ne dépendait pas
  du registre. `forge doctor` conditionne désormais son contrôle d'extensions
  restreintes à la présence de `forge-mvc-files`. Rupture interne pré-1.0 de
  `core.forge.configure` (retrait des quatre kwargs).
- **Découplage complet du mail hors du core** (`MAIL-DECOUPLE-CORE-001`,
  ADR-031). Le noyau ne connaît plus le mail : les slots `mail_*` sont retirés
  de `core.forge` (et `core.forge.configure()` les refuse désormais),
  `_optional_mail_kwargs()` disparaît de `core.app.app_factory`, et le squelette
  nu ne pré-câble plus la plomberie `MAIL_*` (`env/example`, `config.py`,
  `app.py`). `forge-mvc-mail` lit toute sa configuration directement depuis
  l'environnement (`MailConfig.from_env()`), sans passer par le registre du
  noyau. Le défaut de `MAIL_ENABLED` absent devient `false` (zéro envoi
  accidentel). Rupture interne pré-1.0 de `core.forge.configure` (sans alias).
  Pour activer le mail : installer `forge-mvc-mail` et ajouter le bloc `MAIL_*`
  à `env/dev`.
- **`forge doctor` : MFA et RBAC recadrés en gardes-fous de sécurité**
  (`DOCTOR-SECURITY-OPTIN-001`). Le check MFA portait le libellé « opt-in »,
  ce qui laissait croire à un inventaire des briques optionnelles et invitait
  la question « pourquoi seulement MFA ». En réalité ce check est un garde-fou
  *fail-open* : du code MFA présent sans la brique qui l'applique laisse le flux
  ouvert. Le libellé devient « MFA (sécurité) » et un garde-fou symétrique est
  ajouté pour RBAC (« RBAC (sécurité) ») : il détecte un contrôle d'accès
  déclaré (contrat `mvc/security/rbac.json`, ADR-014, ou import
  `forge_mvc_rbac`) sans `forge-mvc-rbac` disponible, et émet un avertissement
  non bloquant. La détection RBAC s'appuie uniquement sur des signaux non
  ambigus (contrat, import effectif), jamais sur un mot-clé de nom de fichier,
  pour éviter les faux positifs des starters `welcome-rbac`.
- **Page d'accueil du squelette refondue** (`SKELETON-HOME-LOGO-001`,
  `SKELETON-HOME-NO-STARTER-BUILD-001`, `SKELETON-HOME-STARTERS-GRID-001`). La
  page servie par un projet `forge new` adopte le logo bandeau et un texte aux
  conventions françaises, ne propose plus `forge starter:build` (commande
  retirée, ADR-035) et présente les parcours opt-in en grille avec leurs icônes
  dédiées, chacun pointant vers son installation dans la documentation.
- **Binding du groupe public renommé `pub` → `public`**
  (`ROUTES-PUBLIC-BINDING-RENAME-001`). Dans le `mvc/routes.py` généré, le nom
  de liaison du groupe de routes publiques devient `public` (au lieu de `pub`),
  plus explicite et cohérent avec la documentation.

### Retiré

- **Génération de starters retirée, parcours réalisés à la main**
  (`ADR-STARTERS-MANUAL-001`, ADR-035). Suppression des commandes
  `forge starter:list` et `forge starter:build`, et de tout le sous-système de
  génération (`cli/starters/` : registre, builder, scaffold, injection de
  routes, et les fichiers de données embarqués). Les parcours pédagogiques
  `welcome-*` deviennent des **tutoriels manuels** suivis depuis la
  documentation : chaque palier indique le contrôleur, la vue et la route à
  créer soi-même, sur le modèle de `welcome-forge`. Conséquence directe : Forge
  n'écrit plus jamais dans `mvc/routes.py` pour un starter (principes 3 et 9).
  Le guide d'auteur de starters (`docs/philosophy/starter-author-guide.md`) est
  supprimé. Cet ADR **supersède l'ADR-023** (`starter:build` comme façon
  canonique) et **clôt le volet `starter:build` de l'ADR-030** (l'injection de
  routes par cette commande devient sans objet). La page d'accueil du squelette
  (`forge new`) ne propose plus `starter:build` : elle présente désormais les
  parcours opt-in en grille avec leurs icônes. Rupture pré-1.0 assumée, sans
  alias ni guide de migration externe.

### Corrigé

- **`forge db:init` ne dépend plus d'un droit de lecture sur `mysql.user`**
  (`DB-INIT-MYSQL-USER-GRANT-001`). Pour décider entre créer, réutiliser ou
  refuser le compte applicatif, `db:init` lisait `mysql.user`, ce qui exige le
  privilège `SELECT` sur cette table. Le compte `forge_admin` recommandé
  (`mariadb-comptes.md`) ne l'a pas : `db:init` échouait avec
  `DB_ADMIN_LOGIN=forge_admin`, défaut resté invisible tant que l'admin était
  `root`. La commande bascule désormais en mode dégradé quand la lecture de
  `mysql.user` est refusée : elle crée le compte applicatif avec
  `CREATE USER IF NOT EXISTS` et signale que la détection multi-hôte a été
  ignorée, au lieu d'échouer. Aucun privilège supplémentaire n'est requis ;
  `forge_admin` reste minimal.
- **`forge db:apply` applique le SQL des entités en `DB_ADMIN_*`**
  (`DB-APPLY-ADMIN-CREDS-FIX-001`). La commande `db:apply` (SQL des entités,
  donc DDL) se connectait encore en `DB_APP_*` alors que `forge_app` est en DML
  strict depuis ADR-033 ; elle échouait sur `CREATE TABLE`. Elle utilise
  désormais `DB_ADMIN_*`, comme `migration:apply`.
- **`forge doctor` : l'absence d'entité n'est plus un avertissement sur un
  projet vierge** (`FIX-DOCTOR-ENTITIES-SKELETON-001`). Un projet nu issu de
  `forge new` (ADR-024) n'a légitimement aucune entité : c'est l'état nominal,
  pas une anomalie. Le check « Entités » passe de `WARN` à `SKIP` (neutre, ne
  compte plus dans le total des avertissements), tout en conservant le conseil
  `forge make:entity`.
- **Resynchronisation du CSS de la landing** (`FIX-LANDING-CSS-RESYNC-001`).
  `docs/static/tailwind.css` avait dérivé de sa source `static/tailwind.css`
  (42 octets d'écart) ; `forge sync:landing` réaligne la copie, rétablissant les
  garde-fous de synchronisation.
- **`forge doctor` n'exige plus `relations.json` sur un projet nu**
  (`FIX-DOCTOR-SKELETON-RELATIONS-001`). Un projet fraîchement créé, sans
  relations déclarées, ne déclenche plus d'anomalie sur l'absence de
  `mvc/entities/relations.json`.
- **`forge update` masque la notice pip** (`FIX-UPDATE-PIP-NOTICE-001`). La
  notice de mise à jour de pip n'apparaît plus dans la sortie de `forge update`,
  qui reste lisible.
- **Identifiants DB du squelette alignés sur `forge_admin` / `forge_app`**
  (`SKELETON-ENV-DB-LOGINS-ALIGN-001`). Les gabarits d'environnement du squelette
  utilisent les identifiants canoniques (`forge_admin` pour l'administration,
  `forge_app` pour le runtime), en cohérence avec la doctrine des comptes MariaDB.
- **Rebuild du CSS Tailwind après la restructuration de la landing**
  (`LANDING-CSS-REBUILD-001`). Le CSS de la landing est régénéré pour refléter
  les classes introduites par la refonte visuelle.


## [1.0.0-beta.15] — 2026-06-08

> Trois chantiers structurants : extraction de l'internationalisation en opt-in
> (`forge-mvc-i18n`, ADR-027), convention de déclaration des routes unifiée
> (ADR-029) et refonte du tutoriel `welcome-forge` en progression continue
> manuelle sur les trois niveaux (ADR-025, ADR-028). Suivis d'un audit de
> pré-publication (sécurité, générateurs, cohérence) dont les correctifs sont
> listés ci-dessous.

### Sécurité

- **Borne haute de longueur de mot de passe** (`SEC-AUTH-PASSWORD-MAXLEN-001`).
  L'authentification imposait un minimum (8 caractères au reset) sans maximum :
  un mot de passe de plusieurs Mo envoyé à Argon2 (`hash_password` à
  l'inscription/reset, `verify_password` au login non authentifié) ouvrait un
  vecteur de déni de service, Argon2 pré-hachant l'entrée entière avant la
  partie mémoire-dure. Un plafond `_MAX_PASSWORD_LENGTH = 128` (OWASP ASVS exige
  d'autoriser au moins 64 caractères) est désormais appliqué dans
  `core.auth.password._validate_password` (rejet **avant** tout calcul Argon2,
  côté hash et verify) et dans `validate_new_password` (message d'erreur propre
  au reset). Aucun mot de passe légitime n'est affecté.
- **Rotation de session après login rendue explicite** (`SEC-AUTH-SESSION-FIXATION-001`).
  `login_user()` ne régénère pas l'identifiant de session et ne le peut pas seul
  (pas d'accès à la réponse HTTP pour réémettre le cookie). Plutôt qu'une magie
  cachée inopérante, le contrat est rendu explicite : la docstring et
  `docs/features/auth.md` exigent désormais `regenerate_session` +
  `set_session_cookie` juste après le login, comme l'applique le contrôleur de
  référence. Garde-fou ajouté.
- **Fallback d'audit sans fuite de secret** (`SEC-AUTH-AUDIT-SANITIZE-001`). En
  cas d'échec de `safe_log_auth_event`, le repli ne journalise plus `kwargs` brut
  (qui pouvait porter un secret) mais seulement la métadonnée sanitisée.
- **Consommation anti-replay TOTP atomique** (`SEC-MFA-TOTP-REPLAY-ATOMIC-001`).
  La séquence vérifier-puis-enregistrer du code TOTP passe par une primitive
  `check_and_record` sous verrou unique : deux requêtes concurrentes portant le
  même code valide ne peuvent plus être acceptées toutes les deux.

### Ajouté

- **La page 500 affiche la cause de l'erreur en mode dev** (`DX-DEV-500-ERROR-001`).
  En `APP_ENV=dev`, lorsqu'une exception non gérée produit une réponse 500, le
  dispatcher passe à `errors/500.html` un contexte `error` (type, message, trace
  Python complète) construit par `build_dev_error_context()`. Le template du
  squelette affiche ces détails dans un bloc `{% if error %}`, avec échappement
  HTML automatique (pas d'injection). En production, `build_dev_error_context()`
  retourne `None` : aucune trace n'est jamais exposée, la page reste la page
  d'erreur sobre. Les projets existants ajoutent le bloc `{% if error %}` à leur
  `mvc/views/errors/500.html` pour en bénéficier.
- **`forge-mvc-i18n` : l'internationalisation devient un opt-in** (ADR-027,
  `I18N-EXTRACT-001`). Le translator runtime (`core/i18n/` : catalogues JSON,
  locale par défaut et fallback, cache, helper `trans()`) est extrait vers le
  paquet `forge-mvc-i18n`. Le noyau conserve un **repli no-op** : le renderer
  Jinja expose toujours un global `trans` qui retourne la clé telle quelle, si
  bien que le CRUD généré (qui appelle `{{ trans(...) }}`) rend sans erreur même
  sans le paquet ; dès que `forge-mvc-i18n` est installé, le vrai `trans()`
  charge les catalogues. Même pattern que `can()` pour RBAC. Les clés de
  configuration `i18n_default_locale` / `i18n_fallback_locale` restent dans le
  registre du noyau, et la CLI de scaffolding `i18n:init` / `i18n:check`
  (autonome) reste dans le CLI cœur.

### Modifié

- **Convention de déclaration des routes** (ADR-029,
  `ROUTE-CONVENTION-ADR-029`). Une route dérive désormais mécaniquement du
  contrôleur et de la méthode visés : chemin `/<contrôleur>/<méthode>` (la
  méthode `index` donne le chemin nu `/<contrôleur>`), nom
  `<contrôleur>-<méthode>` (séparateur trait d'union), avec l'unique exception
  de la racine `/` pour `HomeController.index` nommée `home-index`. Le
  générateur `make:crud` (`ROUTE-CONVENTION-MAKECRUD-001`), le squelette
  `forge new` (`ROUTE-CONVENTION-SKELETON-001`), le tutoriel `welcome-forge`
  (`ROUTE-CONVENTION-WELCOME-001`), les générateurs `make:public-*`
  (`ROUTE-CONVENTION-PUBLIC-001`) et l'application de démonstration
  (`ROUTE-CONVENTION-DOGFOOD-001`) produisent ce format. Rupture franche sans
  alias (phase bêta pré-1.0) : elle remplace l'ancienne convention implicite de
  `make:crud` (`<ressource>_<action>`, chemins REST pluriels) et le nom
  `home_index` du squelette. Divergence transitoire assumée : les ~84 starters
  opt-in gardent encore l'ancienne convention dans leurs snippets, leur
  alignement étant déféré à des tickets dédiés. Page pratique :
  `docs/contributing/route-convention.md`.
- **`make:pivot-crud` génère du code exécutable** (`FIX-PIVOT-CRUD-API-001`). Le
  sous-CRUD pivot s'appuyait sur une API runtime inexistante (`Response.render`,
  `Response.redirect`, `app.route`) et des signatures incompatibles ; il utilise
  désormais `BaseController.render`/`redirect`, lit les identifiants via
  `request.route(...)` et déclare ses routes au format ADR-029.
- **Accesseurs de `Request` renommés par leur source** (ADR-026,
  `HTTP-REQUEST-PARAM-RENAME-001`) : `request.param` devient `request.query`
  (query string) et `request.route_param` devient `request.route` (paramètre de
  route dynamique). Rupture franche sans alias (phase bêta pré-1.0) : tous les
  appels sont migrés (core, starters, modules opt-in, tutoriel welcome-forge,
  tests, doc). Les attributs `request.params` / `request.route_params` et les
  clés de `request.data` restent inchangés. `form`, `json`, `header`, `file`
  étaient déjà nommés par leur source et ne changent pas.
- **welcome-forge : tutoriel continu manuel sur les trois niveaux** (ADR-025,
  ADR-028, `STARTER-WELCOME-FORGE-DOC-CONTINUITY-001`, `WELCOME-FORGE-AVANCE-001`).
  Chaque niveau (débutant, intermédiaire, avancé) se construit à la main dans un
  seul mini-projet qui grandit palier après palier, avec un `mvc/routes.py`
  cumulatif montré à chaque étape, au lieu de starters indépendants. Pages
  francisées (retrait des tirets cadratins). Bootstrap de session corrigé pour
  que le jeton CSRF des formulaires ne soit plus vide (`WELCOME-FORGE-CSRF-SESSION-001`).

### Corrigé

- **`make:public-form` : accesseur de champ corrigé** (`FIX-PUBLIC-FORM-POSTDATA-001`).
  Le contrôleur généré lisait les champs via `request.post_data` (attribut
  inexistant) et plantait à toute soumission ; il utilise désormais
  `request.form(...)`.
- **`make:public-*` : détection robuste du point d'injection** (`FIX-PUBLIC-ROUTES-MARKER-001`).
  La fabrique `router = Router()` est détectée par analyse AST et non plus par
  sous-chaîne, ce qui évite qu'un commentaire trompe le générateur et corrompe le
  `mvc/routes.py` de l'utilisateur.
- **Catalogue d'opt-ins complété** (`FIX-OPTIN-CATALOG-001`). `forge-mvc-mail`,
  `forge-mvc-pivot` et `forge-mvc-i18n` sont enregistrés : `opt-in:install` ne
  répond plus « inconnu » pour eux et `opt-in:list` les surface (12 opt-ins
  officiels).

### Retiré

- **Les 11 starters buildables du niveau débutant welcome-forge** sont retirés
  de `cli/starters/data/` et du contrat public gelé, ramené de 107 à 96
  starters (ADR-025, `STARTER-WELCOME-FORGE-DROP-DATA-001`). Les niveaux
  intermédiaire et avancé, ainsi que tous les parcours opt-in, restent des
  starters `forge starter:build`. La numérotation des starters n'est plus une
  plage dense `1..N` (unicité seule).

### Documentation

- ADR-025, ADR-027, ADR-028 et ADR-029 ajoutés ; ADR-030 (injection de routes
  par commande explicite et portée de la règle 4.3) au statut **proposé** ;
  index ADR et navigation MkDocs à jour. Resync de `CLAUDE.md` (12 paquets,
  retrait de la mention `forge-mvc-media` supprimé, table ADR étendue à 030).
  Section « Nouveautés » de la landing rafraîchie vers beta.15.

### Tests

- Garde-fous de l'audit de pré-publication : accesseurs `Request` du contrôleur
  `make:public-form`, détection AST du marqueur de routes, catalogue d'opt-ins
  (12, sans `media`), code généré par `make:pivot-crud`, anti-fixation de session,
  sanitisation du fallback d'audit, consommation atomique de l'anti-replay TOTP,
  et `csrf_token` runtime.


## [1.0.0-beta.14] — 2026-06-07

> Bootstrap par squelette dédié : `forge new` produit enfin un projet
> réellement nu (ADR-024).

### Modifié

- **`forge new` matérialise un squelette de projet dédié** au lieu de cloner le
  dépôt Forge (ADR-024, `NEW-MATERIALIZE-001`). Le projet généré ne contient
  plus le framework (`core/`, `cli/`, `packages/`, `tests/`, `docs/`) : il
  dépend de `forge-mvc` et récupère le `core` depuis le paquet installé. Le
  squelette curé est embarqué dans `skeleton/data/` et distribué en
  package-data (`SKELETON-TREE-001`, `SKELETON-PKGDATA-001`,
  `SKELETON-REGISTRY-001`).
- **`forge new` ne clone plus le dépôt** : le flag `--ref`, la constante
  `_FORGE_REPO` et la dépendance réseau/git pour les fichiers disparaissent
  (`NEW-MATERIALIZE-001`, `NEW-CLI-CLEANUP-001`). `git` reste requis pour le
  `git init` du projet.
- **`forge new` produit toujours un projet nu** : le flag `--starter` est retiré ;
  `forge starter:build` devient la seule façon officielle de construire un
  starter (ADR-023, `CLI-NEW-DROP-STARTER-001`).

### Corrigé

- Alignement de la documentation sur `forge starter:build` et retrait du bloc
  « raccourci » des pages de palier (`DOC-STARTER-BUILD-ALIGN-001`).
- Test des liens production de la landing aligné sur la réorganisation
  `docs/deployment/` (`LANDING-WSGI-LINK-TEST-FIX-001`).

### Documentation

- ADR-023 (`forge starter:build` canonique) et ADR-024 (bootstrap par squelette
  dédié) ajoutés ; index ADR et navigation MkDocs mis à jour. Documentation
  d'installation et de référence nettoyée des mentions `forge new --ref`.

### Tests

- Garde-fous ajoutés : `test_skeleton_tree_001`, `test_skeleton_pkgdata_001`,
  `test_skeleton_registry_001`, `test_new_core_dep_001`, `test_skeleton_guard_001`
  (squelette nu, distribution wheel/sdist, matérialisation, neutralité, projet
  généré sans `core/`).


## [1.0.0-beta.13] — 2026-06-06

> Dernière beta **fonctionnelle** (consolidation post-beta.12).
> Roadmap : [`docs/roadmap/beta13-roadmap.md`](docs/roadmap/beta13-roadmap.md).

### Unification du modèle opt-in (ADR-016)

- Famille de commandes canonique **`forge opt-in:install / remove / enable /
  disable / list`** (à tiret). `opt-in:install`/`remove` affichent la commande
  pip/pipx sans rien exécuter ; `enable`/`disable` sont *kind-aware* (câblage
  réel pour les opt-ins routiers — iot ; informatif pour bibliothèques et
  transversaux). Anciennes commandes `optin:enable` / `optin:list` **retirées**
  (rupture assumée pré-1.0, sans alias).
- **Squelette neutre** : `mvc/routes.py` livré par défaut n'expose plus que
  `GET /` → landing ; auth, MFA et le starter `welcome` ne sont plus
  pré-câblés (relocalisés dans leurs starters/opt-ins).
- Vocabulaire unifié : « module officiel » → **« opt-in »** (glossaire
  `docs/reference/vocabulaire-opt-in.md`) ; « package » = véhicule de
  distribution. Le système `module:*` (module **local**) reste distinct
  (cycle de vie d'auteur — ADR-016 A2).

### Refonte des starters — un parcours welcome par opt-in

- **107 starters** numérotés de façon contiguë, organisés en **parcours
  pédagogiques par niveau** : la progression cœur `welcome-forge` (11 paliers
  débutant → avancé) plus **un parcours `welcome-<module>` pour chacun des 10
  opt-ins dotés d'un parcours** (iot, video, images, files, audio, mfa, rbac,
  workflow, stats, mail). Préambule d'installation en tête de chaque parcours
  (`pip install --pre forge-mvc-<module>` + `forge starter:build`).
- **Nettoyage** (`STARTERS-DROP-OBSOLETE-001`) : retrait des starters obsolètes
  (`first-crud`, `first-crud-generated`, `users-core-auth`, mono-démos
  `welcome-optin-iot/mfa/video`) et de leurs docs ; archives métier lourdes
  retirées. Le starter d'email a été relocalisé de `welcome-forge` vers le
  parcours `welcome-mail` (`mail-welcome`).

### Slugs canoniques (feature phare)

- **Type de slug canonique** (`core/http/slug.py`) : `slugify` déterministe,
  `is_valid_slug` (contrat de validation unique), génération depuis une colonne
  `source`. Une seule façon officielle de produire un slug (principe 11).
- **SQL/CRUD auto-généré** prenant en charge le slug (colonne, index unique,
  lookup `get_<entité>_by_slug`) et **routing public par slug**.
- **Documentation** dédiée et **une application réelle construite avec** (Phase
  dogfood) pour valider le parcours de bout en bout.

### Forge Video — nouvel opt-in `forge-mvc-video`

- Opt-in **`forge-mvc-video`** (**Beta**) : chaîne complète upload → traitement
  → lecture. Stockage uuid-based, extraction de métadonnées (`ffprobe`),
  **transcodage MP4 (H.264/AAC)**, génération de poster, **lecture en streaming
  HTTP Range**.
- Commandes CLI : `video:doctor` (diagnostic), `video:init` (migration `videos`),
  **`video:upload <fichier> [--title]`** (entrée d'upload officielle),
  `video:process` (worker de transcodage), **`video:cleanup`** (purge des vidéos
  `failed` / fichiers orphelins, dry-run par défaut, anti-traversal).
- FFmpeg/ffprobe traités comme **binaires système** (pas de dépendance pip) ;
  le module se branche sans eux (mode serveur de médias), `video:doctor`
  signale leur absence. Publié sur PyPI avec les autres distributions.

### Dégraissage du core vers des opt-ins

- **`forge-mvc-pivot`** (ADR-021, `PIVOT-EXTRACT-001`) : le service « pivot
  advanced » (associations `many_to_many` enrichies) et le générateur
  `make:pivot-crud` sont extraits du core vers un opt-in dédié.
- **`forge-mvc-mail`** (ADR-022, `MAIL-EXTRACT-001`) : l'email (composition,
  transports interchangeables, templates Jinja, CLI `mail:*`) est extrait du
  core vers un opt-in, accompagné de son parcours `welcome-mail`.
- **Réorganisation de la racine de `core/`** (`CORE-REORG-001`) : regroupement
  en sous-paquets `core/app/` (application, factory WSGI, dev-server,
  prod-warnings) et `core/errors/` (gestion des erreurs runtime) ; `slug`
  rejoint `core/http/`. Racine réduite à `forge.py` + `__init__.py`, sans
  changement de comportement (entrée Gunicorn : `core.app.wsgi:create_configured_wsgi_app`).

### Robustesse & production

- **`forge run` survit aux crashes** de l'application (relance automatique +
  garde anti-boucle après crashes rapides répétés).
- Sécurité uploads : vérification du **contenu réel des images** avant écriture.
- Sécurité uploads : **plafond anti-décompression-bomb** sur les images
  (`upload_max_image_pixels`, défaut 24 Mpx) — la surface est contrôlée dès
  l'en-tête, avant décodage/écriture, et `DecompressionBombError` est désormais
  capturé proprement à la génération des variantes (SEC-UPLOAD-DECOMPRESSION-BOMB-001).
- **Production-readiness** : `forge doctor` durci, `forge migration:apply
  --dry-run`, endpoint de *health*, `forge update` robuste, et **checklist de
  déploiement** documentée.
- **Dogfood MariaDB** : parcours réel exécuté sur MariaDB (go/no-go de clôture)
  validant slugs + CRUD généré.

### Packaging & documentation

- **Dépendance `forge-mvc` des opt-ins unifiée** à `>=1.0.0b13,<2` sur les
  onze opt-ins (fin de la cohabitation `==1.0.0b13` / `>=1.0.0b5` — une seule
  politique de borne, principe 11).
- `requirements-dev.txt` installe désormais **`forge-mvc-video` en éditable** :
  sa suite de tests n'est plus silencieusement skippée (`importorskip`) en CI.
- `tools/release-validate.sh` : correction d'un bug `set -e` qui masquait
  silencieusement un échec d'audit ; l'audit `pip-audit` des dépendances de dev
  distingue désormais une **vulnérabilité** (bloquante) d'une **résolution
  impossible avant publication** (œuf-poule, non bloquante) ; nouveau mode
  opt-in **`--with-packages`** qui build les 12 distributions + `twine check` en
  local (RELEASE-VALIDATE-PACKAGES-001).
- Documentation du contrat CLI : `forge migration:apply --dry-run` documenté
  dans l'aide intégrée et `docs/reference/cli-commands.md`
  (DOCS-MIGRATION-DRY-RUN-001).
- Cadrage Alpha de `forge-mvc-iot` (installation séparée, exclu de
  `forge-mvc[all]`).
- Distribution : exclusion des tests du sdist, exclusion du bytecode des
  artefacts ; build CI étendu à `forge-mvc-iot` et `forge-mvc-video`.
- `BETA13-CLOSING-AUDIT-001` **vert**, versions bumpées **b13** sur le core et
  les onze opt-ins.
- Réorganisation de la documentation (`docs/guide/`, `features/`,
  `philosophy/`, `reference/`, `release/`, `deployment/`), index des ADR,
  URLs harmonisées vers `forgemvc.com`.


## [1.0.0-beta.12] — 2026-05-29

### Forge IoT — nouveau module opt-in `forge-mvc-iot`

- Module IoT opt-in complet : contrat MQTT `forge/{site}/{device_id}/telemetry`,
  subscriber `paho-mqtt`, stockage `iot_events` (migration packagée,
  repository), et API HTTP JSON en lecture
  (`/api/iot/events`, `/api/iot/events/{site}/{device_id}`,
  `/api/iot/devices/{site}/{device_id}/count`).
- CLI : `forge iot:doctor` (diagnostic statique ; `--db` table + schéma,
  `--mqtt` broker), `forge iot:init` (copie la migration), `forge iot:listen`
  (écoute + insère, arrêt propre + résumé), `forge iot:simulate`
  (mesures factices ; profils `temperature`/`humidity`/`presence`/`energy`).
- Sécurité : **TLS MQTT** (`FORGE_IOT_MQTT_TLS_ENABLED`,
  `FORGE_IOT_MQTT_TLS_CA_FILE`) branché dans les clients ; **Bearer token**
  optionnel sur l'API HTTP (`FORGE_IOT_API_TOKEN`).
- Pédagogie : guides Mosquitto local, smoke test local, Bac Pro / BTS CIEL,
  exemple ESP32, évaluation Arduino R4 ; starter `welcome-iot`.
- `forge-mvc-iot` publié sur PyPI (statut Alpha) au même titre que les
  autres opt-ins.

### Opt-ins côté projet utilisateur — structure `optins/`

- Convention `optins/` : couche de branchement local explicite des opt-ins
  (registre `optins/registry.py`, pas de découverte automatique) ; les
  paquets restent distribués dans `packages/forge-mvc-*`.
- `forge optin:enable iot` (dry-run par défaut, `--apply` ; branche
  prudemment `mvc/routes.py` si la structure est reconnue) et
  `forge optin:list` (lecture seule, états absent/partiel/activé).
- Le starter `welcome-iot` génère cette structure `optins/iot/`.

### Qualité

- Référence CLI complétée (commandes IoT + opt-ins).
- Suite de tests complète revenue à **0 échec** avant release
  (corrections de garde-fous méta et de références de doc obsolètes,
  sans affaiblir les garde-fous).


## [1.0.0-beta.11] — 2026-05-27

### Expérience développeur — point d'entrée unifié et inspectabilité

- `forge run` officialise le point d'entrée du serveur de développement
  (FORGE-RUN-COMMAND-001) — refus du serveur intégré en `APP_ENV=prod`
  avec message WSGI clair, délégation à `scripts/dev-server.sh` ou
  `python app.py` en `dev`.
- Superviseur d'autoreload `cli.dev_reloader`
  (DEV-SERVER-AUTORELOAD-001) — polling `stat()` sur `app.py`,
  `config.py`, `env/dev`, `mvc/**/*.{py,html,json,sql}`, `core/**/*.py`,
  stdlib uniquement. Désactivable via `--no-reload`.
- Convention d'inspection des classes API publiques
  (API-INSPECTABLE-OBJECTS-CONVENTION-001) — `Request` et `Response`
  exposent `.data` avec masquage automatique
  (Authorization/Cookie/password/csrf/token/api_key/secret) ; helpers
  `text/html/json/debug` côté `Response` ; convention documentée dans
  `docs/reference/http.md`.
- Squelettes générés typés (DX-TYPED-SKELETONS-001) — imports
  `Request`/`Response` automatiques et annotations
  `def action(request: Request) -> Response:` sur toutes les actions
  publiques du starter `welcome`, des générateurs `make:crud`,
  `make:public-*` et des 6 starters officiels.
- Erreur développeur claire quand `BaseController.render(...)` cible une
  vue inexistante (DX-RENDER-ERROR-001) — `TemplateNotFoundError`
  pédagogique en `dev`, réponse minimale en `prod`, aucun stacktrace.
- Rendu HTML pédagogique pour `Response.debug(obj)`
  (DX-DEBUG-DUMP-HTML-001) — `core.http.debug_dumper` (masquage des clés
  sensibles, profondeur bornée, détection des cycles) ; comportement
  prod inchangé (404 minimal, aucune fuite).

### Starter d'entrée — Bonjour Forge

- Refonte pédagogique du starter `welcome` (STARTER-BONJOUR-FORGE-001) —
  alias `bonjour` / `bonjour-forge` / `bienvenue` / `7`. Progression :
  `index` retourne `Response.text("Bonjour Forge")`, puis
  `/welcome/greet?name=…` (`request.param(...)`),
  `/welcome/inspect` (`Response.debug(request.data)`), enfin
  `/welcome/cycle` introduit `BaseController.render(...)`. Vue
  `welcome/index.html` retirée.

### Documentation, installation et landing

- Clôture documentaire « Bonjour Forge » (DX-DOCS-BONJOUR-FORGE-CLOSE-001)
  — renommage `docs/15-minutes.md` → `docs/bonjour-forge.md`, refonte
  autour du parcours développeur livré.
- Guide officiel d'installation Windows + WSL (INSTALL-WSL-DOCS-001 +
  INSTALL-WSL-DOCS-FIELD-FIX-001) — `docs/install/windows-wsl.md`,
  parcours WSL Ubuntu 24.04 + VS Code Remote WSL + pipx + Node 20 +
  MariaDB avec compte `forge_admin@localhost` dédié.
- Section « Installer Forge selon votre usage » de la landing
  (LANDING-INSTALL-CARDS-001) — 4 cards homogènes
  (`windows-wsl`, `pipx-user`, `core-dev`, `production`).
- Consolidation `docs/install/core-dev.md`
  (INSTALL-CORE-DEV-DOCS-AUDIT-001) — 9 sections couvrant l'installation
  éditable, les 5 validations canoniques avant commit, Tailwind, opt-ins.
- Réorganisation `docs/install/` (INSTALL-DOCS-STRUCTURE-001) —
  `git mv` des 7 pages d'installation sous `docs/install/{index,pipx,
  core-dev,mariadb,vm-debian,windows,github,production}.md`, mise à jour
  des liens internes et de la nav MkDocs.
- Réalignement de la landing canonique sur son contrat public actuel
  (LANDING-PUBLIC-CONTRACT-REALIGN-001) — décisions de suppression
  assumées (5e card Installation, FAQ, Stack technos, compteur tests) ;
  tests landing réalignés.

### Audit

- `BETA11-POST-DOCS-CONSOLIDATION-AUDIT-001` — audit de l'état réel
  après tous les tickets DX/docs/install/landing ; décision OK pour
  lancer `BETA11-DX-CLOSING-AUDIT-001`.
- `BETA11-DX-CLOSING-AUDIT-001` — découpe et commit du WIP en
  5 commits cohérents, suite complète à 15 051 tests passants
  (6 skipped), décision GO pour `RELEASE-BETA11-001`.
- `RELEASE-BETA11-001` (ce ticket) — bump version `1.0.0b10` →
  `1.0.0b11`, validations release, build distributions, twine check,
  tag SemVer `v1.0.0-beta.11`.

### Notes

- Forge core reste autonome ; les opt-ins (`forge-mvc-rbac`,
  `forge-mvc-workflow`, `forge-mvc-stats`, `forge-mvc-mfa`,
  `forge-mvc-media`) restent indépendants.
- La production publique reste WSGI + Gunicorn + reverse proxy.
  `forge run` reste explicitement un outil de développement.


## [1.0.0-beta.10] — 2026-05-25

### Stabilisation B10

- Alignement des tests de durcissement session avec le contrat courant `first_name` / `last_name` + alias legacy `prenom` / `nom`.
- Validation release robuste SemVer ↔ PEP 440 (`tools/release-validate.sh` : mode `--convert`, validation explicite des deux formes en entrée).
- Validation release indépendante du `PATH` : interpréteur Python explicite via `PYTHON_BIN="${PYTHON:-python3}"`, modules invoqués par `python -m <module>`.
- Statut PyPI des opt-ins officiel aligné dans la documentation (5 opt-ins publiés depuis beta.9).
- Headers de sécurité appliqués aussi au chemin WSGI (helper partagé `core/security/headers.py`, HSTS conditionné à `wsgi.url_scheme == "https"`).
- Tests opt-in protégés par `pytest.importorskip(...)` pour les environnements core-only.
- Workflow GitHub Pages passé en `mkdocs build --strict`.
- Audits dépendances (`pip-audit`, `npm audit`) bloquants en validation release ; workflow informatif distinct conservé.
- Défense symlinks uploads/statics verrouillée par tests (`realpath` + `commonpath` + 3 garde-fous source-level sur `app.py`).
- Validation explicite de `FORGE_MFA_SECRET_KEY` au boot côté opt-in MFA (refus des placeholders : `change-me`, `default`, `dev`, etc.).
- Garde `python app.py` contre exposition publique en production (`APP_ENV=prod` + `APP_HOST` ∈ `{0.0.0.0, ::, [::]}` → refus de démarrer).
- Référence CLI restructurée avec parcours rapides + index alphabétique de 63 commandes.
- Imports documentaires validés par tests méta AST (378 tests, 0 import framework invalide).
- Audit fixtures `autouse=True` et correction d'isolation `tests/test_templating.py::_setup`.
- Landing : section contact statique `mailto:forgemvc@gmail.com` (pas de route `/contact`, pas de `ContactController`) ; identité publique alignée sur Roger Lequette / forgemvc@gmail.com.
- Politique `docs/` source canonique vs `site/` artefact MkDocs documentée + verrouillée par tests méta.
- Politique `DB_ADMIN_*` réservée au provisioning CLI documentée ; runtime applicatif sur `DB_APP_*` uniquement ; protection `env/*.local` dans `.gitignore`.
- Roadmap B10 consolidée en 5 sections (Bloquants / Critiques / Durcissement / Cohérence release / Clôture), compteurs fragiles retirés, audit pré-release validé `GO`.
- Convention de tag Git alignée : SemVer publique (`v1.0.0-beta.10`), jamais PEP 440 (`v1.0.0b10`).

### Sécurité

- 0 vulnérabilité détectée par `pip-audit` (runtime + dev) et `npm audit --omit=dev`.
- Renforcement WSGI (headers partagés app.py/WSGI), MFA (validation clé Fernet au boot), uploads/statics (défense symlinks vérifiée), `app.py` prod guard, release validation (Python explicite, audits bloquants).

### Notes

- Forge core reste autonome.
- Les opt-ins (`forge-mvc-rbac`, `forge-mvc-workflow`, `forge-mvc-stats`, `forge-mvc-mfa`, `forge-mvc-media`) restent optionnels et publiés séparément sur PyPI.
- La production publique reste recommandée via WSGI + Gunicorn + reverse proxy. `python app.py` reste un serveur de développement.


## [1.0.0-beta.9] — 2026-05-24

### Added / Changed

- Phase B9 close — release de consolidation production encadrée.
- CLI: `--help`/`-h` interceptés au dispatcher avant exécution métier (12 tickets `CLI-HELP-FLAGS-*`, série close).
- WSGI: `core.app.wsgi.create_configured_wsgi_app()` — factory configurée partagée avec `app.py` via `core.app.app_factory.build_application()`.
- WSGI: warnings production émis à la construction de l'application (`MemorySessionStore` en `APP_ENV=prod`).
- HTTP: `APP_TRUSTED_PROXIES` + `resolve_client_ip()` — `X-Real-IP` honoré uniquement derrière proxy fiable, validation `ipaddress`.
- Sessions: helpers centralisés `core.security.cookies.set_session_cookie()` / `clear_session_cookie()`, migration des contrôleurs Auth et MFA.
- Sessions: `MemorySessionStore.cleanup_expired()` aligné sur File/MariaDb, retourne `int`.
- Sessions: dédomainisation `_normalize_legacy_user()` — `first_name`/`last_name` canoniques (alias FR conservés temporairement).
- Sécurité: `core/security/api_auth.py` utilise `hmac.compare_digest` (comparaison constant-time du token Bearer).
- Sécurité MFA: dépendance `cryptography>=46.0.7,<47` (sortie de la plage vulnérable `>=42,<46`).
- CI: `forge-mvc-media` ajouté à la matrice de build des opt-ins.
- Documentation: nouvelles pages [Déploiement WSGI minimal](wsgi-deployment.md) et [Limites de production](production-limits.md).
- Landing: nav enrichie (`CRUD` + `API`), section Aperçu beta.9, section API à 6 cartes, formule de continuité.

### Packaging

- Tous les packages alignés en `1.0.0b9`.
- `package.json` et `package-lock.json` alignés en `1.0.0-beta.9` (garde-fou méta verrouille la cohérence).
- Pas de changement de dépendance runtime côté core.
- Aucun upload PyPI effectué dans cette release de préparation.

### Security

- `X-Real-IP` ne peut plus être falsifié par un client direct (proxy fiable obligatoire).
- Token API Bearer comparé en temps constant.
- `cryptography` MFA hors zone vulnérable.

## [1.0.0-beta.8] — 2026-05-22

### Added / Changed

- Requalification de `forge-mvc-media` en Alpha.
- Requalification de `forge-mvc-mfa` en Alpha.
- Chiffrement des secrets TOTP MFA au repos via Fernet.
- Documentation opt-ins alignée.
- Préparation des packages `media` et `mfa` pour publication future.

### Security

- Les secrets TOTP MFA ne sont plus stockés en clair.
- `FORGE_MFA_SECRET_KEY` devient obligatoire pour le module MFA.

### Packaging

- Tous les packages sont alignés en `1.0.0b8`.
- Aucun upload PyPI effectué dans cette release de préparation.

## [1.0.0-beta.7] — 2026-05-22

Release documentation pédagogique — Premier pas refondu, logo MkDocs, cycles MVC visuels.

- refonte pédagogique du starter Welcome : diagrammes ASCII, cycles HTML/JSON Mermaid, tables route→concept (DOC-PREMIER-PAS-PEDAGOGY-001) ;
- agrandissement logo MkDocs via CSS dédié (DOCS-NAV-LOGO-SIZE-001) ;
- vues du starter visibles par défaut : `<details open>` (DOC-PREMIER-PAS-CODE-VISIBLE-001) ;
- onglets Cycle HTML/JSON remplacés par diagrammes Mermaid + admonitions (DOC-PREMIER-PAS-CYCLES-TABS-VISUAL-001) ;
- nettoyage final documentation Premier pas (DOC-PREMIER-PAS-FINAL-CLEANUP-001).

Non publié dans cette release :

- `forge-mvc-media`, encore source-only ;
- `forge-mvc-mfa`, encore Pre-Alpha (SEC-MFA-SECRET-ENCRYPTION-001) ;
- packages opt-ins `forge-mvc-rbac`, `forge-mvc-workflow`, `forge-mvc-stats` : publication prévue dans PYPI-OPTINS-001.


## [1.0.0-beta.6] — 2026-05-21

Release post-corrections terrain — RBAC contractuel, Pivot advanced, DX, test terrain et corrections.

- JSON Schema contractuel pour entités, relations, RBAC, pivot (ENTITY-CONTRACT-*) ;
- RBAC déclaratif opt-in : rbac:validate, rbac:audit, make:crud intégration (RBAC-*) ;
- Pivot advanced : PivotAdvancedService, contraintes, erreurs UX (PIVOT-ADVANCED-*) ;
- make:pivot-crud : générateur opt-in de sous-CRUD pivot (PIVOT-CRUD-*) ;
- test terrain FIELD-TEST-APP-001 : flux complet validé ;
- correction F-001 : clé canonique `"name"` documentée clairement (FIELD-FIX-001) ;
- correction F-002 : structure `mvc/entities/<nom>/<nom>.json` documentée (FIELD-FIX-001) ;
- correction F-003 : garde make:crud limité au côté source de la relation (FIELD-FIX-M2M-GUARD-001) ;
- audit post-corrections terrain validé (RELEASE-AUDIT-002).

Non publié dans cette release :

- `forge-mvc-media`, encore source-only ;
- `forge-mvc-mfa`, encore Pre-Alpha (SEC-MFA-SECRET-ENCRYPTION-001) ;
- packages opt-ins `forge-mvc-rbac`, `forge-mvc-workflow`, `forge-mvc-stats` : publication prévue dans PYPI-OPTINS-001.


## [1.0.0-beta.5] — 2026-05-17

Release de consolidation de la Phase 12 — Sécurité, résilience et préparation PyPI opt-ins.

- audit auth : logger best-effort et résilience documentée (AUTH-AUDIT-LOGGER-RESILIENCE-001) ;
- contrat des en-têtes de sécurité documenté et verrouillé (SECURITY-HEADERS-DOC-LOCK-001) ;
- audit des noms PyPI des opt-ins réalisé (OPTIN-PYPI-NAMES-CHECK-001) ;
- préparation locale des opt-ins publiables (OPTIN-PYPI-PUBLISH-PREPARE-001) ;
- extras optionnels `rbac`, `workflow`, `stats` et `all` synchronisés (VERSION-SYNC-OPTIN-EXTRAS-001) ;
- publication groupée du core et des opt-ins publiables `forge-mvc-rbac`, `forge-mvc-workflow`, `forge-mvc-stats`.

Non publié dans cette release :

- `forge-mvc-media`, encore source-only après extraction Phase 11 ;
- `forge-mvc-mfa`, encore Pre-Alpha, bloqué par `SEC-MFA-SECRET-ENCRYPTION-001`.


## [1.0.0-beta.4] — 2026-05-17

Release de consolidation des phases 7 à 10.

- clarification du périmètre audit/auth/MFA/RBAC ;
- warning `forge doctor` pour MFA opt-in manquant ;
- politique de stockage des secrets MFA documentée ;
- politique de publication des opt-ins documentée ;
- tests méta réorganisés, politique de rotation définie, prune prudent appliqué ;
- règle behavior-first documentée ;
- audit des doublons d'API publique réalisé ;
- langage des starters normalisé côté Python / SQL ;
- conventions de langage des starters documentées ;
- surface publique de `BaseController` auditée et documentée.


## [1.0.0-beta.3] — 2026-05-16

Corrections post-audit Phase 2 — sécurité CSRF, routes modules explicites.

### Sécurité

- `tests/meta/test_security_meta_no_csrf_inequality_001.py` : garde-fou méta
  empêchant toute comparaison naïve de tokens CSRF (`==` ou `!=`) dans les
  fichiers canoniques de sécurité (ticket SECURITY-META-NO-CSRF-INEQUALITY-001).

### Modules

- `core/modules/routes.py` : suppression du mécanisme d'injection automatique
  de routes (`prepare_module_route_injection`, `ModuleRouteInjectionResult`,
  `ModuleRoutesAlreadyInjectedError`, `_build_injection_block`, `_module_marker`).
  `generate_module_routes()` reste le seul mécanisme — explicite
  (ticket MODULE-ROUTES-INJECTION-REMOVE-001).
- `docs/module-author-guide.md`, `docs/reference/modules.md` : documentation
  du contrat explicite de branchement de routes de modules
  (ticket MODULE-ROUTES-EXPLICIT-DOC-001).

### Métriques

- Tests : 9 909 passed, 3 skipped (suite complète validée)


## [1.0.0-beta.2] — 2026-05-16

Corrections post-audit Phase 1 et infrastructure release Phase 2.

### Documentation

- `README.md` : retrait de `pyotp` de la liste des dépendances runtime du core
  (ticket README-RUNTIME-DEPS-CLEANUP-001) — PyOTP est une dépendance de `forge-mvc-mfa`,
  pas du core.
- `docs/contributing.md` : même correction sur la liste des dépendances runtime.
- `docs/release-policy.md` : alignement du classifier PyPI `forge-mvc` sur
  `4 - Beta` (ticket PYPI-CLASSIFIER-BETA-ALIGN-001) ; ajout section
  « Verrouillage packaging » (ticket PACKAGE-LOCK-DOC-001).
- `docs/release-local.md` : section « Environnement de validation release »
  documentant la procédure reproductible (ticket RELEASE-VALIDATION-ENV-LOCK-001).
- `docs/positioning.md` : mention de version mise à jour.

### Infrastructure

- `scripts/release_check.sh` : nouveau script de validation release locale
  (ticket RELEASE-CHECK-SCRIPT-001). Mode standard (pytest, compileall, mkdocs
  --strict, git diff --check, git status) et mode `--full` (+ build wheel +
  twine check). Ne publie rien, ne crée aucun tag.

### Packaging

- `pyproject.toml` : classifier `Development Status :: 5 - Production/Stable`
  corrigé en `4 - Beta` (ticket PYPI-CLASSIFIER-BETA-ALIGN-001).


## [1.0.0-beta.1] — 2026-05-15

Première publication publique du code source de Forge et publication sur PyPI.

### Infrastructure PyPI

- Publication PyPI réalisée : `forge-mvc==1.0.0b1` disponible sur [PyPI](https://pypi.org/project/forge-mvc/1.0.0b1/).
- TestPyPI validé avant PyPI — artefacts `twine check` PASSED.
- Installation pip validée : `python -m pip install --pre forge-mvc`.
- Installation pipx validée : `pipx install --pip-args="--pre" forge-mvc`.
- `--pre` est nécessaire car `1.0.0b1` est une préversion bêta PEP 440.
- Extras `[rbac]`, `[workflow]`, `[stats]`, `[all]`, `[mfa]` non publiés — modules opt-in en mode source-only via GitHub (`OPTIN-PYPI-PUBLISH-001`).

### Documentation

- `docs/installation-pipx.md` : note sur l'état de publication des opt-in.
- `docs/installation.md` : section « Modèle de packages » mise à jour.
- `docs/release-policy.md` : table de publication PyPI par package ajoutée.
- `packages/forge-mvc-mfa/README.md` : instructions d'install alignées sur
  le mode source-only (extras PyPI temporairement indisponibles).

### Métriques

- Tests : 9685 passed, 3 skipped (suite complète validée)

---

> **Historique de développement pré-publication.** Les sections ci-dessous
> documentent l'historique des itérations de consolidation interne de Forge
> avant sa première publication publique (1.0.0-beta.1). Elles sont conservées
> à titre de référence. La version publique actuelle est **Forge 1.0.0-beta.1**.

## [3.0.5] — 2026-05-14

Articles de la landing page rendus cliquables (lien vers la doc correspondante).
Aucune rupture d'API publique. Aucune nouvelle fonctionnalité framework.

### Frontend

- `LANDING-ARTICLES-CLICKABLE-001` : 21 articles de la landing page wrappés dans
  `<a href="...">` pointant vers la page de documentation correspondante. Effet
  `group-hover:` sur le titre et la bordure de la carte.

### Tests

- `LANDING-ARTICLES-CLICKABLE-001` : nouveau garde-fou `test_landing_articles_clickable_001.py`
  (22 tests : 21 articles wrappés, hrefs vers docs existantes, cursor-pointer, group-hover h3).

### Métriques

- Tests : 9670 (3.0.4) → 9693 (3.0.5)
- Garde-fous méta : +1 nouveau

## [3.0.4] — 2026-05-14

Consolidation post-audit ChatGPT 3.0.3 (mini-Scénario D, 4 tickets). Aucune
rupture d'API publique. Aucune nouvelle fonctionnalité.

### Documentation

- `ROADMAP-3.0.3-CURRENT-STATE-001` : roadmap reflète l'état courant (3.0.4),
  Scénario D ajouté avec les 4 tickets ciblés.
- `PYTEST-CORE-ONLY-CONTRACT-CLARIFY-001` : CHARTE_DOC.md section 7 réécrite avec
  3 environnements nommés (A. Runtime core-only, B. Test core-only, C. Test complet).
- `DEV-INSTALL-CONTRACT-FIX-001` : ordre canonique `pip install -e .` avant
  `requirements-dev.txt` aligné dans installation.md, installation-github.md,
  README.md et CONTRIBUTING.md. Section « modules PyPI » du README corrigée
  (mode source-only).

### Tests

- `RELEASE-TESTS-CURRENT-VERSION-001` : tests de release version-agnostiques
  (lisent pyproject.toml, plus de version hardcodée). `test_release_3_0_0_stable_001`
  et `test_release_3_0_2_patch_stable_001` remplacés par
  `test_release_current_version_001`. `test_roadmap_3_0_consistency_001` rendu
  dynamique.
- `DEV-INSTALL-CONTRACT-FIX-001` : nouveau garde-fou `test_install_contract_001.py`.
- `PYTEST-CORE-ONLY-CONTRACT-CLARIFY-001` : nouveau garde-fou
  `test_pytest_core_only_contract_clarified_001.py`.

### Métriques

- Tests : 9663 (3.0.3) → 9670 (3.0.4)
- Garde-fous méta : +3 nouveaux, 2 anciens supprimés (remplacés)

## [3.0.3] — 2026-05-14

Consolidation post-audit renforcé (11 tickets de qualité). Aucune rupture
d'API publique. Aucune nouvelle fonctionnalité.

### Documentation

- `DOCS-AUTH-RBAC-IMPORTS-001` : 6 imports MFA/RBAC corrigés dans auth.md
  et rbac.md (ImportError à la copie-colle)
- `DOCS-REFERENCE-API-SYMBOLS-001` : 10+ symboles français alignés sur le
  code anglais réel dans reference/api.md
- `DOCS-VERSION-VARIABLE-001` : hook mkdocs lit pyproject.toml ; 20+ fichiers
  passés à `{{forge_version}}`, `{{forge_tag}}`, `{{python_min}}`
- `DOCS-COMPAT-OPTIONAL-DEPS-001` : pyotp clarifié comme dépendance d'extra
  `[mfa]`, retirée du tableau runtime
- `PACKAGES-OPTIN-INSTALL-001` : 11 mentions install corrigées vers le mode
  source-only, 4 packages opt-in marqués `Private :: Do Not Upload`
- `ROADMAP-ANCHOR-FIX-001` : ancre cassée corrigée dans la roadmap
- `CLI-HELP-HIDDEN-COMMANDS-001` : 8 commandes CLI sorties de l'ombre

### Tests et garde-fous (7 nouveaux tests méta)

- `DOCS-SYMBOL-VALIDATION-001` : vérifie que chaque bloc python de la doc
  s'importe vraiment (révélation : 4 imports doc cassés supplémentaires)
- `PYTEST-DEFAULT-ENV-CONTRACT-001` : contrat charte 'pytest en core-only'
  restauré, 28 fichiers reçoivent pytest.importorskip
- `PYTEST-CORE-ONLY-DEPS-EXTRAS-001` : extension aux deps d'extras (pyotp),
  9 fichiers réorganisés, validation en venv core-only : 8394 passed, 0 errors
- `PACKAGING-CLASSIFIER-STABLE-001` : forge-mvc core passe
  `5 - Production/Stable`

### Métriques

- Tests : 9628 (3.0.2) → 9678 (3.0.3)
- Garde-fous méta : +7 nouveaux tests
- Imports doc cassés : 16+ → 0 (vérifié par garde-fou)
- Mentions versions obsolètes : 20+ fichiers → 0 (variabilisé)
- Commandes CLI cachées : 8 → 0 (vérifié par garde-fou)
- `pytest` en core-only : 30 errors → 0

## [3.0.2] — 2026-05-13

Scénario C — consolidation production-ready (12 tickets livrés, série en cours).

### Stabilisé — Packaging et distribution

- `PACKAGING-SRC-LAYOUT-001` (T2) : migration vers une structure `src/` pour
  l'isolation des packages. `forge-mvc` et les 4 modules utilisent désormais
  `packages/<dist>/src/` comme root — évite les imports parasites depuis la
  racine lors des builds.
  Garde-fou : `tests/meta/test_packaging_src_layout_001.py`.

- `PACKAGING-WHEEL-CONTENT-001` (T2b) : vérification du contenu des 5 wheels
  post-restructuration. Chaque wheel déclaré dans `packages/` contient exactement
  les modules attendus — aucun fichier de développement ou test embarqué.
  Garde-fou : `tests/meta/test_wheel_content_001.py`.

### Stabilisé — Tests et reproductibilité

- `PYTEST-REPRODUCIBLE-001` (T1) : `pyproject.toml` fixe `addopts = "--tb=short"`
  et seed aléatoire stable pour garantir un ordre de collecte pytest reproductible
  entre machines. Garde-fou : `tests/meta/test_pytest_reproducible_001.py`.

### Stabilisé — MFA

- `MFA-SECRET-HASH-DEPRECATION-RESOLVE-001` (T4) : retrait définitif de la propriété
  dépréciée `AuthMfaFactor.secret_hash` (introduite en SEC-MFA-SECRET-NAMING-001).
  `totp_secret` est désormais le seul accès. Aucun consommateur interne trouvé.
  Garde-fou : `tests/meta/test_mfa_secret_hash_remove_001.py`.

- `MFA-PRODUCTION-DECISION-001` (T3) : décision documentée — `forge-mvc-mfa` reste
  en **Pre-Alpha** pour Forge 3.x. La production requiert un audit tiers (secret TOTP
  stocké en clair, absence de chiffrement au repos). Section "Limites MFA Production"
  ajoutée à `docs/stability-contract.md`.
  Garde-fou : `tests/meta/test_mfa_production_decision_001.py`.

### Stabilisé — OIDC et RBAC

- `OIDC-EXCEPTIONS-CLEANUP-001` (T15) : retrait des constantes `AUTH_EVENT_OIDC_*`
  (6 constantes) de `core.auth.exceptions` — vestiges post-ADR-004. Plus aucun code
  productif OIDC dans le core.
  Garde-fou : `tests/meta/test_oidc_exceptions_cleanup_001.py`.

- `CORE-RBAC-PLUGIN-MECHANISM-001` (T14) : mécanisme de plugin Jinja —
  `register_jinja_context_provider(provider_fn)` dans `core.mvc.controller`.
  Permet aux modules opt-in d'injecter du contexte Jinja sans que le core ne les
  nomme. Respecte ADR-004 (périmètre core strict) et le principe 8 (noyau minimal).
  Garde-fou : `tests/meta/test_core_rbac_plugin_mechanism_001.py`.

### Documentation — Cohérence série 3.x

- `DOCS-3.0.1-VERSION-SWEEP-001` (T7) : balayage de toutes les mentions de version
  dans la documentation. Références `2.x` et `3.0.0` non pertinentes remplacées par
  `3.0.1` ou `3.x` selon le contexte.
  Garde-fou : `tests/meta/test_docs_no_stale_versions_001.py`.

- `STABILITY-CONTRACT-3.0-REFRESH-001` (T8) : refonte de `docs/stability-contract.md`
  — titre et garanties actifs alignés sur la série 3.x. Ajout sections modules opt-in
  (RBAC Beta, Workflow Beta, Stats Beta, MFA Pre-Alpha) et mécanisme
  `register_jinja_context_provider`.
  Garde-fou : `tests/meta/test_stability_contract_3_x_001.py`.

- `CLAUDE-MD-3.0.2-REFRESH-001` (T9) : `CLAUDE.md` mis à jour de Forge 2.10.0 →
  Forge 3.0.2. Série 3.x explicite, note `packages/` reformulée pour refléter l'état
  post-T2/T2b, section 10 refondue.
  Garde-fou : `tests/meta/test_claude_md_3_0_2_001.py`.

- `SESSION-KEYS-DOCSTRING-001` (T19) : docstring `core/sessions/keys.py` corrigé —
  "avant Forge 3.1" → "avant Forge 3.0.1". La version de livraison de la migration
  FR→EN était incorrecte. Garde-fou : `tests/meta/test_session_keys_docstring_001.py`.

- `ADR-TITLES-3.0-REFRESH-001` (T17) : décision documentée de conserver les titres
  ADR-001 ("Forge 2.x") et ADR-002 ("Forge 2.x") — ces ADR sont des archives
  historiques, pas des documents actifs (Principe 11 — archives datées). Garde-fou
  de cohérence titre ↔ warning historique ajouté.
  Garde-fou : `tests/meta/test_adr_historical_warnings_001.py`.

## [3.0.1] — 2026-05-12

Phase G — consolidation pré-publication (15 tickets livrés).

### Stabilisé — Sessions

- `SESSIONS-LANG-ALIGN-001` (G1) : migration FR→EN des clés de session internes
  (`authentifie` → `authenticated`, `utilisateur` → `user`). Fallback de lecture
  sur les anciennes clés pour les sessions existantes. Les clés legacy seront
  retirées en Forge 4.0. Garde-fou : `tests/meta/test_sessions_lang_align_001.py`.

- `SESSION-LIMITS-STATUS-AUDIT-001` : audit et documentation des limites du
  `MemorySessionStore` en production (pas de persistence entre redémarrages, pas
  de partage multi-processus). Clarification du statut "développement/test uniquement"
  dans `docs/reference/sessions.md`.

### Stabilisé — CLI et packaging

- `CLI-AUTH-INIT-OIDC-SQL-001` (G8) : retrait des instructions SQL OIDC
  (`auth_oidc_accounts.sql`, `auth_oidc_identities.sql`) de la commande
  `forge auth:init`. Cohérence avec ADR-004 (OIDC supprimé du core).
  Garde-fou : `tests/meta/test_cli_auth_init_oidc_sql_001.py`.

- `PACKAGING-FORGE-MODULE-001` (G6) : restructuration de `forge.py` (module
  racine plat) vers un package `forge/`. Prépare l'installation pip fiable —
  `forge.py` causait des problèmes en mode édition (`pip install -e .`).
  Garde-fou : `tests/meta/test_packaging_forge_module_001.py`.

### Décision documentée

- `AUTH-EXTRA-EXTRACT-DECISION-001` (G2) : décision documentée sur l'extraction
  `auth_extra` — les helpers avancés (reset mot de passe, invitations) restent dans
  `core/auth/` pour Forge 3.x. L'extraction est déférée à Forge 4.0.
  Garde-fou : `tests/meta/test_auth_extra_extract_decision_001.py`.

### Documentation

- `DOCS-V1-V2-TERMINOLOGY-001` (G4) : nettoyage des références terminologiques
  v1/v2 dans la documentation. Mentions "Forge 1.x" actives remplacées par "Forge 3.x"
  dans les guides courants. Garde-fou : `tests/meta/test_docs_v1_v2_terminology_001.py`.

- `DOCS-GETTING-STARTED-CONSOLIDATE-001` (G5) : consolidation des parcours
  getting-started — doublons supprimés, exemples alignés sur Forge 3.0.
  Garde-fou : `tests/meta/test_docs_getting_started_consolidate_001.py`.

- `DOCS-RELEASE-SECTION-AUDIT-001` (G3) : audit de la section release —
  `docs/release.md` enrichi de la procédure de release 3.x, checklist PyPI
  multi-distributions mise à jour.
  Garde-fou : `tests/meta/test_docs_release_section_audit_001.py`.

- `STARTER-AUTH-MFA-PROFILE-001` (G7) : page profil MFA ajoutée au starter
  `utilisateurs-auth` — activation TOTP, codes de récupération, désactivation
  MFA depuis le profil. Garde-fou : `tests/meta/test_starter_auth_mfa_profile_001.py`.

### Correctifs documentation pré-publication (PR1–PR5)

- `DOCS-CLI-COMMANDS-REFERENCE-001` (PR1) : nouvelle section "Référence des commandes
  CLI" avec toutes les commandes `forge` annotées.
  Garde-fou : `tests/meta/test_docs_cli_commands_reference_001.py`.

- `DOCS-INSTALLATION-WINDOWS-001` (PR2) : documentation de l'installation sur
  Windows (MariaDB via Chocolatey/winget, Python 3.12 via winget, gestion chemins).
  Garde-fou : `tests/meta/test_docs_installation_windows_001.py`.

- `LANDING-SEARCH-BAR-001` (PR3) : ajout d'une barre de recherche dans la landing.
  Garde-fou : `tests/meta/test_landing_search_bar_001.py`.

- `LANDING-POSITIONNEMENT-VISIBILITY-001` (PR4) : amélioration de la visibilité
  du positionnement Forge dans la landing (titre hero, section d'encart).
  Garde-fou : `tests/meta/test_landing_positionnement_visibility_001.py`.

- `DOCS-RELEASE-LOCAL-STARTERS-COUNT-001` (PR5) : correction du compteur de
  starters locaux dans la documentation de release.
  Garde-fou : `tests/meta/test_docs_release_local_starters_001.py`.

### Publié

- `RELEASE-3.0.1-PATCH-STABLE-001` : bump coordonné vers `3.0.1` — 6 fichiers
  `pyproject.toml`, `forge/version.py`, `core/__init__.py`. Tag git `v3.0.1`.
  Build des 5 wheels `3.0.1`.

## [3.0.0] — 2026-05-12

### Corrigé — Synchronisation CSS de la landing

- `PRE-RELEASE-FIX-LANDING-CSS-SYNC-001` : correction de trois sujets
  liés à la génération de la landing page.

  **`forge sync:landing` étendue** : la commande synchronise désormais
  `static/` (CSS, JS, images) vers `docs/static/`, en plus du HTML.
  Auparavant, seul `mvc/views/landing/index.html` → `docs/index.html`
  était copié. Ajout de `sync_static()` dans `cli/assets/sync_landing.py`.

  **`package.json build:css` corrigé** : Tailwind v4 a déplacé le
  binaire CLI dans `@tailwindcss/cli`. Le script utilise désormais
  `npx @tailwindcss/cli` pour invoquer la bonne commande.

  **`CONTRIBUTING.md` enrichi** : section "Modifier la landing page"
  documentant le workflow complet (édition HTML, régénération CSS,
  synchronisation vers `docs/`).

  Justification : sans cette correction, modifier des classes Tailwind
  dans la landing causait des bugs visuels silencieux (dropdowns non
  stylés, texte invisible) parce que `docs/static/tailwind.css` restait
  sur l'ancienne version.

## [3.0.0rc1] — 2026-05-12

Release candidate 1 pour Forge 3.0. Fenêtre d'observation interne de 48h
avant le tag stable (`v3.0.0`). Pas de publication PyPI à cette étape.

### Publié — RELEASE-3.0.0-RC1-001

- Bump coordonné des versions vers `3.0.0rc1` :
  `pyproject.toml` racine, `packages/forge-mvc/pyproject.toml`,
  4 modules (`forge-mvc-mfa`, `forge-mvc-rbac`, `forge-mvc-workflow`,
  `forge-mvc-stats`), `forge.py` (`_FORGE_VERSION`, `_FORGE_DEFAULT_REF`),
  `core/__init__.py`.
- Optional-dependencies du core bumpées vers `==3.0.0rc1`.
- `docs/reference.md` : version API actualisée à `3.0.0rc1`.
- Build des 5 wheels `3.0.0rc1` (core + 4 modules).
- Validation locale : `forge --version` → `Forge 3.0.0rc1`.
- Tag git : `v3.0.0-rc1`.

**Découverte non listée** : `packages/forge-mvc/pyproject.toml` (miroir
setuptools tracké git) contenait aussi `2.5.0` — bumped en `3.0.0rc1`.

### Documenté — Synchronisation venv/source

- `PRE-RELEASE-FIX-VENV-STALE-001` : ajout dans `CONTRIBUTING.md`
  d'une section sur la synchronisation du venv local et de l'installation
  pipx avec le code source actuel.

  **Contexte** : l'audit pré-release avait révélé que `forge --version`
  affichait `Forge 2.3.0` alors que le code source était à 2.5.0 — le
  venv et pipx pointaient vers un wheel précompilé jamais régénéré.

  **Correctif appliqué** : wheel 2.5.0 reconstruit depuis le code actuel
  (`python -m build --wheel`) et réinstallé dans le venv local et via pipx.
  `forge --version` retourne maintenant `Forge 2.5.0` dans les deux
  environnements.

  **Procédure documentée** :

  ```bash
  python -m build --wheel
  pip install --force-reinstall --no-deps dist/forge_mvc-X.Y.Z-py3-none-any.whl
  pipx install --force dist/forge_mvc-X.Y.Z-py3-none-any.whl
  ```

  **Cause structurelle** : Forge utilise `py-modules = ["forge"]` qui ne
  supporte pas le mode édition fiable. La restructuration vers un package
  `forge/` est planifiée en post-3.0 (`PACKAGING-FORGE-MODULE-001`).

### Corrigé — Liens cassés dans la landing page

- `PRE-RELEASE-FIX-LANDING-LINKS-001` : correction de 5 URLs cassées
  dans la landing page identifiées par l'audit pré-release.

  **4 liens starters** : préfixe `starter-app-` retiré, regroupés sous
  `/starters/`. Le starter 01 a aussi été renommé (`contacts` →
  `contact-simple`).

  | Avant | Après |
  |---|---|
  | `starter-app-01-contacts/` | `starters/01-contact-simple/` |
  | `starter-app-02-utilisateurs-auth/` | `starters/02-utilisateurs-auth/` |
  | `starter-app-03-carnet-contacts/` | `starters/03-carnet-contacts/` |
  | `starter-app-04-suivi-comportement-eleves/` | `starters/04-suivi-comportement-eleves/` |

  **1 lien roadmap** : la section Roadmap n'a pas d'`index.md`, le slug
  `/roadmap/` ne résolvait rien. Corrigé en `/roadmap/forge-roadmap/`.

  **Source canonique** : `mvc/views/landing/index.html`. La version
  générée `docs/index.html` est régénérée via `forge sync:landing`.

  Tests garde-fous : `tests/meta/test_pre_release_fix_landing_links_001.py`
  (16 tests : absence des anciens slugs, présence des nouveaux, cohérence
  source ↔ généré).

### Corrigé — Alignement requires-python avec ADR-006

- `PRE-RELEASE-FIX-PYPROJECT-PYTHON-001` : `pyproject.toml` racine aligné sur
  Python 3.12+ conformément à ADR-006 :
  - `requires-python` : `>=3.11` → `>=3.12`
  - Classifier `Programming Language :: Python :: 3.11` retiré
  - `[tool.ruff] target-version` : `py311` → `py312`
  - 4 modules (`forge-mvc-mfa`, `forge-mvc-rbac`, `forge-mvc-stats`,
    `forge-mvc-workflow`) : ajout classifiers `Python :: 3.13` et `Python :: 3.14`
    pour cohérence avec le `pyproject.toml` racine

  Tests garde-fous : `tests/meta/test_pre_release_fix_pyproject_python_001.py`
  (11 tests : requires-python, classifiers 3.11 absent, target-version, 3.13/3.14 présents).

### Corrigé — Import top-level de module optionnel dans le code framework

- `PRE-RELEASE-FIX-RBAC-IMPORT-001` : suppression des 3 imports top-level de
  modules optionnels (`forge_mvc_rbac`, `forge_mvc_workflow`) dans le code
  framework qui rendaient la CLI inutilisable sans les extras :
  - `cli/entities/crud/controller_builder.py` : import `normalize_permission_code`
    déplacé en lazy conditionnel (seulement si l'entité déclare des permissions RBAC)
  - `core/mvc/controller/base_controller.py` : import `make_auth_jinja_context, make_can`
    migré en `try/except ImportError` dans `render()` (dégradation gracieuse)
  - `integrations/jinja2/renderer.py` : import `make_workflow_jinja_helpers`
    migré en `try/except ImportError` dans `__init__()` (dégradation gracieuse)

  Tests garde-fous : `tests/meta/test_pre_release_fix_rbac_import_001.py`
  (6 tests : analyse AST des 3 racines framework + bootstrap CLI sans crash).

### Validé — Audit pré-release

- `PRE-RELEASE-AUDIT-3.0-001` : exécution d'un audit pré-release complet
  avant publication du RC. Six familles testées :
  - Install nouvel utilisateur (venv jetable)
  - Cycle complet d'un starter (bloqué — voir correctifs)
  - Lints stricts (pytest 8 920 passants, ruff ALL 22 155 violations cosmétiques,
    mkdocs --strict exit 0, compileall OK, git diff --check OK)
  - Cross-version Python (3.12 : 8 920 tests ✓ ; 3.14 : 1 764 tests ✓ ; 3.13 : non testé)
  - Audit dépendances/sécurité (urllib3 CVE — dépendance dev uniquement, non bloquant)
  - Documentation cohérente (5 liens cassés landing — voir correctifs)

  Rapport complet : `docs/audits/pre-release-3.0-audit-001.md`.

  **Trouvailles principales** :
  - Bloquant RC : `PRE-RELEASE-FIX-RBAC-IMPORT-001` — import top-level
    `forge_mvc_rbac` dans `cli/entities/crud/controller_builder.py`
    rend `forge` inutilisable sans le module optionnel
  - Important : `PRE-RELEASE-FIX-LANDING-LINKS-001` — 5 liens cassés landing
    (4 starters anciens chemins + 1 roadmap sans index)
  - Important : `PRE-RELEASE-FIX-PYPROJECT-PYTHON-001` — `requires-python`
    déclaré `>=3.11` au lieu de `>=3.12` (ADR-006)
  - Important : `PRE-RELEASE-FIX-VENV-STALE-001` — copie figée `forge.py`
    2.3.0 dans `.venv` (ne touche pas les utilisateurs finaux)

  **Verdict** : audit demande corrections — RC non publiable en l'état.

### Documenté — Refonte de la landing page pour Forge 3.0

- `DOCS-LANDING-PAGE-3.0-001` : refonte intégrale de la landing page
  (`mvc/views/landing/index.html`, régénérée vers `docs/index.html`
  via `forge sync:landing`) pour refléter l'état Forge 3.0.

  **Navigation refondue** : 5 entrées principales + 2 dropdowns natifs
  (`<details>`/`<summary>`) : Forge / Installation / Starters / Documentation
  + Dropdown **Briques** (Core / Modules / CLI) + Dropdown **Projet** (Roadmap / GitHub).

  **Hero actualisé** : version strip `v3.0.0 · Python 3.12+ · MariaDB ·
  MVC serveur · Open source`, label encart terminal `workflow Forge 3.0.0`.

  **Section Core refondue** : H2 `L'écosystème Forge.`, structurée en
  deux sous-sections — **Le core Forge** (17 cartes) et **Modules officiels opt-in**
  (4 cartes : MFA, RBAC, Workflow, Stats — avec distributions PyPI et ancre `#modules`).

  **Section Stack** (NOUVELLE) : 6 cartes présentant les fondations techniques
  (Python 3.12+, MariaDB 11.x, Jinja2, HTMX, Alpine.js, Tailwind) avec liens
  vers la documentation officielle de chaque techno.

  **Section Workflow** : correction typo (`auditable` → `auditables`).

  **Section Installation** : note modules optionnels ajoutée après le terminal
  parcours utilisateur (`pipx install "forge-mvc[all]"`).

  **Section État** : refonte totale — bloc gauche `Forge 3.0.0` (ouverture open
  source, core minimal, 4 modules, 41 tickets) ; bloc droite `Après 3.0 /
  Stabilisation` remplace l'ancien `Auth/User avancée`.

  **Section Documentation** : `Plus de 8000 tests` (au lieu de 7000) + bouton
  **Charte** vers `CHARTE_DOC.md` sur GitHub.

  Tests garde-fous : `tests/meta/test_docs_landing_page_3_0_001.py` (53 tests).

## [2.10.0] — 2026-05-11

### Consolidation des roadmaps (DOCS-CONSOLIDATE-ROADMAPS-001)

Réduction de 5 fichiers roadmap à 2 actifs. Enrichissement de `forge-roadmap.md`
avec la section **Phase 14 — Refonte vers Forge 3.0**.

**Archivés vers `docs/history/`** (fichiers désormais obsolètes ou remplacés) :

- `forge_post_2_0_consolidation_roadmap.md` — journal de consolidation post-2.0,
  remplacé par la roadmap unifiée lors de `ROADMAP-UNIFIED-001`.
- `forge-roadmap-post-2.0.md` — feuille de route post-2.0 partielle, tickets livrés
  dans la roadmap unifiée.
- `forge-roadmap-ux.md` — phases 5-10 (DX, E2E, sécurité, release, doc, API JSON),
  toutes terminées et documentées dans la roadmap unifiée.

**Restent dans `docs/roadmap/`** :

- `forge-roadmap.md` — source unique de priorité
- `forge-design-roadmap.md` — roadmap du projet compagnon Forge Design

**Section Phase 14 ajoutée à `forge-roadmap.md`** : sous-phases 14.1
(durcissement pré-refonte — 13 tickets), 14.2 (infrastructure 3.0 — ADR-003/007,
packaging multi-distributions), 14.3 (reconstruction cœur minimal — 14 tickets
d'extractions et nettoyage), 14.4 (clôture pré-3.0, à venir) et déférés post-3.0.

**Autres corrections** :

- `CLAUDE.md` section 8 : `forge-roadmap-post-2.0.md` → `forge-roadmap.md`
- `docs/contributing.md` : références au fichier archivé remplacées par `CHANGELOG.md`
- `tests/test_roadmap_unified.py` et `tests/meta/test_module_lifecycle_doc_001.py` :
  chemins mis à jour (`docs/roadmap/` → `docs/history/`)
- `mkdocs.yml` : section Roadmap épurée (1 entrée en moins), archives ajoutées
  dans la section Historique

Guard-fou : `tests/meta/test_docs_consolidate_roadmaps_001.py` (18 tests).

### Actualisation des ressources d'entrée pour Forge 3.0 (GETTING-STARTED-3.0-001)

Chasse aux mentions obsolètes dans les 4 ressources d'entrée de Forge.

**README.md** :

- Titre : `2.5.0` → `3.0.0`
- ADR : ajout de ADR-001, ADR-002, ADR-008 (liste complète des 8 ADR)
- Nouvelle section "Modules officiels disponibles" : `forge-mvc-mfa`,
  `forge-mvc-rbac`, `forge-mvc-workflow`, `forge-mvc-stats` avec
  installation via extras (`forge-mvc[all]`)
- `core/security/hashing.py` : mention clarifiée (legacy PBKDF2,
  vérification conservée pour compatibilité, création supprimée en 3.0)
- `cmd/` : section "déprécié" reécrite en "supprimé en Forge 3.0" ;
  arbre de fichiers nettoyé ; mentions d'exécution retirées
- Tableau "Ce que Forge n'est pas" : `cmd/make.py` → "supprimé en Forge 3.0"
- Références git clone : `v2.5.0` → `v3.0.0`
- Lien ADR-002 : label nettoyé (suppression de "Forge 2.x")

**docs/15-minutes.md, docs/guide.md, docs/app-complete-tutorial.md** :
propres — aucune mention obsolète trouvée à l'audit.

**Correction de tests** :

- `test_lang_migration_001.py` : exclusion de `test_getting_started_3_0_001.py`
  du grep (le garde-fou liste les noms français à des fins de vérification)
- `test_publication_2_0_version_001.py` : tests README/git-clone adaptés
  pour refléter l'anticipation de la version 3.0.0

Guard-fou : `tests/meta/test_getting_started_3_0_001.py` (73 tests).

### Conventions internes de Forge (DOCS-INTERNAL-CONVENTIONS-001)

Consolidation des 18 patterns émergents de la phase 14 dans
`docs/contributing/conventions.md`. Briefing opérationnel pour tout
contributeur (humain ou agent IA) sur les techniques de travail éprouvées.

**18 patterns documentés en 4 sections** :

- **A. Audit avant action** (5 patterns) : audit 5 racines, `.gitignore`,
  historique git, production interne, doc référencée par les tests
- **B. Tests : conventions et patterns** (6 patterns) : helpers locaux pour
  formats legacy, `module.__file__`, `PROJECT_ROOT` partagé, classification
  sémantique des `_001`, généraliser plutôt que supprimer, cohérence des
  noms de fonctions de tests
- **C. Code : architecture** (5 patterns) : lock + delegate,
  `register_<module>_routes`, note « Module extrait », garde-fous
  documentaires, word boundaries pour renommages
- **D. Documentation : structure** (3 patterns) : MkDocs strict + liens
  hors `docs/`, `docs/history/` comme mémoire brute, section « Historique »
  dans la nav

Chaque pattern : énoncé court + ticket d'origine + exemple ou règle pratique.

**CLAUDE.md section 9** : liste détaillée retirée, résumé thématique conservé,
pointer vers `docs/contributing/conventions.md` comme source canonique.

**`mkdocs.yml`** : entrée "Contribuer" restructurée en "Pour contribuer" avec
deux sous-entrées (Vue d'ensemble, Conventions de travail).

Guard-fou : `tests/meta/test_docs_internal_conventions_001.py` (29 tests).

### Une seule charte canonique (DOCS-CHARTER-DEDUP-001)

`CHARTE_DOC.md` (racine) et `docs/charter.md` étaient deux fichiers identiques
(473 lignes, 14 659 octets chacun). Application du principe 11 de la charte v2.

**Avant** : risque de divergence à la première édition d'un seul des deux fichiers.

**Après** :

- `CHARTE_DOC.md` (racine) est la **source canonique unique**. Note d'autorité
  ajoutée en tête.
- `docs/charter.md` est un **alias court** (~35 lignes) qui présente un aperçu
  des 11 principes et renvoie vers le fichier canonique.
- L'intégration MkDocs reste fonctionnelle (entrée "Philosophie > Charte v2"
  pointe toujours vers `docs/charter.md`).
- Les liens actifs dans `CLAUDE.md`, `README.md`, `docs/adr/007-*.md` pointaient
  déjà vers `CHARTE_DOC.md` — aucune modification nécessaire.

Guard-fou : `tests/meta/test_docs_charter_dedup_001.py` (8 tests).

### Découpage de docs/reference.md (DOCS-REFERENCE-SPLIT-001)

Refonte de la documentation de référence : `docs/reference.md` (4831 lignes)
découpé en 11 sous-fichiers thématiques dans `docs/reference/`.

**`docs/reference.md` devient un index** (≤ 108 lignes) avec le schéma Mermaid
et des liens vers les sous-fichiers.

**Sous-fichiers créés** :

- `reference/api.md` — API Forge complète (routes, entités, CRUD de base, CLI)
- `reference/workflow.md` — Statuts et transitions (module `forge-mvc-workflow`)
- `reference/stats.md` — Statistiques (module `forge-mvc-stats`)
- `reference/auth-mfa.md` — Challenge MFA (module `forge-mvc-mfa`)
- `reference/crud.md` — Relations avancées et CRUD enrichi
- `reference/pages-publiques.md` — Pages publiques sans authentification
- `reference/modules.md` — Modules Forge et intégration
- `reference/profils.md` — Profils de projet et endpoint `/health`
- `reference/tests-e2e.md` — Tests HTTP, MariaDB, CSRF
- `reference/sessions.md` — Sessions et concurrence
- `reference/audit-auth.md` — Audit auth, cookies, headers de sécurité, uploads

**Adaptations autorisées** dans chaque sous-fichier :

- Titre de niveau 1 (passage de `##` à `#`, suppression des mentions "Phase X")
- Note « Module extrait » en tête des fichiers `workflow.md`, `stats.md`, `auth-mfa.md`
- Liens internes corrigés pour le nouveau niveau d'arborescence

**Autres mises à jour** :

- `mkdocs.yml` : section Référence enrichie avec la hiérarchie des 11 sous-fichiers
- `docs/security.md` : lien `reference.md#coresecurity` → `reference/api.md#coresecurity`
- 8 fichiers de tests mis à jour pour pointer vers les bons sous-fichiers
  (`api.md`, `modules.md`, `profils.md`)
- `tests/test_docs_config.py` : label nav `"API et CLI"` → `"API Forge complète"`

Guard-fou : `tests/meta/test_docs_reference_split_001.py` (51 tests).

### forge module:routes n'écrit plus dans mvc/routes.py (MODULES-EXPLICIT-ROUTES-001)

Application du principe 9 de la charte v2 : « pas d'écritures invisibles dans
le code utilisateur ». `mvc/routes.py` est un fichier propriétaire du
développeur — Forge ne doit pas le modifier silencieusement.

**Changements de comportement :**

- `forge module:routes <nom>` génère `mvc/routes_<nom>.py` (write-if-new) et
  **affiche sur stdout** les lignes à ajouter manuellement dans `mvc/routes.py`.
- Si `mvc/routes_<nom>.py` existe déjà, la commande échoue avec un message
  explicite (`ModuleRoutesAlreadyGeneratedError`).
- `mvc/routes.py` n'est **jamais** modifié par Forge.
- `mvc/module_routes.py` n'est **plus** créé par `forge module:routes`.

**API Python :**

- `inject_module_routes` → **supprimée**, remplacée par `generate_module_routes`
- `APP_ROUTES_FILE` → **supprimée** de `core.modules`
- `_ensure_app_routes_bridge_content` → **supprimée**
- Nouveau : `generate_module_routes(module_name, *, registry_path, dry_run)`
- Nouveau : `ModuleRoutesAlreadyGeneratedError(ValueError)`
- Nouveau : `ModuleRouteGenerationResult` (dataclass)

**Migration :**

```python
# Avant
from core.modules import inject_module_routes
inject_module_routes("agenda")  # écrivait dans mvc/routes.py et mvc/module_routes.py

# Après
from core.modules import generate_module_routes
result = generate_module_routes("agenda")  # crée mvc/routes_agenda.py
# Ajouter manuellement dans mvc/routes.py les lignes affichées :
# from mvc.routes_agenda import register_agenda_routes
# register_agenda_routes(router)
```

### Modifie — Hashing PBKDF2 retiré de la création (HASHING-PBKDF2-REMOVE-001)

Suppression de `hacher_mot_de_passe()` et de la constante `ITERATIONS`.
`core/security/hashing.py` est desormais **lecture seule** — verification
des hashes PBKDF2 legacy uniquement.

**Supprime :**
- `hacher_mot_de_passe()` — plus de creation de nouveaux hashes PBKDF2
- Constante `ITERATIONS` (600 000) — retireee avec la fonction de creation

**Conserve pour retrocompatibilite :**
- `verifier_mot_de_passe()` — verification des hashes PBKDF2 existants en base
- `pbkdf2_needs_rehash()` — retourne desormais `True` pour tout hash PBKDF2
  (tous doivent migrer vers Argon2id)
- Rate limiting (`enregistrer_tentative`, `est_limite`) — inchange

**Migration transparente :** les hashes PBKDF2 existants continuent de fonctionner.
A chaque connexion reussie, le hash est automatiquement remplace par Argon2id
(mecanisme AUTH-HASH-MIGRATION-001). Suppression complete du module prevue
quand tous les hashes auront migre (HASHING-PBKDF2-DEFINITIVE-REMOVE-001, post-3.0).

**Pas de consommateurs productifs trouves** dans `core/`, `mvc/`, `cli/`.
Les tests ont ete adaptes avec des helpers internes qui creent les hashes PBKDF2
directement via `hashlib.pbkdf2_hmac`.

Justification : principe 11 de la charte v2 (une seule facon de creer un hash :
Argon2id) et principe 8 (noyau minimal).

### Supprime — Dossier cmd/ legacy (CMD-LEGACY-REMOVE-001)

Suppression definitive du dossier `cmd/` (legacy depuis Forge 1.1.0).

**~2 006 lignes supprimees.** Le dossier contenait des generateurs obsoletes
(`cmd/make.py`, `cmd/mvc/`, `cmd/entities/`, `cmd/security/`, `cmd/sql/`,
`cmd/inspect/`) tous remplaces par les commandes modernes dans `cli/`.

**Migration :** si vous utilisiez encore `python cmd/make.py ...`,
utilisez a la place `forge make:...` (voir `forge help`).

**Pas de shims** (charte v2, note pre-3.0). Les anciens scripts ne sont
plus disponibles.

Justification : application du principe 11 de la charte v2
(*une seule facon officielle de faire chaque chose*). Le dossier etait
declare legacy par son propre README depuis Forge 1.1.0.

Effet de bord positif : retire les usages PBKDF2 dans `cmd/security/`.
Le ticket `HASHING-PBKDF2-REMOVE-001` finalisera la suppression de PBKDF2
dans le reste du projet.

### Renommage API publique en anglais (LANG-MIGRATION-001)

Application de l'ADR-003 : l'API publique de Forge est en anglais.
17 symboles francais renommes dans `core/security/session.py`,
`core/security/hashing.py`, `core/uploads/rate_limit.py` et
`mvc/models/auth_model.py`.

**Correspondance complete :**

| Ancien nom (francais)        | Nouveau nom (anglais)         | Module                      |
|------------------------------|-------------------------------|-----------------------------|
| `DUREE_SESSION`              | `SESSION_DURATION`            | `core.security.session`     |
| `creer_session()`            | `create_session()`            | `core.security.session`     |
| `supprimer_session()`        | `delete_session()`            | `core.security.session`     |
| `regenerer_session()`        | `regenerate_session()`        | `core.security.session`     |
| `authentifier_session()`     | `authenticate_session()`      | `core.security.session`     |
| `est_authentifie()`          | `is_authenticated()`          | `core.security.session`     |
| `get_utilisateur()`          | `get_user()`                  | `core.security.session`     |
| `utilisateur_a_role()`       | `user_has_role()`             | `core.security.session`     |
| `verifier_mot_de_passe()`    | `verify_password_legacy()`    | `core.security.hashing`     |
| `enregistrer_tentative()`    | `record_attempt()`            | `core.security.hashing`     |
| `MAX_TENTATIVES`             | `MAX_ATTEMPTS`                | `core.security.hashing`     |
| `FENETRE_SECONDES`           | `RATE_LIMIT_WINDOW`           | `core.security.hashing`     |
| `est_limite()`               | `is_rate_limited()`           | `core.security.hashing`     |
| `est_limite_upload()`        | `is_upload_rate_limited()`    | `core.uploads.rate_limit`   |
| `enregistrer_upload()`       | `record_upload_attempt()`     | `core.uploads.rate_limit`   |
| `UPLOAD_FENETRE_SECONDES`    | `UPLOAD_RATE_LIMIT_WINDOW`    | `core.uploads.rate_limit`   |
| `utilisateur_id` (param.)    | `user_id`                     | `mvc.models.auth_model`     |

**Pas de shims** (charte v2, note pre-3.0). Migration directe, ~280 occurrences.

Guard-fou : `tests/test_lang_migration_001.py` (51 tests) garantit
l'absence de toute apparition des anciens noms en dehors de ce fichier.

### Réorganisation allégée des tests (TESTS-CLASSIFY-001)

Création de deux sous-dossiers dans `tests/` pour isoler les garde-fous et
les tests de release des tests fonctionnels.

**Nouveau** :
- `tests/meta/` — 41 garde-fous de tickets (`test_*_001.py` et fichiers assimilés)
  qui valident des contrats d'absence ou de migration suite à un ticket structurant
- `tests/release/` — 11 tests de cohérence release (versionning, packaging, publication)

**Inchangé** : les tests fonctionnels (~230 fichiers) restent à plat dans `tests/`.
**Aucun fichier modifié dans son contenu** — pure réorganisation, sauf 3 corrections
de `parents[1]` → `parents[2]` (profondeur +1 due au déplacement).

Pas d'affinage vers `unit/`, `integration/`, `generation/`. Ce découpage est déféré
à `TESTS-CLASSIFY-DEEP-001` (post-3.0).

Guard-fou : `tests/meta/test_tests_classify_001.py` (53 tests).

### Refonte de CLAUDE.md — briefing IA durable (CLAUDE-MD-UPDATE-001)

`CLAUDE.md` refondu intégralement pour refléter l'état Forge 2.10.0 et
survivre aux ticket-cycles.

**Avant** : fichier obsolète décrivant Forge 1.5.0 / 3964 tests / Phase 4.5.
Dangereux pour un agent IA qui s'en servait pour s'orienter.

**Après** : contenu stable par construction — architecture, charte v2 (11 principes),
ADR (001–008), conventions de tickets/tests/commits, patterns émergents, modes
d'action acceptables. Pointeurs vers les sources canoniques pour les informations
volatiles (version, compteur de tests, tickets en cours).

Test garde-fou : `tests/test_claude_md_001.py` (19 tests) vérifie que le fichier
mentionne les éléments structurants et ne contient pas de compteurs de tests précis.

**Prochaine mise à jour prévue** : tag 3.0.0.

### Supprimé — Shims de compat MFA (EXTRACTION-CLEANUP-SHIMS-001)

Suppression des trois shims créés à `MFA-EXTRACT-001` pour adoucir la transition :

- `core/auth/mfa.py` (shim)
- `core/auth/recovery.py` (shim)
- `core/auth/totp_replay.py` (shim)

**Migration :** tout import `from core.auth.mfa import X` (ou `.recovery`, `.totp_replay`)
doit devenir `from forge_mvc_mfa import X`.

**Justification :** pas d'utilisateurs externes à protéger (note pré-3.0). Les autres
extractions (Workflow, Stats, RBAC) ont été faites sans shims. Forge 3.0 sort sans aucun
shim de compat — cohérence du principe 11 de la charte v2.

`TestLegacyShims` dans `test_mfa_extract_001.py` remplacé par `TestShimsRemoved` et
`TestNoShimImportsRemain`. Supprime également un `DeprecationWarning` de la suite de tests.

### Architecture audit auth documentée (AUTH-AUDIT-CLARIFY-ARCHITECTURE-001)

**Pas de changement de code productif** — clarification documentaire pure.

L'architecture existait mais n'était pas documentée. Un développeur découvrant
la table SQL `auth_audit_log` sans documentation pouvait croire que Forge la
remplissait automatiquement.

**Ce que Forge fournit (trois briques distinctes)** :

- Contrat `AuthAuditEvent` : structure validée, 20+ types normalisés.
- Émission Python via `safe_log_auth_event` vers le logger `forge.auth.audit`.
  Le handler est configuré par l'application.
- Table SQL `auth_audit_log` (infrastructure latente, schéma prêt).

**Ce que Forge ne fait pas** : Forge n'écrit pas dans `auth_audit_log`.
La persistance est une décision applicative (rétention, backend, purge, RGPD).

**Nouveautés** :

- `docs/adr/008-auth-audit-architecture.md` — décision d'architecture avec trois
  approches typiques (handler logging SQL, wrapper applicatif, stream externe).
- Section "Architecture audit" dans `docs/auth.md` avec exemple d'intégration.
- Docstring de `core/auth/audit.py` enrichi pour pointer vers l'ADR-008.
- Guard-fou `tests/test_auth_audit_architecture_001.py` (13 tests).

Justification : principe 3 de la charte v2 (refuser la magie cachée) et
principe 1 (séparer framework et application métier).

## [2.9.0] — 2026-05-11

### Extraction RBAC dans forge-mvc-rbac (RBAC-EXTRACT-001)

Quatrieme et derniere extraction de la phase 14.3. RBAC deplace vers
le module separe `forge-mvc-rbac 2.5.0`.

**Fichiers deplaces :**

- `core/security/rbac.py` → `forge_mvc_rbac/rbac.py`
- `core/auth/user_rbac.py` → `forge_mvc_rbac/user_rbac.py`
- `core/auth/user_rbac_resolver.py` → `forge_mvc_rbac/resolver.py`
- `core/auth/authorization.py` → `forge_mvc_rbac/authorization.py`
- `core/auth/jinja.py` → `forge_mvc_rbac/jinja.py`
- `mvc/models/sql/rbac.sql` → `packages/forge-mvc-rbac/sql/rbac.sql`
- `mvc/models/sql/user_roles.sql` → `packages/forge-mvc-rbac/sql/user_roles.sql`

**Reste dans core/auth/** : l'auth basique (login, logout, sessions, password, AuthUser),
les mecanismes transversaux (audit, rate-limit, exceptions, tokens, email, reset).

**Migration :**
- `from core.security.rbac import X` → `from forge_mvc_rbac import X`
- `from core.auth.authorization import X` → `from forge_mvc_rbac import X`
- `from core.auth.user_rbac import X` → `from forge_mvc_rbac import X`
- `from core.auth.user_rbac_resolver import X` → `from forge_mvc_rbac import X`
- `from core.auth.jinja import X` → `from forge_mvc_rbac import X`

**Pas de shims de compat** (note pre-3.0). Les anciens imports levent `ImportError`.

**Installation :**

```bash
pip install forge-mvc-rbac
```

Justification : application de ADR-004. RBAC est un mecanisme metier optionnel.
Toutes les applications n'ont pas besoin de controle d'acces fin par permissions.

## [2.8.0] — 2026-05-11

### Extraction Stats dans forge-mvc-stats (STATS-EXTRACT-001)

Troisieme extraction de la phase 14.3. `core/stats/` deplace vers
le module separe `forge-mvc-stats 2.5.0`.

**Fichiers deplaces :**

- `core/stats/events.py` → `forge_mvc_stats/events.py`
- `core/stats/schema.py` → `forge_mvc_stats/schema.py`
- `core/stats/tracking.py` → `forge_mvc_stats/tracking.py`
- `core/stats/admin.py` → `forge_mvc_stats/admin.py`
- `core/stats/__init__.py` → `forge_mvc_stats/__init__.py` (refait)

**Migration :** `from core.stats import X` → `from forge_mvc_stats import X`

**Pas de shims de compat** (note pre-3.0). Les anciens imports levent `ImportError`.

**Installation :**

```bash
pip install forge-mvc-stats
```

Justification : application de ADR-004. Les statistiques generiques sont
un mecanisme metier optionnel, pas une primitive du framework.

## [2.7.0] — 2026-05-11

### Extraction Workflow dans forge-mvc-workflow (WORKFLOW-EXTRACT-001)

Deuxieme extraction de la phase 14.3. `core/workflow/` deplace vers
le module separe `forge-mvc-workflow 2.6.0`.

**Fichiers deplaces :**

- `core/workflow/status.py` → `forge_mvc_workflow/status.py`
- `core/workflow/transitions.py` → `forge_mvc_workflow/transitions.py`
- `core/workflow/jinja.py` → `forge_mvc_workflow/jinja.py`
- `core/workflow/__init__.py` → `forge_mvc_workflow/__init__.py` (refait)

**Migration :** `from core.workflow import X` → `from forge_mvc_workflow import X`

**Pas de shims de compat** (note pre-3.0). Les anciens imports levent `ImportError`.

**Installation :**

```bash
pip install forge-mvc-workflow
```

Justification : application de ADR-004. Workflow est un mecanisme metier
(cycles de vie applicatifs) optionnel, pas une primitive du framework.

## [2.6.0] — 2026-05-11

### Supprimé — OIDC (OIDC-REMOVE-OR-EXTRACT-001)

Suppression complete du code OIDC du depot. L'implementation etait partielle
(pas de token exchange, pas de validation JWT/JWKS, pas de validation des
claims, pas de liaison utilisateur) et incompatible avec la cible "release
publique stable" de Forge 3.0 (principe 10 de la charte v2 : API publique =
contrat de completude).

**Fichiers supprimes :**

- `core/auth/experimental/oidc.py` (~1 000 lignes) et `oidc_identity.py`
- `core/auth/oidc.py` et `oidc_identity.py` (shims de compat du ticket #7)
- `mvc/models/sql/auth_oidc_accounts.sql` et `auth_oidc_identities.sql`
- `tests/test_auth_oidc_*.py` (7 fichiers de tests)

**Constants retirees :**

- `AUTH_EVENT_OIDC_*` (6 constantes) de `core.auth.audit`
- `AUTH_RATE_LIMIT_OIDC_CALLBACK` de `core.auth.rate_limit`
- Exports OIDC de `core.auth.__init__`

**Recuperation possible :** le code reste dans l'historique git.

```bash
git show HEAD~:core/auth/experimental/oidc.py
```

Si OIDC devient une priorite, un ticket dedie `OIDC-IMPLEMENT-COMPLETE-001`
partira d'une page blanche. Justification : application stricte du principe 10
de la charte v2 et de la note pre-3.0. Decision finale ADR-004.

## [2.5.0] — 2026-05-10

### Extraction MFA dans forge-mvc-mfa (MFA-EXTRACT-001)

Pilote du plan d'extraction ADR-004 / ADR-005. Toute la brique MFA est
physiquement déplacée de `core/auth/` vers `packages/forge-mvc-mfa/`.

**Ce qui a changé :**

- `core/auth/mfa.py`, `core/auth/recovery.py`, `core/auth/totp_replay.py`
  deviennent des **shims de compatibilité** qui émettent `DeprecationWarning`
  et réexportent depuis `forge_mvc_mfa`. Ils seront retirés en Forge 3.0.
- `core.auth.__all__` ne réexporte plus les noms MFA
  (`AuthMfaFactor`, `MFA_FACTOR_TOTP`, `is_mfa_enabled`, etc.).
  Les exceptions `InvalidMfaFactorError` et `InvalidMfaRecoveryCodeError`
  restent dans `core.auth.exceptions` (transversales).
- `mvc/models/mfa_model.py` → `packages/forge-mvc-mfa/forge_mvc_mfa/model.py`.
- `mvc/models/sql/auth_mfa_factors.sql` et `auth_mfa_recovery_codes.sql`
  → `packages/forge-mvc-mfa/sql/`.
- `forge-mvc-mfa 2.5.0` publie l'API publique complète avec `pyotp>=2.9,<3`
  comme dépendance déclarée.

**Migration :**

```python
# Avant (déprécié — shim Forge 2.x)
from core.auth import AuthMfaFactor, is_mfa_enabled

# Après (Forge 2.5+)
from forge_mvc_mfa import AuthMfaFactor, is_mfa_enabled
```

Les projets existants continuent de fonctionner via les shims jusqu'à Forge 3.0.

## [2.4.0] — 2026-05-10

### Infrastructure multi-distributions PyPI (PACKAGING-MULTI-DIST-001)

Première étape de l'infrastructure de packaging multi-distributions préparée par ADR-005.

- Nouveau répertoire `packages/` contenant 5 distributions indépendantes :
  - `packages/forge-mvc/` — noyau complet, 3.0-ready (Python ≥ 3.12), référence le source racine via `where = ["../.."]`
  - `packages/forge-mvc-mfa/` — brique MFA (placeholder, distribuable)
  - `packages/forge-mvc-rbac/` — brique RBAC (placeholder, distribuable)
  - `packages/forge-mvc-workflow/` — brique workflow (placeholder, distribuable)
  - `packages/forge-mvc-stats/` — brique statistiques (placeholder, distribuable)
- `pyproject.toml` racine mis à jour : ajout de `[project.optional-dependencies]` (`mfa`, `rbac`, `workflow`, `stats`, `all`), version bump 2.3.0 → 2.4.0.
- `requirements-dev.txt` : ajout de `setuptools>=77.0.3` (nécessaire pour les builds `--no-isolation`).
- CI `.github/workflows/tests.yml` : ajout de l'étape "Build optional distributions" — toutes les distributions sont construites à chaque push.
- Documentation `docs/installation.md` : section "Modèle de packages" ajoutée.

Les distributions optionnelles sont des placeholders vides (`__init__.py` + `pyproject.toml`) qui ne seront peuplées que lors de la migration Forge 3.0. Chacune est buildable dès maintenant via `python -m build --no-isolation packages/<dist>/`.

### Charte philosophique et décisions architecturales (CHARTER-V2-ADOPTION-001)

- Adoption formelle de la charte philosophique v2 (`CHARTE_DOC.md`), qui remplace la charte documentaire v1 (archivée dans `docs/history/charte-v1.md`). La v2 ajoute 4 principes structurants (noyau minimal, pas d'écriture invisible, API publique = contrat de complétude, une seule façon officielle de faire chaque chose) et 4 règles d'évolution (A-D).
- 5 ADR publiés dans `docs/adr/` qui actent les décisions structurantes de Forge 3.0 :
  - ADR-003 : API publique en anglais
  - ADR-004 : périmètre du `core/` minimal strict (5 modules à extraire)
  - ADR-005 : packaging hybride monorepo, multi-distributions PyPI
  - ADR-006 : Python 3.12+ minimum
  - ADR-007 : adoption formelle de la charte v2

Ces décisions guideront la phase 14.3 (reconstruction) et la sortie de Forge 3.0.

### Sécurité — CSP complétée (SEC-CSP-COMPLETENESS-001)

- `img-src 'self' data:` : autorise les images encodées en `data:` URI (SVG inline, avatars, placeholders). Sans cette directive, `default-src 'self'` les bloquait silencieusement.
- `form-action 'self'` : limite la destination des `<form action>` à l'origine. Cette directive n'a pas de fallback sur `default-src` selon la spécification CSP — elle doit être déclarée explicitement.

Aucun impact sur les applications légitimes. La CSP passe de 6 à 8 directives.

### Audit — Propagation des erreurs dans log_auth_event (AUTH-AUDIT-PROPAGATE-001)

**Comportement modifié.**

- `log_auth_event()` propage désormais ses exceptions au lieu de les avaler silencieusement. En particulier, un `event_type` invalide (vide, None, espaces) lève `InvalidAuthAuditEventError`, et toute défaillance interne du logger est propagée.
- Ce changement rend effectif le mécanisme d'observabilité installé par `AUTH-AUDIT-RESILIENCE-001` : `safe_log_auth_event` peut maintenant observer des échecs réels en production, sans mock.
- Les 7 appels directs à `log_auth_event` dans `mvc/controllers/` migrés vers `safe_log_auth_event`.
- Les 6 blocs `try: log_auth_event(...) except: pass` dans `cli/security/auth.py` remplacés par `safe_log_auth_event(...)`.

**Migration :** si votre code appelait `log_auth_event` directement dans un contexte métier, remplacer par `safe_log_auth_event`. Si vous l'appelez dans un contexte administratif et souhaitez connaître l'échec, entourer d'un `try/except` explicite et documenté.

### Audit — Résilience des appels log_auth_event (AUTH-AUDIT-RESILIENCE-001)

- Nouvelle fonction `safe_log_auth_event()` dans `core.auth.audit` : encapsule `log_auth_event` avec gestion d'exception, logging des échecs via le logger Python `forge.auth.audit` (niveau `WARNING`, traceback inclus), et compteur d'échecs observable via `get_audit_failure_count()`.
- `reset_audit_failure_count()` fourni pour les tests.
- Les 3 appels `try: log_auth_event(...) except: pass` dans `core/auth/mfa.py` remplacés par `safe_log_auth_event(...)`.
- `safe_log_auth_event`, `get_audit_failure_count`, `reset_audit_failure_count` exportés depuis `core.auth`.
- **Pas de rupture API** : `log_auth_event` reste disponible et inchangé.

### Sécurité — Vérification d'identité dans la revalidation MFA (SEC-MFA-REVALIDATION-IDENTITY-001)

**Rupture comportementale.**

- `verify_mfa_revalidation` et `mark_mfa_revalidated` vérifient désormais que la session courante est authentifiée et que son utilisateur correspond au `user_id` passé en paramètre.
- Sans cette vérification, un contrôleur mal formé pouvait appeler `verify_mfa_revalidation` avec un `user_id` arbitraire — revalidant un user différent de l'utilisateur de la session courante.
- Comportement en cas d'échec d'identité : `verify_mfa_revalidation` retourne `None`, `mark_mfa_revalidated` est un no-op silencieux. **Le rate-limit n'est pas incrémenté** (l'échec d'identité est distinct d'une tentative de code invalide).
- Nouvel événement audit `mfa.revalidation.identity_mismatch` (`AUTH_EVENT_MFA_REVALIDATION_IDENTITY_MISMATCH`) émis à chaque échec d'identité.

**Migration :** tout code appelant ces fonctions hors d'une session authentifiée doit être placé après la connexion. La session doit avoir `authentifie=True` et `utilisateur["id"] == user_id`.

### Modifié — Sécurité MFA (SEC-MFA-SECRET-NAMING-001)

- Renommage du champ `AuthMfaFactor.secret_hash` → `totp_secret` (nom plus précis, sans suggestion de hachage).
- Renommage de la colonne SQL `secret_hash` → `totp_secret` dans `auth_mfa_factors`.
- `AuthMfaFactor.secret_hash` reste disponible comme propriété dépréciée (émet `DeprecationWarning`) ; sera retiré en Forge 3.0.
- `create_totp_factor()` émet désormais un `UserWarning` unique par processus pour signaler que le secret TOTP est stocké en clair.
- Documentation mise à jour : section "Limites connues MFA" ajoutée à `docs/auth.md`.

### Changements cassants

- **Migration SQL requise** pour les bases existantes : `ALTER TABLE auth_mfa_factors RENAME COLUMN secret_hash TO totp_secret;`
- Tout code utilisant `AuthMfaFactor(secret_hash=...)` doit passer à `AuthMfaFactor(totp_secret=...)`.
- Tout code accédant à `factor.secret_hash` doit passer à `factor.totp_secret` (l'alias émet un `DeprecationWarning`).

### Sécurité

- `core/security/middleware.py` et `mvc/controllers/auth_controller.py` utilisent `hmac.compare_digest()` pour la comparaison des tokens CSRF (SEC-CSRF-CONSTANT-TIME-001).

### Backends de session

- Introduction d'un contrat de session pluggable (`SessionStore` Protocol) avec trois backends : `MemorySessionStore`, `FileSessionStore`, `MariaDbSessionStore` (SESSIONS-CONTRACT-001).
- `core/security/session.py` délègue toutes ses opérations au store actif via l'API publique ; les accès directs `_sessions`/`_lock` ont été supprimés.

### Rate-limit MFA (SEC-MFA-RATELIMIT-001)

- `verify_mfa_challenge` et `verify_mfa_revalidation` appliquent un rate-limit par utilisateur (5 tentatives/5 min pour le challenge, 3/5 min pour la revalidation).
- `core/auth/rate_limit.py` enrichi d'un store in-memory process-local (`record_attempt`, `is_locked_out`, `clear_attempts`, `purge_all_attempts`).
- Nouvel événement d'audit `AUTH_EVENT_MFA_RATE_LIMITED` ("mfa.rate_limited").
- Le lockout retourne la même réponse qu'un échec de code — pas de fuite d'information.

### Anti-replay TOTP (SEC-MFA-TOTP-REPLAY-001)

- `verify_mfa_challenge` et `verify_mfa_revalidation` appliquent RFC 6238 §5.2 : un code TOTP accepté ne peut pas être rejoué dans la même step (30 s).
- Nouveau module `core/auth/totp_replay.py` : store in-memory `factor_id → last_used_step`, thread-safe, avec purge opportuniste toutes les 100 opérations.
- Un replay est traité comme un échec normal (incrémente le rate-limit, pas de fuite d'information).

### Persistence de session MFA (MFA-SESSION-PERSISTENCE-001)

- Correction d'un bug silencieux : les mutations en place sur le dict retourné par `store.get()` étaient perdues pour `FileSessionStore` et `MariaDbSessionStore` (backends désérialisés), alors qu'elles persistaient pour `MemorySessionStore` (référence vivante).
- Nouveau helper `_persist_session_changes(request, *, set_keys, unset_keys)` dans `core/auth/mfa.py` : effectue un cycle read-modify-write explicite sur le store pour garantir la persistence sur tous les backends.
- Fonctions `start_mfa_challenge`, `clear_mfa_challenge`, `mark_mfa_revalidated`, `clear_mfa_revalidation` réécrites pour utiliser ce helper.
- Nouveau méthode `replace(session_id, data)` ajoutée au contrat `SessionStore` et aux trois backends (`MemorySessionStore`, `FileSessionStore`, `MariaDbSessionStore`) : remplace intégralement les données sans merge (contrairement à `set()`).
- `MemorySessionStore.replace()` opère sur le dict interne en place (préserve les références vivantes) via snapshot avant clear.

### Modèles applicatifs — API canonique (SQL-EXAMPLES-CANONICAL-001)

- Les modèles livrés (`mvc/models/auth_model.py`, `mvc/models/mfa_model.py`) et
  les modèles des starters (`carnet-contacts`, `suivi-comportement-eleves`,
  `utilisateurs-auth`) utilisent désormais exclusivement `core.database.db`
  (`fetch_one`, `fetch_all`, `execute`, `insert`).
- Le générateur CRUD (`cli/entities/crud/model_builder.py`) produit
  maintenant du code utilisant l'API canonique. Les opérations M2M multi-statement
  utilisent `transaction()` de `core.database.transaction`.
- `core.database.connection` est documenté comme API interne dans son docstring
  et dans `docs/reference.md` — à n'utiliser que pour les cas avancés
  (transactions complexes, bulk).
- Le code généré par le builder passe de ~12 lignes par fonction à ~2 lignes,
  plus lisible et pédagogique (principe Forge n°11).

### Sécurité — durcissement CSP (SEC-CSP-HARDEN-001)

- Ajout de `object-src 'none'` à la Content Security Policy par défaut.
  Refuse le chargement de plugins legacy (`<object>`, `<embed>`, `<applet>`).
  `default-src 'self'` couvre partiellement ce cas mais `object-src` n'a pas
  de fallback garanti sur Firefox et Safari (certaines versions).
- Ajout de `base-uri 'none'` à la Content Security Policy par défaut.
  Empêche l'injection d'une balise `<base>` qui détournerait toutes les URLs
  relatives de la page (formulaires inclus). `default-src` ne couvre pas
  `base-uri`. Aucun impact sur les applications existantes (Forge n'utilise
  ni `<object>` ni `<base>`).

### OIDC déplacé vers core.auth.experimental (OIDC-SCOPE-CLARIFY-001)

- Les modules `oidc.py` et `oidc_identity.py` sont déplacés dans `core/auth/experimental/`.
- Toutes les classes et fonctions OIDC (`OidcProvider`, `OidcClientConfig`, `OidcExternalIdentity`, `AuthOidcAccount`, `build_oidc_authorization_url`, `validate_oidc_callback`, `start_oidc_login`, etc.) sont retirées de l'API publique `core.auth`.
- Les constantes d'audit `AUTH_EVENT_OIDC_*` restent dans `core.auth` (le mécanisme d'audit est indépendant).
- Un `UserWarning` est émis au premier import depuis `core.auth.experimental.oidc`.
- Les anciens chemins `core.auth.oidc` et `core.auth.oidc_identity` restent fonctionnels comme shims de compatibilité mais émettent un `DeprecationWarning` — ils seront supprimés en Forge 3.0.

**Migration :**
```python
# Avant (supprimé de core.auth)
from core.auth import OidcProvider, build_oidc_authorization_url

# Après
from core.auth.experimental.oidc import OidcProvider, build_oidc_authorization_url
```

**Pourquoi :** OIDC est incomplet (pas d'échange de code, pas de validation JWT/JWKS, pas de claims validation). Exposer du code partiel comme API publique serait trompeur — une API publique est un contrat de complétude (principe Forge n°10).

### Statistiques — suppression des constantes d'événements nommés (STATS-GENERIC-EVENTS-001)

**Rupture d'API publique.**

- Retrait de `core.stats` (et `core.stats.events`) : `PAGE_VIEW`, `CONTACT_CLICK`, `FORM_SUBMIT`, `DOWNLOAD_CLICK`, `EXTERNAL_LINK_CLICK`, `MEDIA_VIEW`, `is_known_event_name()`, `_KNOWN_EVENT_NAMES`.
- Les noms d'événements sont de simples chaînes `snake_case` définies par l'application — Forge ne préconise aucune liste.

**Migration :**
```python
# Avant
from core.stats import PAGE_VIEW, track_event
track_event(db.execute, PAGE_VIEW, label="Vue")

# Après
from core.stats import track_event
track_event(db.execute, "page_view", label="Vue")
```

**Pourquoi :** Nommer les événements applicatifs dans le framework viole le Principe 1 de la Charte Forge (le framework n'est pas l'application). Une application de gestion de communes ne partage aucun vocabulaire métier avec une boutique en ligne. Les chaînes restent valides comme noms d'événements, elles ne sont simplement plus des constantes exportées.

## [2.3.0] — 2026-05-10

### Ajouté — Phase 13 CRUD avancé (close)

- Filtres déclaratifs CRUD (`list.filter=true`) avec génération automatique de `<select>` et `<input>` (CRUD-FILTER-001, CRUD-FILTER-HTMX-001, CRUD-FILTER-DOC-001).
- Tri sécurisé par whitelist (`_ALLOWED_SORT`) avec liens HTMX progressifs et fallback `<a href>` (CRUD-SORT-001).
- Consolidation HTMX CRUD : cible unique `#crud-results`, `hx-swap="innerHTML"`, `hx-push-url="true"` cohérents sur pagination, tri, filtres et reset (CRUD-HTMX-001).
- Suppression groupée minimale : cases à cocher HTML5 (`form=`), confirmation, CSRF automatique, RBAC optionnel, SQL paramétrée `IN(?,?,?)` (CRUD-BULK-DELETE-001).
- Export CSV filtré : route `GET /{plural}/export.csv`, `_EXPORT_LIMIT=1000`, `_csv_escape` (protection injection CSV OWASP), `Cache-Control: no-store`, RBAC via permission `index`, lien `<a href>` classique sans HTMX (CRUD-EXPORT-CSV-001).
- Documentation `docs/reference.md` : sections tri, HTMX CRUD, suppression groupée, export CSV.

### Version figée

Forge 2.3.0 fige l'état post Phase 13 avant une refonte/consolidation profonde ultérieure.

## [2.2.0] — 2026-05-09

### Ajouté

- Tests HTTP E2E via subprocess sur un serveur réel (HTTP-E2E-TESTS-001) : 21 tests couvrant routes, en-têtes de sécurité, fichiers statiques, traversée de chemin, nonce CSP.
- Tests de concurrence sur `MemorySessionStore` et helpers legacy (CONCURRENCY-SESSION-TESTS-001) : 14 tests avec 50 threads concurrents.
- Endpoint de santé `GET /health` → `{"status": "ok"}` 200 JSON (HEALTH-ENDPOINT-001).
- Audit contractuel des profils de projet et tableau comparatif dans `docs/reference.md` (PROFILE-DIFFERENTIATION-001).

### Tests

- Ajout de `tests/test_http_e2e_001.py`.
- Ajout de `tests/_e2e_launcher.py`.
- Ajout de `tests/test_concurrency_session_001.py`.
- Ajout de `tests/test_health_endpoint_001.py`.
- Ajout de `tests/test_profile_differentiation_001.py`.

## [2.1.0] — 2026-05-09

### Modifié

- Dépréciation officielle du dossier legacy `cmd/` avec avertissement à l'exécution (CMD-LEGACY-DEPRECATION-001).
- Clarification de la frontière entre `core.auth` (API officielle) et `core.security` (compat/transversal) (AUTH-LEGACY-BOUNDARY-001).
- Découpage interne de `make_crud.py` (2396 lignes) en sous-modules `cli/entities/crud/` sans changement fonctionnel (CRUD-GENERATOR-SPLIT-001).
- Ajout d'un cache `lru_cache` aux catalogues de traduction i18n, avec `clear_translation_cache()` (I18N-CACHE-001).
- Intégration de `ruff` (règles E+F) comme validation qualité Python dans la CI et la checklist de release (QUALITY-RUFF-001).

### Documentation

- Mise à jour de `cmd/README.md` avec tableau d'équivalences et notice de dépréciation.
- Mise à jour de `docs/auth.md` avec la section frontière API officielle / legacy.
- Mise à jour de `docs/reference.md` : cache i18n, `clear_translation_cache()`, frontière auth.
- Mise à jour de `docs/release.md` avec l'étape Ruff dans la checklist.

### Tests

- Ajout de `tests/test_cmd_legacy_deprecation_001.py`.
- Ajout de `tests/test_auth_legacy_boundary_001.py`.
- Ajout de `tests/test_crud_generator_split_001.py`.
- Ajout de `tests/test_i18n_cache_001.py`.
- Ajout de `tests/test_quality_ruff_001.py`.

## [2.0.2] — 2026-05-09

### Documentation

- Nettoyage des incohérences documentaires post-2.0.1 (POST-2.0-DOC-CLEANUP-001).
- Restructuration de la roadmap active post-2.0, extraction de l'historique dans `docs/history/` (POST-2.0-ROADMAP-RESTRUCTURE-001).
- Ajout d'une politique de sécurité publique `SECURITY.md` (SECURITY-MD-001).
- Ajout d'une checklist de release officielle `docs/release.md` (RELEASE-CHECKLIST-001).

### Sécurité

- Ajout d'un audit de dépendances Python avec `pip-audit` (DEPENDENCY-SCAN-001).
- Ajout d'un workflow GitHub Actions non bloquant pour le scan de dépendances hebdomadaire.

### Tests

- Ajout de tests documentaires liés à `SECURITY.md`, `pip-audit` et à la checklist de release.

---

## [2.0.1] — 2026-05-09

### Corrigé

- Alignement de l'authentification par défaut sur `core.auth` et Argon2id (AUTH-DEFAULT-ALIGN-001).
- Ajout d'un test de non-régression CLI Auth → login (AUTH-CLI-LOGIN-E2E-TEST-001).
- Audit et alignement Auth des starters — élimination des usages PBKDF2 legacy (STARTERS-AUTH-AUDIT-001).
- Whitelist des clés de filtres dans le CRUD généré — prévention injection SQL (CRUD-FILTER-WHITELIST-001).
- Durcissement du PBKDF2 legacy : format versionné, 600 000 itérations, fonction `pbkdf2_needs_rehash` (SECURITY-PBKDF2-HARDENING-001).
- Migration transparente PBKDF2 → Argon2id après login réussi (AUTH-HASH-MIGRATION-001).
- Documentation claire des limites des sessions mémoire et warning runtime (DEPLOY-SESSION-LIMITS-001).
- Formalisation des décisions d'architecture Auth et Session (ADR-001, ADR-002).

---

## 2.0.0

Version de publication officielle. Forge 2.0.0 marque la fin de la phase Alpha et l'entrée en Beta.

### Ajouté

- Phase 4.5 complète : authentification avancée (Auth/User, sessions, MFA TOTP, codes de récupération, OIDC, interface admin utilisateurs).
- Phase 6 complète : pages publiques génériques (`make:public-page`, `make:public-list`, `make:public-show`, `make:public-form`, `make:public-contact`).
- Starters intégrés dans le wheel : contacts, utilisateurs-auth, blog, portfolio, communes-séjours.
- Commande `forge starter:build` pour installer un starter en local sans réseau.

### Modifié

- `Development Status` PyPI : `3 - Alpha` → `4 - Beta`.
- Référence stable par défaut : `v1.5.0` → `v2.0.0`.

---

## 1.5.0

Version de stabilisation de la phase 3 : socle front léger, JavaScript optionnel, internationalisation simple et templates standardisés.

### Ajouté

- Structure JavaScript applicative standard avec `static/js/app.js`.
- Commandes :
  - `forge js:init htmx`
  - `forge js:init alpine`
  - `forge js:init htmx-alpine`
- Support local optionnel de HTMX et Alpine.js via `static/vendor/`.
- Zone `{% block scripts %}` dans les layouts.
- Documentation HTMX et Alpine.js.
- Socle i18n :
  - `core/i18n`
  - `translations/fr.json`
  - `trans()` côté Python
  - `trans()` dans Jinja
  - langue par défaut configurable
  - fallback i18n
- Commandes :
  - `forge i18n:init`
  - `forge i18n:check`
- Utilisation de clés i18n génériques dans les templates CRUD générés.
- Layouts standards :
  - `mvc/views/layouts/public.html`
  - `mvc/views/layouts/admin.html`
- Composants Jinja de base :
  - button
  - alert
  - form_field
  - table
  - badge
  - pagination
- Boutons CRUD standardisés.
- Messages flash standardisés.
- États vides dans les listes CRUD.
- Confirmations natives de suppression CRUD.

### Limites connues

- HTMX et Alpine.js sont préparés mais non injectés automatiquement.
- Les CRUD dynamiques HTMX viendront plus tard.
- Seul `translations/fr.json` est fourni.
- Pas encore de langue par session ou par requête.
- Les composants ne sont pas encore utilisés partout.
- RBAC non commencé.

## 1.4.0

### Ajouté
- Migrations SQL versionnées.
- Table technique `forge_migrations` créée par `forge db:init`.
- Commande `forge migration:status`.
- Commande `forge migration:apply`.
- Commande `forge migration:make <nom>`.
- Génération de migration depuis une entité avec `--from-entity`.
- Génération de migration depuis toutes les entités avec `--from-entities`.
- Diff de schéma en lecture seule avec `forge migration:diff --entity`.
- Génération prudente depuis diff avec `--from-diff`.
- Documentation dédiée `docs/migrations.md`.

### Sécurité / prudence
- Refus automatique des diffs risqués `COLUMN_CHANGED` et `COLUMN_EXTRA`.
- Pas de `DROP COLUMN`, `MODIFY COLUMN` ou `CHANGE COLUMN` automatique.
- Pas de rollback prétendu sur les DDL MariaDB.
- SQL visible et relu avant application.

## 1.3.0

Version mineure centrée sur la stabilisation complète de Média v2 côté serveur.

- Suppression automatique des médias liés lors du destroy d'une entité CRUD.
- Conservation du contexte média dans les vues edit et après erreur de validation.
- Ajout du champ alt_text générique aux médias.
- Gestion de alt_text dans le CRUD généré.
- Support des galeries multiple=true en lecture.
- Ajout append-only de médias dans une galerie.
- Suppression individuelle des médias de galerie.
- Ajout d'une position numérique et réorganisation simple des galeries.
- Support du multi-upload HTML multiple pour les galeries.
- Validation serveur de chaque fichier d'un multi-upload avant tout accès DB.
- Ajout d'un test d'intégration média complet avec storage temporaire.
- Documentation Média v2, CRUD et référence mises à jour.

## 1.2.1

Version corrective de stabilisation.

- Correction de `Form.from_request` pour transmettre `request.body` et `request.files`.
- Ajout de `Pillow>=10.0,<12` dans les dépendances projet (`requirements.txt` et `pyproject.toml`).
- Retrait du GIF des formats image acceptés par défaut (`ImageField`, `save_image`).
- Ajout de tests runtime pour le CRUD média généré (exécution réelle avec mocks).
- Documentation alignée avec l'état réel 1.2.1 (CRUD média, relations, roadmap).
- Nettoyage des règles `.gitignore` pour les artefacts `build/`, `.mypy_cache/`, `.ruff_cache/`.

## [1.2.0] - CRUD enrichi, formulaires avancés et mail générique

### Ajouté
- Stabilisation de `core.forms` et des champs avancés de formulaire.
- Métadonnée `form.field` dans les JSON d'entités pour piloter les champs générés.
- Génération CRUD avec `EmailField`, `PhoneField`, `UrlField`, `TextAreaField`, `SlugField`, `DateField` et `DateTimeField`.
- Recherche `q` dans les listes CRUD générées.
- Pagination `page` avec `per_page=20`.
- Filtres simples déclarés avec `list.filter`.
- Filtres relationnels `many_to_one` depuis `relations.json`.
- Select relationnels dans les listes CRUD, avec libellé déduit du premier champ textuel de l'entité liée.
- `MailMessage` — représentation d'un message (sujet, corps texte/HTML, destinataires multiples).
- `Mailer` — point d'entrée unique pour envoyer un message via le transport configuré.
- Transports interchangeables : `NullTransport`, `FakeTransport`, `ConsoleTransport`, `LogTransport`, `SmtpTransport`.
- `MailTemplateRenderer` — rendu Jinja2 de templates mail (`*_subject.txt`, `*_text.txt`, `*_html.html`).
- `MailLogger` et table SQL `mail_log` — journalisation optionnelle des envois (sans corps du message).
- Variables d'environnement : `MAIL_TRANSPORT`, `MAIL_LOG_ENABLED`, `MAIL_FROM_ADDRESS`, `MAIL_FROM_NAME`.
- Commandes CLI :
  - `forge mail:init` — crée `mvc/mail/templates/`, `storage/mail/` et génère `mail_log.sql`.
  - `forge mail:test --to <email>` — envoie un message de test via le transport configuré.
  - `forge mail:render <template> [--context ctx.json]` — affiche le rendu d'un template sans envoyer.
  - `forge mail:doctor` — vérifie la cohérence de la configuration mail.
  - `forge mail:logs [--limit N]` — affiche les derniers enregistrements de `mail_log`.

### Sécurité
- Protection contre l'injection de headers dans `MailMessage` (`_NEWLINE_RE`).
- `MAIL_ENABLED=false` par défaut dans `env/example` — aucun envoi réel sans activation explicite.
- `MAIL_TRANSPORT=log` par défaut — les mails de développement sont écrits en `.eml`, pas envoyés.

### Tests
- Suite mail : `tests/test_mail.py`, `tests/test_mail_transports.py`, `tests/test_mailer.py`,
  `tests/test_mail_templates.py`, `tests/test_mail_cli.py`, `tests/test_mail_log.py`.

### Compatibilité
- `SMTPMailer` (`core/mail/smtp.py`) conservé provisoirement. Le système recommandé est `Mailer + SmtpTransport`.
- `FileField` et `ImageField` existent dans `core.forms` ; leur intégration à `make:crud` est désormais assurée via la clé `"media"` dans `entity.json` (voir `[Unreleased] - Média v2`).

## [1.1.0] - Socle média

### Ajouté
- `save_image`, `MediaRecord`, `image_variant_paths` — service générique d'upload image.
- `forge media:init` — initialisation des dossiers variantes (`thumbnail/`, `medium/`).
- Documentation `docs/media.md`.

## [1.0.1] - Stabilisation

### Corrigé
- Alignement de la version Forge en 1.0.1.
- Inclusion complète des fichiers starters dans le package Python.
- Correction de la gestion des fichiers statiques pour éviter une erreur 500 sur `/static/`.
- Sécurisation de `forge new` : un échec du commit Git initial ne supprime plus le projet généré.
- Nettoyage de l'incohérence entre le layout Jinja réel et la documentation.

### Documentation
- Clarification de l'usage du layout Jinja.
- Mise à jour des références de version.

## 1.0.0

Version initiale stable de Forge.

Fonctionnalités principales :
- framework Python MVC minimal
- routeur HTTP
- contrôleurs / vues / modèles
- entités JSON canoniques
- génération SQL visible
- génération de CRUD
- sessions
- CSRF
- erreurs HTTP propres
- upload local sécurisé
- déploiement minimal guidé
- starter-apps
- documentation MkDocs avec recherche
