# scripts/main.py

import os
import time
from camera_capture import capture_image
from inference import run_inference
from mqtt_handler import MQTTHandler
from logger_setup import setup_logger

logger = setup_logger()

MODEL_PATH = os.path.abspath("model/rpi4-blokjes.eim")
IMAGE_PATH = os.path.abspath("images/captured_image.jpg")
SAVE_PATH = os.path.abspath("debug")

CONFIDENCE_THRESHOLD = 0.7

def handle_detection_trigger(payload):
    logger.info("MQTT-trigger ontvangen: %s", payload)

    try:
        max_retries = 5
        retry_count = 0
        label = "onbekend"
        confidence = 0.0

        while retry_count < max_retries:
            try:
                capture_image(IMAGE_PATH, camera_index=0)
                result = run_inference(MODEL_PATH, IMAGE_PATH, save_path=SAVE_PATH)
                logger.info("Inference resultaat: %s", result)

                label = result.get("highest_label", "onbekend")
                confidence = result.get("highest_confidence", 0.0)

                logger.info("Poging %d: %s (confidence: %.2f)", retry_count + 1, label, confidence)

                if confidence >= CONFIDENCE_THRESHOLD:
                    logger.info("Detectie boven drempel (%s, %.2f)", label, confidence)
                    break
                else:
                    logger.warning("Confidence te laag (%.2f), opnieuw proberen...", confidence)
                    retry_count += 1
                    time.sleep(1)

            except Exception as inner_error:
                logger.error("Fout tijdens poging %d: %s", retry_count + 1, inner_error)
                retry_count += 1
                time.sleep(1)

        if confidence < CONFIDENCE_THRESHOLD:
            logger.warning("Geen betrouwbare detectie na %d pogingen, label = 'onbekend'", max_retries)
            label = "onbekend"

        mqtt.publish_detectie_resultaat(label)

    except Exception as outer_error:
        logger.critical("Fout in detectieproces: %s", outer_error)

if __name__ == "__main__":
    mqtt = MQTTHandler(config_path="config/config.ini", on_trigger=handle_detection_trigger, logger=logger)
    mqtt.start()
    logger.info("Systeem gestart. Wacht op MQTT-trigger...")

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        logger.info("Programma afgesloten door gebruiker.")
