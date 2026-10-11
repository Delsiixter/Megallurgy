# Metallia (Minecraft Java 1.20.1 – Forge)

Mod inspiré de Metallurgy : de nouveaux métaux trouvables dans les trois dimensions, des outils et armures, et un fourneau dédié pour créer des alliages.

## Contenu de la version 0.1.0

| Métal | Où le trouver | Outils / armure |
|---|---|---|
| **Étain** (Tin) | Overworld (sous terre, y -16 à 112) | Entre pierre et fer |
| **Bronze** | Alliage : 3 lingots de cuivre + 1 lingot d'étain → 4 bronze | Un peu mieux que le fer |
| **Ignatium** | Nether (minerai dans la netherrack) | Résiste au feu, niveau diamant+ |
| **Voidium** | End (minerai dans la pierre de l'End) | Niveau supérieur à la netherite |

Chaque métal a : lingot, bloc, épée, pioche, hache, pelle, houe, casque, plastron, jambières, bottes. Les trois métaux à minerai ont aussi un minerai et un métal brut (compatible Fortune / Toucher de soie).

**Fourneau à alliages** : se fabrique avec 8 briques + 1 fourneau. Deux emplacements d'ingrédients (dans n'importe quel ordre), un de combustible, un de résultat. Les recettes sont de simples fichiers JSON : `data/metallia/recipes/alloying/`.

Tout est regroupé dans l'onglet créatif « Metallia ».

## Obtenir le fichier .jar sans rien installer (via GitHub)

1. Créez un compte gratuit sur https://github.com.
2. Cliquez sur **+ → New repository**, nommez-le `metallia`, laissez-le public ou privé, puis **Create repository**.
3. Sur la page du dépôt, cliquez sur **uploading an existing file**, puis glissez-déposez **tout le contenu** du dossier `metallia` (y compris le dossier caché `.github`). Cliquez sur **Commit changes**.
4. Ouvrez l'onglet **Actions** : la compilation démarre toute seule (environ 3 à 6 minutes). Attendez la coche verte.
5. Cliquez sur l'exécution terminée, descendez jusqu'à **Artifacts** et téléchargez `metallia-mod`. Le zip contient `metallia-0.1.0.jar`.
6. Copiez ce `.jar` dans le dossier `mods` de votre Minecraft 1.20.1 avec Forge (version 47 ou plus).

Si le dossier `.github` n'a pas été envoyé (dossier caché) : sur GitHub, **Add file → Create new file**, tapez `.github/workflows/build.yml` comme nom, collez le contenu du fichier du même nom, puis validez.

Si la compilation échoue (croix rouge), cliquez sur l'exécution, copiez les lignes d'erreur et envoyez-les à Claude pour correction.

## Structure du projet

- `src/main/java/com/metallia/` : le code (registres, matériaux, fourneau à alliages).
- `src/main/resources/` : textures, modèles, traductions (FR/EN), recettes, génération des minerais.
- `tools/generate_assets.py` : script qui régénère toutes les ressources (utile pour ajouter un métal).
