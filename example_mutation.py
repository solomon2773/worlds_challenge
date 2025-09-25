import requests
import json
import os
from datetime import datetime, timedelta

# Configuration
GRAPHQL_HTTP_ENDPOINT = os.getenv("GRAPHQL_HTTP_ENDPOINT")
GRAPHQL_TOKEN_ID = os.getenv("GRAPHQL_TOKEN_ID")
GRAPHQL_TOKEN_VALUE = os.getenv("GRAPHQL_TOKEN_VALUE")
EVENT_PRODUCER_ID = os.getenv("EVENT_PRODUCER_ID")
NAME_OF_THE_EVENT = os.getenv("NAME_OF_THE_EVENT")

if not GRAPHQL_TOKEN_ID or not GRAPHQL_TOKEN_VALUE:
    raise ValueError("GRAPHQL_TOKEN_ID and GRAPHQL_TOKEN_VALUE environment variables must be set")
if not EVENT_PRODUCER_ID:
    raise ValueError("EVENT_PRODUCER_ID environment variable must be set")


def run_query(query, variables=None):
    """Function to run a GraphQL query or mutation."""
    try:
        headers = {
            'X-Token-Id': GRAPHQL_TOKEN_ID,
            'X-Token-Value': GRAPHQL_TOKEN_VALUE,
            'Content-Type': 'application/json'
        }
        response = requests.post(GRAPHQL_HTTP_ENDPOINT, json={'query': query, 'variables': variables}, headers=headers)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"HTTP Request failed: {e}")
        return None

def create_event_producer():
    """Create a custom event producer with metadata."""
    print("--- Creating Event Producer ---")
    
    # Generate timestamp for unique event name
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    mutation = f"""
    mutation CreateHiIAmHereEvent {{
        createEventProducer(
            eventProducer: {{ 
              name: "Custom Event_{timestamp}", 
              description: "i am here!!", 
              active: true,
              metadata:{{
                name : "Solomon Tsao"
                style : "Free Style"
                todo:"Jump into the water. GoGoGo!!!"
              }}
            }}
        ) {{
            id
            name
            metadata
            active
            description
        }}
    }}
    """
    
    result = run_query(mutation)
    
    if result and 'data' in result:
        event_producer = result['data']['createEventProducer']
        print("Event Producer created successfully:")
        print(json.dumps(event_producer, indent=2))
        return event_producer
    else:
        print("Failed to create event producer:")
        if result and 'errors' in result:
            print(json.dumps(result['errors'], indent=2))
        return None

def create_detection_event(track_id, tag, confidence=None):
    """Create an event based on detection criteria."""
    print(f"--- Creating Detection Event for Track {track_id} ---")
    
    mutation = """
    mutation CreateDetectionEvent($input: CreateEventInput!) {
        createEvent(event: $input) {
            id
            type
            subType
            startTime
            endTime
            draft
            metadata
            eventProducer {
                id
                name
            }
        }
    }
    """
    
    # Create event based on detection criteria
    event_metadata = {
        "name": "Solomon Tsao",
        "trackId": track_id,
        "tag": tag,
        "detectedAt": datetime.now().isoformat() + "Z",
        "confidence": confidence or "high",
        "detector": NAME_OF_THE_EVENT,
        "action": "Detection Alert"
    }
    
    # Determine event type based on tag
    if tag.lower() == "person":
        event_type = "PersonDetection"
        sub_type = "SecurityAlert"
        event_metadata["priority"] = "high"
        event_metadata["description"] = f"Person Solomon Tsao detected on track {track_id}"
    elif tag.lower() == "vehicle":
        event_type = "VehicleDetection"
        sub_type = "TrafficAlert"
        event_metadata["priority"] = "medium"
        event_metadata["description"] = f"Solomon's Ford Raptor detected on track {track_id}"
    else:
        event_type = "ObjectDetection"
        sub_type = "GeneralAlert"
        event_metadata["priority"] = "low"
        event_metadata["description"] = f"Special object '{tag}' detected on track {track_id}"
    
    variables = {
        "input": {
            "eventProducerId": EVENT_PRODUCER_ID,
            "type": event_type,
            "subType": sub_type,
            "startTime": datetime.now().isoformat() + "Z",
            "endTime": (datetime.now() + timedelta(minutes=5)).isoformat() + "Z",
            "draft": False,
            "metadata": event_metadata
        }
    }
    
    result = run_query(mutation, variables)
    
    if result and 'data' in result:
        event = result['data']['createEvent']
        print("Event created successfully:")
        print(json.dumps(event, indent=2))
        return event
    else:
        print("Failed to create event:")
        if result and 'errors' in result:
            print(json.dumps(result['errors'], indent=2))
        return None

def create_high_confidence_event(track_id, confidence_threshold=0.8):
    """Create an event for high confidence detections."""
    print(f"--- Creating High Confidence Event for Track {track_id} ---")
    
    mutation = """
    mutation CreateHighConfidenceEvent($input: CreateEventInput!) {
        createEvent(event: $input) {
            id
            type
            subType
            startTime
            endTime
            draft
            metadata
        }
    }
    """
    
    variables = {
        "input": {
            "eventProducerId": EVENT_PRODUCER_ID,
            "type": "HighConfidenceDetection",
            "subType": "QualityAlert",
            "startTime": datetime.now().isoformat() + "Z",
            "endTime": (datetime.now() + timedelta(minutes=10)).isoformat() + "Z",
            "draft": False,
            "metadata": {
                "trackId": track_id,
                "confidenceThreshold": confidence_threshold,
                "detector": NAME_OF_THE_EVENT,
                "description": f"High confidence detection (>{confidence_threshold}) on track {track_id}",
                "priority": "high",
                "requiresReview": True
            }
        }
    }
    
    result = run_query(mutation, variables)
    
    if result and 'data' in result:
        event = result['data']['createEvent']
        print("High confidence event created successfully:")
        print(json.dumps(event, indent=2))
        return event
    else:
        print("Failed to create high confidence event:")
        if result and 'errors' in result:
            print(json.dumps(result['errors'], indent=2))
        return None

def create_zone_violation_event(track_id, zone_ids, violation_type="entry"):
    """Create an event for zone violations."""
    print(f"--- Creating Zone Violation Event for Track {track_id} ---")
    
    mutation = """
    mutation CreateZoneViolationEvent($input: CreateEventInput!) {
        createEvent(event: $input) {
            id
            type
            subType
            startTime
            endTime
            draft
            metadata
        }
    }
    """
    
    variables = {
        "input": {
            "eventProducerId": EVENT_PRODUCER_ID,
            "type": "ZoneViolation",
            "subType": f"Zone{violation_type.title()}Alert",
            "startTime": datetime.now().isoformat() + "Z",
            "endTime": (datetime.now() + timedelta(minutes=15)).isoformat() + "Z",
            "draft": False,
            "metadata": {
                "trackId": track_id,
                "zoneIds": zone_ids,
                "violationType": violation_type,
                "detector": NAME_OF_THE_EVENT,
                "description": f"Zone {violation_type} violation on track {track_id}",
                "priority": "high",
                "requiresImmediateAction": True,
                "affectedZones": len(zone_ids)
            }
        }
    }
    
    result = run_query(mutation, variables)
    
    if result and 'data' in result:
        event = result['data']['createEvent']
        print("Zone violation event created successfully:")
        print(json.dumps(event, indent=2))
        return event
    else:
        print("Failed to create zone violation event:")
        if result and 'errors' in result:
            print(json.dumps(result['errors'], indent=2))
        return None

def run_all_mutations():
    """Run all example mutations."""
    print("=== GraphQL Mutation Examples ===\n")
    
    # 1. Create event producer
    event_producer = create_event_producer()
    
    # 2. Create detection events based on different criteria
    print("\n" + "="*50)
    detection_event = create_detection_event("track_123", "CatchMeIfYouCan", 0.95)
    
    print("\n" + "="*50)
    vehicle_event = create_detection_event("track_456", "vehicle", 0.87)
    
    print("\n" + "="*50)
    object_event = create_detection_event("track_789", "bicycle", 0.72)
    
    # 3. Create high confidence event
    print("\n" + "="*50)
    high_conf_event = create_high_confidence_event("track_999", 0.9)
    
    # 4. Create zone violation event
    print("\n" + "="*50)
    zone_event = create_zone_violation_event("track_555", ["zone_1", "zone_2"], "entry")
    

    
    return {
        'event_producer': event_producer,
        'detection_events': [detection_event, vehicle_event, object_event],
        'high_confidence_event': high_conf_event,
        'zone_violation_event': zone_event,
    }

if __name__ == "__main__":
    # Run examples when executed directly
    run_all_mutations()
