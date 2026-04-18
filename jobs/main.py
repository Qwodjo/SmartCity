import os
import random
import uuid
from confluent_kafka import SerializingProducer
import simplejson as json
from datetime import datetime, timedelta
import time  


# These represent real-world GPS coordinates for London and Birmingham, UK
LONDON_COORDINATES = {"latitude": 51.5074, "longitude": -0.1278}
BIRMINGHAM_COORDINATES = {"latitude": 52.4862, "longitude": -1.8904}

# Calculate the step size for smooth vehicle movement
# We divide the total distance by 100 so the vehicle moves 1% closer to Birmingham with each data point
# This creates 100 intermediate points between the two cities for smooth simulation
LATITUDE_INCREMENT = (BIRMINGHAM_COORDINATES["latitude"] - LONDON_COORDINATES["latitude"]) / 100
LONGITUDE_INCREMENT = (BIRMINGHAM_COORDINATES["longitude"] - LONDON_COORDINATES["longitude"]) / 100


# KAFKA CONFIGURATION: Define where and what data to send to Kafka
# These environment variables tell the producer where to find Kafka and which topics to use
# In production, these values are set via environment variables (e.g., in Docker containers)
# If not set, they default to local development values
KAFKA_BOOTSTRAP_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")
VEHICLE_TOPIC = os.getenv("VEHICLE_TOPIC", "vehicle_data")
GPS_TOPIC = os.getenv("GPS_TOPIC", "gps_data")
TRAFFIC_TOPIC = os.getenv("TRAFFIC_TOPIC", "traffic_data")
WEATHER_TOPIC = os.getenv("WEATHER_TOPIC", "weather_data")
EMERGENCY_TOPIC = os.getenv("EMERGENCY_TOPIC", "emergency_data")




random.seed(42)  # For reproducibility of random data
start_time = datetime.now()
start_location = LONDON_COORDINATES.copy()



 # Advance simulated time by random interval (30-60 seconds) for realistic pacing
def get_next_time():
    global start_time
    start_time += timedelta(seconds=random.randint(30, 60))
    return start_time



#generate GPS data with realistic speed and direction, simulating a vehicle's movement towards Birmingham
def generate_gps_data(device_id, timestamp, vehicle_type="private"):
    return {
        "id": uuid.uuid4(),
        "deviceId": device_id,
        "timestamp": timestamp,
        "speed": random.uniform(0, 40),
        "direction": "North-East",
        "vehicleType": vehicle_type
    }

#generate weather data based on the vehicle's location, simulating changing conditions as it moves towards Birmingham
def generate_traffic_camera_data(device_id, timestamp, camera_id, location):
    return {
        "id": uuid.uuid4(),
        "deviceId": device_id,
        "timestamp": timestamp,
        "location": location,
        "cameraId": camera_id,
        "snapshot": "Base64EncodedString" # Placeholder for actual image data
    }


#generate weather data based on the vehicle's location, simulating changing conditions as it moves towards Birmingham
def generate_weather_data(device_id, timestamp, location):
    return {
        "id": uuid.uuid4(),
        "deviceId": device_id,
        "timestamp": timestamp,
        "location": location,
        "temperature": random.uniform(-5, 26),
        "weatherConditions": random.choice(["Sunny", "Cloudy", "Rainy", "snowy"]),
        "precipitation": random.uniform(0, 25),
        "windSpeed": random.uniform(0, 100),
        "humidity": random.uniform(0, 100),  #percentage
        "airQualityIndex": random.randint(0, 500) # AQI scale 

         }


#generate emergency incident data with varying types and severities, simulating potential incidents that could occur during the journey
def generate_emergency_data(device_id, timestamp, location):
    return {
        "id": uuid.uuid4(),
        "deviceId": device_id,
        "incidentId": uuid.uuid4(),
        "timestamp": timestamp,
        "location": location,
        "incidentType": random.choice(["Accident", "Fire", "Medical", "Police", "None"]),
        "status": random.choice(["Active", "Resolved"]),
        "description": "Simulated emergency incident for testing purposes."

        }


# Move vehicle towards Birmingham and add GPS noise for realism
def simulate_vihicle_movement():
    global start_location

    start_location["latitude"] += LATITUDE_INCREMENT
    start_location["longitude"] += LONGITUDE_INCREMENT

    start_location["latitude"] += random.uniform(-0.0005, 0.0005)
    start_location["longitude"] += random.uniform(-0.0005, 0.0005)

    return start_location





# Create a vehicle telemetry record with location, speed, and vehicle details
def generate_vehicle_data(device_id):
    location = simulate_vihicle_movement()

    return {
        "id": uuid.uuid4(),
        "deviceId": device_id,
        "timestamp": get_next_time().isoformat(),
        "location": (location["latitude"], location["longitude"]),
        "speed": random.uniform(10, 40),
        "direction": "North-East",
        "make": "Tesla",
        "model": "Model 3",
        "year": 2020,
        "fuelType": "Electric"


    }

def json_serializer(obj):
    if isinstance(obj, uuid.UUID):
        return str(obj)
    raise TypeError(f"object of type {obj.__class__.__name__} is not JSON serializable")



def delivery_report(err, msg):
    if err is not None:
        print(f"Delivery failed for record: {err}")
    else:
        print(f"Message delivered to {msg.topic()} [{msg.partition()}])")


def produce_data_to_kafka(producer, topic, data):
    producer.produce(
        topic,
        key=str(data["id"]),
        value=json.dumps(data, default=json_serializer).encode("utf-8"),
        on_delivery=delivery_report
        )
    producer.flush()  # Ensure the message is sent before proceeding
    

# Generate and output vehicle data points (TODO: send to Kafka)
def simulate_journey(producer, device_id):
    while True:
        vehicle_data = generate_vehicle_data(device_id)
        gps_data = generate_gps_data(device_id, vehicle_data["timestamp"])
        traffic_camera_data = generate_traffic_camera_data(device_id, vehicle_data["timestamp"], camera_id="cam-5678", location=vehicle_data["location"])
        weather_data = generate_weather_data(device_id, vehicle_data["timestamp"], vehicle_data["location"])
        emergency_incident_data = generate_emergency_data(device_id, vehicle_data["timestamp"], vehicle_data["location"])
        


        if vehicle_data["location"][0] >= BIRMINGHAM_COORDINATES["latitude"] and vehicle_data["location"][1] >= BIRMINGHAM_COORDINATES["longitude"]:
            print("Vehicle has reached Birmingham. Ending simulation.")
            break

        produce_data_to_kafka(producer, VEHICLE_TOPIC, vehicle_data)
        produce_data_to_kafka(producer, GPS_TOPIC, gps_data)
        produce_data_to_kafka(producer, TRAFFIC_TOPIC, traffic_camera_data)
        produce_data_to_kafka(producer, WEATHER_TOPIC, weather_data)
        produce_data_to_kafka(producer, EMERGENCY_TOPIC, emergency_incident_data)   

        time.sleep(5)  # Simulate time delay between data points










 # Initialize Kafka producer, run simulation, and handle errors gracefully
if __name__ == "__main__":

    producer_config = {
        "bootstrap.servers": KAFKA_BOOTSTRAP_SERVERS,
        "error_cb": lambda err: print(f"Kafka error: {err}")
    }
    producer = SerializingProducer(producer_config)

    try:
        simulate_journey(producer, "vehicle-1234")

    except KeyboardInterrupt:
        print("Simulation interrupted by user.")
    except Exception as e:
        print(f"An error occurred during simulation: {e}")