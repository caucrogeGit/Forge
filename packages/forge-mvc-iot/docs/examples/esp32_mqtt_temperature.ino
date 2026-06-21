/*
 * esp32_mqtt_temperature.ino — Exemple Forge IoT (IOT-ESP32-EXAMPLE-001)
 *
 * Publie une mesure de température conforme au contrat MQTT Forge IoT :
 *
 *   topic   : forge/atelier/esp32-001/telemetry
 *   payload : {"kind":"temperature","value":22.4,"unit":"°C",
 *              "timestamp":"2026-05-29T10:00:00Z"}
 *
 * Le timestamp est obtenu via NTP (heure UTC, suffixe Z). La mesure est
 * ici simulée (valeur fixe) pour garder le code lisible : remplace
 * readTemperature() par la lecture d'un vrai capteur.
 *
 * Dépendances Arduino (à installer via le gestionnaire de bibliothèques) :
 *   - WiFi (intégrée au coeur ESP32)
 *   - PubSubClient (Nick O'Leary)
 *
 * À ADAPTER : WIFI_SSID, WIFI_PASSWORD, MQTT_HOST (voir ci-dessous).
 *
 * Hors périmètre : pas de TLS/auth MQTT, pas de gestion Wi-Fi avancée,
 * cible ESP32 uniquement (pas Arduino R4).
 */

#include <WiFi.h>
#include <PubSubClient.h>
#include <time.h>

// ─── Paramètres À ADAPTER ───────────────────────────────────────────────────

const char* WIFI_SSID     = "CHANGE_ME";   // nom de ton réseau Wi-Fi
const char* WIFI_PASSWORD = "CHANGE_ME";   // mot de passe Wi-Fi

// Adresse IP du poste qui fait tourner Mosquitto (PAS "localhost" :
// l'ESP32 n'est pas sur la même machine). Exemple : 192.168.1.222.
const char* MQTT_HOST = "192.168.1.222";
const int   MQTT_PORT = 1883;

// ─── Contrat Forge IoT (ne pas changer la structure) ────────────────────────

// forge/{site}/{device_id}/telemetry
const char* MQTT_TOPIC     = "forge/atelier/esp32-001/telemetry";
const char* MQTT_CLIENT_ID = "esp32-001";

// NTP en UTC (offset 0) pour produire un timestamp ISO 8601 suffixe Z.
const char* NTP_SERVER = "pool.ntp.org";

// Intervalle entre deux publications (millisecondes).
const unsigned long PUBLISH_INTERVAL_MS = 5000;

WiFiClient   wifiClient;
PubSubClient mqtt(wifiClient);

// ─── Connexions ──────────────────────────────────────────────────────────────

void connectWifi() {
  Serial.printf("Connexion Wi-Fi a %s ...\n", WIFI_SSID);
  WiFi.mode(WIFI_STA);
  WiFi.begin(WIFI_SSID, WIFI_PASSWORD);
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  Serial.printf("\nWi-Fi OK, IP = %s\n", WiFi.localIP().toString().c_str());
}

void connectMqtt() {
  while (!mqtt.connected()) {
    Serial.printf("Connexion MQTT a %s:%d ...\n", MQTT_HOST, MQTT_PORT);
    if (mqtt.connect(MQTT_CLIENT_ID)) {
      Serial.println("MQTT OK");
    } else {
      Serial.printf("Echec MQTT (rc=%d), nouvel essai dans 2 s\n", mqtt.state());
      delay(2000);
    }
  }
}

// ─── Horodatage UTC ISO 8601 (suffixe Z) ─────────────────────────────────────

String isoTimestampUtc() {
  struct tm timeinfo;
  if (!getLocalTime(&timeinfo)) {
    // NTP pas encore synchronise : valeur de repli (le message restera
    // conforme au format, mais l'heure ne sera pas juste).
    return String("1970-01-01T00:00:00Z");
  }
  char buf[25];
  strftime(buf, sizeof(buf), "%Y-%m-%dT%H:%M:%SZ", &timeinfo);
  return String(buf);
}

// ─── Mesure (a remplacer par un vrai capteur) ────────────────────────────────

float readTemperature() {
  // TODO: lire un capteur reel (DHT22, DS18B20, ...).
  return 22.4;
}

// ─── Cycle de vie Arduino ────────────────────────────────────────────────────

void setup() {
  Serial.begin(115200);
  delay(100);
  connectWifi();
  configTime(0, 0, NTP_SERVER);   // 0,0 = UTC
  mqtt.setServer(MQTT_HOST, MQTT_PORT);
}

void loop() {
  if (!mqtt.connected()) {
    connectMqtt();
  }
  mqtt.loop();

  float value = readTemperature();
  String timestamp = isoTimestampUtc();

  // Payload JSON conforme au contrat Forge IoT.
  char payload[192];
  snprintf(
    payload, sizeof(payload),
    "{\"kind\":\"temperature\",\"value\":%.1f,\"unit\":\"\xC2\xB0""C\",\"timestamp\":\"%s\"}",
    value, timestamp.c_str()
  );

  if (mqtt.publish(MQTT_TOPIC, payload)) {
    Serial.printf("Publie sur %s : %s\n", MQTT_TOPIC, payload);
  } else {
    Serial.println("Echec de publication");
  }

  delay(PUBLISH_INTERVAL_MS);
}
