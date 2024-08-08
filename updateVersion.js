const fs = require('fs');
const path = require('path');

// Función para actualizar el JSON
function updateJsonFile(filePath, version) {
  const json = JSON.parse(fs.readFileSync(filePath, 'utf8'));
  json.version = version;
  fs.writeFileSync(filePath, JSON.stringify(json, null, 2), 'utf8');
}

// Obtiene la nueva versión desde la línea de comando
const newVersion = process.argv[2];

if (!newVersion) {
  console.log('Please provide a version number.');
  process.exit(1);
}

// Rutas a los archivos
const packageJsonPath = path.join(__dirname, 'package.json');
const versionJsonPath = path.join(__dirname, 'version.json');

// Actualiza ambos archivos
updateJsonFile(packageJsonPath, newVersion);
updateJsonFile(versionJsonPath, newVersion);

console.log(`Version updated to ${newVersion} in both package.json and version.json`);