// Publicador MQTT do ESP32 para o broker Mosquitto no Raspberry Pi.
//
// A cada leitura: conecta ao broker, publica e desconecta. Cada publicacao
// vira uma sessao TCP completa (SYN ... FIN), como num sensor a bateria que
// acorda, publica e dorme. Com conexao persistente, o flowmeter.py veria um
// fluxo a cada 120 s (ACTIVE_TIMEOUT) e 30 minutos dariam uns 15 fluxos.
//
// Placa "esp32" (Espressif) e biblioteca PubSubClient (Nick O'Leary).
// Nome e senha do Wi-Fi ficam em segredos.h, que nao vai para o repositorio.

#include <WiFi.h>
#include <PubSubClient.h>

#include "segredos.h"

const char *BROKER_IP = "192.168.18.123";  // IP do Raspberry Pi
const uint16_t BROKER_PORTA = 1883;
const char *TOPICO = "lab/esp32/telemetria";
const unsigned long INTERVALO_MS = 5000;

WiFiClient rede;
PubSubClient mqtt(rede);
unsigned long enviadas = 0;

void conectarWifi() {
  if (WiFi.status() == WL_CONNECTED) return;
  Serial.print("Conectando ao Wi-Fi");
  WiFi.mode(WIFI_STA);
  WiFi.begin(WIFI_SSID, WIFI_SENHA);
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  Serial.print("\nWi-Fi conectado. IP do ESP32: ");
  Serial.println(WiFi.localIP());
}

void setup() {
  Serial.begin(115200);
  conectarWifi();
  mqtt.setServer(BROKER_IP, BROKER_PORTA);
}

void loop() {
  conectarWifi();

  // Leitura sintetica: o valor nao muda o resultado, so o padrao de trafego.
  float temperatura = 24.0 + random(0, 50) / 10.0;
  float umidade = 55.0 + random(0, 100) / 10.0;
  char msg[80];
  snprintf(msg, sizeof(msg), "{\"n\":%lu,\"temp\":%.1f,\"umid\":%.1f}",
           enviadas, temperatura, umidade);

  if (mqtt.connect("esp32-sensor")) {
    mqtt.publish(TOPICO, msg);
    mqtt.disconnect();
    enviadas++;
    Serial.printf("Publicado: %s\n", msg);
  } else {
    // Codigos do PubSubClient: -2 = broker inalcancavel (IP errado, Mosquitto
    // parado ou porta fechada); 5 = broker recusou (falta allow_anonymous).
    Serial.printf("Falha ao conectar no broker (estado %d)\n", mqtt.state());
  }

  delay(INTERVALO_MS);
}
