# Importing the external libraries.
from flask import Flask, request, jsonify
from flask_script import Manager
from flask_migrate import Migrate
import threading
import requests
import uuid
import time

# Importing all needed modules.
from cerber import SecurityManager
from schemas import MetricsSchema
from config import ConfigManager

NER_SERVICE_DATA = {}
INTENT_SERVICE_DATA = {}
SENTIMENT_SERVICE_DATA = {}
SEQUENCE2SEQUENCE_SERVICE_DATA = {}

# Loading the configuration from the configuration file.
config = ConfigManager("config.ini")

# Creation of the metrics validation schema object.
metrics_schema = MetricsSchema()

# Creation of the Security Manager.
security_manager = SecurityManager(config.security.secret_key)

# Creating the security manager for the service discovery.
service_discovery_security_manager = SecurityManager(config.service_discovery.secret_key)

# Computing the HMAC for Service Discovery registration.
SERVICE_DISCOVERY_HMAC = service_discovery_security_manager._SecurityManager__encode_hmac(
    config.generate_info_for_service_discovery()
)


def control(service_name, endpoint):
    payload = {
        "code" : str(uuid.uuid4())
    }
    if service_name == "intent-service":
        host = INTENT_SERVICE_DATA["host"]
        port = INTENT_SERVICE_DATA["port"]
        hmac = INTENT_SERVICE_DATA["security"]._ServiceManager__encode_hmac(payload)
    elif service_name == "named-entity-recognition-service":
        host = NER_SERVICE_DATA["host"]
        port = NER_SERVICE_DATA["port"]
        hmac = NER_SERVICE_DATA["security"]._ServiceManager__encode_hmac(payload)
    elif service_name == "sentiment-service":
        host = SENTIMENT_SERVICE_DATA["host"]
        port = SENTIMENT_SERVICE_DATA["port"]
        hmac = SENTIMENT_SERVICE_DATA["security"]._ServiceManager__encode_hmac(payload)
    elif service_name == "sequence2sequence-service":
        host = SEQUENCE2SEQUENCE_SERVICE_DATA["host"]
        port = SEQUENCE2SEQUENCE_SERVICE_DATA["port"]
        hmac = SEQUENCE2SEQUENCE_SERVICE_DATA["security"]._ServiceManager__encode_hmac(payload)
    url = f"http://{host}:{port}/{endpoint}"
    res = requests.post(url, json = payload, headers = {"Token" : hmac})


def send_heartbeats():
    '''
        This function sends heartbeat requests to the service discovery.
    '''
    # Getting the Service discovery hmac for message.
    service_discovery_hmac = service_discovery_security_manager._SecurityManager__encode_hmac({"status_code" : 200})
    while True:
        # Senting the request.
        response = requests.post(
            f"http://{config.service_discovery.host}:{config.service_discovery.port}/heartbeat/{config.general.name}",
            json = {"status_code" : 200},
            headers = {"Token" : service_discovery_hmac}
        )
        # Making a pause of 30 seconds before sending the next request.
        status_code = response.status_code
        time.sleep(30)

# Generating the registration credentials for Service Discovery.
credentials_for_service_discovery = config.generate_info_for_service_discovery()

# Computing the HMAC for the registration request.
service_discovery_hmac = SecurityManager(config.service_discovery.secret_key)._SecurityManager__encode_hmac(credentials_for_service_discovery)


while True:
    # Sending the request to the Service Discovery until a successful response.
    res = requests.post(
        f"http://{config.service_discovery.host}:{config.service_discovery.port}/{config.service_discovery.register_endpoint}",
        json=credentials_for_service_discovery,
        headers={"Token" : service_discovery_hmac}
    )
    if res.status_code == 200:
        while True:
            # In case of a successful registration the service is asking for needed services credentials.
            time.sleep(3)

            # Computing the request HMAC.
            service_discovery_hmac = SecurityManager(config.service_discovery.secret_key)._SecurityManager__encode_hmac(
                {"service_names" : ["named-entity-recognition-sidecar-service", "intent-sidecar-service", "sentiment-sidecar-service", "sequence2sequence-sidecar-service"]}
            )
            # Sending the request.
            res = requests.get(
                f"http://{config.service_discovery.host}:{config.service_discovery.port}/get_services",
                json = {"service_names" : ["named-entity-recognition-sidecar-service", "intent-sidecar-service", "sentiment-sidecar-service", "sequence2sequence-sidecar-service"]},
                headers={"Token" : service_discovery_hmac}
            )
            if res.status_code == 200:
                # In case of the successful request the process of sending heartbeat requests is starting.
                time.sleep(5)
                threading.Thread(target=send_heartbeats).start()
                res_json = res.json()

                # Extracting the credentials of the Named Entity Recognition Service.
                NER_SERVICE_DATA = {
                    "host" : res_json["named-entity-recognition-sidecar-service"]["host"],
                    "port" : res_json["named-entity-recognition-sidecar-service"]["port"],
                    "security" : SecurityManager(res_json["named-entity-recognition-sidecar-service"]["security"]["secret_key"])
                }

                # Extracting the credentials of the Intent Service.
                INTENT_SERVICE_DATA = {
                    "host" : res_json["intent-sidecar-service"]["host"],
                    "port" : res_json["intent-sidecar-service"]["port"],
                    "security" : SecurityManager(res_json["intent-sidecar-service"]["security"]["secret_key"])
                }

                # Extracting the credentials of the Sentiment Service.
                SENTIMENT_SERVICE_DATA = {
                    "host" : res_json["sentiment-sidecar-service"]["host"],
                    "port" : res_json["sentiment-sidecar-service"]["port"],
                    "security" : SecurityManager(res_json["sentiment-sidecar-service"]["security"]["secret_key"])
                }

                # Extracting the credentials of the Sequence to Sequence service.
                SEQUENCE2SENQUENCE_SERVICE_DATA = {
                    "host" : res_json["sequence2sequence-sidecar-service"]["host"],
                    "port" : res_json["sequence2sequence-sidecar-service"]["port"],
                    "security" : SecurityManager(res_json["sequence2sequence-sidecar-service"]["security"]["secret_key"])
                }

# Setting up the Flask dependencies.
app = Flask(__name__)

@app.route("/metrics", methods=["POST"])
def metrics():
    # Checking the access token.
    check_response = security_manager.check_request(request)
    if check_response != "OK":
        return check_response, check_response["code"]
    else:
        status_code = 200

        # Validation of the json.
        result, status_code = metrics_schema.validate_json(request.json)
        if status_code != 200:
            # If the request body didn't passed the json validation a error is returned.
            return result, status_code
        else:
            # Extraction metrics.
            queue_waiting_time = result["latency"]["queue_waiting_time"]
            lock_time = result["latency"]["lock_time"]
            waiting_queue_length = result["saturation"]["waiting_queue_length"]
            thread_capacity = result["saturation"]["thread_capacity"]
            cpu_utilization = result["saturation"]["cpu_utilization"]
            ram_utilization = result["saturation"]["ram_utilization"]

            # Comparing the metrics to the set thresholds.
            if queue_waiting_time > 5:
                endpoint = "decrease"
            elif cpu_utilization > 80:
                endpoint = "decrease"
            elif ram_utilization > 80:
                endpoint = "decrease"
            elif lock_time > 5:
                endpoint = "decrease"
            elif thread_capacity > 0.9:
                endpoint = "increase"
            elif waiting_queue_length > 3:
                endpoint = "increase"
            control(result["service_name"], endpoint)
            return {
                "code" : 200,
                "message" : "Success"
            }, 200

# Running the main flask module.
if __name__ == "__main__":
    app.run(
        #port=config.general.port,
        port=config.general.port,
        #host=config.general.host
        host=config.general.host
    )