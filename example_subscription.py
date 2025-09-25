import asyncio
import json
import os
import websockets
import ssl

async def device_subscription_loop(device_id):
    ssl_context = ssl._create_unverified_context()
    GRAPHQL_WS_ENDPOINT = os.getenv("GRAPHQL_WS_ENDPOINT")
    GRAPHQL_TOKEN_ID = os.getenv("GRAPHQL_TOKEN_ID")
    GRAPHQL_TOKEN_VALUE = os.getenv("GRAPHQL_TOKEN_VALUE")
    
    if not GRAPHQL_TOKEN_ID or not GRAPHQL_TOKEN_VALUE:
        raise ValueError("GRAPHQL_TOKEN_ID and GRAPHQL_TOKEN_VALUE environment variables must be set")

    subscription_id = f"sub_{device_id}"

    subscription_query = """
    subscription OnDeviceDetection($deviceId: ID!) {
      detectionActivity(filter: { dataSourceId: { eq: $deviceId }}) {
        track {  tag }
        timestamp
        position { coordinates }
      }
    }
    """

    try:
        async with websockets.connect(
            GRAPHQL_WS_ENDPOINT,
            subprotocols=["graphql-transport-ws"],
            extra_headers={
                "x-token-id": GRAPHQL_TOKEN_ID,
                "x-token-value": GRAPHQL_TOKEN_VALUE,
            },
            ssl=ssl_context,
        ) as ws:
            # 1. connection_init
            await ws.send(json.dumps({
                "type": "connection_init",
                "payload": { 
                    "x-token-id": GRAPHQL_TOKEN_ID,
                "x-token-value": GRAPHQL_TOKEN_VALUE,
                }  # can also include auth here if required
            }))
            print(f"[{device_id}] Sent connection_init")
  
            # 2. wait for ack
            while True:
                resp = json.loads(await ws.recv())
                print("Server ->", resp)
                if resp.get("type") == "connection_ack":
                    break

            # 3. send subscription
            await ws.send(json.dumps({
                "id": subscription_id,
                "type": "subscribe",
                "payload": {
                    "query": subscription_query,
                    "variables": {"deviceId": device_id}
                }
            }))
            print(f"[{device_id}] Subscription started")

            # 4. listen for data
            while True:
                raw = await ws.recv()
                msg = json.loads(raw)

                if msg.get("type") == "next":
                    print(f"[{device_id}] Data:", msg["payload"]["data"])

                elif msg.get("type") == "error":
                    print(f"[{device_id}] Error:", msg)
                    break

                elif msg.get("type") == "complete":
                    print(f"[{device_id}] Subscription complete")
                    break

                elif msg.get("type") == "ping":
                    await ws.send(json.dumps({"type": "pong"}))

    except Exception as e:
        print(f"[{device_id}] Subscription error: {e}")

if __name__ == "__main__":
    asyncio.run(device_subscription_loop("4d5239e2-1c7a-4f12-a889-2554e61472ec"))
