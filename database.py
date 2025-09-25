import json
import sqlite3
from typing import Dict, List, Optional


class DetectionDatabase:
    """SQLite database for storing real-time detection data."""

    def __init__(self, db_path: str = "detections.db"):
        self.db_path = db_path
        self.init_database()

    def init_database(self):
        """Initialize the database with required tables."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Create detections table
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS detections (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                device_id TEXT NOT NULL,
                track_id TEXT,
                tag TEXT,
                timestamp DATETIME NOT NULL,
                direction TEXT,
                position_type TEXT,
                position_coordinates TEXT,  -- JSON string
                polygon_type TEXT,
                polygon_coordinates TEXT,  -- JSON string
                geofence_ids TEXT,         -- JSON string
                zone_ids TEXT,             -- JSON string
                global_track_id TEXT,
                device_name TEXT,
                metadata TEXT,             -- JSON string
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """
        )

        # Create tracks table
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS tracks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                track_id TEXT UNIQUE NOT NULL,
                device_id TEXT NOT NULL,
                tag TEXT,
                data_source_name TEXT,
                video_url TEXT,
                video_thumbnail_url TEXT,
                video_display_name TEXT,
                video_resolution_height INTEGER,
                video_resolution_width INTEGER,
                video_frame_rate REAL,
                video_data_source_id TEXT,
                video_data_source_name TEXT,
                video_data_source_type TEXT,
                video_device_name TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """
        )

        # Create devices table
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS devices (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                device_id TEXT UNIQUE NOT NULL,
                device_name TEXT,
                device_address TEXT,
                enabled BOOLEAN,
                frame_rate REAL,
                position_type TEXT,
                position_coordinates TEXT,  -- JSON string
                site_id TEXT,
                site_name TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """
        )

        # Create indexes for better query performance
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_detections_device_id ON detections(device_id)"
        )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_detections_timestamp ON detections(timestamp)"
        )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_detections_track_id ON detections(track_id)"
        )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_detections_tag ON detections(tag)"
        )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_tracks_device_id ON tracks(device_id)"
        )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_devices_device_id ON devices(device_id)"
        )

        conn.commit()
        conn.close()
        print(f"Database initialized at {self.db_path}")

    def insert_detection(self, detection_data: Dict) -> bool:
        """Insert a single detection record."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # Extract data from detection activity
            track = detection_data.get("track") or {}
            position = detection_data.get("position") or {}
            polygon = detection_data.get("polygon") or {}

            # Get device info from track video data
            video = track.get("video") or {}
            video_data_source = video.get("dataSource") or {}
            device_info = video_data_source.get("device") or {}

            # Get first detection for additional info
            detections = track.get("detections") or []
            first_detection = detections[0] if detections else {}

            insert_data = (
                detection_data.get("device_id", "unknown"),
                track.get("id"),
                track.get("tag"),
                detection_data.get("timestamp"),
                detection_data.get("direction"),
                position.get("type"),
                json.dumps(position.get("coordinates", [])),
                polygon.get("type"),
                json.dumps(polygon.get("coordinates", [])),
                json.dumps(first_detection.get("geofenceIds", [])),
                json.dumps(first_detection.get("zoneIds", [])),
                first_detection.get("globalTrackId"),
                device_info.get("name"),
                json.dumps(first_detection.get("metadata", {})),
            )
            cursor.execute(
                """
                INSERT INTO detections (
                    device_id, track_id, tag, timestamp, direction,
                    position_type, position_coordinates, polygon_type, polygon_coordinates,
                    geofence_ids, zone_ids, global_track_id, device_name, metadata
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
                insert_data,
            )

            conn.commit()
            conn.close()
            return True

        except Exception as e:
            print(f"Error inserting detection: {e}")
            return False

    def insert_track(self, track_data: Dict, device_id: str) -> bool:
        """Insert or update track information."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            video = track_data.get("video") or {}
            video_data_source = video.get("dataSource") or {}
            device_info = video_data_source.get("device") or {}

            cursor.execute(
                """
                INSERT OR REPLACE INTO tracks (
                    track_id, device_id, tag, data_source_name,
                    video_url, video_thumbnail_url, video_display_name,
                    video_resolution_height, video_resolution_width, video_frame_rate,
                    video_data_source_id, video_data_source_name, video_data_source_type,
                    video_device_name, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            """,
                (
                    track_data.get("id"),
                    device_id,
                    track_data.get("tag"),
                    track_data.get("dataSource", {}).get("name"),
                    video.get("url"),
                    video.get("thumbnailUrl"),
                    video.get("displayName"),
                    video.get("resolutionHeight"),
                    video.get("resolutionWidth"),
                    video.get("frameRate"),
                    video_data_source.get("id"),
                    video_data_source.get("name"),
                    video_data_source.get("type"),
                    device_info.get("name"),
                ),
            )

            conn.commit()
            conn.close()
            return True

        except Exception as e:
            print(f"Error inserting track: {e}")
            return False

    def insert_device(self, device_data: Dict) -> bool:
        """Insert or update device information."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            site = device_data.get("site") or {}
            position = device_data.get("position") or {}

            cursor.execute(
                """
                INSERT OR REPLACE INTO devices (
                    device_id, device_name, device_address, enabled, frame_rate,
                    position_type, position_coordinates, site_id, site_name, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            """,
                (
                    device_data.get("id"),
                    device_data.get("name"),
                    device_data.get("address"),
                    device_data.get("enabled"),
                    device_data.get("frameRate"),
                    position.get("type"),
                    json.dumps(position.get("coordinates", [])),
                    site.get("id"),
                    site.get("name"),
                ),
            )

            conn.commit()
            conn.close()
            return True

        except Exception as e:
            print(f"Error inserting device: {e}")
            return False

    def get_detection_stats(
        self, device_id: Optional[str] = None, hours: int = 24
    ) -> Dict:
        """Get detection statistics for a device or all devices."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Base query
        base_query = """
            SELECT 
                COUNT(*) as total_detections,
                COUNT(DISTINCT track_id) as unique_tracks,
                COUNT(DISTINCT tag) as unique_tags,
                device_id,
                device_name
            FROM detections 
            WHERE timestamp >= datetime('now', '-{} hours')
        """.format(
            hours
        )

        if device_id:
            base_query += " AND device_id = ?"
            cursor.execute(base_query, (device_id,))
        else:
            base_query += " GROUP BY device_id, device_name"
            cursor.execute(base_query)

        results = cursor.fetchall()
        conn.close()

        if device_id and results:
            return {
                "total_detections": results[0][0],
                "unique_tracks": results[0][1],
                "unique_tags": results[0][2],
                "device_id": results[0][3],
                "device_name": results[0][4],
            }
        else:
            return [
                {
                    "total_detections": row[0],
                    "unique_tracks": row[1],
                    "unique_tags": row[2],
                    "device_id": row[3],
                    "device_name": row[4],
                }
                for row in results
            ]

    def get_detections_by_time_range(
        self, start_time: str, end_time: str, device_id: Optional[str] = None
    ) -> List[Dict]:
        """Get detections within a time range."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        query = """
            SELECT * FROM detections 
            WHERE timestamp BETWEEN ? AND ?
        """
        params = [start_time, end_time]

        if device_id:
            query += " AND device_id = ?"
            params.append(device_id)

        query += " ORDER BY timestamp DESC"

        cursor.execute(query, params)
        columns = [description[0] for description in cursor.description]
        results = [dict(zip(columns, row)) for row in cursor.fetchall()]

        conn.close()
        return results

    def get_recent_detections(
        self, limit: int = 100, device_id: Optional[str] = None
    ) -> List[Dict]:
        """Get recent detections."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        query = """
            SELECT * FROM detections
        """
        params = []

        if device_id:
            query += " WHERE device_id = ?"
            params.append(device_id)

        query += " ORDER BY timestamp DESC LIMIT ?"
        params.append(limit)

        cursor.execute(query, params)
        columns = [description[0] for description in cursor.description]
        results = [dict(zip(columns, row)) for row in cursor.fetchall()]

        conn.close()
        return results

    def get_database_stats(self) -> Dict:
        """Get overall database statistics."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Get counts
        cursor.execute("SELECT COUNT(*) FROM detections")
        detection_count = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM tracks")
        track_count = cursor.fetchone()[0]

        # Get latest detection
        cursor.execute("SELECT MAX(timestamp) FROM detections")
        latest_detection = cursor.fetchone()[0]

        # Get oldest detection
        cursor.execute("SELECT MIN(timestamp) FROM detections")
        oldest_detection = cursor.fetchone()[0]

        conn.close()

        return {
            "total_detections": detection_count,
            "total_tracks": track_count,
            "latest_detection": latest_detection,
            "oldest_detection": oldest_detection,
        }

    def get_all_tags(self) -> List[Dict]:
        """Get all unique tags from the database with their counts."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT 
                tag,
                COUNT(*) as detection_count,
                COUNT(DISTINCT track_id) as track_count,
                COUNT(DISTINCT device_id) as device_count
            FROM detections 
            WHERE tag IS NOT NULL AND tag != ''
            GROUP BY tag
            ORDER BY detection_count DESC
        """
        )

        columns = [description[0] for description in cursor.description]
        results = [dict(zip(columns, row)) for row in cursor.fetchall()]

        conn.close()
        return results

    def get_longest_track_per_tag(self) -> List[Dict]:
        """Get the longest track for each tag based on detection count."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute(
            """
            WITH track_durations AS (
                SELECT 
                    track_id,
                    tag,
                    device_id,
                    device_name,
                    COUNT(*) as detection_count,
                    MIN(timestamp) as first_detection,
                    MAX(timestamp) as last_detection,
                    (julianday(MAX(timestamp)) - julianday(MIN(timestamp))) * 24 * 60 * 60 as duration_seconds
                FROM detections 
                WHERE tag IS NOT NULL AND tag != ''
                GROUP BY track_id, tag, device_id, device_name
            ),
            ranked_tracks AS (
                SELECT 
                    *,
                    ROW_NUMBER() OVER (PARTITION BY tag ORDER BY detection_count DESC, duration_seconds DESC) as rank
                FROM track_durations
            )
            SELECT 
                tag,
                track_id,
                device_id,
                device_name,
                detection_count,
                first_detection,
                last_detection,
                duration_seconds
            FROM ranked_tracks 
            WHERE rank = 1
            ORDER BY detection_count DESC
        """
        )

        columns = [description[0] for description in cursor.description]
        results = [dict(zip(columns, row)) for row in cursor.fetchall()]

        conn.close()
        return results


# Global database instance
db = DetectionDatabase()


def save_detection_to_db(detection_data: Dict, device_id: str) -> bool:
    """Save detection data to the database."""
    # Add device_id to detection data
    detection_data["device_id"] = device_id

    # Insert detection
    detection_result = db.insert_detection(detection_data)

    # Insert track info if available
    track = detection_data.get("track", {})
    track_result = True
    if track:
        track_result = db.insert_track(track, device_id)

    return detection_result and track_result
