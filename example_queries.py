import requests
import json
import os
from datetime import datetime, timedelta

# Configuration
GRAPHQL_HTTP_ENDPOINT = os.getenv("GRAPHQL_HTTP_ENDPOINT")
GRAPHQL_TOKEN_ID = os.getenv("GRAPHQL_TOKEN_ID")
GRAPHQL_TOKEN_VALUE = os.getenv("GRAPHQL_TOKEN_VALUE")

if not GRAPHQL_TOKEN_ID or not GRAPHQL_TOKEN_VALUE:
    raise ValueError("GRAPHQL_TOKEN_ID and GRAPHQL_TOKEN_VALUE environment variables must be set")

def run_query(query, variables=None):
    """Function to run a GraphQL query or mutation."""
    try:
        headers = {
            'X-Token-Id': GRAPHQL_TOKEN_ID,
            'X-Token-Value': GRAPHQL_TOKEN_VALUE,
        }
        response = requests.post(GRAPHQL_HTTP_ENDPOINT, json={'query': query, 'variables': variables}, headers=headers)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"HTTP Request failed: {e}")
        return None

def fetch_devices():
    """Fetches device information."""
    print("--- Fetching Devices ---")
    query = """
    query GetDevices {
     devices(first: 100, sort: { direction: ASC, field: ID }) {
        edges {
            cursor
            node {
                id
                uuid
                externalId
                name
                enabled
                address
                frameRate
                position {
                    type
                    coordinates
                }
                site {
                    id
                    name
                }
            }
        }
        pageInfo {
            hasNextPage
            hasPreviousPage
            startCursor
            endCursor
        }
    }
    }
    """
    result = run_query(query)

    if result and 'data' in result:
        devices = [edge['node'] for edge in result['data']['devices']['edges']]
        print(f"Found {len(devices)} devices:")
        for device in devices:
            status = 'Enabled' if device.get('enabled', False) else 'Disabled'
            print(f"Device ID: {device['id']}, Name: {device.get('name', 'N/A')}, Status: {status}")
        return devices
    return None

def fetch_tracks_detailed():
    """Fetches detailed track information with detections."""
    print("--- Fetching Detailed Tracks ---")
    query = """
    query GetDetailedTracks {
     tracks(
        filter: { time: { between: ["2025-09-22T12:00:00Z", "2025-09-22T15:00:00Z"] } }

    ) {
        edges {
            node {
                id
                tag
                startTime
                endTime
                video {
                    id
                    dataSource {
                        name
                        id
                        device {
                            id
                            uuid
                            name
                            site {
                                id
                                name
                            }
                        }
                        type
                    }
                    thumbnailUrl
                    url
                    resolutionWidth
                    resolutionHeight
                    frameRate
                }
                detections {
                    timestamp
                    position {
                        coordinates
                    }
                }
                dataSource {
                    id
                    name
                    type
                    device {
                        id
                        uuid
                        externalId
                        name
                        enabled
                        address
                        frameRate
                        site {
                            id
                            name
                        }
                    }
                }
            }
            cursor
        }
        pageInfo {
            hasNextPage
            hasPreviousPage
            startCursor
            endCursor
        }
    }
    }
    """
    result = run_query(query)

    if result and 'data' in result:
        tracks = [edge['node'] for edge in result['data']['tracks']['edges']]
        print(f"Found {len(tracks)} tracks:")
        for track in tracks:
            detection_count = len(track.get('detections', []))
            data_source = track.get('dataSource', {})
            device = data_source.get('device', {})
            print(f"Track ID: {track['id']}, Tag: {track['tag']}, Device: {device.get('name', 'N/A')}, Detections: {detection_count}")
        return tracks
    return None

def fetch_detections_by_time_range():
    """Fetches detections within a specific time range."""
    print("--- Fetching Detections by Time Range ---")
    query = """
    query GetDetectionsByTimeRange($start: DateTimeOffset!, $end: DateTimeOffset!) {
       detections(
       filter: { time: { between: [$start, $end] } }
       sort: { field: DETECTION_TIME, direction: ASC }
       ) {
        edges {
            node {
                direction
                createdAt
                updatedAt
                timestamp
                track {
                    id
                    startTime
                    endTime
                    metadata
                    dataSource {
                        id
                        name
                        type
                        device {
                            id
                            uuid
                            name
                            address
                            frameRate
                            site {
                                name
                            }
                        }
                        zones {
                            id
                            name
                        }
                    }
                }
            }
        }
    }
    }
    """
    variables = {
        "start": (datetime.now() - timedelta(hours=12)).isoformat() + "Z",
        "end": datetime.now().isoformat() + "Z"
    }
    result = run_query(query, variables)
    if result and 'data' in result:
        detections = [edge['node'] for edge in result['data']['detections']['edges']]
        print(f"Found {len(detections)} detections :")
        for detection in detections:
            track = detection.get('track', {})
            data_source = track.get('dataSource', {})
            device = data_source.get('device', {})
            print(f"Detection Time: {detection['timestamp']}, Track: {track.get('id', 'N/A')}, Device: {device.get('name', 'N/A')}, Site: {device.get('site', {}).get('name', 'N/A')}")
        return detections
    return None

def fetch_detections_by_tag(tag_filter="person"):
    """Fetches detections filtered by tag."""
    print(f"--- Fetching Detections for Tag: {tag_filter} ---")
    query = """
    query GetDetectionsByTag($tag: String!) {
      detections(
        first: 30
        filter: {
          track: {
            tag: {
              eq: $tag
            }
          }
        }
        sort: [{field: TIMESTAMP, direction: DESC}]
      ) {
        edges {
          node {
            id
            timestamp
            position {
              coordinates
            }
            confidence
            track {
              id
              tag
              startTime
            }
            device {
              id
              name
            }
          }
        }
      }
    }
    """
    variables = {"tag": tag_filter}
    result = run_query(query, variables)
    if result and 'data' in result:
        detections = [edge['node'] for edge in result['data']['detections']['edges']]
        print(f"Found {len(detections)} detections for tag '{tag_filter}':")
        for detection in detections:
            track = detection.get('track', {})
            device = detection.get('device', {})
            coords = detection.get('position', {}).get('coordinates', [])
            print(f"Detection ID: {detection['id']}, Track: {track.get('id', 'N/A')}, Device: {device.get('name', 'N/A')}, Position: {coords}, Confidence: {detection.get('confidence', 'N/A')}")
        return detections
    return None

def run_all_examples():
    """Runs all example queries."""
    print("=== GraphQL Query Examples ===\n")
    
    # Fetch devices
    devices_data = fetch_devices()
    
    # Fetch detailed tracks
    tracks_detailed = fetch_tracks_detailed()
    
    # Fetch detections by time range
    detections_time = fetch_detections_by_time_range()
    
    # Fetch detections by tag
    detections_person = fetch_detections_by_tag("person")
    
    return {
        'devices': devices_data,
        'tracks': tracks_detailed,
        'detections_time': detections_time,
        'detections_person': detections_person
    }

if __name__ == "__main__":
    # Run examples when executed directly
    run_all_examples()
