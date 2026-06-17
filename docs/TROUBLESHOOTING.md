# Troubleshooting

## Problèmes fréquents

---

## 1. Le plugin ne démarre pas

Vérifier :

- que la configuration initiale du plugin a bien été réalisée dans les options QGIS
- que la version de QGIS installée est bien la version attendue
- que les fichiers du plugin ont été correctement installés

---

## 2. Certains outils de géotraitement sont absents

Vérifier :

- que le provider **SAGA GIS** est bien activé
- que les plugins complémentaires requis sont installés

---

## 3. Le fichier GPS n’est pas reconnu

Vérifier :

- que le nom du fichier contient bien `GPS`
- que les données d’entrée sont valides

---

## 4. Le kriging ne fonctionne pas correctement

Vérifier :

- que le plugin **Smart Map** est installé
- que l’échantillonnage a bien été réalisé avant le kriging
- que les couches générées sont bien organisées après chaque exécution

---

## 5. L’installation a échoué

Vérifier :

- que l’ancien dossier de configuration utilisateur QGIS a bien été supprimé
- que le dossier de l’installateur a bien été copié sous `C:\`
- que les versions logicielles requises ont bien été respectées
- que **Processing R Provider** a bien été installé au moment demandé pendant l’installation

---

## 6. Problèmes liés aux outils d’accessibilité Windows

Dans certains cas, l’activation d’outils d’accessibilité Windows peut perturber la gestion des fenêtres dans QGIS.

Cela concerne notamment :

- la **Loupe Windows**
- l’**agrandissement des fenêtres**
- certaines formes de **zoom d’affichage**
- certains réglages avancés de **mise à l’échelle**

### Symptômes possibles

- certaines fenêtres du plugin ne s’ouvrent pas correctement
- certaines boîtes de dialogue apparaissent partiellement hors écran
- certaines fenêtres semblent bloquées ou impossibles à valider
- le plugin semble ne plus répondre alors qu’il attend une interaction dans une fenêtre non visible
- l’enchaînement normal des étapes du plugin est interrompu

### Cause probable

QGIS peut rencontrer des difficultés de gestion du fenêtrage lorsque des outils d’accessibilité modifient fortement l’affichage ou la taille apparente des fenêtres.

Comme ce plugin utilise de nombreuses fenêtres successives, il est particulièrement sensible à ce type de perturbation.

### Recommandations

Si ce problème apparaît :

- désactiver temporairement la **Loupe Windows**
- réduire ou réinitialiser les paramètres d’agrandissement de l’affichage si possible
- éviter les agrandissements extrêmes des fenêtres
- relancer QGIS après modification des paramètres d’affichage
- tester à nouveau le plugin étape par étape

### Remarque importante

Cette situation ne signifie pas nécessairement que le plugin est défaillant.  
Le blocage peut provenir d’un problème de rendu ou de positionnement des fenêtres dans QGIS lié aux outils d’accessibilité de Windows.
``
