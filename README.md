<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Screenshot Manager - README</title>
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Helvetica, Arial, sans-serif, 'Apple Color Emoji', 'Segoe UI Emoji';
            line-height: 1.6;
            color: #24292e;
            background-color: #ffffff;
            max-width: 960px;
            margin: 0 auto;
            padding: 20px;
        }
        h1, h2, h3 {
            border-bottom: 1px solid #eaecef;
            padding-bottom: 0.3em;
        }
        h1 {
            color: #0366d6;
        }
        h2 {
            color: #0366d6;
            margin-top: 24px;
        }
        code {
            background-color: rgba(27,31,35,0.05);
            border-radius: 3px;
            padding: 0.2em 0.4em;
            font-family: 'SFMono-Regular', Consolas, 'Liberation Mono', Menlo, monospace;
            font-size: 85%;
        }
        pre {
            background-color: #f6f8fa;
            border-radius: 6px;
            padding: 16px;
            overflow: auto;
            font-family: 'SFMono-Regular', Consolas, 'Liberation Mono', Menlo, monospace;
            font-size: 85%;
        }
        .feature-list {
            background-color: #f6f8fa;
            border-radius: 6px;
            padding: 16px;
        }
        .feature-list li {
            margin-bottom: 8px;
        }
        .warning {
            background-color: #fff5f5;
            border-left: 4px solid #ff5555;
            padding: 10px 15px;
            margin: 15px 0;
        }
        .success {
            background-color: #f0fff4;
            border-left: 4px solid #28a745;
            padding: 10px 15px;
            margin: 15px 0;
        }
        .info {
            background-color: #f1f8ff;
            border-left: 4px solid #0366d6;
            padding: 10px 15px;
            margin: 15px 0;
        }
        table {
            border-collapse: collapse;
            width: 100%;
            margin: 15px 0;
        }
        th, td {
            border: 1px solid #dfe2e5;
            padding: 6px 13px;
        }
        th {
            background-color: #f6f8fa;
            font-weight: 600;
        }
        .center {
            text-align: center;
        }
        .btn {
            display: inline-block;
            padding: 6px 12px;
            font-size: 14px;
            font-weight: 600;
            line-height: 20px;
            white-space: nowrap;
            vertical-align: middle;
            cursor: pointer;
            border: 1px solid rgba(27,31,35,0.15);
            border-radius: 6px;
            background-color: #f6f8fa;
            background-image: linear-gradient(-180deg, #f0f3f6, #e6ebf1 90%);
            color: #0366d6;
            text-decoration: none;
        }
        .btn:hover {
            background-color: #e6ebf1;
            background-image: linear-gradient(-180deg, #e6ebf1, #d1d8e0 90%);
            border-color: rgba(27,31,35,0.35);
        }
    </style>
</head>
<body>
    <h1>📸 Screenshot Manager</h1>
    
    <p><strong>Screenshot Manager</strong> est une application complète qui vous permet de capturer des captures d'écran de sites web à partir d'une liste d'URLs, avec une interface graphique élégante ou une interface en ligne de commande.</p>
    
    <div class="info">
        <p><strong>💡 Note:</strong> Cette application extrait automatiquement les URLs d'un fichier texte et capture des captures d'écran de chaque site web.</p>
    </div>
    
    <h2>✨ Fonctionnalités</h2>
    
    <div class="feature-list">
        <ul>
            <li>📸 <strong>Capture automatique</strong> des sites web à partir d'une liste d'URLs</li>
            <li>⚡ <strong>Multithreading</strong> pour des captures rapides et efficaces</li>
            <li>🎨 <strong>Interface graphique</strong> moderne et intuitive (PyQt6)</li>
            <li>⌨️ <strong>Interface en ligne de commande</strong> pour l'automatisation</li>
            <li>📊 <strong>Barre de progression</strong> en temps réel avec affichage des résultats</li>
            <li>🔍 <strong>Recherche</strong> par nom de domaine dans l'interface graphique</li>
            <li>🔄 <strong>Navigation</strong> entre les captures avec boutons Précédent/Suivant</li>
            <li>🔍 <strong>Zoom</strong> avant/arrière sur les images</li>
            <li>🗑️ <strong>Suppression</strong> des captures individuelles</li>
            <li>📤 <strong>Export</strong> en ZIP ou PDF</li>
            <li>📚 <strong>Historique</strong> des scans avec statistiques</li>
            <li>⚙️ <strong>Configuration</strong> sauvegardée automatiquement</li>
            <li>🖥️ <strong>Mode plein écran</strong> pour la visualisation</li>
            <li>🔗 <strong>Liens cliquables</strong> vers les sites capturés</li>
        </ul>
    </div>
    
    <h2>📥 Installation</h2>
    
    <h3>Prérequis</h3>
    <ul>
        <li>Python 3.8 ou supérieur</li>
        <li>Pip (gestionnaire de paquets Python)</li>
    </ul>
    
    <h3>Installation des dépendances</h3>
    <pre><code>pip install PyQt6 playwright reportlab</code></pre>
    
    <h3>Installation de Chromium pour Playwright</h3>
    <pre><code>playwright install chromium</code></pre>
    
    <div class="success">
        <p><strong>✅ Installation terminée!</strong> L'application est maintenant prête à l'emploi.</p>
    </div>
    
    <h2>🚀 Utilisation</h2>
    
    <h3>Interface Graphique</h3>
    <pre><code>python screenshot_manager.py</code></pre>
    
    <h4>Utilisation de base :</h4>
    <ol>
        <li>Cliquez sur <strong>"📁 Select URLs File"</strong> et choisissez votre fichier texte contenant les URLs</li>
        <li>(Optionnel) Cliquez sur <strong>"📂 Output Folder"</strong> pour choisir le dossier de destination</li>
        <li>Cliquez sur <strong>"▶️ Start Scan"</strong> pour démarrer la capture</li>
        <li>Les captures apparaissent en temps réel dans la liste de gauche</li>
        <li>Cliquez sur une miniature pour l'afficher en grand à droite</li>
    </ol>
    
    <h3>Interface en Ligne de Commande</h3>
    <pre><code>python screenshot_cli.py -i urls.txt -o captures -t 5 --quality 85</code></pre>
    
    <h4>Options disponibles :</h4>
    <table>
        <thead>
            <tr>
                <th>Option</th>
                <th>Description</th>
                <th>Valeur par défaut</th>
            </tr>
        </thead>
        <tbody>
            <tr>
                <td><code>-i, --input</code></td>
                <td>Fichier d'entrée contenant les URLs</td>
                <td>Requis</td>
            </tr>
            <tr>
                <td><code>-o, --output</code></td>
                <td>Dossier de sortie pour les captures</td>
                <td>screenshots</td>
            </tr>
            <tr>
                <td><code>-t, --threads</code></td>
                <td>Nombre de threads pour le traitement</td>
                <td>4</td>
            </tr>
            <tr>
                <td><code>--quality</code></td>
                <td>Qualité JPEG (1-100)</td>
                <td>85</td>
            </tr>
            <tr>
                <td><code>--timeout</code></td>
                <td>Timeout de page en ms</td>
                <td>15000</td>
            </tr>
            <tr>
                <td><code>--history</code></td>
                <td>Afficher l'historique des scans</td>
                <td>False</td>
            </tr>
            <tr>
                <td><code>--export</code></td>
                <td>Exporter les images en ZIP</td>
                <td>False</td>
            </tr>
            <tr>
                <td><code>--list</code></td>
                <td>Lister les images capturées</td>
                <td>False</td>
            </tr>
        </tbody>
    </table>
    
    <h4>Exemples d'utilisation CLI :</h4>
    <pre><code># Capture de base
python screenshot_cli.py -i urls.txt

# Capture avec paramètres personnalisés
python screenshot_cli.py -i urls.txt -o mes_captures -t 6 --quality 90

# Voir l'historique
python screenshot_cli.py --history

# Exporter en ZIP
python screenshot_cli.py --export archive.zip

# Lister les images
python screenshot_cli.py --list</code></pre>
    
    <h2>📦 Compilation en Exécutable (.exe)</h2>
    
    <h3>Installation de PyInstaller</h3>
    <pre><code>pip install pyinstaller</code></pre>
    
    <h3>Compilation</h3>
    <pre><code>pyinstaller --onefile --windowed screenshot_manager.py</code></pre>
    
    <div class="info">
        <p><strong>📁 Résultat:</strong> L'exécutable sera créé dans le dossier <code>dist/</code></p>
    </div>
    
    <h2>⌨️ Raccourcis Clavier (Interface Graphique)</h2>
    
    <table>
        <thead>
            <tr>
                <th>Raccourci</th>
                <th>Action</th>
            </tr>
        </thead>
        <tbody>
            <tr>
                <td><code>Ctrl+F</code></td>
                <td>Focus sur la barre de recherche</td>
            </tr>
            <tr>
                <td><code>F11</code></td>
                <td>Mode plein écran</td>
            </tr>
            <tr>
                <td><code>Ctrl++</code></td>
                <td>Zoom avant</td>
            </tr>
            <tr>
                <td><code>Ctrl+-</code></td>
                <td>Zoom arrière</td>
            </tr>
            <tr>
                <td><code>Ctrl+0</code></td>
                <td>Réinitialiser le zoom</td>
            </tr>
            <tr>
                <td><code>Flèches ← →</code></td>
                <td>Navigation entre images</td>
            </tr>
            <tr>
                <td><code>Suppr</code></td>
                <td>Supprimer l'image courante</td>
            </tr>
            <tr>
                <td><code>Ctrl+S</code></td>
                <td>Sauvegarder la configuration</td>
            </tr>
        </tbody>
    </table>
    
    <h2>🔧 Configuration</h2>
    
    <p>L'application sauvegarde automatiquement la configuration dans le registre Windows (ou fichiers système sous Linux/Mac) :</p>
    <ul>
        <li>Position et taille de la fenêtre</li>
        <li>État de la barre d'outils</li>
        <li>Dossier de sortie par défaut</li>
        <li>Paramètres utilisateur</li>
    </ul>
    
    <h2>🛡️ Sécurité</h2>
    
    <div class="warning">
        <p><strong>⚠️ Avertissement:</strong> Cette application utilise Playwright pour contrôler un navigateur Chromium. Assurez-vous que les URLs que vous capturez proviennent de sources fiables.</p>
    </div>
    
    <ul>
        <li>Blocage automatique des ressources lourdes (vidéos, audio)</li>
        <li>Navigation en mode headless (sans interface visible)</li>
        <li>Timeout configurable pour éviter les blocages</li>
        <li>Pas de téléchargement de fichiers pendant la capture</li>
    </ul>
    
    <h2>🤝 Contribution</h2>
    
    <p>Les contributions sont les bienvenues ! Voici comment contribuer :</p>
    <ol>
        <li>Fork le projet</li>
        <li>Créez une branche pour votre fonctionnalité (<code>git checkout -b feature/AmazingFeature</code>)</li>
        <li>Committez vos changements (<code>git commit -m 'Add some AmazingFeature'</code>)</li>
        <li>Poussez vers la branche (<code>git push origin feature/AmazingFeature</code>)</li>
        <li>Ouvrez une Pull Request</li>
    </ol>
    
    <h2>📄 Licence</h2>
    
    <p>Distribué sous la licence MIT. Voir le fichier <code>LICENSE</code> pour plus d'informations.</p>
    
    <h2>📧 Support</h2>
    
    <p>Pour signaler un bug ou demander une fonctionnalité, veuillez ouvrir une <a href="https://github.com/votre-username/screenshot-manager/issues">issue</a>.</p>
    
    <h2>🌟 Merci d'utiliser Screenshot Manager !</h2>
    
    <p>Si vous trouvez cette application utile, n'hésitez pas à ⭐️ l'ajouter à vos favoris sur GitHub !</p>
    
    <div class="center">
        <a href="#" class="btn">⭐️ Star on GitHub</a>
        <a href="#" class="btn">🐛 Report Issue</a>
        <a href="#" class="btn">📥 Download Latest</a>
    </div>
</body>
</html>