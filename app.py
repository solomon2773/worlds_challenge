import asyncio
import json
import os
import ssl
import threading

import websockets
from flask import Flask, jsonify, render_template, request
from flask_basicauth import BasicAuth
from flask_socketio import SocketIO, emit, join_room, leave_room

from database import db, save_detection_to_db
from example_mutation import (
    create_detection_event,
    create_event_producer,
    run_all_mutations,
)
from example_queries import fetch_devices, run_all_examples

app = Flask(__name__)
app.config["BASIC_AUTH_USERNAME"] = "WorldsIO"
app.config["BASIC_AUTH_PASSWORD"] = "LetMe!n@2025!!!"
basic_auth = BasicAuth(app)
socketio = SocketIO(app, cors_allowed_origins="*")

# Store results globally
query_results = {}
mutation_results = {}

# WebSocket connection storage
active_connections = {}
websocket_connections = {}  # Store actual WebSocket connections for cleanup


def run_queries_background():
    """Run queries in background and store results."""
    global query_results
    try:
        results = run_all_examples()
        query_results = results
        print("Queries completed successfully")
    except Exception as e:
        query_results = {"error": str(e)}
        print(f"Error running queries: {e}")


def run_mutations_background():
    """Run mutations in background and store results."""
    global mutation_results
    try:
        results = run_all_mutations()
        mutation_results = results
        print("Mutations completed successfully")
    except Exception as e:
        mutation_results = {"error": str(e)}
        print(f"Error running mutations: {e}")


@app.route("/")
@basic_auth.required
def index():
    return render_template("index.html")


@app.route("/api/run-queries", methods=["POST"])
def run_queries():
    """Execute example queries and return results."""
    global query_results
    query_results = {}  # Clear previous results

    # Run queries in background thread
    thread = threading.Thread(target=run_queries_background)
    thread.daemon = True
    thread.start()

    return jsonify(
        {"status": "started", "message": "Queries are running in background"}
    )


@app.route("/api/query-results")
def get_query_results():
    """Get the latest query results."""
    return jsonify(query_results)


@app.route("/api/devices")
def get_devices():
    """Get list of available devices."""
    try:
        devices = fetch_devices()
        if devices:
            return jsonify({"devices": devices})
        else:
            return jsonify({"devices": [], "error": "No devices found"})
    except Exception as e:
        return jsonify({"devices": [], "error": str(e)})


@app.route("/api/run-mutations", methods=["POST"])
def run_mutations():
    """Execute example mutations and return results."""
    global mutation_results
    mutation_results = {}  # Clear previous results

    # Run mutations in background thread
    thread = threading.Thread(target=run_mutations_background)
    thread.daemon = True
    thread.start()

    return jsonify(
        {"status": "started", "message": "Mutations are running in background"}
    )


@app.route("/api/mutation-results")
def get_mutation_results():
    """Get the latest mutation results."""
    return jsonify(mutation_results)


@app.route("/api/database/stats")
def get_database_stats():
    """Get database statistics."""
    try:
        stats = db.get_database_stats()
        return jsonify(stats)
    except Exception as e:
        return jsonify({"error": str(e)})


@app.route("/api/database/detection-stats")
def get_detection_stats():
    """Get detection statistics."""
    try:
        device_id = request.args.get("device_id")
        hours = int(request.args.get("hours", 24))
        stats = db.get_detection_stats(device_id, hours)
        return jsonify(stats)
    except Exception as e:
        return jsonify({"error": str(e)})


@app.route("/api/database/recent-detections")
def get_recent_detections():
    """Get recent detections."""
    try:
        device_id = request.args.get("device_id")
        limit = int(request.args.get("limit", 100))
        detections = db.get_recent_detections(limit, device_id)
        return jsonify(detections)
    except Exception as e:
        return jsonify({"error": str(e)})


@app.route("/api/database/detections-by-time")
def get_detections_by_time():
    """Get detections within time range."""
    try:
        start_time = request.args.get("start_time")
        end_time = request.args.get("end_time")
        device_id = request.args.get("device_id")

        if not start_time or not end_time:
            return jsonify({"error": "start_time and end_time are required"})

        detections = db.get_detections_by_time_range(start_time, end_time, device_id)
        return jsonify(detections)
    except Exception as e:
        return jsonify({"error": str(e)})


@app.route("/api/database/tags")
def get_all_tags():
    """Get all unique tags with their statistics."""
    try:
        tags = db.get_all_tags()
        return jsonify(tags)
    except Exception as e:
        return jsonify({"error": str(e)})


@app.route("/api/database/longest-tracks-per-tag")
def get_longest_tracks_per_tag():
    """Get the longest track for each tag."""
    try:
        tracks = db.get_longest_track_per_tag()
        return jsonify(tracks)
    except Exception as e:
        return jsonify({"error": str(e)})


@socketio.on("connect")
def handle_connect():
    print("Client connected")


@socketio.on("disconnect")
def handle_disconnect():
    print("Client disconnected")


@socketio.on("join_device")
def handle_join_device(data):
    device_id = data.get("device_id")
    if device_id:
        join_room(f"device_{device_id}")
        print(f"Client joined device room: {device_id}")

        # Start WebSocket subscription for this device
        start_device_subscription(device_id)


@socketio.on("leave_device")
def handle_leave_device(data):
    device_id = data.get("device_id")
    if device_id:
        leave_room(f"device_{device_id}")
        print(f"Client left device room: {device_id}")

        # Stop WebSocket subscription if no more clients
        stop_device_subscription(device_id)


def start_device_subscription(device_id):
    """Start GraphQL WebSocket subscription for a device."""
    if device_id in active_connections:
        return  # Already subscribed

    def subscription_worker():
        asyncio.run(device_subscription_loop(device_id))

    thread = threading.Thread(target=subscription_worker)
    thread.daemon = True
    thread.start()
    active_connections[device_id] = thread


def stop_device_subscription(device_id):
    """Stop GraphQL WebSocket subscription for a device."""
    if device_id in active_connections:
        del active_connections[device_id]
        print(f"[{device_id}] Stopped subscription thread")

    # Close the WebSocket connection if it exists
    if device_id in websocket_connections:
        try:
            websocket_connections[device_id].close()
            del websocket_connections[device_id]
            print(f"[{device_id}] Closed WebSocket connection")
        except Exception as e:
            print(f"[{device_id}] Error closing WebSocket: {e}")


async def device_subscription_loop(device_id):
    ssl_context = ssl._create_unverified_context()
    GRAPHQL_WS_ENDPOINT = os.getenv("GRAPHQL_WS_ENDPOINT")
    GRAPHQL_TOKEN_ID = os.getenv("GRAPHQL_TOKEN_ID")
    GRAPHQL_TOKEN_VALUE = os.getenv("GRAPHQL_TOKEN_VALUE")

    if not GRAPHQL_TOKEN_ID or not GRAPHQL_TOKEN_VALUE:
        raise ValueError(
            "GRAPHQL_TOKEN_ID and GRAPHQL_TOKEN_VALUE environment variables must be set"
        )

    subscription_id = f"sub_{device_id}"

    subscription_query = """
    subscription OnDeviceDetection($deviceId: ID!) {
      detectionActivity(filter: { dataSourceId: { eq: $deviceId }}) {
        track {
            id
            dataSource {
                name
            }
            tag
            video {
                url
                thumbnailUrl
                displayName
                resolutionHeight
                resolutionWidth
                dataSource {
                    id
                    name
                    type
                    device {
                        name
                    }
                }
            }
            detections {
                timestamp
                metadata
                createdAt
                updatedAt
                direction
                geofenceIds
                zoneIds
                globalTrackId
                deviceId
                tag
                polygon {
                    type
                    coordinates
                }
                position {
                    type
                    coordinates
                }
            }
        }
        timestamp
        direction
        position { 
            type
            coordinates 
            }
        polygon {
            type
            coordinates
        }
      }
    }
    """

    try:
        async with websockets.connect(
            GRAPHQL_WS_ENDPOINT,
            subprotocols=["graphql-transport-ws"],
            additional_headers={
                "x-token-id": GRAPHQL_TOKEN_ID,
                "x-token-value": GRAPHQL_TOKEN_VALUE,
            },
            ssl=ssl_context,
        ) as ws:
            # Store the WebSocket connection for cleanup
            websocket_connections[device_id] = ws
            # 1. connection_init
            await ws.send(
                json.dumps(
                    {
                        "type": "connection_init",
                        "payload": {
                            "x-token-id": GRAPHQL_TOKEN_ID,
                            "x-token-value": GRAPHQL_TOKEN_VALUE,
                        },  # can also include auth here if required
                    }
                )
            )
            print(f"[{device_id}] Sent connection_init")

            # 2. wait for ack
            while True:
                resp = json.loads(await ws.recv())
                print("Server ->", resp)
                if resp.get("type") == "connection_ack":
                    break

            # 3. send subscription
            await ws.send(
                json.dumps(
                    {
                        "id": subscription_id,
                        "type": "subscribe",
                        "payload": {
                            "query": subscription_query,
                            "variables": {"deviceId": device_id},
                        },
                    }
                )
            )
            print(f"[{device_id}] Subscription started")

            # Emit connection status to frontend
            socketio.emit(
                "connection_status",
                {"status": "connected", "device_id": device_id},
                room=f"device_{device_id}",
            )

            # 4. listen for data
            while device_id in active_connections:
                try:
                    raw = await ws.recv()
                    msg = json.loads(raw)

                    if msg.get("type") == "next":
                        print(f"[{device_id}] Data:", msg["payload"]["data"])
                        # Emit data to frontend via Socket.IO
                        detection_data = msg["payload"]["data"].get("detectionActivity")
                        if detection_data:
                            # Save to database
                            save_detection_to_db(detection_data, device_id)
                            # Emit to frontend
                            socketio.emit(
                                "detection_data",
                                detection_data,
                                room=f"device_{device_id}",
                            )

                    elif msg.get("type") == "error":
                        print(f"[{device_id}] Error:", msg)
                        break

                    elif msg.get("type") == "complete":
                        print(f"[{device_id}] Subscription complete")
                        break

                    elif msg.get("type") == "ping":
                        await ws.send(json.dumps({"type": "pong"}))

                except websockets.exceptions.ConnectionClosed:
                    print(f"[{device_id}] WebSocket connection closed")
                    break
                except Exception as e:
                    print(f"[{device_id}] Error in message loop: {e}")
                    break

    except Exception as e:
        print(f"[{device_id}] Subscription error: {e}")
    finally:
        # Clean up the connection
        if device_id in active_connections:
            del active_connections[device_id]
        if device_id in websocket_connections:
            del websocket_connections[device_id]
        print(f"[{device_id}] Subscription cleanup completed")


if __name__ == "__main__":
    socketio.run(app, host="0.0.0.0", port=5001, debug=True, allow_unsafe_werkzeug=True)
